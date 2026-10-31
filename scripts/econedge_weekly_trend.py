#!/usr/bin/env python3
"""ECONEDGE FX v1 — pre-registered weekly time-series trend versus matched placebo.

Dukascopy authentic H1 bid/ask; signal uses ONLY 480 closed observed H1 bars,
and one position per week, from Monday 08 UTC through Friday 20 UTC.
Real broker overnight swap and tick OHLC unavailable: never represent as
complete Exness execution. No orders, live broker APIs, or optimizer.
"""
import json,math
from pathlib import Path
import numpy as np
import pandas as pd
from htf_limit_mid_yearly import historical_prices
from portfolio_research import SYMBOLS,PIPS

OUT=Path("econedge_weekly_trend_results")
START_CAPITAL=1000.
RISK=.005
LEVERAGE=5.
LOT_STEP=.01
HISTORY_BARS=480
ROLLING_VOL_BARS=480
STOP_MEDIAN_BARS=72
STOP_ATR_MULT=6.
STOP_MIN_PIPS=8.
STOP_MAX_PIPS=70.
MIN_TREND_Z=.8
SLIPPAGE_PIPS=.1
SPREAD_MAX_PIPS=8.
BOOTSTRAP_SEED=20261031
BOOTSTRAP_BLOCK_WEEKS=8
BOOTSTRAP_REPLICATES=2500
PERIODS={
 "discovery_2019_2021":(2019,2022),
 "validation_2022_2023":(2022,2024),
 "later_2024_2025":(2024,2026)
}

def raw_signal_from_closed_closes(close, signal_index,logret=None):
    """Causal: latest observed close index j, compare exactly j-480."""
    j=int(signal_index)
    if j<HISTORY_BARS:return None
    if logret is None:logret=np.diff(np.log(np.asarray(close,float)),prepend=np.nan)
    window=np.asarray(logret[j-ROLLING_VOL_BARS+1:j+1],float)
    if len(window)!=ROLLING_VOL_BARS or not np.isfinite(window).all():return None
    volatility=float(np.std(window,ddof=1))
    if not np.isfinite(volatility) or volatility<1e-10:return None
    z=(float(np.log(close[j]))-float(np.log(close[j-HISTORY_BARS])))/(volatility*np.sqrt(ROLLING_VOL_BARS))
    return float(z)

def build_weekly_events(index,prices,first_year=2019,last_year=2025):
    # Candidate decision at Monday 08:00 UTC, ONLY uses previous closed H1.
    monday=np.flatnonzero((index.dayofweek==0)&(index.hour==8))
    computed={}
    for sym in SYMBOLS:
        p=prices[sym];pip=PIPS[sym]
        closes=p.close.to_numpy(float)
        hi=p.high.to_numpy(float);lo=p.low.to_numpy(float)
        logret=np.diff(np.log(closes),prepend=np.nan)
        med=(pd.Series((hi-lo)/pip)
            .rolling(STOP_MEDIAN_BARS,min_periods=STOP_MEDIAN_BARS)
            .median().to_numpy(float))
        computed[sym]=(closes,logret,med)
    events=[]
    for i in monday:
        now=index[i];j=i-1
        if now.year<first_year or now.year>last_year or j<HISTORY_BARS:continue
        opportunities=[]
        for sym in SYMBOLS:
            closes,ret,med=computed[sym]
            score=raw_signal_from_closed_closes(closes,j,ret)
            if score is None or not np.isfinite(med[j]):continue
            stop_pips=max(STOP_MIN_PIPS,STOP_ATR_MULT*float(med[j]))
            opportunities.append(dict(sym=sym,z=score,stop_pips=float(stop_pips)))
        if not opportunities:continue
        opportunities.sort(key=lambda x:(-abs(x["z"]),x["sym"]))
        top=opportunities[0]
        cutoff=now.normalize()+pd.Timedelta(days=4,hours=20)
        end=int(index.searchsorted(cutoff,side="right")-1)
        if end<=i or cutoff.year!=now.year:continue
        # Never include next week because Monday signal needs flat portfolio.
        if index[end].isocalendar().week!=now.isocalendar().week:
            continue
        events.append(dict(entry_idx=int(i),end_idx=end,time=now,
            exit_deadline=cutoff,sym=top["sym"],
            z=top["z"],stop_pips=top["stop_pips"],
            momentum_direction=1 if top["z"]>0 else -1,
            qualifies=abs(top["z"])>=MIN_TREND_Z))
    return events

def quote_spread(p,i,pip):
    spread=(float(p.ask_open.iloc[i])-float(p.bid_open.iloc[i]))/pip
    if not np.isfinite(spread) or spread<0:raise ValueError("Invalid genuine quote spread")
    return float(spread)

def evaluate_trade(prices,event,side,cash):
    sym=event["sym"];p=prices[sym];pip=PIPS[sym]
    i=event["entry_idx"];end=event["end_idx"]
    if event["stop_pips"]>STOP_MAX_PIPS:
        return None,"stop_too_wide"
    sp=quote_spread(p,i,pip)
    if sp>SPREAD_MAX_PIPS:return None,"spread_too_wide"
    entry_q=(float(p.ask_open.iloc[i])+SLIPPAGE_PIPS*pip if side==1
             else float(p.bid_open.iloc[i])-SLIPPAGE_PIPS*pip)
    stop=(entry_q-side*event["stop_pips"]*pip)
    riskp=event["stop_pips"]+SLIPPAGE_PIPS
    point=10. if sym!="usdjpy" else 1000./entry_q
    maxlot_by_risk=(cash*RISK)/(riskp*point)
    maxlot_by_lev=(cash*LEVERAGE)/(100000*(1. if sym=="usdjpy" else entry_q))
    lots=math.floor((min(maxlot_by_risk,maxlot_by_lev,.5)+1e-11)/LOT_STEP)*LOT_STEP
    if lots<LOT_STEP-1e-10:return None,"min_lot_incompatible_with_risk"
    # Respect optional 0.001 lot research variant; 0.01 baseline unchanged.
    # Rounding every size to two decimals would overstate a 0.003-lot position
    # as 0.00 or 0.01 and invalidate its fixed 0.5% risk guarantee.
    lots=round(lots,max(2,round(-math.log10(LOT_STEP))))
    designed_risk_usd=riskp*point*lots
    if designed_risk_usd>cash*RISK+1e-6:
        raise AssertionError("Designed stop risk >0.5%")
    result=None
    # Friday 20:00 exit is at the beginning of cutoff H1 (so don't peek
    # at its future HIGH/LOW); previous bars are used for stop.
    for k in range(i,end+1):
        if k==end and p.index[k]==event["exit_deadline"]:
            break
        spread_k=quote_spread(p,k,pip)
        if side==1:
            # H1 low is mid-price; bid_low approximated using known OPEN spread.
            observed_low=float(p.low.iloc[k])-.5*spread_k*pip
            if observed_low<=stop:
                exit_quote=min(stop,float(p.bid_open.iloc[k]))
                reason="stop";result=(k,exit_quote,reason);break
        else:
            observed_high=float(p.high.iloc[k])+.5*spread_k*pip
            if observed_high>=stop:
                exit_quote=max(stop,float(p.ask_open.iloc[k]))
                reason="stop";result=(k,exit_quote,reason);break
    if result is None:
        k=end
        if p.index[k]==event["exit_deadline"]:
            exit_q=(float(p.bid_open.iloc[k]) if side==1
                    else float(p.ask_open.iloc[k]))
        else:
            # Source's CSV verifies opening bid/ask but not closing bid/ask.
            # The last H1 midpoint CLOSE is converted to an estimated
            # exit quote using half this bar's observed OPEN spread.
            sp_at_close_proxy=quote_spread(p,k,pip)
            exit_q=float(p.close.iloc[k])-side*.5*sp_at_close_proxy*pip
        result=(k,exit_q,"friday_flat")
    k,exit_quote,reason=result
    spread_out=quote_spread(p,k,pip)
    # Quote already includes roundtrip spread. One 0.1 pip slippage was added
    # at the entry side. Subtract one extra 0.1pip for exit slippage only.
    gross_pips=side*(exit_quote-entry_q)/pip
    net_pips=gross_pips-SLIPPAGE_PIPS
    pnlusd=net_pips*point*lots
    spread_stress_extra=(sp+spread_out)*.5*point*lots
    trade=dict(time=event["time"].isoformat(),year=int(event["time"].year),
        week=f"{event['time'].isocalendar().year}-{event['time'].isocalendar().week:02d}",
        pair=sym,side="BUY" if side==1 else "SELL",
        z_momentum=event["z"],signal_stop_pips=event["stop_pips"],
        entry_mid=float(p.open.iloc[i]),entry_quote=entry_q,stop_quote=stop,
        exit_time=p.index[k].isoformat(),exit_quote=exit_quote,
        exit_reason=reason,lot=lots,designed_risk_usd=designed_risk_usd,
        budget_usd=cash*RISK,entry_spread_pips=sp,exit_spread_pips=spread_out,
        quote_and_slippage_net_pips=net_pips,pnl_usd=pnlusd,
        extra_spread_x2_cost_usd=spread_stress_extra,
        pnl_x2_usd=pnlusd-spread_stress_extra,
        equity_usd=cash+pnlusd)
    return trade,None

def weekly_replay(events,prices,start_year,end_year,mode):
    cash=START_CAPITAL
    ledger=[];counts=dict(weekly_decisions=0,rejected_zscore=0,
       rejected_stop=0,rejected_spread=0,rejected_min_lot=0,entered=0)
    decisions=[]
    for event in events:
        if not(start_year<=event["time"].year<end_year):continue
        counts["weekly_decisions"]+=1
        if not event["qualifies"]:
            counts["rejected_zscore"]+=1
            decisions.append(dict(time=event["time"].isoformat(),pair=event["sym"],
                 score=event["z"],reason="below_threshold",mode=mode))
            continue
        side=event["momentum_direction"]*(1 if mode=="trend" else -1)
        tr,why=evaluate_trade(prices,event,side,cash)
        if tr is None:
            counts[{"stop_too_wide":"rejected_stop",
                 "spread_too_wide":"rejected_spread",
                 "min_lot_incompatible_with_risk":"rejected_min_lot"}[why]]+=1
            decisions.append(dict(time=event["time"].isoformat(),pair=event["sym"],
                   score=event["z"],reason=why,mode=mode))
            continue
        cash+=tr["pnl_usd"]
        if abs(cash-tr["equity_usd"])>1e-5:raise AssertionError("Broken equity")
        tr["mode"]=mode
        ledger.append(tr);counts["entered"]+=1
        decisions.append(dict(time=event["time"].isoformat(),pair=event["sym"],
          score=event["z"],reason="entered",mode=mode))
    trades=pd.DataFrame(ledger)
    return trades,counts,pd.DataFrame(decisions)

def block_bootstrap_lower(weekly_dollars,nreps=BOOTSTRAP_REPLICATES):
    """Circular moving-block bootstrap on a weekly $1,000-account ledger;
    return 5th percentile mean weekly PnL (one-sided 95% proxy).
    """
    x=np.asarray(weekly_dollars,dtype=float)
    if len(x)<10:return None
    rng=np.random.default_rng(BOOTSTRAP_SEED)
    b=min(BOOTSTRAP_BLOCK_WEEKS,len(x))
    k=math.ceil(len(x)/b)
    out=[]
    for _ in range(nreps):
        starts=rng.integers(0,len(x),size=k)
        draw=np.concatenate([np.take(x,np.arange(i,i+b)%len(x)) for i in starts])[:len(x)]
        out.append(draw.mean())
    return float(np.percentile(out,5))

def metrics(trades,counts,events,start_year,end_year):
    valid=[e for e in events if start_year<=e["time"].year<end_year]
    weekly={e["time"].isoformat():0. for e in valid}
    if trades.empty:
        return dict(**counts,net_return_pct=0.,net_usd=0.,spread_x2_net_usd=0.,
            spread_x2_return_pct=0.,pf=None,win_rate=None,
            dd_closed_pct=0.,bootstrap_lower_mean_week_usd=block_bootstrap_lower(list(weekly.values())),
            median_stop_pips=None,stop_fills=0)
    for rec in trades.itertuples(index=False):
        weekly[rec.time]=rec.pnl_usd
    pnl=trades.pnl_usd.to_numpy(float)
    eq=START_CAPITAL+np.cumsum(pnl)
    peak=np.maximum.accumulate(np.r_[START_CAPITAL,eq])[1:]
    pos=float(pnl[pnl>0].sum());neg=float(-pnl[pnl<0].sum())
    return dict(**counts,net_return_pct=float((eq[-1]/START_CAPITAL-1)*100),
        net_usd=float(pnl.sum()),spread_x2_net_usd=float(trades.pnl_x2_usd.sum()),
        spread_x2_return_pct=float(trades.pnl_x2_usd.sum()/START_CAPITAL*100),
        pf=pos/neg if neg else None,win_rate=float((pnl>0).mean()),
        dd_closed_pct=float(np.min((eq/peak-1)*100)),
        bootstrap_lower_mean_week_usd=block_bootstrap_lower(list(weekly.values())),
        median_stop_pips=float(trades.signal_stop_pips.median()),
        stop_fills=int((trades.exit_reason=="stop").sum()))

def audit(trades):
    if trades.empty:return
    if (trades.designed_risk_usd>trades.budget_usd+1e-6).any():
        raise AssertionError("Risk >0.5%")
    if not (trades.lot>=LOT_STEP-1e-10).all():raise AssertionError("Min configured lot")
    weeks=trades.week.to_numpy(str)
    if len(np.unique(weeks))!=len(weeks):raise AssertionError("Duplicate weekly trade")
    if (trades.extra_spread_x2_cost_usd<0).any() or (trades.pnl_x2_usd>trades.pnl_usd+1e-7).any():
        raise AssertionError("Stress cannot improve return")
    if not (trades.signal_stop_pips>=STOP_MIN_PIPS).all() or not (trades.signal_stop_pips<=STOP_MAX_PIPS).all():
        raise AssertionError("Stop outside frozen bands")

def main():
    OUT.mkdir(exist_ok=True)
    ix,prices=historical_prices()
    events=build_weekly_events(ix,prices)
    if len(events)<270:raise RuntimeError("Not enough jointly observed real H1 Monday entries")
    results={};weekly_details=[]
    for part,(first,last) in PERIODS.items():
        results[part]={}
        for model in ("trend","opposite_control"):
            trades,counts,decisions=weekly_replay(events,prices,first,last,model)
            audit(trades)
            trades.to_csv(OUT/(part+"_"+model+"_trades.csv"),index=False)
            decisions.to_csv(OUT/(part+"_"+model+"_decisions.csv"),index=False)
            result=metrics(trades,counts,events,first,last)
            result["yearly_realized_pnl_usd"]={
               str(year):round(float(trades.loc[trades.year==year,"pnl_usd"].sum()),7)
               if not trades.empty else 0. for year in range(first,last)}
            results[part][model]=result
            print("ECONEDGE",part,model,"trades",result["entered"],
               "pnlUSD",round(result["net_usd"],4),"x2",round(result["spread_x2_net_usd"],4),flush=True)
    v=results["validation_2022_2023"];h=results["later_2024_2025"]
    def gate(main,ctrl,n):
        return (main["entered"]>=n and main["net_usd"]>0 and
           main["spread_x2_net_usd"]>0 and (main["pf"] or 0)>1.1 and
           main["net_usd"]>ctrl["net_usd"] and
           (main["bootstrap_lower_mean_week_usd"] or -1000)>0)
    validated=gate(v["trend"],v["opposite_control"],35)
    later_pass=gate(h["trend"],h["opposite_control"],45)
    summary=dict(research_only=True,method="4-week causal H1 time-series momentum weekly hold with matched opposite sign",
       data="SHA256 verified Dukascopy BID/ASK H1 2018-2025 four pairs; H1 mid high/low quote proxy for stop; no swap",
       common_observed_hourly_bars=len(ix),weekly_opportunities=len(events),
       symbols=SYMBOLS,z_threshold=MIN_TREND_Z,
       history_bars=HISTORY_BARS,stop_atr_multiple=STOP_ATR_MULT,
       stop_min_pips=STOP_MIN_PIPS,stop_max_pips=STOP_MAX_PIPS,
       exit="Flat by Friday 20 UTC or stop-first",
       risk_fraction=RISK,leverage=LEVERAGE,min_lot=LOT_STEP,
       stress="Same filled trades, extra half entry and half exit quoted spread",
       reset="Separate $1000 account for discovery/validation/later; each segment internally compounds",
       results=results,validation_pass=validated,later_pass=later_pass,
       verdict="NO_GO" if not(validated and later_pass) else "PAPER_FORWARD_ONLY",
       place_real_orders=False,
       caveats=["Past years 2019-25 have been studied under other price action strategies: not pristine out-of-sample",
        "This is spot FX quote-price profit only; no carry/swap/financing included",
        "H1 OHLC midpoint extremes with half opening spread approximate real bid-low/ask-high; not true tick",
        "No guaranteed maximum 0.5% realized loss on gaps",
        "One trading idea weekly and minimum 0.01 lot creates many real-world lot size rejections"])
    (OUT/"RESULTS_ECONEDGE_TREND.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str))
    lines=["# ECONEDGE FX v1 — xu hướng bốn tuần, giữ một tuần — kiểm định có đối chứng ngược hướng",
        "","Dùng giá Bid/Ask H1 Dukascopy THẬT; quyết định từ 480 nến H1 đã đóng; nhập lệnh thứ Hai 08 UTC, chốt trước cuối tuần hoặc SL. Không TP 2R cố định, vì nghiên cứu sự kéo dài của xu hướng.",
        "Rủi ro stop thiết kế tối đa 0,5% equity; 0,01 lot tối thiểu, 5× đòn bẩy, không vượt 1 entry/tuần. Không tính swap/carry.",
        "","| Kỳ (vốn reset $1000) | Nhánh | Tuần quan sát | Lệnh | Bỏ do min lot | Lãi/lỗ USD | Return kỳ | PF | DD | Stress spread x2 USD | Bootstrap lower mean $/week |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    f=lambda z:"—" if z is None else f"{z:.3f}"
    for part in PERIODS:
        for model in ("trend","opposite_control"):
            r=results[part][model]
            lines.append(f"| {part} | {model} | {r['weekly_decisions']} | {r['entered']} | {r['rejected_min_lot']} | {r['net_usd']:+.2f} | {r['net_return_pct']:+.2f}% | {f(r['pf'])} | {r['dd_closed_pct']:.2f}% | {r['spread_x2_net_usd']:+.2f} | {f(r['bootstrap_lower_mean_week_usd'])} |")
    lines+=["",f"Validation gate: **{validated}**; later gate: **{later_pass}**. **Quyết định:** {summary['verdict']}.",
      "Đây là kết quả giá spot chưa tính swap/financing: không thể đồng nhất với lợi nhuận carry hay PnL broker. Kiểm định spread x2 vẫn không mô phỏng tick/overnight gap thực.",
      "Khối giá 2024–25 từng được sử dụng trong nhiều vòng chiến lược, nên kết quả khám phá không được gọi xác nhận ngoài mẫu nguyên vẹn. Nếu muốn carry cần lịch sử rates+swap có kiểm toán."]
    (OUT/"BAO_CAO_ECONEDGE_TREND.md").write_text("\n".join(lines))
    print("ECONEDGE COMPLETE",json.dumps({p:{m:[r['entered'],round(r['net_usd'],2)] for m,r in arms.items()} for p,arms in results.items()}),flush=True)
if __name__=="__main__":main()
