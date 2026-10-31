import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import pandas as pd
import numpy as np
import econedge_macro_cftc_v1 as m

def test_only_four_native_cme_currency_contracts():
    assert m.classify("EURO FX - CHICAGO MERCANTILE EXCHANGE")=="eurusd"
    assert m.classify("BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE")=="gbpusd"
    assert m.classify("AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE")=="audusd"
    assert m.classify("JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE")=="usdjpy"
    assert m.classify("EURO FX/JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE") is None
    assert m.classify("E-MICRO EURO FX - CHICAGO MERCANTILE EXCHANGE") is None
    assert m.classify("EURO FX - ICE FUTURES") is None

def test_fixed_research_calendar_and_COT_publication_lag():
    assert m.MIN_PUBLICATION_LAG_CALENDAR_DAYS==13
    assert m.YEARS==list(range(2010,2026))
    assert m.PERIODS["historic_2011_2017"]==(2011,2018)
    assert m.PERIODS["reused_2018_2025"]==(2018,2026)
    assert m.LOT_STEP==.001

def test_asset_manager_position_change_is_past_only():
    ix=pd.to_datetime(["2024-01-02","2024-01-09","2024-01-16","2024-01-23","2024-01-30","2024-02-06"],utc=True)
    f=pd.DataFrame(dict(pair=["eurusd"]*6,tuesday=ix,net_ratio=[.1,.2,.3,.4,.5,.6]))
    out=m.add_available_fourweek_change(f)
    assert np.isnan(out.delta4.iloc[3])
    assert abs(out.delta4.iloc[4]-.4)<1e-12
    assert abs(out.delta4.iloc[5]-.4)<1e-12
    assert (out.tuesday==ix).all()

def test_cot_is_futures_not_fake_spot_money():
    assert "gpe5-46if.csv" in m.BASE_COT
    import inspect
    raw=inspect.getsource(m.run)
    assert "separate_carry_interest_income_modeled=False" in raw
    assert "no_live_orders=True" in raw

def test_untruncated_weekly_reference():
    import inspect
    s=inspect.getsource(m.events)
    assert "ts.year<2011" in s
    assert "MIN_PUBLICATION_LAG_CALENDAR_DAYS" in s
    assert '"usdjpy"' in s
