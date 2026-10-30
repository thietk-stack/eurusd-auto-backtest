import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import numpy as np
import pandas as pd
from quantmind_v3_m1_confirm import (
    confirmation_event, permit_clock, quality_checks, WEEKDAYS, HOURS,
    CONFIRM_DELTA_PIPS, CONFIRM_SPREAD_MAX_RATIO_TO_SIGNAL
)

def data():
    idx=pd.date_range("2026-01-07 10:00Z",periods=200,freq="min")
    df=pd.DataFrame(index=idx)
    df["open"]=1.1000;df["high"]=1.1005
    df["low"]=1.0995;df["close"]=1.1000
    # False break at index 129; confirmation 130 closes 0.5pip lower.
    df.iloc[129,df.columns.get_loc("high")]=1.1020
    df.iloc[130,df.columns.get_loc("high")]=1.1010
    df.iloc[130,df.columns.get_loc("close")]=1.09995
    for suf in ("open","high","low","close"):
        df["bid_"+suf]=df[suf]-.00005
        df["ask_"+suf]=df[suf]+.00005
    return df

def event(df):
    return dict(idx=130,side=-1,symbol="eurusd",time=df.index[130],
        signal_at=df.index[129],stop=1.1021,
        sweep_distance_pips=1.2)

def test_confirmation_uses_closed_next_bar_then_enters_next_open():
    df=data()
    out=confirmation_event(df,event(df),.0001)
    assert out is not None
    assert out["idx"]==131
    assert out["time"]==df.index[131]
    assert out["signal_at"]==df.index[130]
    assert out["confirm_delta_pips"]>=CONFIRM_DELTA_PIPS

def test_worse_spread_vetoes_even_if_candle_confirms():
    df=data()
    df.loc[df.index[130],"ask_close"]+=.0001
    assert confirmation_event(df,event(df),.0001) is None

def test_retest_of_sweep_extreme_rejected():
    df=data()
    df.loc[df.index[130],"high"]=1.1021
    assert confirmation_event(df,event(df),.0001) is None

def test_confirm_closing_too_close_rejected():
    df=data()
    df.loc[df.index[130],"close"]=1.099985
    assert confirmation_event(df,event(df),.0001) is None

def test_no_gap_between_confirmation_and_entry():
    df=data()
    df=df.drop(df.index[131])
    assert confirmation_event(df,event(df),.0001) is None

def test_no_monday_first_trade_in_new_strategy():
    assert not permit_clock(pd.Timestamp("2026-01-05 11:00Z"))
    assert permit_clock(pd.Timestamp("2026-01-07 11:00Z"))
    assert not permit_clock(pd.Timestamp("2026-01-07 16:00Z"))
    assert WEEKDAYS==(1,2,3) and HOURS==(10,16)

def test_lock_spread_threshold():
    assert CONFIRM_SPREAD_MAX_RATIO_TO_SIGNAL==1.0
