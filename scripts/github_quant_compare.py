#!/usr/bin/env python3
"""Two frozen, transparent research strategies on real Dukascopy EURUSD H1. No live trading."""
import sys, json, math
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from real_backtest import load_data

CAPITAL=1000.0
SPLITS=[("original_author_era","2010-01-01","2019-01-01"),
        ("post_publication_2019_2022","2019-01-01","2023-01-01"),
        ("untouched_2023_2026","2023-01-01","2026-10-30")]

def streak(series):
    """Consecutive positive/negative sign count; zero -> zero."""
    vals=np.sign(np.asarray(series,dtype=float))
    out=np.zeros(len(vals),dtype=int)
    for i in range(1,len(vals)):
        v=vals[i]
        out[i]=(out[i-1]+1 if out[i-1]>0 else 1) if v>0 else (
               (out[i-1]-1 if out[i-1]<0 else -1) if v<0 else 0)
    return out

def factors(df):
    c=df.close.astype(float);h=df.high.astype(float);l=df.low.astype(float)
    daily_index=df.timestamp.dt.strftime("%Y-%m-%d")
    daily_close=c.groupby(daily_index).last()
    short_daily=daily_close.rolling(7,min_periods=7).mean()
    long_daily=daily_close.rolling(21,min_periods=21).mean()
    daily_signed=streak((short_daily-long_daily).to_numpy())
    daily_map=pd.Series(daily_signed,index=daily_close.index).shift(1).fillna(0)
    daily_streak=daily_index.map(daily_map).to_numpy(dtype=float)
    short_hour=c.rolling(50,min_periods=50).mean()
    long_hour=c.rolling(200,min_periods=200).mean()
    hourly_delta=short_hour-long_hour
    hour_signed=streak(hourly_delta.to_numpy())
    hourly_trend_id=np.cumsum(np.r_[True,(np.sign(hour_signed[1:])!=np.sign(hour_signed[:-1]))]).astype(int)
    stoch_raw=100*(c-l.rolling(9,min_periods=9).min())/(h.rolling(9,min_periods=9).max()-l.rolling(9,min_periods=9).min()).replace(0,np.nan)
    stoch_d=stoch_raw.rolling(9,min_periods=9).mean().rolling(5,min_periods=5).mean()
    # Rebound out of stochastic extreme, current bar closed, order next bar open.
    stoch_prev=stoch_d.shift(1)
    github_signal=np.where((hour_signed>=17)&(daily_streak>=4)&(stoch_prev<=20)&(stoch_d>20),1,
                    np.where((hour_signed<=-17)&(daily_streak<=-4)&(stoch_prev>=80)&(stoch_d<80),-1,0)).astype(np.int8)
    # Predeclared systematic time-series momentum (5 and 20 trading days ~120/480 hourly candles).
    # Volatility regime from rolling closed bar returns, never current future values.
    ret=c.pct_change()
    signal_strength=(c-c.shift(120))/(c.diff().rolling(120,min_periods=120).std()*np.sqrt(120))
    mom5=c/c.shift(120)-1
    mom20=c/c.shift(480)-1
    rv20=ret.rolling(480,min_periods=480).std()
    rv60=ret.rolling(1440,min_periods=1440).std()
    volok=(rv20<1.30*rv60)&(rv20>0)
    quant=np.where((mom5>0)&(mom20>0)&(signal_strength>1.0)&volok,1,
          np.where((mom5<0)&(mom20<0)&(signal_strength< -1.0)&volok,-1,0)).astype(np.int8)
    tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean().to_numpy()
    github_signal[:700]=0
    quant[:1600]=0
    return dict(github_original=github_signal,quant_tsmom=quant),hourly_trend_id,atr

def run(df,signals,trend_ids,atr,kind,begin,end,spread=.8,slip=.1):
    first=int(df.timestamp.searchsorted(pd.Timestamp(begin,tz="UTC")))
    last=int(df.timestamp.searchsorted(pd.Timestamp(end,tz="UTC")))
    o=df.open.to_numpy(float);h=df.high.to_numpy(float);l=df.low.to_numpy(float)
    c=df.close.to_numpy(float); t=df.timestamp
    cash=CAPITAL;side=0;entry_ix=0;mid=0.;lots=0.;stop=target=0.;counter={}
    rows=[]
    total_cost_pips=spread+slip*2
    for i in range(max(first,1601),last):
        closed=False;reason=None;exitmid=None
        # any existing position can only expire at next candle OPEN (before intrabar SL/TP)
        if side and i>entry_ix:
            if kind=="quant_tsmom" and i-entry_ix>=96:
                reason="max_hold_96h";exitmid=o[i]
            elif kind=="github_original" and i-entry_ix>=500:
                reason="safety_limit_500h";exitmid=o[i]
        if side and reason is None:
            # Stops applied on entry bar (conservative); when TP and SL both touch => stop.
            if side>0:
                if l[i]<=stop:reason="stop";exitmid=min(o[i],stop)
                elif h[i]>=target:reason="target";exitmid=target
            else:
                if h[i]>=stop:reason="stop";exitmid=max(o[i],stop)
                elif l[i]<=target:reason="target";exitmid=target
        if side and reason:
            gross=(exitmid-mid)*side*100000*lots
            cost=total_cost_pips*10*lots
            net=gross-cost
            cash+=net
            rows.append(dict(entry_time=t.iloc[entry_ix].isoformat(),exit_time=t.iloc[i].isoformat(),side=side,
                    lots=lots,gross_usd=gross,spread_usd=spread*10*lots,slippage_usd=2*slip*10*lots,
                    net_usd=net,balance_usd=cash,exit_reason=reason))
            closed=True;side=0
        if not side and not closed and cash>=100 and t.iloc[i].weekday()<5:
            if kind=="github_original":
                direction=int(signals[kind][i-1])
                # Max 3 trades per hourly SMA trend direction.
                allow=(counter.get(int(trend_ids[i-1]),0)<3)
                stopdist=.0017;targetdist=.0007
                # Trade on any trading hour as in the reference.
            else:
                # One decision per UTC day based on most recently completed hourly bar.
                direction=int(signals[kind][i-1]) if t.iloc[i].hour==8 else 0
                allow=True
                stopdist=max(2*atr[i-1],.0004)
                targetdist=max(3*atr[i-1],.0006)
            if direction and allow and np.isfinite(stopdist):
                # Independent risk management for comparable capital, NOT original fixed 5,000 units.
                max_by_risk=cash*.005/((stopdist/0.0001+total_cost_pips)*10)
                max_by_lev=cash*5/(100000*o[i])
                qty=math.floor((min(max_by_risk,max_by_lev,.5)+1e-12)/.01)*.01
                if qty>=.01:
                    side=direction;entry_ix=i;mid=o[i];lots=qty
                    stop=mid-side*stopdist;target=mid+side*targetdist
                    if kind=="github_original":
                        ident=int(trend_ids[i-1]);counter[ident]=counter.get(ident,0)+1
                    # Check the first hour for stops. Enter at open, stop-first within bar.
                    if (side>0 and l[i]<=stop) or (side<0 and h[i]>=stop):
                        x=min(o[i],stop) if side>0 else max(o[i],stop)
                        gross=(x-mid)*side*100000*lots
                        net=gross-total_cost_pips*10*lots
                        cash+=net
                        rows.append(dict(entry_time=t.iloc[entry_ix].isoformat(),exit_time=t.iloc[i].isoformat(),
                         side=side,lots=lots,gross_usd=gross,spread_usd=spread*10*lots,
                         slippage_usd=2*slip*10*lots,net_usd=net,balance_usd=cash,exit_reason="first_bar_stop"))
                        side=0
                    elif (side>0 and h[i]>=target) or (side<0 and l[i]<=target):
                        x=target
                        gross=(x-mid)*side*100000*lots
                        net=gross-total_cost_pips*10*lots
                        cash+=net
                        rows.append(dict(entry_time=t.iloc[entry_ix].isoformat(),exit_time=t.iloc[i].isoformat(),
                         side=side,lots=lots,gross_usd=gross,spread_usd=spread*10*lots,
                         slippage_usd=2*slip*10*lots,net_usd=net,balance_usd=cash,exit_reason="first_bar_target"))
                        side=0
    if side: # close open position at last observed close; no carry across independent test periods
        x=c[last-1];gross=(x-mid)*side*100000*lots
        net=gross-total_cost_pips*10*lots;cash+=net
        rows.append(dict(entry_time=t.iloc[entry_ix].isoformat(),exit_time=t.iloc[last-1].isoformat(),
          side=side,lots=lots,gross_usd=gross,spread_usd=spread*10*lots,slippage_usd=2*slip*10*lots,
          net_usd=net,balance_usd=cash,exit_reason="period_end"))
    return pd.DataFrame(rows)

def metrics(df,begin,end):
    if df.empty:return dict(trades=0,net_pct=0.,end_usd=CAPITAL,profit_factor=None,win_pct=None,
        closed_dd_pct=0,monthly_compound_pct=0,months_ge_5=0,months_ge_8=0)
    net=df.net_usd.to_numpy(float)
    curve=CAPITAL+np.cumsum(net)
    high=np.maximum.accumulate(np.r_[CAPITAL,curve])[1:]
    sumwin=net[net>0].sum();sumloss=-net[net<0].sum()
    dates=pd.to_datetime(df.exit_time,utc=True)
    by_month=df.assign(month=dates.dt.strftime('%Y-%m')).groupby("month").net_usd.sum().to_dict()
    months=pd.period_range(begin[:7],(pd.Timestamp(end)-pd.Timedelta(days=1)).strftime('%Y-%m'),freq='M')
    bal=CAPITAL;returns=[]
    for mo in months:
        profit=by_month.get(str(mo),0)
        returns.append(100*profit/bal if bal>0 else None)
        bal+=profit
    duration=len(months)
    return dict(trades=len(df),net_pct=float((curve[-1]/CAPITAL-1)*100),end_usd=float(curve[-1]),
      profit_factor=float(sumwin/sumloss) if sumloss else None,
      win_pct=float((net>0).mean()*100),
      closed_dd_pct=float(np.min((curve/high-1)*100)),
      monthly_compound_pct=float((curve[-1]/CAPITAL)**(1/duration)*100-100) if curve[-1]>0 else None,
      months_ge_5=sum(v is not None and v>=5 for v in returns),
      months_ge_8=sum(v is not None and v>=8 for v in returns),
      spread_paid=float(df.spread_usd.sum()),slippage_paid=float(df.slippage_usd.sum()))

def main():
    out=Path("github_strategy_results");out.mkdir(exist_ok=True)
    d=load_data(Path("data"),"2010-01-01","2026-10-30")
    if len(d)<90000:raise ValueError("Verified dataset too short")
    signs,trend_ids,atr=factors(d)
    result={}
    for name in signs:
        result[name]={}
        for phase,begin,end in SPLITS:
            trades=run(d,signs,trend_ids,atr,name,begin,end)
            result[name][phase]=metrics(trades,begin,end)
            trades.to_csv(out/(name+"_"+phase+".csv"),index=False)
        # only the recent independent period for spread stress, not tuned/selected.
        for cost in (1.2,2.0):
            phase,begin,end=SPLITS[-1]
            tr=run(d,signs,trend_ids,atr,name,begin,end,spread=cost)
            result[name]["stress_"+str(cost)]=metrics(tr,begin,end)
    output=dict(source="Verified Dukascopy EURUSD H1 candles; spread is Exness illustrative, NOT broker tick data",
       candles=len(d),reference="https://github.com/jgardezi/Eurodollars",
       github_port_caveat="Simplified directional one-position H1 port; approximates published SMA50/200 17h streak, daily SMA7/21 4-day streak, STO 9/9/5, <=3 entries per hourly trend, 7-pip TP, 17-pip SL. Uses risk-based size instead of original fixed 5000 units; safety max hold 500h. Not a 1:1 LEAN engine reproduction.",
       quantitative_rule="Frozen 120/480 closed-hour momentum directions with strength z>1.0 and realized-vol 480/1440 <1.3, enter 08UTC, 2ATR stop/3ATR target, max 96h hold.",
       conditions="1000 USD, max 0.5% risk/position, effective leverage <=5x, 0.01 lots, 0.8pip spread and 0.1pip slippage each side; commission 0, swap unmodelled",results=result)
    (out/"RESULTS_GITHUB_VS_QUANT.json").write_text(json.dumps(output,indent=2,ensure_ascii=False))
    s=["# GitHub public EUR/USD strategy vs frozen quantitative time-series momentum",
       "","Source price: verified Dukascopy H1 Bid/Ask (not Exness), fixed Exness Standard cost scenario; no actual orders.",
       "","Original reference: [jgardezi/Eurodollars](https://github.com/jgardezi/Eurodollars) with claimed ~938% return 2008–18 in its author's historical report. This study independently tests a simplified port on post-publication EUR/USD history, **not** the identical LEAN trading engine.",
       "","| Strategy | Test period | Closed trades | Net return | PF | Closed DD | Compound / month | Months >=5% | Months >=8% |",
       "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name,stages in result.items():
        for phase,_,_ in SPLITS:
            a=stages[phase]
            pct=lambda x:f"{x:.2f}%" if x is not None else "N/A"
            pf=("N/A" if a["profit_factor"] is None else format(a["profit_factor"],".3f"))
            s.append(f"| {name} | {phase} | {a['trades']} | {pct(a['net_pct'])} | {pf} | {pct(a['closed_dd_pct'])} | {pct(a['monthly_compound_pct'])} | {a['months_ge_5']} | {a['months_ge_8']} |")
    s+=["","**Critical:** Stars/follows represent community attention, not profitability. Neither Github's historic claim nor a positive backtest result guarantees stable 5–8% monthly. Equity drawdown is estimated from closed trades only. Intrabar orders use stop-first conservative approximations. Exness real spread/swap/slippage not verified. Original reference used fixed 5,000 units while here sizing is 0.5% risk <=5x leverage, so results are NOT directly comparable to claimed +938%."]
    (out/"REPORT_VI.md").write_text("\n".join(s))
    print("BENCHMARK COMPLETE",json.dumps({n:{p:round(result[n][p]["net_pct"],3) for p,_,_ in SPLITS} for n in result}),flush=True)
if __name__=="__main__": main()
