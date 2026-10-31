import sys,inspect
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import numpy as np
import pandas as pd
import econedge_eurgbp_15years_exact2026 as study
import econedge_weekly_trend as base

def test_exact_pairs_and_period():
    assert study.PAIRS==("eurusd","gbpusd")
    assert study.FIRST=="2010-01" and study.LAST=="2025-12"
    assert study.WINDOWS["historic_2011_2017"]==(2011,2018)
    assert study.WINDOWS["reused_2018_2025"]==(2018,2026)
    assert study.WINDOWS["full_2011_2025"]==(2011,2026)

def test_identical_original_stop_momentum_risk_and_lots():
    assert study.LOT_LEVELS==(.01,.001)
    assert base.HISTORY_BARS==480
    assert base.MIN_TREND_Z==.8
    assert base.STOP_ATR_MULT==6
    assert base.STOP_MAX_PIPS==70
    assert base.RISK==.005
    assert base.LEVERAGE==5.

def test_source_uses_exact_192_months_real_sha256():
    s=inspect.getsource(study.load_quotes)
    assert "len(months)==192" in s
    assert "verify_month(" in s
    assert "sha256" in s
    assert "interpolate" not in s and "ffill" not in s

def test_no_four_pair_candidate_ranking():
    s=inspect.getsource(study.frozen_two_pair_events)
    assert "base.SYMBOLS=PAIRS" in s
    assert "first_year=2011,last_year=2025" in s
    assert "exit_deadline" in s

def test_yearly_attribution_is_continuous_not_reset():
    trade=pd.DataFrame([
      dict(year=2011,time="2011-01-03T08:00:00+00:00",pnl_usd=10.,exit_reason="friday_flat"),
      dict(year=2012,time="2012-01-02T08:00:00+00:00",pnl_usd=-4.,exit_reason="stop")
    ])
    decisions=pd.DataFrame([
      dict(time="2011-01-03T08:00:00+00:00",reason="entered"),
      dict(time="2012-01-02T08:00:00+00:00",reason="entered")
    ])
    y=study.year_breakdown(trade,decisions,2011,2013)
    assert y["2011"]["starting_equity_usd"]==1000
    assert y["2012"]["starting_equity_usd"]==1010
    assert abs(y["2012"]["return_pct"]-100*(-4)/1010)<1e-10

def test_no_automatic_live_trading():
    s=inspect.getsource(study.main)
    assert "live_orders=0" in s
    assert "2026" in study.__doc__
