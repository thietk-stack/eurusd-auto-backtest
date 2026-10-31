import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import numpy as np
import pandas as pd
import econedge_long_2011_2025 as long
from econedge_weekly_trend import build_weekly_events, raw_signal_from_closed_closes

def test_long_15year_study_periods_frozen():
    assert long.FIRST_MONTH=="2010-01"
    assert long.FINAL_MONTH=="2025-12"
    assert long.PERIODS["new_2011_2017"]==(2011,2018)
    assert long.PERIODS["all_2011_2025"]==(2011,2026)
    assert long.PERIODS["reused_2018_2025"]==(2018,2026)

def test_trade_signal_no_future_data():
    x=np.exp(np.cumsum(np.r_[np.log(1.1),np.linspace(.00002,.0001,650)]))
    z=raw_signal_from_closed_closes(x,510)
    future=x.copy()
    future[511:]*=1.03
    assert raw_signal_from_closed_closes(future,510)==z

def test_original_default_not_mutated():
    assert build_weekly_events.__defaults__==(2019,2025)

def test_long_extension_must_use_real_sha256_192months():
    import inspect
    src=inspect.getsource(long.verified_16_year_data)
    assert "verify_month(" in src
    assert "len(months)==192" in src
    assert "ffill" not in src and "interpolate" not in src

def test_new_earlier_sample_not_forward_holdout():
    assert long.PERIODS["new_2011_2017"][1] <= long.PERIODS["reused_2018_2025"][0]
