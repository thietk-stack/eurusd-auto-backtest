"""EconEdge H1: causal volatility clustering test on independently verified hourly CSV.
Input must have timestamp,open,high,low,close,volume columns in UTC.
Research only: no orders, no PnL, no parameter optimization.
"""
import argparse, csv, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

TRAIN_END='2024-01-01T00:00:00+00:00'
VALID_END='2025-01-01T00:00:00+00:00'
TEST_END='2026-10-01T00:00:00+00:00'

def load(path):
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(newline='') as f: rows=list(csv.DictReader(f))
    assert len(rows)>24*90, 'Insufficient rows'
    times=[]; closes=[]
    for r in rows:
        t=datetime.fromisoformat(r['timestamp'].replace('Z','+00:00'))
        assert t.tzinfo is not None and t.utcoffset().total_seconds()==0, 'UTC required'
        o,h,l,c=[float(r[k]) for k in ('open','high','low','close')]
        assert all(math.isfinite(x) and x>0 for x in (o,h,l,c)) and l<=min(o,c)<=max(o,c)<=h
        times.append(t);closes.append(c)
    stamps=np.array([int(t.timestamp()) for t in times],dtype=np.int64)
    assert np.all(np.diff(stamps)==3600), 'Missing/duplicate/nonhourly timestamps'
    return np.array(closes),stamps,digest

def run(path):
    close,ts,digest=load(path)
    ret=np.diff(np.log(close),prepend=np.nan)
    # At bar t, past 24 completed hourly returns; future next 24 hourly returns.
    past=np.full(len(close),np.nan);future=np.full(len(close),np.nan)
    for t in range(24,len(close)-24):
        past[t]=np.sqrt(np.mean(ret[t-23:t+1]**2))
        future[t]=np.sqrt(np.mean(ret[t+1:t+25]**2))
    train_end=int(datetime.fromisoformat(TRAIN_END).timestamp())
    valid_end=int(datetime.fromisoformat(VALID_END).timestamp())
    test_end=int(datetime.fromisoformat(TEST_END).timestamp())
    # embargo 24h at both sides of every chronological boundary
    train=(ts<train_end-86400)&np.isfinite(past)&np.isfinite(future)
    valid=(ts>=train_end+86400)&(ts<valid_end-86400)&np.isfinite(past)&np.isfinite(future)
    test=(ts>=valid_end+86400)&(ts<test_end-86400)&np.isfinite(past)&np.isfinite(future)
    assert train.sum()>1000 and valid.sum()>1000 and test.sum()>1000, 'Required split missing'
    edges=np.quantile(past[train],[.2,.4,.6,.8])
    assert np.all(np.diff(edges)>0), 'Degenerate quintile edges'
    out={'source':str(path),'sha256':digest,'rows':len(close),'start_utc':datetime.fromtimestamp(int(ts[0]),timezone.utc).isoformat(),'end_utc':datetime.fromtimestamp(int(ts[-1]),timezone.utc).isoformat(),'training_quintile_edges':edges.tolist(),'splits':{}}
    for name,mask in [('train',train),('validation',valid),('untouched_test',test)]:
        # Non-overlapping observations: one observation every 24h, anchored to UTC epoch.
        mask=mask&(ts%86400==0)
        bins=np.searchsorted(edges,past[mask],side='right')
        x=future[mask]
        stats=[]
        for q in range(5):
            y=x[bins==q]
            stats.append({'quintile':q+1,'n':len(y),'mean_future_rv':float(np.mean(y)) if len(y) else None})
        out['splits'][name]={'n':int(mask.sum()),'quintiles':stats,'q5_q1_ratio':float(np.mean(x[bins==4])/np.mean(x[bins==0])) if np.any(bins==4) and np.any(bins==0) else None}
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--expected-sha256',required=True,help='SHA256 independently recorded for raw input')
    a=p.parse_args();actual=hashlib.sha256(a.csv.read_bytes()).hexdigest()
    if actual.lower()!=a.expected_sha256.lower():raise SystemExit('SHA256 mismatch: refusing analysis')
    print(json.dumps(run(a.csv),indent=2))
