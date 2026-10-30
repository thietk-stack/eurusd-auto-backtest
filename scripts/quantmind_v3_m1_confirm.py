#!/usr/bin/env python3
"""QuantMind FX v3: precommitted M1 confirmation to avoid Monday-first bias.

Two separate trading policies on authentic Dukascopy M1 bid/ask:
  CONTROL: first false-break reclaim Tue-Thu 10-16 UTC each ISO week.
  CONFIRMED: same false-break, then a COMPLETED following M1 candle that
    closes >=.25 pip further inside reclaimed range without retesting sweep
    extreme and with compressed spread. Entry at subsequent real M1 OPEN.

Frozen design BEFORE looking at 2026 M1 performance. No fitted or prompt-
generated labels, no fake interpolation, no trade execution. Monthly resets.
"""
import os,json
from pathlib import Path
import pandas as pd
import numpy as np
from portfolio_research import SYMBOLS,PIPS
import quantmind_m1_reclaim as prior

OUT=Path("v3_confirmed_reclaim_results")
CONFIRM_DELTA_PIPS=.25
CONFIRM_SPREAD_MAX_RATIO_TO_SIGNAL=1.0
CONFIRM_SPREAD_MAX_RATIO_TO_PREV_MEDIAN=1.10
WEEKDAYS=(1,2,3)   # Tue Wed Thu in UTC
HOURS=(10,16)     # [10:00,16:00) UTC
DATE_START="2026-01-01"
DATE_END="2026-10-01"

def same_utc_minute(df,i,k):
    return (i>=0 and k<len(df) and
            df.index[k]-df.index[i]==pd.Timedelta(minutes=(k-i)))

def permit_clock(ts):
    return ts.dayofweek in WEEKDAYS and HOURS[0]<=ts.hour<HOURS[1]

def confirmation_event(df, event, pip):
    """No future values used before the confirmation M1 CLOSE."""
    i=event["idx"]     # first bar after original sweep j=i-1
    j=i-1;k=i+1       # trade entry only at OPEN of k
    if not same_utc_minute(df,j,i) or not same_utc_minute(df,i,k):
        return None
    signal=df.iloc[j];confirm=df.iloc[i]
    direction=event["side"]  # reversal BUY=+1 after down-sweep, SELL=-1 after up
    if direction*(float(confirm.close)-float(signal.close)) < CONFIRM_DELTA_PIPS*pip-1e-9:
        return None
    if direction==1 and confirm.low<signal.low-1e-9:return None
    if direction==-1 and confirm.high>signal.high+1e-9:return None
    # Spread from ACTUAL completed bid/ask quotes at M1 close.
    cs=max(0.,float(confirm.ask_close-confirm.bid_close)/pip)
    ss=max(0.,float(signal.ask_close-signal.bid_close)/pip)
    if cs>ss*CONFIRM_SPREAD_MAX_RATIO_TO_SIGNAL+1e-8:return None
    start=max(0,i-120)
    if i-start<120:return None
    hist=(df.ask_close.iloc[start:i]-df.bid_close.iloc[start:i]).to_numpy(float)/pip
    typical=float(np.median(hist))
    if not np.isfinite(typical) or typical<=0:return None
    if cs>CONFIRM_SPREAD_MAX_RATIO_TO_PREV_MEDIAN*typical+1e-8:return None
    if cs>prior.MAX_SPREAD_PIPS:return None
    new=dict(event)
    new["idx"]=k;new["time"]=df.index[k]
    new["initial_sweep_at"]=event["signal_at"]
    new["signal_at"]=df.index[i] # at i's CLOSE, only then submitted
    new["confirm_close_spread_pips"]=cs
    new["confirm_delta_pips"]=direction*(float(confirm.close)-float(signal.close))/pip
    return new

def select_event_cohorts(data):
    raw,source_stats=prior.event_candidates(data,"reversal")
    control=[];confirmed=[]
    reject={"all_false_break_candidates":len(raw),"control_in_window":0,
        "confirmation_after_valid_reclaim":0,"confirmation_in_window":0}
    for e in raw:
        sym=e["symbol"];df=data[sym];pip=PIPS[sym]
        if permit_clock(e["time"]):
            control.append(e);reject["control_in_window"]+=1
        ce=confirmation_event(df,e,pip)
        if ce is None:continue
        reject["confirmation_after_valid_reclaim"]+=1
        if permit_clock(ce["time"]):
            confirmed.append(ce);reject["confirmation_in_window"]+=1
    for events in (control,confirmed):
        events.sort(key=lambda x:(x["time"],-x["sweep_distance_pips"],x["symbol"]))
    return {"control":control,"confirmed":confirmed},source_stats,reject

def quality_checks(df,mode):
    if df.empty:return
    t=pd.to_datetime(df.time,utc=True)
    if not t.dt.dayofweek.isin(WEEKDAYS).all() or not t.dt.hour.between(HOURS[0],HOURS[1]-1).all():
        raise AssertionError("Trade outside frozen Tue-Thu 10-16 UTC window")
    if t.dt.strftime("%G-%V").duplicated().any():
        raise AssertionError("Over one trade per ISO week within month")
    if (df.planned_risk_usd>df.max_planned_risk_usd+1e-6).any():
        raise AssertionError("Exceeded 0.5% designed stop risk")
    if (df.lots<.01).any():raise AssertionError("Below .01 lot")
    if mode=="confirmed":
        ts=pd.to_datetime(df.signal_time,utc=True)
        if not ((t-ts)==pd.Timedelta(minutes=1)).all():
            raise AssertionError("Entered before the confirmation bar was fully closed")

def main():
    OUT.mkdir(exist_ok=True)
    data,sources,start,end=prior.load_actual_quotes()
    if start<DATE_START or end>DATE_END:
        raise RuntimeError("Period not part of pre-registered 2026 Jan-Sep evaluation")
    cohorts,source_counts,audit=select_event_cohorts(data)
    result={}
    for mode,events in cohorts.items():
        trades,count=prior.simulate(data,events,mode)
        quality_checks(trades,mode)
        stress=prior.stress_cost_only(trades)
        trades.to_csv(OUT/(mode+"_trades.csv"),index=False)
        result[mode]={"base":prior.performance(trades,count),
           "spread_x2_same_fills":prior.performance(stress,count)}
        print("V3",start,mode,"candidates",len(events),"trades",len(trades),
           "pnl",round(result[mode]["base"]["pnl_usd"],4),flush=True)
    obj=dict(status="HISTORICAL_RESEARCH_ONLY",date_from=start,date_to=end,
      data_source="Genuine Dukascopy M1 bid and ask with SHA256 checked",
      symbols=list(SYMBOLS),source_audit=sources,
      confirmation="Next M1 closes >=0.25pip farther inside original range, never revisits the extreme, completed close spread <= original and <=1.10x last 120 M1",
      entry="Following confirmed bar OPEN executable BID ASK; no contemporaneous use of incomplete candle",
      time_window="Tue-Wed-Thu 10:00-16:00 UTC",
      stop="Outside sweep M1 extreme by 1pip",target="Projected net +2R",
      cost="Real bid/ask and estimated 0.1pip slippage per side; spread x2 subtracts same-trade additional spread only",
      risk_fraction=.005,account_reset_each_month=1000,
      max_one_entry_per_iso_week_per_month=True,
      original_event_counts=source_counts,filter_counts=audit,results=result,
      live_broker_orders=0,limitations=[
      "M1 OHLC lacks true quote tick ordering. Stop first on entry minute.",
      "The initial old event extractor includes first-next-open stop-distance feasibility; kept identical in both arms.",
      "Monthly accounts reset independently; no continuous nine-month compounded result.",
      "Historical quote prices from Dukascopy do not assure actual Exness execution, swap or fill.","2026 M1 study is a new price resolution but not pristine multi-research holdout at overall project level."])
    (OUT/"RESULTS_V3_MONTH.json").write_text(json.dumps(obj,ensure_ascii=False,indent=2))
    print("V3_MONTH_COMPLETE",start,audit,flush=True)
if __name__=="__main__":main()
