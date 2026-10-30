#!/usr/bin/env python3
"""HTF 4-touch zones -> H1 BODY engulf -> 50% of H1 candle RANGE as resting limit.
Reproduces four already defined price-action zone families without parameter tuning.
Research only. No fabricated data, real orders, Exness history, carry or swap.
"""
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from portfolio_research import SYMBOLS, PIPS, verify_month
from htf_hard_zones_engulf import build_all, CFG

MODELS=("H4_same","H4_flip","D1_same","D1_flip")
YEARS=range(2019,2026)
DATA_FROM="2018-01-01";DATA_END="2026-01-01"
RISK=.005                 # 0.5R: intended stop loss ≤ 0.5% account equity
START_CAPITAL=1000.
LEVERAGE=5.
MIN_RR_NET=1.5
SLIP_EACH=.1              # pip each side
STOP_BUFFER_PIPS=1.0      # 1 pip below H1 low (BUY), above H1 high (SELL)
TARGET_R=2.0
LIMIT_TTL_BARS=12         # 12 *observed* common H1 bars; never force fills
TP_ZONE_BUFFER_PIPS=1.
MAX_HOLD_BARS=96

def historical_prices(root=Path(".")):
    months=[str(p) for p in pd.period_range("2018-01","2025-12",freq="M")]
    raw={}
    for sym in SYMBOLS:
        folder=root/"data" if sym=="eurusd" else root/"portfolio_data"/sym
        frames=[verify_month(folder,m,sym) for m in months]
        df=pd.concat(frames,ignore_index=True)
        df["timestamp"]=pd.to_datetime(df.timestamp,utc=True)
        if df["timestamp"].duplicated().any():raise ValueError("Duplicate H1 bars: "+sym)
        df=df.sort_values("timestamp").set_index("timestamp")
        if not ((df["ask_open"]>=df["bid_open"])&(df["open"]>0)&(df["high"]>=df["low"])).all():
            raise ValueError("Invalid bid/ask or OHLC: "+sym)
        raw[sym]=df
    timestamps=raw["eurusd"].index
    for sym in SYMBOLS[1:]:timestamps=timestamps.intersection(raw[sym].index)
    timestamps=timestamps.sort_values()
    if len(timestamps)<45000:raise ValueError("Not enough four-pair historical overlapping candles")
    return timestamps,{sym:raw[sym].loc[timestamps].copy() for sym in SYMBOLS}

def possible_limit_fill(direction,limit,op,high,low):
    """Return mid-price fill ONLY if market crosses resting limit.
    Better fills when next open gaps through limit are credited at open (best
    available price); when both stop and limit touched, stop wins.
    """
    if direction==1:
        if op<=limit:return float(op)
        return float(limit) if low<=limit else None
    if op>=limit:return float(op)
    return float(limit) if high>=limit else None

def trade_one_year(index,feat,kind,year,spread_multiplier=1.0):
    start=int(index.searchsorted(pd.Timestamp(f"{year}-01-01",tz="UTC")))
    end=int(index.searchsorted(pd.Timestamp(f"{year+1}-01-01",tz="UTC")))
    if end-start<3000:raise ValueError("Incomplete year "+str(year))
    events={s:feat[s][kind] for s in SYMBOLS}
    ptr={s:0 for s in SYMBOLS};zones={s:[] for s in SYMBOLS}
    cash=START_CAPITAL;pos=None;pending=None;last_filled_week=None;ledger=[]
    counts=dict(signal_engulf=0,limit_created=0,limit_filled=0,expired=0,
       canceled_bad_spread=0,canceled_rr=0,canceled_risk=0,canceled_year_end=0,
       veto_rr=0,veto_stop=0,veto_lot=0,veto_no_retest=0,fill_same_bar_stop=0)
    def close(i,exit_mid,why):
        nonlocal cash,pos
        p=pos;f=feat[p["sym"]];pip=f["pip"]
        exit_spread=float(f["spread"][i])
        # Historical spread at opening of exit bar; intrabar spread unobservable.
        if not np.isfinite(exit_spread) or not 0<=exit_spread<=120:
            raise ValueError("Invalid observed exit spread "+p["sym"])
        cost_pips=(p["fill_spread"]+exit_spread)*.5*spread_multiplier+2*SLIP_EACH
        pipusd=10.0 if p["sym"]!="usdjpy" else 1000./max(exit_mid,1)
        gross=p["side"]*(exit_mid-p["fill_price"])/pip*pipusd*p["lot"]
        fee=cost_pips*pipusd*p["lot"]
        net=gross-fee;cash+=net
        ledger.append(dict(year=year,pair=p["sym"],mode=kind,
            signal_time=p["signal_time"].isoformat(),order_time=p["order_time"].isoformat(),
            entry_time=p["fill_time"].isoformat(),exit_time=index[i].isoformat(),
            side="BUY" if p["side"]==1 else "SELL",touch_count=p["touches"],
            zone_mid=p["zone"],engulfing_high=p["engulf_high"],engulfing_low=p["engulf_low"],
            limit_requested=p["limit"],entry_mid=p["fill_price"],stop=p["stop"],
            takeprofit=p["target"],lot=p["lot"],entry_spread_pips=p["fill_spread"],
            planned_net_rr=p["rr_at_fill"],planned_risk_usd=p["designed_risk"],
            gross_usd=gross,fee_usd=fee,net_usd=net,balance_usd=cash,exit_reason=why))
        pos=None
    for i in range(max(10,start),end):
        now=index[i];week=(int(now.isocalendar().year),int(now.isocalendar().week))
        # Rebuild zone state from historical activation as of the current bar;
        # when the loop starts on Jan 1, restore zones activated last year.
        if i==start:
            for sym in SYMBOLS:
                ev=events[sym]
                ptr[sym]=int(np.searchsorted([z["available_index"] for z in ev],i,side="right"))
                age=CFG[kind[:2]]["age_hours"]
                zones[sym]=[z for z in ev[:ptr[sym]]
                    if (now-z["available"]).total_seconds()<=age*3600]
        else:
            for sym in SYMBOLS:
                ev=events[sym]
                while ptr[sym]<len(ev) and ev[ptr[sym]]["available_index"]<=i:
                    zones[sym].append(ev[ptr[sym]]);ptr[sym]+=1
                age=CFG[kind[:2]]["age_hours"]
                zones[sym]=[z for z in zones[sym]
                    if (now-z["available"]).total_seconds()<=age*3600]
        just_closed=False
        if pos is not None:
            p=pos;f=feat[p["sym"]]
            exit_mid=None;why=None
            if i>p["fill_idx"] and i-p["fill_idx"]>=MAX_HOLD_BARS:
                exit_mid=float(f["open"][i]);why="timeout"
            if why is None:
                if p["side"]==1:
                    if f["low"][i]<=p["stop"]:
                        exit_mid=min(float(f["open"][i]),p["stop"]);why="SL"
                    elif f["high"][i]>=p["target"]:
                        exit_mid=p["target"];why="TP"
                else:
                    if f["high"][i]>=p["stop"]:
                        exit_mid=max(float(f["open"][i]),p["stop"]);why="SL"
                    elif f["low"][i]<=p["target"]:
                        exit_mid=p["target"];why="TP"
            if why:
                close(i,exit_mid,why);just_closed=True
        if pending is not None:
            # No new order while pending; a pending order may expire unused.
            p=pending;f=feat[p["sym"]]
            if i-p["i"]>=LIMIT_TTL_BARS:
                pending=None;counts["expired"]+=1
            elif last_filled_week==week:
                pending=None;counts["expired"]+=1
            else:
                fill=possible_limit_fill(p["side"],p["limit"],float(f["open"][i]),
                                        float(f["high"][i]),float(f["low"][i]))
                if fill is not None:
                    # Executed ask/bid spread at bar open may be worse than order time.
                    sp=float(f["spread"][i])
                    if not np.isfinite(sp) or sp<0 or sp>12:
                        counts["canceled_bad_spread"]+=1;pending=None
                    else:
                        pip=f["pip"];distance=p["side"]*(fill-p["stop"])/pip
                        projected_cost=(sp*spread_multiplier+2*SLIP_EACH)
                        reward=p["side"]*(p["target"]-fill)/pip
                        rr=(reward-projected_cost)/(distance+projected_cost) if distance+projected_cost>0 else -1
                        if distance<2 or distance>160 or rr<MIN_RR_NET:
                            counts["canceled_rr"]+=1;pending=None
                        else:
                            pipusd=10 if p["sym"]!="usdjpy" else 1000/max(fill,1)
                            cap_risk=cash*RISK/((distance+projected_cost)*pipusd)
                            cap_notional=cash*LEVERAGE/(100000*(1 if p["sym"]=="usdjpy" else fill))
                            lots=math.floor((min(cap_risk,cap_notional,.5)+1e-10)/.01)*.01
                            if lots<.01:
                                counts["canceled_risk"]+=1;pending=None
                            else:
                                pos=dict(p,fill_price=fill,fill_time=now,fill_idx=i,
                                    fill_spread=sp,lot=round(lots,2),rr_at_fill=rr,
                                    designed_risk=(distance+projected_cost)*pipusd*lots)
                                pending=None;last_filled_week=week;counts["limit_filled"]+=1
                                if pos["designed_risk"]>cash*RISK+1e-6:
                                    raise AssertionError("Exceeds max designed 0.5R")
                                # Conservative first fill bar: stop is assumed possible
                                # even if its touch could precede the limit fill. Never
                                # credit same-bar take-profit without actual tick sequence.
                                if (pos["side"]==1 and f["low"][i]<=pos["stop"]) or (
                                    pos["side"]==-1 and f["high"][i]>=pos["stop"]):
                                    counts["fill_same_bar_stop"]+=1
                                    stop_fill=min(float(f["open"][i]),pos["stop"]) if pos["side"]==1 else max(float(f["open"][i]),pos["stop"])
                                    close(i,stop_fill,"fill_bar_stop")
                                    just_closed=True
        if just_closed or pos is not None or pending is not None or cash<100 or last_filled_week==week:
            continue
        # Generate on completed engulfing candle j=i-1 and submit at next i OPEN.
        if now.weekday()>4 or not 7<=now.hour<19 or i<=start:continue
        j=i-1;candidates=[]
        for sym in SYMBOLS:
            f=feat[sym];pip=f["pip"];sp=float(f["spread"][i])
            if not np.isfinite(sp) or sp<0 or sp>12:continue
            seen=[]
            for z in reversed(zones[sym]):
                if any(abs(z["center"]-center)<=z["half_width"] for center in seen):continue
                seen.append(z["center"])
                touched=(f["low"][j]<=z["center"]+z["half_width"] and
                         f["high"][j]>=z["center"]-z["half_width"])
                if not touched:continue
                side=1 if z["role"]=="support" else -1
                if side==1:
                    if not f["bull"][j] or f["close"][j]<=z["center"]:continue
                else:
                    if not f["bear"][j] or f["close"][j]>=z["center"]:continue
                counts["signal_engulf"]+=1
                # Exactly midpoint of FULL H1 engulfing candle (not body).
                limit=(float(f["high"][j])+float(f["low"][j]))/2
                # Retracement: limit must be behind the engulfing candle close.
                if side*(float(f["close"][j])-limit)<=0:continue
                stop=(float(f["low"][j])-STOP_BUFFER_PIPS*pip if side==1 else
                      float(f["high"][j])+STOP_BUFFER_PIPS*pip)
                distance=side*(limit-stop)/pip
                if distance<2 or distance>160 or not np.isfinite(distance):
                    counts["veto_stop"]+=1;continue
                target=limit+side*TARGET_R*distance*pip
                # Existing opposing HTF hard zone limits available reward.
                for opp in zones[sym]:
                    if opp["role"]==z["role"]:continue
                    bound=opp["center"]-opp["half_width"]-TP_ZONE_BUFFER_PIPS*pip if side==1 else opp["center"]+opp["half_width"]+TP_ZONE_BUFFER_PIPS*pip
                    if side==1 and limit<bound<target:target=bound
                    if side==-1 and target<bound<limit:target=bound
                projected=sp*spread_multiplier+2*SLIP_EACH
                netrr=(side*(target-limit)/pip-projected)/(distance+projected)
                if netrr<MIN_RR_NET:
                    counts["veto_rr"]+=1;continue
                pipusd=10 if sym!="usdjpy" else 1000/max(limit,1)
                max_by_risk=cash*RISK/((distance+projected)*pipusd)
                max_by_lev=cash*LEVERAGE/(100000*(1 if sym=="usdjpy" else limit))
                if min(max_by_risk,max_by_lev)<.01:
                    counts["veto_lot"]+=1;continue
                candidates.append(dict(i=i,sym=sym,side=side,time=now,signal_time=index[j],
                    order_time=now,limit=limit,stop=stop,target=target,
                    zone=z["center"],touches=z["touches"],width=z["half_width"],
                    engulf_high=float(f["high"][j]),engulf_low=float(f["low"][j]),
                    netrr=netrr))
        if candidates:
            candidates.sort(key=lambda q:(-q["touches"],q["width"],-q["netrr"],q["sym"]))
            pending=candidates[0];counts["limit_created"]+=1
            # Process the current candle, since the limit became live at its OPEN.
            p=pending;f=feat[p["sym"]]
            fill=possible_limit_fill(p["side"],p["limit"],float(f["open"][i]),float(f["high"][i]),float(f["low"][i]))
            if fill is not None:
                sp=float(f["spread"][i]);cost=sp*spread_multiplier+2*SLIP_EACH
                dist=p["side"]*(fill-p["stop"])/f["pip"]
                reward=p["side"]*(p["target"]-fill)/f["pip"]
                rr=(reward-cost)/(dist+cost) if dist+cost>0 else -1
                pipusd=10 if p["sym"]!="usdjpy" else 1000/max(fill,1)
                lot=math.floor((min(cash*RISK/((dist+cost)*pipusd),
                             cash*LEVERAGE/(100000*(1 if p["sym"]=="usdjpy" else fill)),.5)+1e-10)/.01)*.01 if dist+cost>0 else 0
                if dist<2 or rr<MIN_RR_NET or lot<.01 or not (0<=sp<=12):
                    counts["canceled_rr"]+=1;pending=None
                else:
                    pos=dict(p,fill_price=fill,fill_time=now,fill_idx=i,fill_spread=sp,
                         lot=round(lot,2),rr_at_fill=rr,designed_risk=(dist+cost)*pipusd*lot)
                    pending=None;last_filled_week=week;counts["limit_filled"]+=1
                    if (pos["side"]==1 and f["low"][i]<=pos["stop"]) or (pos["side"]==-1 and f["high"][i]>=pos["stop"]):
                        counts["fill_same_bar_stop"]+=1
                        exit_at=min(float(f["open"][i]),pos["stop"]) if pos["side"]==1 else max(float(f["open"][i]),pos["stop"])
                        close(i,exit_at,"fill_bar_stop")
    if pending is not None:counts["canceled_year_end"]+=1
    if pos is not None:
        i=end-1;f=feat[pos["sym"]]
        close(i,float(f["close"][i]),"annual_boundary")
    return pd.DataFrame(ledger),counts

def summary(ledger,counters,year):
    if ledger.empty:
        return dict(year=year,submitted=counters["limit_created"],filled=0,expired=counters["expired"],
            win_rate_pct=None,return_pct=0,profit_factor=None,max_dd_pct=0,
            net_usd=0,fees_usd=0,min_rr=None,pairs={},**{f"count_{k}":v for k,v in counters.items()})
    pnl=ledger.net_usd.to_numpy(float)
    bal=START_CAPITAL+np.cumsum(pnl);peak=np.maximum.accumulate(np.r_[START_CAPITAL,bal])[1:]
    pos=pnl[pnl>0].sum();neg=-pnl[pnl<0].sum()
    return dict(year=year,submitted=counters["limit_created"],filled=len(ledger),expired=counters["expired"],
        win_rate_pct=float((pnl>0).mean()*100),
        return_pct=100*(bal[-1]/START_CAPITAL-1),
        profit_factor=float(pos/neg) if neg else None,
        max_dd_pct=float((bal/peak-1).min()*100),
        net_usd=float(pnl.sum()),fees_usd=float(ledger.fee_usd.sum()),
        min_rr=float(ledger.planned_net_rr.min()),
        max_intended_risk_usd=float(ledger.planned_risk_usd.max()),
        max_realized_loss_usd=float(-pnl.min()),
        pairs={str(k):int(v) for k,v in ledger.groupby("pair").size().items()},
        **{f"count_{k}":v for k,v in counters.items()})

def main():
    index,prices=historical_prices()
    feat,zone_stats=build_all(index,prices)
    out=Path("limit_yearly_results");out.mkdir(exist_ok=True)
    res={}
    for mode in MODELS:
        res[mode]={}
        for year in YEARS:
            trades,count=trade_one_year(index,feat,mode,year)
            trades.to_csv(out/f"{mode}_{year}_trades.csv",index=False)
            stats=summary(trades,count,year)
            # One stress scenario per year, no optimization/tuning on stressed outcomes.
            stress_trades,stress_counts=trade_one_year(index,feat,mode,year,spread_multiplier=2)
            stats["double_spread_return_pct"]=summary(stress_trades,stress_counts,year)["return_pct"]
            res[mode][str(year)]=stats
        print("MODEL",mode,[(y,res[mode][str(y)]["filled"],round(res[mode][str(y)]["return_pct"],2)) for y in YEARS],flush=True)
    result=dict(status="COMPLETE_HISTORICAL_RESEARCH_ONLY",source="Actual historical Dukascopy H1 Bid/Ask, not Exness",
      common_h1_candles=len(index),data_range=[DATA_FROM,DATA_END],
      report_years=list(YEARS),mode_names=MODELS,zone_pivots=zone_stats,
      limit="midpoint of FULL signal engulfing H1 High-Low; order at next H1 OPEN",
      stop="BUY: engulfing H1 LOW - 1 pip; SELL: HIGH + 1 pip (not beyond HTF zone)",
      target="gross 2R from requested limit, capped ahead of confirmed opposite HTF zone; net RR>=1.5",
      limit_ttl_observed_H1_bars=LIMIT_TTL_BARS,hold_max_observed_H1_bars=MAX_HOLD_BARS,
      risk_fraction=.005,yearly_accounts_reset_to_usd=START_CAPITAL,
      max_one_filled_trade_per_ISO_week=True,results=res,zone_constraints="4 causal confirmed pivots on H4/D1",
      real_trades=0,caveats=[
       "Limit fill and intrabar SL/TP order approximated from OHLC: stop first if fill bar also touches stop",
       "TP within entry bar not credited without tick sequence",
       "Bid/ask spread estimated at hourly opens, no Exness swap or actual tick fills",
       "All annual results are independently reset to $1000, not chained compounding",
       "Latest backtest periods already seen in earlier research and are not fresh untouched out-of-sample data"])
    (out/"RESULTS_LIMIT_2019_2025.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
    lines=["# Vùng cứng H4/D1 + nến engulfing H1, đặt LIMIT 50% và SL 1 pip",
        "", "Cả bốn mô hình: H4_same, H4_flip, D1_same, D1_flip. Chỉ giá H1 thực Dukascopy, H4/D1 dựng từ H1, không có lệnh thật.",
        "", "Limit tại giữa **High–Low toàn bộ nến H1 engulfing**, không phải 50% thân nến. Limit hết hạn sau 12 nến H1 quan sát nếu không khớp.",
        "SL BUY = Low engulfing - 1 pip, SL SELL = High engulfing + 1 pip; TP cơ sở 2R từ Limit, hạ trước vùng đối diện khi cần.",
        "R:R kỳ vọng sau phí >=1,5; 0,5R=0,5% vốn/lệnh, vốn thử nghiệm mỗi năm được reset về $1000; tối đa 1 lệnh/tuần toàn danh mục.",
        "", "| Mô hình | Năm | Limit đặt | Khớp | Không khớp hết hạn | Lãi/lỗ sau phí | Tỷ lệ thắng | PF | DD đóng lệnh | Spread x2 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for mode in MODELS:
        for year in YEARS:
            s=res[mode][str(year)]
            pf="—" if s["profit_factor"] is None else f"{s['profit_factor']:.2f}"
            wr="—" if s["win_rate_pct"] is None else f"{s['win_rate_pct']:.1f}%"
            lines.append(f"| {mode} | {year} | {s['submitted']} | {s['filled']} | {s['expired']} | {s['return_pct']:+.2f}% | {wr} | {pf} | {s['max_dd_pct']:.2f}% | {s['double_spread_return_pct']:+.2f}% |")
    lines+=["","## Hạn chế quan trọng",
       "Đây là so sánh hiệu suất từng năm với vốn khởi đầu $1000 *riêng từng năm*, không được cộng các phần trăm thành tổng lợi nhuận kép.",
       "Giá khớp Limit chỉ ước lượng từ H1 OHLC, không có tick để xác nhận thứ tự chạm TP/SL trong nến; nếu cùng nến chạm limit rồi SL, ghi nhận SL.",
       "Không có swap, lịch tin tức, spread tick thực của Exness; giới hạn 0,5R chỉ là rủi ro dự kiến tại thời điểm đặt lệnh.",
       "Các năm này không hoàn toàn còn là holdout nguyên vẹn do nghiên cứu những giai đoạn này trước đó. Đây là backtest khám phá, không phải bảo đảm lợi thế 5–8%/tháng."]
    (out/"BAO_CAO_LIMIT_TUNG_NAM.md").write_text("\n".join(lines))
    print("LIMIT YEARLY COMPLETE",json.dumps({m:{y:[round(v["return_pct"],2),v["filled"]] for y,v in rs.items()} for m,rs in res.items()}),flush=True)

if __name__=="__main__":main()
