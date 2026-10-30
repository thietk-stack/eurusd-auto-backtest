#!/usr/bin/env python3
"""Causal HTF four-touch zones + H1 engulfing. No indicators or synthetic prices.

4 predeclared families: H4/D1 x same-role/role-flip.
One global trade at a time, <=1 entry/week, >=1.5 net projected RR, <=0.5% equity stop risk.
Historical Dukascopy H1 bars are validated by portfolio_research.load_prices().
"""
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from portfolio_research import load_prices, SYMBOLS, PIPS

INITIAL=1000.0
RISK=.005
MAX_LEVERAGE=5.0
MIN_RR=1.5
GROSS_TARGET_R=2.0
SLIP_EACH_PIPS=.1
STOP_BUFFER_PIPS=1.5
TP_BUFFER_PIPS=1.0
MAX_HOLD_H1=96
MODELS=("H4_same","H4_flip","D1_same","D1_flip")
WINDOWS=(("validation","2021-01-01","2023-01-01"),
         ("holdout","2023-01-01","2026-10-30"))
CFG={
 "H4":dict(freq="4h",min_count=3,left=2,right=2,min_gap=6,
           history=240,age_hours=24*24,width_pips=6),
 "D1":dict(freq="1D",min_count=16,left=2,right=2,min_gap=3,
           history=220,age_hours=24*55,width_pips=10)
}

def htfcandles(d,tf):
    cfg=CFG[tf];r=d.resample(cfg["freq"],label="right",closed="left")
    x=pd.DataFrame(dict(open=r.open.first(),high=r.high.max(),low=r.low.min(),
                        close=r.close.last(),bars=r.close.count()))
    x=x[x.bars>=cfg["min_count"]].dropna()
    return x

def build_zones(d,tf,mode,pip):
    x=htfcandles(d,tf);cfg=CFG[tf]
    lo=x.low.to_numpy(float);hi=x.high.to_numpy(float)
    cl=x.close.to_numpy(float)
    width_med=pd.Series(hi-lo).rolling(40,min_periods=20).median().to_numpy()
    n=len(x);pivots=[]
    left=cfg["left"];right=cfg["right"]
    for p in range(40,n-right):
        lowpivot=(lo[p]<min(lo[p-left:p]) and lo[p]<=min(lo[p+1:p+right+1]))
        highpivot=(hi[p]>max(hi[p-left:p]) and hi[p]>=max(hi[p+1:p+right+1]))
        amp=width_med[p+right]
        if not np.isfinite(amp) or amp<=0:continue
        if lowpivot and max(cl[p+1:p+right+1])-lo[p]>=.65*amp:
            pivots.append((p+right,p,"support",lo[p]))
        if highpivot and hi[p]-min(cl[p+1:p+right+1])>=.65*amp:
            pivots.append((p+right,p,"resistance",hi[p]))
    pivots.sort(key=lambda z:(z[0],z[1]))
    events=[];recent=[]
    for conf,p,role,price in pivots:
        recent=[v for v in recent if p-v[1]<=cfg["history"]]
        recent.append((conf,p,role,price))
        half_width=max(cfg["width_pips"]*pip,.32*width_med[conf])
        near=[v for v in recent if abs(v[3]-price)<=half_width]
        # Sample from newest pivot back: touches separated by minimum HTF bars.
        isolated=[]
        for item in reversed(near):
            if all(abs(item[1]-old[1])>=cfg["min_gap"] for old in isolated):
                isolated.append(item)
        isolated.reverse()
        if mode=="same":
            isolated=[v for v in isolated if v[2]==role]
            qualified=len(isolated)>=4
        elif mode=="flip":
            roles=[v[2] for v in isolated]
            qualified=len(isolated)>=4 and "support" in roles and "resistance" in roles
        else:
            raise ValueError(mode)
        if not qualified:continue
        # Zone is activated only after the last pivot's right-side confirmation closes.
        # Timestamp for HTF close equals its right-label (known then, not before).
        events.append(dict(available=x.index[conf],center=float(np.median([v[3] for v in isolated])),
                    half_width=float(half_width),role=role,touches=len(isolated),
                    confirmed_pivot_time=x.index[p],tf=tf))
    return events,dict(htf_bars=len(x),confirmed_pivots=len(pivots),qualified_zone_events=len(events))

def build_all(index,price):
    output={};diagnostics={}
    for symbol in SYMBOLS:
        d=price[symbol];pip=PIPS[symbol]
        o=d.open.to_numpy(float);cl=d.close.to_numpy(float)
        hi=d.high.to_numpy(float);lo=d.low.to_numpy(float)
        # Classical BODY engulfing; signal on H1 candle j that just completed.
        # Bull: prior bearish, new bullish, current body fully engulfs previous body.
        bull=(cl>o)&(np.r_[False,cl[:-1]<o[:-1]])&(
             o<=np.r_[np.nan,cl[:-1]])&(cl>=np.r_[np.nan,o[:-1]])
        bear=(cl<o)&(np.r_[False,cl[:-1]>o[:-1]])&(
             o>=np.r_[np.nan,cl[:-1]])&(cl<=np.r_[np.nan,o[:-1]])
        info=dict(open=o,close=cl,high=hi,low=lo,
             spread=((d.ask_open-d.bid_open)/pip).to_numpy(float),
             bull=bull,bear=bear,pip=pip)
        for tf in ("H4","D1"):
            for role in ("same","flip"):
                mode=tf+"_"+role
                ev,stats=build_zones(d,tf,role,pip)
                # Converting completed HTF close time to index of earliest H1 OPEN at/after close.
                for e in ev:
                    e["available_index"]=int(index.searchsorted(e["available"]))
                info[mode]=ev
                diagnostics[symbol+"_"+mode]=stats
        output[symbol]=info
    return output,diagnostics

def rejection(f,j,z):
    # Price touches zone and last completed H1 engulfing rejects it.
    center=z["center"];width=z["half_width"]
    if not (f["low"][j]<=center+width and f["high"][j]>=center-width):return False
    if z["role"]=="support":
        return bool(f["bull"][j] and f["close"][j]>center)
    return bool(f["bear"][j] and f["close"][j]<center)

def trade_run(index,features,mode,begin,end,spread_mult=1.0):
    first=int(index.searchsorted(pd.Timestamp(begin,tz="UTC")))
    last=int(index.searchsorted(pd.Timestamp(end,tz="UTC")))
    ptr={s:0 for s in SYMBOLS};zones={s:[] for s in SYMBOLS}
    cash=INITIAL;position=None;last_week=None;rows=[]
    diagnostics=dict(engulfing_retests=0,rejected_distance=0,rejected_RR=0,
                     rejected_minlot=0,eligible=0,entry_weeks=0)
    weeks=set()
    def finish(i,mid,reason):
        nonlocal position,cash
        p=position;f=features[p["symbol"]];pip=f["pip"]
        # Historical H1 bid/ask quote at exit candle OPEN only; intrabar spread is unobserved.
        exitspread=float(f["spread"][i])
        if not np.isfinite(exitspread) or exitspread<0:raise ValueError("Invalid exit spread")
        two_sided_cost=(p["spread"]+exitspread)*.5*spread_mult+2*SLIP_EACH_PIPS
        per_pip=(10.0 if p["symbol"]!="usdjpy" else 1000.0/max(mid,1))
        gpips=p["side"]*(mid-p["entry"])/pip
        gross=gpips*per_pip*p["lots"]
        fees=two_sided_cost*per_pip*p["lots"]
        net=gross-fees;cash+=net
        rows.append(dict(entry_time=p["time"].isoformat(),exit_time=index[i].isoformat(),
            symbol=p["symbol"],mode=mode,side="BUY" if p["side"]>0 else "SELL",
            touch_count=p["touches"],zone_center=p["zone_center"],zone_half_width_pips=p["width"]/pip,
            entry_mid=p["entry"],stop=p["stop"],target=p["target"],
            engulfing_low=p["engulfing_low"],engulfing_high=p["engulfing_high"],
            lot=p["lots"],designed_risk_usd=p["risk"],expected_net_rr=p["net_rr"],
            gross_usd=gross,fees_usd=fees,net_usd=net,balance_usd=cash,exit_reason=reason))
        position=None
    for i in range(max(200,first),last):
        now=index[i];week=(int(now.isocalendar().year),int(now.isocalendar().week))
        # A zone known at the END of HTF candle can only influence decisions after that.
        for sym in SYMBOLS:
            ev=features[sym][mode]
            while ptr[sym]<len(ev) and ev[ptr[sym]]["available_index"]<=i:
                zones[sym].append(ev[ptr[sym]])
                ptr[sym]+=1
            # Drop zone snapshots after fixed age, without future information.
            age=CFG[mode[:2]]["age_hours"]
            zones[sym]=[z for z in zones[sym] if (now-z["available"]).total_seconds()<=age*3600]
        just_closed=False
        if position is not None:
            p=position;f=features[p["symbol"]];side=p["side"]
            out=None;why=None
            if i>p["i"] and i-p["i"]>=MAX_HOLD_H1:
                out=float(f["open"][i]);why="timeout"
            if why is None:
                if side==1:
                    if f["low"][i]<=p["stop"]:
                        out=min(float(f["open"][i]),p["stop"]);why="stop"
                    elif f["high"][i]>=p["target"]:
                        out=p["target"];why="takeprofit"
                else:
                    if f["high"][i]>=p["stop"]:
                        out=max(float(f["open"][i]),p["stop"]);why="stop"
                    elif f["low"][i]<=p["target"]:
                        out=p["target"];why="takeprofit"
            if why is not None:
                finish(i,out,why);just_closed=True
        if position is not None or just_closed or last_week==week or cash<100:continue
        if now.weekday()>4 or not 7<=now.hour<19:continue
        j=i-1;candidates=[]
        for sym in SYMBOLS:
            f=features[sym];pip=f["pip"]
            # Observable entry quote must be used in the RR and risk check.
            entryspread=float(f["spread"][i])
            if not np.isfinite(entryspread) or entryspread<0 or entryspread>12:continue
            cost=entryspread*spread_mult+2*SLIP_EACH_PIPS
            # Only the most recent version of near-identical zones per price band.
            seen=[]
            for z in reversed(zones[sym]):
                if any(abs(z["center"]-c)<=z["half_width"] for c in seen):continue
                seen.append(z["center"])
                if not rejection(f,j,z):continue
                diagnostics["engulfing_retests"]+=1
                side=1 if z["role"]=="support" else -1
                entry=float(f["open"][i])
                buf=STOP_BUFFER_PIPS*pip
                # Stop beyond BOTH the HTF zone and the confirming H1 engulfing wick.
                stop=(min(z["center"]-z["half_width"],f["low"][j])-buf
                      if side>0 else max(z["center"]+z["half_width"],f["high"][j])+buf)
                riskp=side*(entry-stop)/pip
                if riskp<5 or riskp>150 or not np.isfinite(riskp):
                    diagnostics["rejected_distance"]+=1;continue
                # Use 2R by default, capped strictly BEFORE nearest known opposing hard level.
                target=entry+side*GROSS_TARGET_R*riskp*pip
                for opposite in zones[sym]:
                    if opposite["role"]==z["role"]:continue
                    bound=(opposite["center"]-opposite["half_width"]-TP_BUFFER_PIPS*pip if side>0
                           else opposite["center"]+opposite["half_width"]+TP_BUFFER_PIPS*pip)
                    if side>0 and entry<bound<target:target=bound
                    if side<0 and target<bound<entry:target=bound
                rewardp=side*(target-entry)/pip
                netrr=(rewardp-cost)/(riskp+cost)
                if netrr<MIN_RR:
                    diagnostics["rejected_RR"]+=1;continue
                dollar_per_pip=10.0 if sym!="usdjpy" else 1000.0/entry
                perlot_risk=(riskp+cost)*dollar_per_pip
                max_by_risk=cash*RISK/perlot_risk
                max_by_leverage=cash*MAX_LEVERAGE/(100000*(1 if sym=="usdjpy" else entry))
                lots=math.floor((min(max_by_risk,max_by_leverage,.5)+1e-10)/.01)*.01
                if lots<.01:
                    diagnostics["rejected_minlot"]+=1;continue
                designed_risk=perlot_risk*lots
                if designed_risk>cash*RISK+1e-7:
                    raise AssertionError("More than 0.5% designed equity risk")
                diagnostics["eligible"]+=1
                candidates.append(dict(symbol=sym,side=side,score=z["touches"],width=z["half_width"],
                    i=i,time=now,entry=entry,stop=stop,target=target,net_rr=netrr,
                    spread=entryspread,lots=round(lots,2),risk=designed_risk,
                    touches=z["touches"],zone_center=z["center"],
                    engulfing_low=float(f["low"][j]),engulfing_high=float(f["high"][j])))
        if not candidates:continue
        candidates.sort(key=lambda x:(-x["touches"],x["width"],-x["net_rr"],x["symbol"]))
        position=candidates[0];last_week=week;weeks.add(week)
        # Entry at current OPEN. H1 first-bar stop check: stop-first when both touched.
        p=position;f=features[p["symbol"]]
        hit_stop=(f["low"][i]<=p["stop"] if p["side"]>0 else f["high"][i]>=p["stop"])
        hit_tp=(f["high"][i]>=p["target"] if p["side"]>0 else f["low"][i]<=p["target"])
        if hit_stop or hit_tp:
            mid=(min(f["open"][i],p["stop"]) if p["side"]>0 else max(f["open"][i],p["stop"])) if hit_stop else p["target"]
            finish(i,mid,"entry_stop" if hit_stop else "entry_target")
    if position is not None:
        # Mandatory liquidation at last observed close, not silent omission of floating PnL.
        finish(last-1,float(features[position["symbol"]]["close"][last-1]),"end_period")
    diagnostics["weeks_traded"]=len(weeks)
    return pd.DataFrame(rows),diagnostics

def stats(trades,begin,end):
    months=pd.period_range(begin[:7],(pd.Timestamp(end)-pd.Timedelta(days=1)).strftime("%Y-%m"),freq="M")
    if trades.empty:
        return dict(trades=0,net_pct=0.,pf=None,win_rate_pct=None,dd_closed_pct=0.,
             months_ge5=0,months_ge8=0,min_net_rr=None,cost_usd=0,pairs={})
    pnl=trades.net_usd.to_numpy(float)
    balance=INITIAL+np.cumsum(pnl)
    peak=np.maximum.accumulate(np.r_[INITIAL,balance])[1:]
    wins=pnl[pnl>0].sum();loss=-pnl[pnl<0].sum()
    monthly=trades.assign(month=pd.to_datetime(trades.exit_time,utc=True).dt.strftime("%Y-%m")).groupby("month").net_usd.sum().to_dict()
    wallet=INITIAL;five=eight=0
    for m in months:
        gain=monthly.get(str(m),0)
        rr=gain/wallet*100 if wallet>0 else -100
        five+=rr>=5;eight+=rr>=8
        wallet+=gain
    return dict(trades=int(len(trades)),net_pct=float((balance[-1]/INITIAL-1)*100),
        end_cash_usd=float(balance[-1]),pf=float(wins/loss) if loss else None,
        win_rate_pct=float(np.mean(pnl>0)*100),
        dd_closed_pct=float(np.min((balance/peak-1)*100)),
        months_ge5=int(five),months_ge8=int(eight),
        min_net_rr=float(trades.expected_net_rr.min()),
        max_intended_risk_usd=float(trades.designed_risk_usd.max()),
        max_realized_loss_usd=float(-pnl.min()),
        cost_usd=float(trades.fees_usd.sum()),
        pairs={str(s):int(n) for s,n in trades.groupby("symbol").size().items()})

def main():
    out=Path("htf_zone_results");out.mkdir(exist_ok=True)
    index,price=load_prices()
    features,pivotstats=build_all(index,price)
    results={}
    for mode in MODELS:
        results[mode]={}
        for phase,start,end in WINDOWS:
            trades,diag=trade_run(index,features,mode,start,end)
            stressed,_=trade_run(index,features,mode,start,end,spread_mult=2)
            trades.to_csv(out/(mode+"_"+phase+".csv"),index=False)
            stressed.to_csv(out/(mode+"_"+phase+"_spread_x2.csv"),index=False)
            results[mode][phase]=dict(base=stats(trades,start,end),spread_x2=stats(stressed,start,end),diagnostics=diag)
        print("MODEL",mode,results[mode]["validation"]["base"]["trades"],results[mode]["holdout"]["base"]["trades"],flush=True)
    # Choose only from validation; do NOT rank or re-tune using 2023–26.
    eligible=[mode for mode in MODELS if
         results[mode]["validation"]["base"]["trades"]>=25 and
         results[mode]["validation"]["base"]["net_pct"]>0 and
         (results[mode]["validation"]["base"]["pf"] or 0)>=1.10 and
         results[mode]["validation"]["base"]["dd_closed_pct"]>=-15]
    winner=sorted(eligible,key=lambda mode:(-results[mode]["validation"]["base"]["net_pct"],mode))[0] if eligible else None
    holdout=results[winner]["holdout"] if winner else None
    accepted=bool(winner and holdout["base"]["trades"]>=25 and holdout["base"]["net_pct"]>0 and
             (holdout["base"]["pf"] or 0)>=1.10 and holdout["base"]["dd_closed_pct"]>=-15 and
             holdout["spread_x2"]["net_pct"]>0)
    final=dict(source="Dukascopy H1 bid ask historical verified; NOT Exness tick execution",
         periods=dict(validation=WINDOWS[0][1:],holdout=WINDOWS[1][1:]),symbols=list(SYMBOLS),
         common_h1_bars=len(index),framework="4-touch support resistance on CLOSED H4 or D1 with H1 body engulfing",
         models=list(MODELS),zone_stats=pivotstats,stop="farther of HTF zone outer edge or H1 engulfing wick, +1.5 pip",
         tp="2.0 gross R, capped before closest known opposite HTF hard zone; net R:R >=1.5",
         risk_per_trade=.005,max_one_entry_per_week=True,
         data_constraints="No volume, EMA, RSI, ATR or macro calendar, no Exness rollover historical swap",
         risk_note="Historical OHLC stop-first intrabar approximation; gap can exceed 0.5% intended equity risk",
         results=results,eligible_on_validation=eligible,
         selected_validation_only=winner,passes_holdout_threshold=accepted,
         live_trade_orders=0)
    (out/"RESULTS_HTF_PRICE_ACTION.json").write_text(json.dumps(final,ensure_ascii=False,indent=2))
    lines=["# Vùng cứng H4/D1 + engulfing H1 — dữ liệu thật", "",
           "Tín hiệu chỉ từ nến giá: H4/D1 4 pivot đảo chiều cách nhau, đợi H1 body engulfing đóng rồi vào tại H1 open kế tiếp.",
           "SL ngoài xa hơn giữa đáy/đỉnh engulfing và mép vùng +1,5 pip; TP ban đầu 2R, đặt trước vùng đối diện gần hơn.",
           "R:R sau phí >=1,5; 0,5R/lệnh = 0,5% vốn; tối đa một lệnh/tuần trên bốn cặp.",
           "", "| Khung / kiểu vùng | Giai đoạn | Lệnh | Lãi ròng | PF | Thắng | DD đóng lệnh | Net R:R min | Spread x2 | Tháng >=5% |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for mode in MODELS:
        for phase,_,_ in WINDOWS:
            t=results[mode][phase]["base"];s=results[mode][phase]["spread_x2"]
            fmt=lambda x:"—" if x is None else f"{x:.2f}"
            lines.append(f"| {mode} | {phase} | {t['trades']} | {t['net_pct']:+.2f}% | {fmt(t['pf'])} | {fmt(t['win_rate_pct'])}% | {t['dd_closed_pct']:.2f}% | {fmt(t['min_net_rr'])} | {s['net_pct']:+.2f}% | {t['months_ge5']} |")
    lines+=["",f"Được chọn hoàn toàn dựa trên validation: **{winner or 'Không có cấu hình đủ điều kiện'}**",
           f"Đạt điều kiện holdout: **{'CÓ, chỉ nghiên cứu tiếp' if accepted else 'KHÔNG'}**",
           "", "Không bảo đảm lãi 5–8%/tháng. Swap chưa tính, spread Exness chưa xác minh. Một lần nến chạm cả SL/TP thì giả định SL trước.",
           "Đây là thử nghiệm không thực hiện lệnh tiền thật. CSV các giao dịch và JSON đầy đủ đi kèm artifact."]
    (out/"BAO_CAO_HTF_ENGULFING.md").write_text("\n".join(lines))
    print("HTF BACKTEST COMPLETE",json.dumps({mode:{phase:{'trades':results[mode][phase]['base']['trades'],'net':round(results[mode][phase]['base']['net_pct'],3)} for phase,_,_ in WINDOWS} for mode in MODELS}),"selected",winner,"gate",accepted,flush=True)

if __name__=="__main__":main()
