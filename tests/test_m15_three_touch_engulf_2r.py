import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import numpy as np
from m15_three_touch_engulf_2r import (
    three_touch_signal, TOUCH_MAX_BARS, TOUCH_MIN_BARS, 
    ZONE_WIDTH_MIN_PIPS, PIVOT_RIGHT,
)

def values(p1=6,p2=12,j=18):
    n=35
    lows=np.full(n,1.105)
    highs=np.full(n,1.106)
    closes=np.full(n,1.1055)
    lows[[p1,p2,j]]=1.1000
    highs[[p1,p2,j]]=1.1010
    closes[j]=1.1012
    support=np.zeros(n,dtype=bool)
    support[p1]=support[p2]=True
    resist=np.zeros(n,dtype=bool)
    med=np.full(n,.0005)
    return lows,highs,closes,(support,resist,med),med

def test_3_consecutive_same_zone_touches_gap_6_pass():
    lows,highs,closes,pivots,med=values()
    r=three_touch_signal(18,1,lows,highs,closes,pivots,med,.0001)
    assert r is not None
    assert r["gap_12"]==6 and r["gap_23"]==6
    assert len(r["prices"])==3

def test_gap_over_10_m15_candles_fails():
    lows,highs,closes,pivots,med=values(p1=4,p2=15,j=18)
    assert three_touch_signal(18,1,lows,highs,closes,pivots,med,.0001) is None

def test_same_price_zone_required():
    lows,highs,closes,pivots,med=values()
    lows[6]=1.0980
    assert three_touch_signal(18,1,lows,highs,closes,pivots,med,.0001) is None

def test_wrong_direction_fails():
    lows,highs,closes,pivots,med=values()
    assert three_touch_signal(18,-1,lows,highs,closes,pivots,med,.0001) is None

def test_gap_contract():
    assert TOUCH_MAX_BARS==10
    assert TOUCH_MIN_BARS==2
    assert PIVOT_RIGHT==1
    assert ZONE_WIDTH_MIN_PIPS==2
