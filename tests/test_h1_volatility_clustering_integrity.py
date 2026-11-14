import sys, csv, hashlib
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
import h1_volatility_clustering as h

def make(tmp_path,market='crypto',gap=False):
    path=tmp_path/'realistic_synthetic_fixture.csv'
    t=datetime(2021,1,1,tzinfo=timezone.utc)
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['timestamp','open','high','low','close','volume'])
        for i in range(24*95):
            if gap and i==100:t+=timedelta(hours=48)
            price=100+np.sin(i/20)*2+i*.01
            w.writerow([t.isoformat(),price,price+1,price-1,price,1])
            t+=timedelta(hours=1)
    return path

def test_crypto_gap_fails(tmp_path):
    p=make(tmp_path,gap=True)
    with pytest.raises(ValueError,match='missing candles'):h.load(p,'crypto')

def test_fx_weekend_allowed_and_window_dropped(tmp_path):
    p=make(tmp_path)
    close,ts,_=h.load(p,'crypto')
    ts2=ts.copy()
    # Friday Jan 1 2021 index 20 -> Sunday Jan 3 (delta 49h).
    ts2[21:]+=48*3600
    assert datetime.fromtimestamp(int(ts2[21]),timezone.utc).weekday()==6
    # Valid fixture timestamps for FX weekend semantics; no imputation.
    past,future=h.window_features(close,ts2)
    assert np.isnan(past[25]) and np.isnan(future[25])
    assert np.isfinite(past[100]) and np.isfinite(future[100])

def test_feature_never_looks_into_future(tmp_path):
    p=make(tmp_path)
    close,ts,_=h.load(p,'crypto')
    before,_=h.window_features(close,ts)
    modified=close.copy();modified[120:]*=2
    after,_=h.window_features(modified,ts)
    np.testing.assert_allclose(before[:119],after[:119],equal_nan=True)

def test_bad_timestamp_rejected(tmp_path):
    p=make(tmp_path)
    rows=p.read_text().splitlines()
    rows[5]=rows[4]
    p.write_text('\n'.join(rows)+'\n')
    with pytest.raises(ValueError,match='Duplicate'):h.load(p,'crypto')

def test_bootstrap_zero_and_negative():
    assert h.block_ci(np.zeros(50))==[0,0]
    assert h.block_ci(-np.ones(50))[1]<0
