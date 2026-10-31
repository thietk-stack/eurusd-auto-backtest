import sys,inspect
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import numpy as np,pandas as pd
import winnerfx_v1 as m

def test_frozen_economic_hypothesis_no_profit_tuning():
    assert m.BREAK_DAYS==55 and m.EMA_FAST==20 and m.EMA_SLOW==100
    assert m.ATR_DAYS==20 and m.STOP_ATR==3.
    assert m.MAX_HOLD_TRADING_DAYS==90
    assert m.RISK==.005 and m.MAX_LEV==5.
    assert m.LOT_STEPS==(.001,.01)
    assert m.ERAS["historic_2011_2017"]==(2011,2018)
    assert m.ERAS["reused_2018_2025"]==(2018,2026)

def test_trailing_stop_never_widens_even_if_atr_expands():
    assert m.better_stop(1.1,1.099, .03,1)==1.1
    assert m.better_stop(1.1,1.102,.03,-1)==1.1
    assert m.better_stop(1.1,1.120,.003,1)>1.1
    assert m.better_stop(1.1,1.080,.003,-1)<1.1

def test_lot_minimum_and_usdjpy_value_and_risk():
    a=m.lot_size(1000,1.10,.0001,60,"eurusd",.001)
    assert a and 0.001<=a[0]<=.05
    assert a[2]<=5.00000001
    b=m.lot_size(1000,145,.01,120,"usdjpy",.001)
    assert b and b[2]<=5.00000001
    assert m.lot_size(1000,1.10,.0001,200,"eurusd",.01) is None

def test_benchmark_reverse_must_be_opposite_of_trend():
    code=inspect.getsource(m.select_and_replay)
    assert 'if mode=="trend" else -1' in code

def test_uses_genuine_sha_sources_not_synthetic():
    code=inspect.getsource(m.main)
    assert "verified_16_year_data()" in code
    source=inspect.getsource(m.build_daily)
    import ast
    methods={getattr(n.func,"attr",None) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Call)}
    assert "ffill" not in methods and "interpolate" not in methods

def test_reward_not_forced_2r():
    src=inspect.getsource(m.exit_check)
    assert "target" not in src and "tp2r" not in src
    assert "stop" in src

def test_selected_day_only_reads_yesterday_closed():
    src=inspect.getsource(m.selection)
    assert "j=day_idx-1" in src
    assert "prev55hi" in src and "prev55lo" in src

def test_weekly_cost_bootstrap_data_zero():
    assert m.block_bootstrap_lower(np.zeros(16),64)==0.
    assert m.block_bootstrap_lower(np.full(16,-1.),64)<0
