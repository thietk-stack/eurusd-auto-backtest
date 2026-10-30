import sys
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from htf_engulf_next_candle import allowed_limit_fill, signal_at, MIN_RR_NET, RISK

def test_next_candle_buy_limit_only_if_price_retraces():
    assert allowed_limit_fill(1,1.0850,1.0860,1.0870,1.0851,1.0830) is None
    assert allowed_limit_fill(1,1.0850,1.0860,1.0870,1.0845,1.0830) == 1.0850
    assert allowed_limit_fill(1,1.0850,1.0848,1.0860,1.0840,1.0830) == 1.0848
    assert allowed_limit_fill(1,1.0850,1.0825,1.0870,1.0810,1.0830) is None

def test_next_candle_sell_limit_only_if_retraces():
    assert allowed_limit_fill(-1,1.0850,1.0840,1.0849,1.0830,1.0880) is None
    assert allowed_limit_fill(-1,1.0850,1.0840,1.0852,1.0830,1.0880) == 1.0850
    assert allowed_limit_fill(-1,1.0850,1.0860,1.0870,1.0840,1.0880) == 1.0860
    assert allowed_limit_fill(-1,1.0850,1.0890,1.09,1.084,1.0880) is None

def test_h4_signal_only_on_4h_close():
    ix=pd.date_range("2024-04-01 00:00",periods=16,freq="h",tz="UTC")
    feat={"eurusd":{"bull":np.zeros(16,dtype=bool),"bear":np.zeros(16,dtype=bool),
       "high":np.ones(16),"low":np.zeros(16),"close":np.ones(16)}}
    e={("eurusd","H4"):{4:dict(high=1.,low=.5,close=.9,side=1)}}
    assert signal_at(ix,feat,e,"eurusd","H4",4)["side"]==1
    assert signal_at(ix,feat,e,"eurusd","H4",5) is None

def test_fixed_risk_and_after_cost_rr():
    assert RISK==0.005
    assert MIN_RR_NET==1.5
