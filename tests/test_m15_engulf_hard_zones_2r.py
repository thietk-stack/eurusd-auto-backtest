import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import pandas as pd
from m15_engulf_hard_zones_2r import try_fill, signal_indices, MIN_NET_RR, RISK

def prices(ao, al, bo, bh, bidl, askh):
    return pd.DataFrame([dict(ask_open=ao,ask_low=al,ask_high=askh,
        bid_open=bo,bid_high=bh,bid_low=bidl)])

def signal(side,limit,stop):
    return dict(side=side,limit=limit,stop=stop)

def test_buy_real_ask_low_must_touch_limit():
    d=prices(1.1051,1.10501,1.1050,1.10515,1.1048,1.1055)
    assert try_fill(d,0,signal(1,1.1050,1.1030)) is None
    d=prices(1.1052,1.10499,1.1050,1.1053,1.1048,1.1057)
    assert try_fill(d,0,signal(1,1.1050,1.1030))==1.1050

def test_sell_real_bid_high_must_touch_limit():
    d=prices(1.1051,1.1049,1.1048,1.10499,1.104,1.1059)
    assert try_fill(d,0,signal(-1,1.105,1.107)) is None
    d=prices(1.1051,1.1049,1.10499,1.10501,1.104,1.1059)
    assert try_fill(d,0,signal(-1,1.105,1.107))==1.105

def test_gap_beyond_stop_skipped():
    d=prices(1.1020,1.100,1.1019,1.103,1.099,1.1039)
    assert try_fill(d,0,signal(1,1.1050,1.1030)) is None

def test_m15_strong_engulf_requires_real_next_bar():
    # Deliberately no close-in-time next 15m: should not count a candidate
    idx=pd.to_datetime(["2024-01-02T08:00Z","2024-01-02T08:15Z","2024-01-02T09:15Z"],utc=True)
    d=pd.DataFrame([
        dict(open=1.1,close=1.101,high=1.102,low=1.099),
        dict(open=1.101,close=1.099,high=1.101,low=1.099),
        dict(open=1.098,close=1.104,high=1.104,low=1.098)
    ],index=idx)
    selected,_,_=signal_indices(d)
    assert len(selected)==0

def test_risk_rr_not_changed():
    assert RISK==.005
    assert MIN_NET_RR==2.
