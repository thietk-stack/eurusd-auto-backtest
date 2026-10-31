import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import numpy as np
import pandas as pd
from econedge_weekly_trend import (raw_signal_from_closed_closes,
    evaluate_trade,block_bootstrap_lower,RISK,START_CAPITAL,
    MIN_TREND_Z,STOP_ATR_MULT,LOT_STEP,SPREAD_MAX_PIPS,PIPS)

def sample_prices():
    idx=pd.date_range("2024-01-01 08:00",periods=110,freq="h",tz="UTC")
    df=pd.DataFrame(index=idx)
    df["open"]=1.1000;df["high"]=1.1004;df["low"]=1.0996;df["close"]=1.1000
    df["bid_open"]=1.09995;df["ask_open"]=1.10005
    return df

def event(df):
    return dict(sym="eurusd",entry_idx=0,end_idx=108,time=df.index[0],
        exit_deadline=df.index[108],stop_pips=12.,z=1.5,
        momentum_direction=1,qualifies=True)

def test_momentum_uses_only_closed_data():
    x=np.exp(np.cumsum(np.r_[np.log(1.1),np.full(600,0.00008)+
        .00001*np.sin(np.arange(600))]))
    z=raw_signal_from_closed_closes(x,490)
    assert z>0
    altered=x.copy()
    altered[491:]*=0.5
    assert raw_signal_from_closed_closes(altered,490)==z

def test_stop_has_at_most_half_percent_designed_risk():
    df=sample_prices()
    rec,reason=evaluate_trade({"eurusd":df},event(df),1,START_CAPITAL)
    assert reason is None
    assert rec["lot"]>=LOT_STEP
    assert rec["designed_risk_usd"]<=START_CAPITAL*RISK+1e-7
    assert rec["pnl_x2_usd"]<=rec["pnl_usd"]+1e-8
    assert rec["exit_reason"]=="friday_flat"

def test_stop_first_and_gap_worse_than_planned_stop():
    df=sample_prices()
    df.iloc[1,df.columns.get_loc("low")]=1.0986
    tr,_=evaluate_trade({"eurusd":df},event(df),1,1000.)
    assert tr["exit_reason"]=="stop"
    assert pd.Timestamp(tr["exit_time"])==df.index[1]

def test_min_lot_not_force_oversized_risk():
    df=sample_prices()
    e=event(df);e["stop_pips"]=70
    tr,why=evaluate_trade({"eurusd":df},e,1,START_CAPITAL)
    assert tr is None
    assert why=="min_lot_incompatible_with_risk"

def test_stop_too_wide_skips_instead_of_truncating():
    df=sample_prices();e=event(df);e["stop_pips"]=71
    tr,why=evaluate_trade({"eurusd":df},e,1,START_CAPITAL)
    assert tr is None and why=="stop_too_wide"

def test_bootstrap_zero_returns_no_fake_profits():
    a=block_bootstrap_lower([0]*16,128)
    assert a==0
    b=block_bootstrap_lower([-1]*16,128)
    assert b<0

def test_parameters_frozen():
    assert RISK==.005 and MIN_TREND_Z==.8
    assert STOP_ATR_MULT==6 and LOT_STEP==.01
    assert SPREAD_MAX_PIPS==8
    assert PIPS["usdjpy"]==.01
