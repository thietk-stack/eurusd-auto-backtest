import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from htf_engulf_body2x_wick5 import is_strong_body_engulfing, WICK_MAX_FRACTION, BODY_MULTIPLIER

def test_bull_body_doubled_both_wicks_under_five_pct():
    assert is_strong_body_engulfing(1.1000,1.1021,1.0999,1.1020,1.1010,1.1020,1)

def test_bear_body_doubled_both_wicks_under_five_pct():
    assert is_strong_body_engulfing(1.1020,1.1021,1.0999,1.1000,1.1010,1.1020,-1)

def test_wick_over_five_pct_rejected():
    assert not is_strong_body_engulfing(1.1000,1.1022,1.0999,1.1020,1.1010,1.1020,1)
    assert not is_strong_body_engulfing(1.1000,1.1021,1.0998,1.1020,1.1010,1.1020,1)

def test_body_smaller_than_twice_prior_body_rejected():
    assert not is_strong_body_engulfing(1.1000,1.1021,1.0999,1.1020,1.1000,1.1011,1)

def test_very_small_doji_previous_not_valid_comparator():
    assert not is_strong_body_engulfing(1.1000,1.1021,1.0999,1.1020,1.1000,1.1000,1)

def test_wrong_direction_rejected():
    assert not is_strong_body_engulfing(1.1000,1.1021,1.0999,1.1020,1.1010,1.1020,-1)

def test_thresholds_frozen():
    assert WICK_MAX_FRACTION==0.05
    assert BODY_MULTIPLIER==2.0
