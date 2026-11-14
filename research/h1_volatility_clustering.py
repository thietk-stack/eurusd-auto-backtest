"""EconEdge H1 volatility clustering diagnostic; no trade simulation or PnL.

FX: weekend gaps are permitted but NEVER imputed. Both 24h windows must
contain uninterrupted hourly candles. Crypto: all hours must be present.
Source CSV SHA256 must match an independently obtained expected digest.
"""
import argparse, csv, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

TRAIN_END='2024-01-01T00:00:00+00:00'
VALID_END='2025-01-01T00:00:00+00:00'
TEST_END='2026-10-01T00:00:00+00:00'
SEED=20261114

def load(path,market):
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(newline='') as f: rows=list(csv.DictReader(f))
    if len(rows)<24*90: raise ValueError('Insufficient real H1 rows')
    times=[];closes=[]
    for r in rows:
        t=datetime.fromisoformat(r['timestamp'].replace('Z','+00:00'))
        if t.tzinfo is None or t.utcoffset().total_seconds()!=0:
            raise ValueError('UTC timestamps required')
        o,h,l,c=[float(r[k]) for k in ('open','high','low','close')]
        if not all(math.isfinite(x) and x>0 for x in (o,h,l,c)) or not (l<=min(o,c)<=max(o,c)<=h):
            raise ValueError('Invalid OHLC')
        times.append(t);closes.append(c)
    stamps=np.array([int(t.timestamp()) for t in times],dtype=np.int64)
    gaps=np.diff(stamps)
    if np.any(gaps<=0) or np.any(gaps%3600!=0):
        raise ValueError('Duplicate, out-of-order or non-hourly timestamp')
    if market=='crypto' and np.any(gaps!=3600):
        raise ValueError('Crypto H1 source missing candles')
    if market=='fx':
        for a,b,delta in zip(times[:-1],times[1:],gaps):
            if delta==3600: continue
            # Only known weekend closures, not unexplained missing intraday bars.
            # From Friday UTC to Sunday UTC, or early Monday UTC.
            if not (a.weekday()==4 and b.weekday() in (6,0)
                    and 24*3600<=delta<=75*3600):
                raise ValueError('Unexpected FX H1 gap; do not fill synthetic bars')
    return np.asarray(closes),stamps,digest

def window_features(close,ts):
    ret=np.diff(np.log(close),prepend=np.nan)
    past=np.full(len(close),np.nan);future=np.full(len(close),np.nan)
    gaps=np.diff(ts)!=3600
    cumulative=np.concatenate(([0],np.cumsum(gaps.astype(int))))
    for t in range(24,len(close)-24):
        # Need 24 past returns from t-23..t (requires bars t-24..t)
        # and 24 future returns from t+1..t+24.
        if cumulative[t+24]!=cumulative[t-24]:continue
        past[t]=np.sqrt(np.mean(ret[t-23:t+1]**2))
        future[t]=np.sqrt(np.mean(ret[t+1:t+25]**2))
    return past,future

def block_ci(x,block=5,reps=2500):
    x=np.asarray(x,float)
    if len(x)<20:return None
    rng=np.random.default_rng(SEED)
    n=len(x);out=[]
    for _ in range(reps):
        starts=rng.integers(0,n,size=math.ceil(n/block))
        sample=np.concatenate([x[(np.arange(k,k+block))%n] for k in starts])[:n]
        out.append(float(np.mean(sample)))
    return [float(v) for v in np.percentile(out,[2.5,97.5])]

def run(path,market):
    close,ts,digest=load(path,market)
    past,future=window_features(close,ts)
    bounds=[int(datetime.fromisoformat(x).timestamp()) for x in (TRAIN_END,VALID_END,TEST_END)]
    train_end,valid_end,test_end=bounds
    valid=np.isfinite(past)&np.isfinite(future)&(ts%86400==0)
    # 24h embargo on either side of each boundary, applied to independent samples.
    train=valid&(ts<train_end-86400)
    validation=valid&(ts>=train_end+86400)&(ts<valid_end-86400)
    test=valid&(ts>=valid_end+86400)&(ts<test_end-86400)
    if any(mask.sum()<50 for mask in (train,validation,test)):
        raise ValueError('Insufficient independent observations in train/validation/test')
    edges=np.quantile(past[train],[.2,.4,.6,.8])
    if not np.all(np.diff(edges)>0):raise ValueError('Degenerate training quintiles')
    out=dict(source=str(path),sha256=digest,market=market,rows=len(close),
             start_utc=datetime.fromtimestamp(int(ts[0]),timezone.utc).isoformat(),
             end_utc=datetime.fromtimestamp(int(ts[-1]),timezone.utc).isoformat(),
             training_quintile_edges=edges.tolist(),splits={},
             limitations=['Historical test set may have been viewed in prior FX research',
                          'Volatility predictability is not executable net trading edge',
                          'No broker spread, slippage, commission or swap modeled',
                          'Daily samples exclude windows spanning FX closures; not a 24/7 FX sample'])
    for name,mask in [('train',train),('validation',validation),('untouched_test',test)]:
        bins=np.searchsorted(edges,past[mask],side='right')
        y=future[mask];stats=[]
        for q in range(5):
            vals=y[bins==q]
            stats.append(dict(quintile=q+1,n=len(vals),
                 mean_future_rv=float(vals.mean()) if len(vals) else None))
        q1=y[bins==0];q5=y[bins==4]
        # Bootstrap separately within quintiles; descriptive only, not Holm-corrected.
        ci1=block_ci(q1);ci5=block_ci(q5)
        out['splits'][name]=dict(n=int(mask.sum()),quintiles=stats,
           q5_q1_ratio=float(q5.mean()/q1.mean()) if len(q1) and len(q5) and q1.mean()>0 else None,
           q1_mean_95ci=ci1,q5_mean_95ci=ci5,
           significance_claim='NONE: multiple-testing correction and paired regime inference not yet implemented')
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('csv',type=Path)
    p.add_argument('--market',choices=('fx','crypto'),required=True)
    p.add_argument('--expected-sha256',required=True,help='Independent raw CSV hash')
    a=p.parse_args()
    actual=hashlib.sha256(a.csv.read_bytes()).hexdigest()
    if actual.lower()!=a.expected_sha256.lower():
        raise SystemExit('SHA256 mismatch: refusing analysis')
    print(json.dumps(run(a.csv,a.market),indent=2))
