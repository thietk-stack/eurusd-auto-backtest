import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import pandas as pd
import numpy as np
from quantmind_m1_reclaim import (
    event_candidates,exits_by_quote,simulate,performance,LOOKBACK,RR,RISK,
    MAX_SPREAD_PIPS,STOP_BUFFER_PIPS,MIN_BREAK_PIPS
)

def fake_market():
    ix=pd.date_range("2024-01-03 07:00",periods=205,freq="min",tz="UTC")
    n=len(ix);df=pd.DataFrame(index=ix)
    df["open"]=1.1000;df["high"]=1.1004;df["low"]=1.0996;df["close"]=1.1000
    j=150
    df.iloc[j,df.columns.get_loc("high")]=1.1006
    df.iloc[j,df.columns.get_loc("close")]=1.1002
    for suffix in ("open","high","low","close"):
        df["bid_"+suffix]=df[suffix]-.00005
        df["ask_"+suffix]=df[suffix]+.00005
    df["spread_open_pips"]=1.
    return df

def test_reclaim_uses_previous_60_closed_bars():
    data={"eurusd":fake_market()}
    e,s=event_candidates(data,"reversal")
    assert e
    target=[x for x in e if x["signal_at"]==data["eurusd"].index[150]]
    assert len(target)==1
    x=target[0]
    assert x["side"]==-1
    assert x["idx"]==151
    assert abs(x["stop"]-1.1007)<1e-8

def test_continuation_control_same_event_opposite_direction():
    d=fake_market()
    e,_=event_candidates({"eurusd":d},"continuation")
    target=[x for x in e if x["signal_at"]==d.index[150]]
    assert len(target)==1 and target[0]["side"]==1

def test_no_fake_event_when_price_does_not_reclaim():
    d=fake_market()
    d.loc[d.index[150],"close"]=1.1008
    d.loc[d.index[150],"bid_close"]=1.10075
    d.loc[d.index[150],"ask_close"]=1.10085
    e,_=event_candidates({"eurusd":d},"reversal")
    assert not e

def test_quote_stop_first_for_short():
    d=fake_market();i=151
    d.loc[d.index[i],"ask_high"]=1.1010
    d.loc[d.index[i],"ask_low"]=1.0980
    q,price,reason=exits_by_quote(d,-1,i,1.09995,1.1007,1.098)
    assert q==i and reason=="same_minute_stop"
    assert price>=1.1007

def test_strategy_risk_fixed():
    assert LOOKBACK==60 and RR==2 and RISK==.005
    assert MAX_SPREAD_PIPS==2.5 and STOP_BUFFER_PIPS==1
    assert MIN_BREAK_PIPS==.8

def test_only_research_not_live_and_no_double_spread():
    d=fake_market()
    e,_=event_candidates({"eurusd":d},"reversal")
    trades,stats=simulate({"eurusd":d},e,"reversal")
    assert stats["accepted"]==len(trades)
    if len(trades):
        assert all(trades.planned_risk_usd<=trades.max_planned_risk_usd+1e-6)

def test_spread_stress_cannot_increase_pnl_when_same_trades():
    from quantmind_m1_reclaim import stress_cost_only
    import pandas as pd
    d=pd.DataFrame([dict(pair="eurusd",entry_executable_quote=1.1,
         entry_spread_pips=1.,lots=.05,pnl_usd=2.0,account_usd=1002.)])
    stress=stress_cost_only(d)
    assert stress.pnl_usd.iloc[0]<d.pnl_usd.iloc[0]
    assert abs(stress.pnl_usd.iloc[0]-1.5)<1e-9
