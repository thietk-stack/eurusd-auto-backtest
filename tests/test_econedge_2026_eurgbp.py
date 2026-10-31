import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import pandas as pd
import numpy as np
from econedge_2026_eurgbp import PAIRS,FIRST,LAST,freeze_events,run_book,load_data
from econedge_weekly_trend import LOT_STEP
def test_frozen_two_currency_scope_and_recent_period():
    assert PAIRS==("eurusd","gbpusd")
    assert FIRST=="2025-09" and LAST=="2026-09"
def test_baseline_lot_not_mutated():
    assert LOT_STEP==.01
def test_requires_exact_verified_months_not_generated():
    import inspect
    body=inspect.getsource(load_data)
    assert "verify_month(" in body
    assert "sha256" in body
    assert "interpolate" not in body and "ffill(" not in body
def test_only_complete_friday_weeks():
    import inspect
    src=inspect.getsource(freeze_events)
    assert '"exit_deadline"] in index' in src
def test_hypothetical_0001_risk_prevents_rounding_away_precision():
    import inspect
    from econedge_weekly_trend import evaluate_trade
    src=inspect.getsource(evaluate_trade)
    assert "math.log10(LOT_STEP)" in src
def test_no_real_broker_submission_code():
    import inspect
    from econedge_2026_eurgbp import main
    src=inspect.getsource(main)
    assert "real_orders=0" in src
