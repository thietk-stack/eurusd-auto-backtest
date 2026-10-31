import sys,inspect
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import econedge_macro_rate_proxy_v1 as m

def test_five_official_three_month_rate_series():
    assert m.RATE_SERIES["usd"]=="IR3TIB01USM156N"
    assert m.RATE_SERIES["eurusd"]=="IR3TIB01EZM156N"
    assert m.RATE_SERIES["gbpusd"]=="IR3TIB01GBM156N"
    assert m.RATE_SERIES["audusd"]=="IR3TIB01AUM156N"
    assert m.RATE_SERIES["usdjpy"]=="IR3TIB01JPM156N"

def test_two_month_information_lag_and_no_carry_added():
    assert m.REFERENCE_LAG_MONTHS==2
    source=inspect.getsource(m.signal_monthly)
    assert "month-REFERENCE_LAG_MONTHS" in source
    assert "for sym in PAIRS" in source
    assert '"usdjpy"' in source
    result=inspect.getsource(m.main)
    assert "NO interest revenue or swap added to PnL" in result
    assert "real_orders=0" in result

def test_bootstrap_no_prepaid_profit():
    assert m.block_boot_lower([0]*24)==0
    assert m.block_boot_lower([-1]*24)<0

def test_no_rate_or_price_interpolation():
    import ast
    methods={getattr(a.func,"attr",None) for a in ast.walk(ast.parse(inspect.getsource(m.signal_monthly))) if isinstance(a,ast.Call)}
    assert "ffill" not in methods and "interpolate" not in methods
