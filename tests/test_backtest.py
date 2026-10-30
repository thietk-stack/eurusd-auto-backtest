"""Offline algorithm unit tests: fixtures are never used as historical research data."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from real_backtest import backtest,performance,monthly_results,load_data

def test_missing_month_fails(tmp_path):
    try:
        load_data(tmp_path,'2024-01-01','2024-02-01')
    except ValueError as err:
        assert 'MISSING VERIFIED REAL-DATA' in str(err)
    else:
        assert False,'Must not silently synthesize missing prices'

def test_empty_trade_stats():
    assert performance(pd.DataFrame())['trades']==0
    assert monthly_results(pd.DataFrame())==[]

def test_trade_cost_and_chronological_signal():
    n=1200
    t=pd.date_range('2023-01-02',periods=n,freq='h',tz='UTC')
    x=np.arange(n)
    # Artificial trend regimes for ONLY offline fixture unit tests.
    close=1.11+np.cumsum(np.where((x//120)%2==0,.00015,-.00014))
    op=np.r_[close[0],close[:-1]]
    d=pd.DataFrame(dict(timestamp=t,open=op,high=np.maximum(op,close)+.0003,
       low=np.minimum(op,close)-.0003,close=close))
    trades,equity,unclosed=backtest(d,'2023-01-07',spread=.8,slip=.1)
    assert len(equity)>0
    assert isinstance(unclosed,bool)
    if not trades.empty:
        assert all(pd.to_datetime(trades.entry_time)<=pd.to_datetime(trades.exit_time))
        assert np.allclose(trades.gross_usd-trades.spread_usd-trades.slippage_usd,
                           trades.net_pnl_usd,atol=1e-6)
        assert np.all(trades.lots>=.01)
