import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from htf_engulf_2x_no_wick import is_strong_wickless, PRICE_EPS, RANGE_MULTIPLIER

def test_wickless_big_bullish_passes():
    # prev range 10 pip, current 20 pip, open at low, close at high
    assert is_strong_wickless(1.100,1.102,1.100,1.102,1.1006,1.0996,1)

def test_wickless_big_bearish_passes():
    assert is_strong_wickless(1.102,1.102,1.100,1.100,1.1006,1.0996,-1)

def test_rejects_any_shadows_even_short_ones():
    assert not is_strong_wickless(1.1000005,1.102,1.100,1.102,1.1006,1.0996,1)
    assert not is_strong_wickless(1.100,1.1020005,1.100,1.102,1.1006,1.0996,1)
    assert not is_strong_wickless(1.102,1.102,1.0999995,1.100,1.1006,1.0996,-1)

def test_rejects_not_full_twice_previous_candle():
    assert not is_strong_wickless(1.100,1.10199,1.100,1.10199,1.1006,1.0996,1)

def test_rejects_other_direction_or_zero_prev():
    assert not is_strong_wickless(1.100,1.102,1.100,1.102,1.1006,1.0996,-1)
    assert not is_strong_wickless(1.100,1.102,1.100,1.102,1.1,1.1,1)

def test_definitions_locked():
    assert PRICE_EPS==1e-8
    assert RANGE_MULTIPLIER==2
