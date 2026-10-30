#!/usr/bin/env python3
"""One next SAME-timeframe candle ONLY: H1 or H4 engulfing at confirmed 4-touch HTF zones.

Signals are generated only from completed H1/H4 candles. Every limit order has
exactly one following H1 or H4 candle to fill. On expiration, it is canceled.
No lookahead to the best candle of the week. Historical price action research,
not broker order execution. No actual broker credentials or trade placement.
"""
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from htf_limit_mid_yearly import historical_prices, START_CAPITAL, RISK, LEVERAGE, \
    MIN_RR_NET, SLIP_EACH, TARGET_R, STOP_BUFFER_PIPS, TP_ZONE_BUFFER_PIPS, MAX_HOLD_BARS
from htf_hard_zones_engulf import build_all, CFG
from portfolio_research import SYMBOLS, PIPS

YEARS=list(range(2019,2026))
ZONE_MODES=("H4_same","H4_flip","D1_same","D1_flip")
SIGNAL_TIMEFRAMES=("H1","H4")
OUT=Path("next_candle_htf_results")

def engulf_signals(prices,index,features):
    """Information at close of the signal candle. H4 candle is complete
    only after 4 actual consecutive hourly bars; no synthetic/partial H4.
    Each H4 signal maps to first H1 bar opening at its HTF closing time.
    """
    s={}
    for sym in SYMBOLS:
        f=features[sym]
        s[(sym,"H1")]=None # original H1 body-engulfing features are in f
        data=prices[sym]
        r=data.resample("4h",label="right",closed="left")
        frame=pd.DataFrame({"open":r.open.first(),"high":r.high.max(),
            "low":r.low.min(),"close":r.close.last(),"n":r.close.count()}).dropna()
        # Require exactly four actual H1 bars, and no sub-hour gaps.
        complete=frame.n.eq(4)
        op=frame.open;cl=frame.close
        bull=(cl>op)&(cl.shift(1)<op.shift(1))&(
            op<=cl.shift(1))&(cl>=op.shift(1))
        bear=(cl<op)&(cl.shift(1)>op.shift(1))&(
            op>=cl.shift(1))&(cl<=op.shift(1))
        both=complete&complete.shift(1).fillna(False)
        # We only accept clock-aligned continuous 4-hour candles.
        signs={}
        for time,bar in frame.loc[both&(bull|bear)].iterrows():
            i=int(index.searchsorted(time))
            if i>=len(index) or index[i]!=time:continue
            signs[i]=dict(signal_time=time,high=float(bar.high),
                  low=float(bar.low),close=float(bar.close),
                  side=1 if bull.loc[time] else -1)
        s[(sym,"H4")]=signs
    return s

def signal_at(index,features,engulf,sym,tf,i):
    if tf=="H1":
        j=i-1
        if j<1 or index[i]-index[j]!=pd.Timedelta(hours=1):return None
        f=features[sym]
        if not(f["bull"][j] or f["bear"][j]):return None
        return dict(signal_time=index[i],high=float(f["high"][j]),
            low=float(f["low"][j]),close=float(f["close"][j]),
            side=1 if f["bull"][j] else -1,
            event_time=index[j]+pd.Timedelta(hours=1))
    if tf=="H4":
        return engulf[(sym,"H4")].get(i)
    raise ValueError("Unexpected signal TF")

def allowed_limit_fill(side,limit,opening,high,low,stop):
    """Midpoint LIMIT in just the next candle. If the bar opens beyond the
    stop, entry is not credible; cancel instead of inventing an instant
    risk-free/bad-price reversal. Better opening prices otherwise allowed.
    """
    if side==1:
        if opening<=stop:return None
        if opening<=limit:return float(opening)
        return float(limit) if low<=limit else None
    if opening>=stop:return None
    if opening>=limit:return float(opening)
    return float(limit) if high>=limit else None

def backtest(index,features,engulf,zone_mode,signal_tf,year,spread_mult=1.):
    begin=pd.Timestamp(f"{year}-01-01",tz="UTC")
    end_time=pd.Timestamp(f"{year+1}-01-01",tz="UTC")
    first=int(index.searchsorted(begin));last=int(index.searchsorted(end_time))
    if last-first<3300:raise ValueError("Missing full trading history for "+str(year))
    ptr={sym:0 for sym in SYMBOLS}
    zones={sym:[] for sym in SYMBOLS}
    for sym in SYMBOLS:
        events=features[sym][zone_mode]
        # Events confirmed before the year must remain usable until they age out.
        while ptr[sym]<len(events) and events[ptr[sym]]["available_index"]<first:
            ptr[sym]+=1
        age=CFG[zone_mode[:2]]["age_hours"]
        zones[sym]=[z for z in events[:ptr[sym]]
            if (begin-z["available"]).total_seconds()<=age*3600]
    wallet=START_CAPITAL
    position=None;pending=None;last_entry_week=None
    trades=[]
    count=dict(signal=0,limits_placed=0,limits_filled=0,limits_expired=0,
       refused_rr=0,refused_lot=0,refused_spread=0,canceled_on_gap=0,
       canceled_year_end=0,entry_candle_sl=0,expired_no_fill=0)
    def finish(i,mid,why):
        nonlocal wallet,position
        p=position;f=features[p["sym"]];pip=f["pip"]
        sp_out=float(f["spread"][i])
        if not np.isfinite(sp_out) or sp_out<0:raise ValueError("Bad observed exit spread")
        # Spread model approximates roundtrip using half spread at both opens.
        total_cost=(p["spread_at_fill"]+sp_out)*spread_mult/2+2*SLIP_EACH
        pip_usd=10. if p["sym"]!="usdjpy" else 1000./max(float(mid),1.)
        gross=p["side"]*(mid-p["fill"])/pip*pip_usd*p["lots"]
        fees=total_cost*pip_usd*p["lots"]
        net=gross-fees;wallet+=net
        trades.append(dict(year=year,hard_zone=zone_mode,signal_tf=signal_tf,
          pair=p["sym"],side="BUY" if p["side"]==1 else "SELL",
          engulfing_time=p["engulf_time"].isoformat(),
          order_live_time=p["order_time"].isoformat(),
          fill_time=p["fill_time"].isoformat(),exit_time=index[i].isoformat(),
          touch_count=p["touches"],zone=p["zone"],engulf_low=p["sig_low"],
          engulf_high=p["sig_high"],limit_price=p["limit"],
          filled_price=p["fill"],stop=p["stop"],tp=p["tp"],lots=p["lots"],
          intended_risk_usd=p["risk"],net_rr_at_fill=p["rr"],
          gross_usd=gross,fees_usd=fees,net_usd=net,equity_usd=wallet,exit_reason=why))
        position=None
    def try_fill(i):
        """Attempt only inside next SAME TF candle. Subsequent H1 bars belong to
        the one H4 candle only if their UTC time is strictly before expiry.
        Re-evaluate R:R and quantity on observed fill bar."""
        nonlocal pending,position,last_entry_week
        p=pending;f=features[p["sym"]]
        op=float(f["open"][i]);h=float(f["high"][i]);l=float(f["low"][i])
        filled=allowed_limit_fill(p["side"],p["limit"],op,h,l,p["stop"])
        if filled is None:
            if (p["side"]==1 and op<=p["stop"]) or(p["side"]==-1 and op>=p["stop"]):
                count["canceled_on_gap"]+=1;pending=None
            return False
        spread=float(f["spread"][i]);pip=f["pip"]
        if not np.isfinite(spread) or spread<0 or spread>12:
            count["refused_spread"]+=1;pending=None;return False
        riskp=p["side"]*(filled-p["stop"])/pip
        rewardp=p["side"]*(p["tp"]-filled)/pip
        costp=spread*spread_mult+2*SLIP_EACH
        rr=(rewardp-costp)/(riskp+costp) if riskp+costp>0 else -1
        if riskp<2 or riskp>160 or rr<MIN_RR_NET:
            count["refused_rr"]+=1;pending=None;return False
        pip_usd=10. if p["sym"]!="usdjpy" else 1000./max(filled,1.)
        per_lot=(riskp+costp)*pip_usd
        by_risk=wallet*RISK/per_lot
        by_leverage=wallet*LEVERAGE/(100000*(1 if p["sym"]=="usdjpy" else filled))
        lots=math.floor((min(by_risk,by_leverage,.5)+1e-10)/.01)*.01
        if lots<.01:
            count["refused_lot"]+=1;pending=None;return False
        intended_risk=per_lot*lots
        if intended_risk>wallet*RISK+1e-6:
            raise AssertionError("Position risk >0.5% at intended SL")
        position=dict(p,fill_idx=i,fill_time=index[i],
            fill=filled,spread_at_fill=spread,lots=round(lots,2),
            risk=intended_risk,rr=rr)
        pending=None;last_entry_week=(int(index[i].isocalendar().year),int(index[i].isocalendar().week))
        count["limits_filled"]+=1
        # H1 OHLC cannot resolve fill vs SL order within same bar.
        # Conservative: if the stop is present in the same bar, count stop.
        if (p["side"]==1 and l<=p["stop"]) or(p["side"]==-1 and h>=p["stop"]):
            count["entry_candle_sl"]+=1
            mid=min(op,p["stop"]) if p["side"]==1 else max(op,p["stop"])
            finish(i,mid,"same_hour_limit_and_stop")
        # Same-hour TP is never credited unless tick sequence is known.
        return True

    for i in range(first,last):
        now=index[i];iso=(int(now.isocalendar().year),int(now.isocalendar().week))
        for sym in SYMBOLS:
            ev=features[sym][zone_mode]
            while ptr[sym]<len(ev) and ev[ptr[sym]]["available_index"]<=i:
                zones[sym].append(ev[ptr[sym]]);ptr[sym]+=1
            age=CFG[zone_mode[:2]]["age_hours"]
            zones[sym]=[z for z in zones[sym]
                if (now-z["available"]).total_seconds()<=age*3600]
        exited=False
        if position is not None:
            p=position;f=features[p["sym"]];mid=None;why=None
            if i>p["fill_idx"] and i-p["fill_idx"]>=MAX_HOLD_BARS:
                mid=float(f["open"][i]);why="max_hold"
            if why is None:
                if p["side"]==1:
                    if f["low"][i]<=p["stop"]:
                        mid=min(float(f["open"][i]),p["stop"]);why="SL"
                    elif f["high"][i]>=p["tp"]:
                        mid=p["tp"];why="TP"
                else:
                    if f["high"][i]>=p["stop"]:
                        mid=max(float(f["open"][i]),p["stop"]);why="SL"
                    elif f["low"][i]<=p["tp"]:
                        mid=p["tp"];why="TP"
            if why is not None:
                finish(i,mid,why);exited=True
        if pending is not None:
            if now>=pending["expire"]:
                count["limits_expired"]+=1
                pending=None
            elif last_entry_week==iso:
                count["limits_expired"]+=1
                pending=None
            else:
                opened=try_fill(i)
                if opened or pending is not None or position is not None:
                    continue
        if exited or position is not None or pending is not None or last_entry_week==iso or wallet<100:
            continue
        # Orders are placed at OPEN immediately after the completed signal bar;
        # never submitted retrospectively later in the 4h block.
        if now.weekday()>4 or not 7<=now.hour<19:continue
        # H4 signal only when a full aligned H4 engulfing bar has just closed.
        if signal_tf=="H4" and now.hour%4!=0:continue
        cands=[]
        for sym in SYMBOLS:
            f=features[sym];pip=f["pip"]
            sig=signal_at(index,features,engulf,sym,signal_tf,i)
            if sig is None:continue
            side=sig["side"]
            # Engulfing candle must close on correct side of the 50% limit.
            limit=(sig["high"]+sig["low"])/2
            if side*(sig["close"]-limit)<=0:continue
            sp=float(f["spread"][i])
            if not np.isfinite(sp) or not 0<=sp<=12:continue
            tried=[]
            for zone in reversed(zones[sym]):
                if any(abs(zone["center"]-v)<=zone["half_width"] for v in tried):continue
                tried.append(zone["center"])
                if not(f["low"][i-1]<=zone["center"]+zone["half_width"] and
                       f["high"][i-1]>=zone["center"]-zone["half_width"]) and signal_tf=="H1":
                    continue
                if signal_tf=="H4" and not(sig["low"]<=zone["center"]+zone["half_width"] and
                    sig["high"]>=zone["center"]-zone["half_width"]):continue
                if side==1 and (zone["role"]!="support" or sig["close"]<=zone["center"]):continue
                if side==-1 and(zone["role"]!="resistance" or sig["close"]>=zone["center"]):continue
                count["signal"]+=1
                stop=(sig["low"]-STOP_BUFFER_PIPS*pip if side==1 else
                      sig["high"]+STOP_BUFFER_PIPS*pip)
                distance=side*(limit-stop)/pip
                if distance<2 or distance>160:continue
                target=limit+side*TARGET_R*distance*pip
                # Cap to the closest known opposing hard zone, only already confirmed.
                for opp in zones[sym]:
                    if opp["role"]==zone["role"]:continue
                    bound=(opp["center"]-opp["half_width"]-TP_ZONE_BUFFER_PIPS*pip if side==1
                           else opp["center"]+opp["half_width"]+TP_ZONE_BUFFER_PIPS*pip)
                    if side==1 and limit<bound<target:target=bound
                    if side==-1 and target<bound<limit:target=bound
                costp=sp*spread_mult+2*SLIP_EACH
                reward=side*(target-limit)/pip
                rr=(reward-costp)/(distance+costp)
                if rr<MIN_RR_NET:count["refused_rr"]+=1;continue
                pipusd=10. if sym!="usdjpy" else 1000./max(limit,1)
                by_risk=wallet*RISK/((distance+costp)*pipusd)
                by_lev=wallet*LEVERAGE/(100000*(1 if sym=="usdjpy" else limit))
                if min(by_risk,by_lev)<.01:count["refused_lot"]+=1;continue
                expiry=now+pd.Timedelta(hours=1 if signal_tf=="H1" else 4)
                cands.append(dict(i=i,sym=sym,side=side,order_time=now,
                    engulf_time=now,limit=limit,stop=stop,tp=target,
                    touches=zone["touches"],zone=zone["center"],width=zone["half_width"],
                    sig_low=sig["low"],sig_high=sig["high"],
                    requested_rr=rr,expire=expiry))
        if not cands:continue
        # First available time wins. Same clock: strongest 4-touch reaction zone,
        # narrower zone, highest initial R:R, then symbol name.
        cands.sort(key=lambda p:(-p["touches"],p["width"],-p["requested_rr"],p["sym"]))
        pending=cands[0]
        count["limits_placed"]+=1
        try_fill(i)

    if pending is not None:count["canceled_year_end"]+=1
    if position is not None:
        finish(last-1,float(features[position["sym"]]["close"][last-1]),"end_year")
    ledger=pd.DataFrame(trades)
    return ledger,count

def metrics(t,c):
    if t.empty:return dict(submitted=c["limits_placed"],filled=0,expired=c["limits_expired"],
        return_pct=0.,pf=None,win_pct=None,dd_pct=0.,min_net_rr=None,fee_usd=0.,end_usd=START_CAPITAL)
    pnl=t.net_usd.to_numpy(float)
    eq=START_CAPITAL+np.cumsum(pnl)
    peak=np.maximum.accumulate(np.r_[START_CAPITAL,eq])[1:]
    w=float(pnl[pnl>0].sum());loss=float(-pnl[pnl<0].sum())
    return dict(submitted=c["limits_placed"],filled=int(len(t)),expired=c["limits_expired"],
        return_pct=float((eq[-1]/START_CAPITAL-1)*100),
        end_usd=float(eq[-1]),pf=(w/loss if loss else None),
        win_pct=float(np.mean(pnl>0)*100),dd_pct=float(np.min((eq/peak-1)*100)),
        min_net_rr=float(t.net_rr_at_fill.min()),fee_usd=float(t.fees_usd.sum()),
        max_designed_risk_usd=float(t.intended_risk_usd.max()),
        max_realized_loss_usd=float(-pnl.min()),
        by_symbol={str(s):int(n) for s,n in t.groupby("pair").size().items()})

def audit(t,year):
    if t.empty:return
    if not (t.touch_count>=4).all():raise AssertionError("zone does not have 4 touches")
    if not (t.net_rr_at_fill>=MIN_RR_NET-1e-8).all():raise AssertionError("R:R below 1.5")
    if not ((t.gross_usd-t.fees_usd-t.net_usd).abs()<1e-7).all():raise AssertionError("Pnl mismatch")
    if t.fill_time.isna().any():raise AssertionError("Unfilled order counted as trade")
    iso=pd.to_datetime(t.fill_time,utc=True).dt.strftime("%G-%V")
    if iso.duplicated().any():raise AssertionError("Multiple fills in one ISO week")
    prior=START_CAPITAL
    for row in t.itertuples(index=False):
        pip=PIPS[row.pair]
        if abs(row.limit_price-(row.engulf_high+row.engulf_low)/2)>1e-7:
            raise AssertionError("Not exactly 50% engulfing range")
        expected_sl=row.engulf_low-pip if row.side=="BUY" else row.engulf_high+pip
        if abs(row.stop-expected_sl)>1e-7:raise AssertionError("Wrong wick ±1 pip stop")
        if row.intended_risk_usd>prior*RISK+1e-6:raise AssertionError("Risk >0.5% equity")
        if abs(row.equity_usd-(prior+row.net_usd))>1e-6:
            raise AssertionError("Broken equity chain")
        if pd.Timestamp(row.fill_time)>=pd.Timestamp(row.order_live_time)+pd.Timedelta(
            hours=1 if row.signal_tf=="H1" else 4):
            raise AssertionError("Fill after next candle expiration")
        if pd.Timestamp(row.fill_time).year!=year:
            raise AssertionError("Cross-year fill")
        prior=row.equity_usd

def main():
    OUT.mkdir(exist_ok=True)
    idx,raw=historical_prices()
    features,zone_stats=build_all(idx,raw)
    signals=engulf_signals(raw,idx,features)
    result={}
    for tf in SIGNAL_TIMEFRAMES:
        result[tf]={}
        for mode in ZONE_MODES:
            result[tf][mode]={}
            for year in YEARS:
                trades,c=backtest(idx,features,signals,mode,tf,year)
                audit(trades,year)
                stress,sc=backtest(idx,features,signals,mode,tf,year,spread_mult=2)
                audit(stress,year)
                x=metrics(trades,c)
                x["stress_x2_pct"]=metrics(stress,sc)["return_pct"]
                x["diagnostics"]=c
                trades.to_csv(OUT/f"{tf}_{mode}_{year}.csv",index=False)
                result[tf][mode][str(year)]=x
            print(tf,mode,[(yr, result[tf][mode][str(yr)]["filled"],
                round(result[tf][mode][str(yr)]["return_pct"],3)) for yr in YEARS],flush=True)
    final=dict(data="Verified Dukascopy actual H1 bid/ask (not Exness historical fills)",
        bars_common_4pairs=len(idx),years=YEARS,
        hard_zone_models=ZONE_MODES,signal_timeframes=SIGNAL_TIMEFRAMES,
        next_candle_only={"H1":"exactly next 1 clock hour","H4":"exactly next UTC-aligned 4-hour candle"},
        entry="BUY/SELL pending limit exactly 50% of engulfing candle HIGH-LOW",
        stop="BUY below engulfing candle LOW by 1 pip; SELL above HIGH by 1 pip",
        target="2R initial from limit, capped by earlier verified opposite HTF zone",
        intended_risk_fraction=.005,net_rr_min=MIN_RR_NET,
        active_order_fills_not_forced=True,max_one_filled_trade_per_ISO_week=True,
        results=result,zone_stats=zone_stats,broker_orders_placed=0,
        limitations=["OHLC H1 does not reveal intra-hour tick sequence",
          "Inside one H1 candle, stop takes precedence; no same-bar target credited",
          "H4 candle is constructed from four complete H1 price observations",
          "No real Exness spread/swap/slippage execution history",
          "2019-2025 already partly studied in prior experiments; exploratory not untouched holdout"])
    (OUT/"RESULTS_H1_H4_NEXT_CANDLE.json").write_text(json.dumps(final,ensure_ascii=False,indent=2))
    lines=["# Engulfing tại vùng cứng: H1 vs H4, LIMIT chỉ trong nến cùng khung kế tiếp", "",
      "Vùng H4/D1 >=4 phản ứng được xác nhận trước khi đặt lệnh. Nến Engulfing H1/H4 độc lập.",
      "Limit giữa High-Low của nến tín hiệu, hủy khi nến tiếp theo đóng mà chưa khớp.",
      "SL BUY dưới Low nến engulfing 1 pip, SELL trên High 1 pip. R:R sau chi phí >=1:1,5; rủi ro thiết kế 0,5% vốn/lệnh; tối đa 1 khớp lệnh/tuần trên 4 cặp.",
      "", "| Engulfing | Vùng cứng | Năm | Limit đặt | Limit khớp | Limit hết hạn | Lãi ròng | PF | Win rate | DD lệnh đóng | Spread x2 |",
      "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for tf in SIGNAL_TIMEFRAMES:
        for mode in ZONE_MODES:
            for y in YEARS:
                x=result[tf][mode][str(y)]
                pf="—" if x["pf"] is None else f"{x['pf']:.2f}"
                wr="—" if x["win_pct"] is None else f"{x['win_pct']:.1f}%"
                lines.append(f"| {tf} | {mode} | {y} | {x['submitted']} | {x['filled']} | {x['expired']} | {x['return_pct']:+.2f}% | {pf} | {wr} | {x['dd_pct']:.2f}% | {x['stress_x2_pct']:+.2f}% |")
    lines+=["", "Mỗi năm/vùng/khung tín hiệu bắt đầu với vốn mô phỏng $1.000 riêng, không phải một tài khoản gộp 8 chiến lược.",
        "Tín hiệu trong cùng nến chạm LIMIT và SL được ghi lỗ SL; giá H1 không cho thứ tự tick chính xác.",
        "Không kiểm định swap hoặc điều kiện broker Exness. Lỗ thực có thể lớn hơn ngân sách 0,5R khi gap.",
        "Đây là khám phá các quy tắc mới trên giai đoạn 2019-2025 đã được nghiên cứu trước, KHÔNG phải holdout nguyên vẹn."]
    (OUT/"BAO_CAO_H1_H4_LIMIT_NEN_KE_TIEP.md").write_text("\n".join(lines))
    print("NEXT-CANDLE COMPLETE",json.dumps({tf:{mode:{year:[round(st["return_pct"],2),st["filled"]] for year,st in years.items()} for mode,years in mods.items()} for tf,mods in result.items()}),flush=True)

if __name__=="__main__":main()
