import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from htf_limit_mid_yearly import possible_limit_fill, summary, RISK, MIN_RR_NET
import pandas as pd

def test_buy_limit_touches_only_on_retracement():
    assert possible_limit_fill(1,1.105,1.11,1.112,1.106) is None
    assert possible_limit_fill(1,1.105,1.11,1.112,1.104) == 1.105
    # Better price if next candle opens below our limit:
    assert possible_limit_fill(1,1.105,1.103,1.105,1.101) == 1.103

def test_sell_limit_touches_only_on_retracement():
    assert possible_limit_fill(-1,1.105,1.10,1.104,1.099) is None
    assert possible_limit_fill(-1,1.105,1.10,1.106,1.099) == 1.105
    assert possible_limit_fill(-1,1.105,1.107,1.110,1.104) == 1.107

def test_empty_year_has_no_imaginary_profit():
    x=summary(pd.DataFrame(),{"limit_created":0,"expired":0},2019)
    assert x["filled"]==0 and x["return_pct"]==0

def test_nonnegotiable_limits():
    assert RISK == 0.005 and MIN_RR_NET == 1.5
