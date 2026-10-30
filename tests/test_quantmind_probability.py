import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import numpy as np
import pandas as pd
from quantmind_probability import (
    label_first_touch,TRAIN_END,CAL_END,VAL_END,TEST_END,
    MODEL_PROB_MIN,MEMORY_PROB_MIN,FINAL_PROB_MIN,HORIZON,RISK,
    predictive_quality
)

def market(hi,lo,op,close):
    n=len(hi)
    t=pd.date_range("2023-01-02",periods=n,freq="h",tz="UTC")
    return pd.DataFrame(dict(high=hi,low=lo,open=op,close=close),index=t)

def test_takes_profit_exact_net_two_r():
    d=market([1.1005,1.1035]*12,[1.0995,1.0995]*12,
             [1.1]*24,[1.102]*24)
    x=label_first_touch(d,0,1,1.1000,10,23,1,.0001)
    assert x["target_hit"]
    assert abs(x["net_pips"]-22)<1e-8

def test_stop_first_when_target_and_stop_in_same_bar():
    d=market([1.1035]*24,[1.0985]*24,[1.1000]*24,[1.1000]*24)
    x=label_first_touch(d,0,1,1.1000,10,23,1,.0001)
    assert not x["target_hit"]
    assert x["reason"]=="stop"
    assert abs(x["net_pips"]+11)<1e-8

def test_symmetric_short_tp():
    d=market([1.1005]*24,[1.0965]*24,[1.1]*24,[1.098]*24)
    x=label_first_touch(d,0,-1,1.1000,10,23,1,.0001)
    assert x["target_hit"]
    assert abs(x["net_pips"]-22)<1e-8

def test_zero_trades_not_fictitious_profitable():
    from quantmind_probability import metrics
    x=metrics(pd.DataFrame())
    assert x["trades"]==0 and x["net_pct"]==0

def test_probability_quality_training_prior_only():
    df=pd.DataFrame({"y":[1,0,0,0],
      "prob_guarded":[.25,.25,.25,.25],
      "prob_ml":[.5]*4,"prob_memory":[.5]*4})
    q=predictive_quality(df,.4)
    assert abs(q["constant_prior_brier"]-(.6**2+3*.4**2)/4)<1e-10

def test_locked_periods_risk_and_gate():
    assert [TRAIN_END,CAL_END,VAL_END,TEST_END]==[
        "2023-01-01","2023-07-01","2024-01-01","2026-01-01"]
    assert HORIZON==24 and RISK==.005
    assert [MODEL_PROB_MIN,MEMORY_PROB_MIN,FINAL_PROB_MIN]==[.4,.4,.48]
