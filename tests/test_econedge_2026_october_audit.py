import sys,inspect
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import econedge_2026_october_audit as a
import econedge_2026_eurgbp as frozen
import econedge_weekly_trend as base

def test_no_strategy_changes_and_strict_months():
    assert frozen.PAIRS==("eurusd","gbpusd")
    assert a.FIRST=="2025-09" and a.LAST=="2026-10"
    assert a.BASELINE_WEEKS==38
    assert a.BASELINE_26_MONTH_MANIFEST_SHA256=="303b518abd5600ed91a6cb68f28b8a865cc919043c15abf4e19b7876e7496829"
    assert a.BASELINE_EXPECTED[(".001","opposite_control")]==(13,17.7985)
    assert a.BASELINE_EXPECTED[(".01","opposite_control")]==(2,-4.5350)

def test_new_data_must_be_complete_through_last_friday():
    assert a.LAST_COMPLETE_FRIDAY.isoformat()=="2026-10-30T20:00:00+00:00"
    s=inspect.getsource(a.load_extended)
    assert "LAST_COMPLETE_FRIDAY not in idx" in s
    assert "BASELINE_26_MONTH_MANIFEST_SHA256" in s
    assert "verify_month(" in s
    assert "hashlib.sha256(raw)" in s
    assert "ffill" not in s and "interpolate" not in s

def test_fixed_risk_and_no_orders():
    assert base.RISK==.005
    assert base.LEVERAGE==5
    assert base.MIN_TREND_Z==.8
    assert base.HISTORY_BARS==480
    assert base.STOP_ATR_MULT==6.
    assert base.STOP_MAX_PIPS==70.
    assert base.SLIPPAGE_PIPS==.1
    src=inspect.getsource(a.main)
    assert "old.freeze_events(idx,quotes)" in src
    assert "old.run_book" in inspect.getsource(a.replay)
    assert "real_orders=0" in src
    assert "No swap" in src
