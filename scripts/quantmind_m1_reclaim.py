#!/usr/bin/env python3
"""QuantMind v2: observe authentic M1 BID/ASK false-break + reclaim events.

This is a FROZEN hypothesis test, not a fitted ML strategy. Screening is
causal, signals use only closed M1, BUY executes at next ASK+slip and SELL
at next BID-slip. Exit uses real observed opposing quote OHLC (SL first if
same candle touches target and stop). No historical H1 interpolation.
The terms 'liquidity sweep' and 'order flow' are not inferred from quotes:
this only measures price false-breaks and quote spread.
"""
import os,json,hashlib,math
from pathlib import Path
import numpy as np
import pandas as pd
from portfolio_research import PIPS, SYMBOLS

START_EQUITY=1000.
STOP_BUFFER_PIPS=1.
SLIPPAGE_PIPS=.1
RISK=.005
MAX_LEVERAGE=5.
RR=2.
LOOKBACK=60
SPREAD_LOOKBACK=120
MAX_SPREAD_PIPS=2.5
SPREAD_MULTIPLE=1.25
MIN_BREAK_PIPS=.8
MIN_RECLAIM_PIPS=.1
MAX_HOLD_MINS=120
OUT=Path("m1_reclaim_results")
M1_COLS=["timestamp","open","high","low","close","bid_open","bid_high","bid_low",
         "bid_close","ask_open","ask_high","ask_low","ask_close","spread_open_pips"]

def month_list(start,end):
    return [str(x) for x in pd.period_range(start[:7],
         (pd.Timestamp(end)-pd.Timedelta(days=1)).strftime("%Y-%m"),freq="M")]

def load_actual_quotes():
    start=os.environ.get("M1_FROM","2024-01-01")
    end=os.environ.get("M1_TO","2024-02-01")
    months=month_list(start,end)
    if not months:raise ValueError("Empty period")
    source={}
    data={}
    for symbol in SYMBOLS:
        files=[]
        for month in months:
            path=Path("m1_market")/symbol/(month+".csv.gz")
            meta=Path(str(path)+".source.json")
            if not path.exists() or not meta.exists():
                raise RuntimeError("Real M1 Bid/Ask data unavailable, cannot interpolate H1: "+str(path))
            m=json.loads(meta.read_text())
            if (m.get("source")!="dukascopy-node" or m.get("timeframe")!="m1"
                    or m.get("symbol")!=symbol or
                    hashlib.sha256(path.read_bytes()).hexdigest()!=m.get("sha256")):
                raise ValueError("M1 data hash/provenance invalid: "+str(path))
            x=pd.read_csv(path,compression="gzip")
            if len(x)!=m["candles"] or not set(M1_COLS).issubset(x.columns):
                raise ValueError("M1 month missing actual quotes "+str(path))
            files.append(x[M1_COLS])
        df=pd.concat(files,ignore_index=True)
        df["timestamp"]=pd.to_datetime(df.timestamp,utc=True,errors="raise")
        df=df.set_index("timestamp").sort_index()
        if df.index.has_duplicates:raise ValueError("Duplicate M1 timestamp "+symbol)
        arr=df[M1_COLS[1:]].to_numpy(float)
        if not np.isfinite(arr).all():raise ValueError("Nonfinite data "+symbol)
        if (df.ask_open<df.bid_open).any():raise ValueError("Inverted BID ASK "+symbol)
        source[symbol]={"months":months,"real_m1_bars":len(df)}
        data[symbol]=df
    return data,source,start,end

def event_candidates(quotes,mode):
    if mode not in ("reversal","continuation"):raise ValueError("Mode")
    events=[];stats={}
    for symbol,df in quotes.items():
        pip=PIPS[symbol];n=len(df)
        h=df.high.to_numpy(float);lo=df.low.to_numpy(float)
        cl=df.close.to_numpy(float);op=df.open.to_numpy(float)
        bidc=df.bid_close.to_numpy(float);askc=df.ask_close.to_numpy(float)
        spreads=np.maximum(0,(askc-bidc)/pip)
        medspread=pd.Series(spreads).shift(1).rolling(SPREAD_LOOKBACK,min_periods=SPREAD_LOOKBACK).median().to_numpy(float)
        priorhi=pd.Series(h).shift(1).rolling(LOOKBACK,min_periods=LOOKBACK).max().to_numpy(float)
        priorlo=pd.Series(lo).shift(1).rolling(LOOKBACK,min_periods=LOOKBACK).min().to_numpy(float)
        ts=df.index
        ns=ts.asi8
        continuity=np.zeros(n,bool)
        # Requirement: 60 preceding observed minutes cover no more than 90
        # calendar minutes, and next-minute quote exists.
        ids=np.arange(LOOKBACK,n-1)
        continuity[ids]=(ns[ids]-ns[ids-LOOKBACK]<=90*60*10**9)&(
             ns[ids+1]-ns[ids]==60*10**9)
        session=(ts.weekday<5)&(ts.hour>=7)&(ts.hour<17)
        spread_ok=(spreads<=MAX_SPREAD_PIPS)&(spreads<=SPREAD_MULTIPLE*medspread)
        up=(h>=priorhi+MIN_BREAK_PIPS*pip)&(cl<=priorhi-MIN_RECLAIM_PIPS*pip)&(cl>=priorlo)
        down=(lo<=priorlo-MIN_BREAK_PIPS*pip)&(cl>=priorlo+MIN_RECLAIM_PIPS*pip)&(cl<=priorhi)
        eligible=continuity&session&spread_ok&np.isfinite(priorhi)&np.isfinite(priorlo)
        baseup=np.flatnonzero(eligible&up)
        basedown=np.flatnonzero(eligible&down)
        stats[symbol]={"m1_candles":n,"candidate_up_false_break":len(baseup),
            "candidate_down_false_break":len(basedown),"session_m1":int(session.sum()),
            "median_quote_spread_pips":float(np.nanmedian(spreads))}
        for indices,fade_side in ((baseup,-1),(basedown,1)):
            for j in indices:
                i=j+1
                side=fade_side if mode=="reversal" else -fade_side
                stop=((h[j]+STOP_BUFFER_PIPS*pip) if side==-1
                       else (lo[j]-STOP_BUFFER_PIPS*pip))
                # Continuation control has stop on opposite extreme of sweep bar:
                # Long fade-side opposite = trend breakout; stop still outside bar.
                distance=side*((float(df.ask_open.iloc[i])+SLIPPAGE_PIPS*pip
                        if side==1 else float(df.bid_open.iloc[i])-SLIPPAGE_PIPS*pip)-stop)/pip
                if not 2<=distance<=40:continue
                signal_score=(h[j]-priorhi[j] if indices is baseup else priorlo[j]-lo[j])/pip
                events.append(dict(signal_at=ts[j],time=ts[i],symbol=symbol,idx=int(i),
                    side=side,stop=stop,upper=priorhi[j],lower=priorlo[j],
                    spread_signal_pips=spreads[j],span_pips=float((h[j]-lo[j])/pip),
                    sweep_distance_pips=float(signal_score)))
    events.sort(key=lambda x:(x["time"],-x["sweep_distance_pips"],x["symbol"]))
    return events,stats

def exits_by_quote(df,side,entry_i,entry_quote,stop,tp):
    """Tick order within a minute is unknown: always assume STOP first.
    The entry minute may also touch both; do not claim a free TP there.
    """
    last_i=min(entry_i+MAX_HOLD_MINS,len(df)-1)
    for k in range(entry_i,last_i+1):
        if k==entry_i:
            # Even on the entry minute, a touched stop counts as loss.
            if side==1 and df.bid_low.iloc[k]<=stop:
                return k,min(float(df.bid_open.iloc[k]),stop),"same_minute_stop"
            if side==-1 and df.ask_high.iloc[k]>=stop:
                return k,max(float(df.ask_open.iloc[k]),stop),"same_minute_stop"
            continue
        q=df.iloc[k]
        if side==1:
            if q.bid_low<=stop:return k,min(float(q.bid_open),stop),"stop"
            if q.bid_high>=tp:return k,tp,"tp2r"
        else:
            if q.ask_high>=stop:return k,max(float(q.ask_open),stop),"stop"
            if q.ask_low<=tp:return k,tp,"tp2r"
    k=last_i
    return k,(float(df.bid_close.iloc[k]) if side==1 else
              float(df.ask_close.iloc[k])),"timeout"

def simulate(quotes,events,mode,spread_stress=False):
    cash=START_EQUITY;last_week=None;busy_until=None
    count={"candidate_count":len(events),"attempted":0,"accepted":0,
           "skip_risk":0,"skip_spread":0,"skip_occupied":0,"skip_week":0}
    trades=[];seen_timestamps=set()
    for e in events:
        t=e["time"];wk=(t.isocalendar().year,t.isocalendar().week)
        if last_week==wk:count["skip_week"]+=1;continue
        if busy_until is not None and t<=busy_until:
            count["skip_occupied"]+=1;continue
        if t in seen_timestamps:continue
        # Same timestamp across symbols: highest a-priori sweep score, deterministic.
        seen_timestamps.add(t);count["attempted"]+=1
        sym=e["symbol"];pip=PIPS[sym];df=quotes[sym];i=e["idx"];side=e["side"]
        bar=df.iloc[i]
        observed_spread=(bar.ask_open-bar.bid_open)/pip
        if not np.isfinite(observed_spread) or observed_spread>MAX_SPREAD_PIPS:
            count["skip_spread"]+=1;continue
        # Spread stress: add one extra observed quoted spread (half at entry and
        # half at exit in a symmetric scenario), not a fabricated alternate path.
        extra_stress=.5*observed_spread*pip if spread_stress else 0.
        entry=(float(bar.ask_open)+SLIPPAGE_PIPS*pip+extra_stress if side==1
               else float(bar.bid_open)-SLIPPAGE_PIPS*pip-extra_stress)
        stop=e["stop"]
        distance=side*(entry-stop)/pip+SLIPPAGE_PIPS+(
                .5*observed_spread if spread_stress else 0.)
        if not 2<=distance<=45:
            count["skip_risk"]+=1;continue
        # The exit quote must be >2R from actual executable entry incl slippage.
        target=entry+side*(2*distance+SLIPPAGE_PIPS
                          +(.5*observed_spread if spread_stress else 0.))*pip
        point=10. if sym!="usdjpy" else 1000./max(entry,1.)
        max_by_risk=cash*RISK/(distance*point)
        max_by_leverage=cash*MAX_LEVERAGE/(100000*(1 if sym=="usdjpy" else entry))
        lots=math.floor((min(max_by_risk,max_by_leverage,.5)+1e-10)/.01)*.01
        if lots<.01:
            count["skip_risk"]+=1;continue
        risk_usd=distance*point*lots
        if risk_usd>cash*RISK+1e-7:raise AssertionError("Risk >0.5%")
        k,exit_quote,reason=exits_by_quote(df,side,i,entry,stop,target)
        if spread_stress:
            exit_quote=exit_quote-side*.5*observed_spread*pip
        # No double counting spread: the actual execution quotes are used.
        pnlp=side*(exit_quote-entry)/pip-SLIPPAGE_PIPS
        pnlusd=pnlp*point*lots
        before=cash;cash+=pnlusd
        record=dict(signal_time=e["signal_at"].isoformat(),time=t.isoformat(),
            pair=sym,side="BUY" if side>0 else "SELL",mode=mode,
            breakout_high=e["upper"],breakout_low=e["lower"],
            sweep_pips=e["sweep_distance_pips"],signal_spread=e["spread_signal_pips"],
            entry_spread_pips=float(observed_spread),
            entry_executable_quote=entry,stop=stop,target=target,
            planned_risk_usd=risk_usd,lots=lots,
            max_planned_risk_usd=before*RISK,
            exit_time=df.index[k].isoformat(),exit_quote=exit_quote,reason=reason,
            pnl_usd=pnlusd,account_usd=cash)
        trades.append(record)
        count["accepted"]+=1;busy_until=df.index[k];last_week=wk
    return pd.DataFrame(trades),count

def stress_cost_only(trades):
    """Reprice the SAME entries and original TP/SL with extra observed spread.
    Reusing realized paths avoids giving extra spread a better profit target.
    This is a conservative *cost sensitivity*, not a new broker tick replay.
    """
    if trades.empty:return trades.copy()
    t=trades.copy()
    point=np.where(t.pair.to_numpy()=="usdjpy",
        1000/np.maximum(t.entry_executable_quote.to_numpy(float),1),
        10.)
    t["added_spread_cost_usd"]=t.entry_spread_pips.to_numpy(float)*point*t.lots.to_numpy(float)
    t["pnl_usd"]=t.pnl_usd-t.added_spread_cost_usd
    t["account_usd"]=START_EQUITY+t.pnl_usd.cumsum()
    if (t.added_spread_cost_usd<0).any():raise AssertionError("Spread stress must cost >=0")
    return t

def performance(trades,counts):
    if trades.empty:
        return dict(trades=0,net_return_pct=0.,win_rate=None,pf=None,
          drawdown_closed_pct=0.,pnl_usd=0.,wilson95_lower_winrate=None,
          **counts)
    pnl=trades.pnl_usd.to_numpy(float)
    b=START_EQUITY+np.cumsum(pnl)
    peak=np.maximum.accumulate(np.r_[START_EQUITY,b])[1:]
    wins=int((pnl>0).sum());n=len(pnl)
    pf=float(pnl[pnl>0].sum()/(-pnl[pnl<0].sum())) if (pnl<0).any() else None
    # One-sided 95% Wilson lower bound; a low-N win streak will not
    # be mistaken for statistically established TP 2R profitability.
    z=1.645;p=wins/n
    lower=(p+z*z/(2*n)-z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n)
    return dict(trades=n,net_return_pct=float(100*(b[-1]/START_EQUITY-1)),
        pnl_usd=float(pnl.sum()),win_rate=float(p),
        pf=pf,drawdown_closed_pct=float(np.min((b/peak-1)*100)),
        wilson95_lower_winrate=float(lower),**counts)

def main():
    OUT.mkdir(exist_ok=True)
    data,sources,start,end=load_actual_quotes()
    results={}
    for mode in ("reversal","continuation"):
        events,diag=event_candidates(data,mode)
        trades,count=simulate(data,events,mode)
        trades.to_csv(OUT/f"{mode}_trades.csv",index=False)
        stressed=stress_cost_only(trades)
        results[mode]=dict(performance=performance(trades,count),
             spread_x2=performance(stressed,count),signals=diag)
        print("RECLAIM",mode,"candidate",len(events),"filled",len(trades),
            "net_pct",round(results[mode]["performance"]["net_return_pct"],4),flush=True)
    all_months=month_list(start,end)
    completed=dict(period=[start,end],months=all_months,
        market_source="Authentic Dukascopy M1 BID ASK, SHA256 verified, not H1/M15 interpolation",
        source_audit=sources,lookback_prior_m1=LOOKBACK,
        candidate="M1 false breakout beyond previous 60-min high/low by >=0.8pip then CLOSE back inside >=0.1pip",
        spread_rule="Signal close <= 1.25x trailing 120 observed M1 close-spread median and <=2.5pip; entry spread <=2.5pip",
        scenarios=["reversal","continuation"],risk_fraction=RISK,
        take_profit="NET projected 2R, TP2R stops first conservative",
        stop_buffer_pips=STOP_BUFFER_PIPS,trade_limit="At most one filled position per ISO week across four pairs",
        max_hold_mins=MAX_HOLD_MINS,results=results,live_orders=0,
        caveats=["M1 OHLC not tick; same-minute fill versus stop order unknown; stop-first",
          "Dukascopy is quote provider, not centralized FX order-flow/order book",
          "Spread sensitivity x2 keeps identical trades, original TP/SL and lots and subtracts one extra quoted entry spread; no favorable repricing of TP",
          "Period subset may not be a complete year; never annualize percentage without evidence",
          "One-sided Wilson lower 95% bound cannot by itself account for dependence/nonstationarity"])
    (OUT/"RESULTS_M1_RECLAIM.json").write_text(json.dumps(completed,ensure_ascii=False,indent=2))
    lines=["# QuantMind FX v2 — M1 false-break/reclaim + spread, TP dự kiến 2R",
      "", f"Khoảng thời gian **{start} tới {end}** (không được gọi một năm nếu chỉ có một tháng).",
      "Dữ liệu **M1 BID/ASK thật từ Dukascopy**, không dùng M15/H1 tổng hợp để phỏng đoán đường giá trong 1 phút.",
      "So sánh hai giả thuyết định trước: **đảo chiều sau reclaim** và **đi tiếp theo hướng phá vỡ làm đối chứng**.",
      "", "| Giả thuyết | Ứng viên | Lệnh thực hiện | Thắng | PnL sau quote spread/trượt giá | PF | DD đóng lệnh | Spread x2 | Wilson lower p(win) |",
      "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for mode in ("reversal","continuation"):
        p=results[mode]["performance"];s=results[mode]["spread_x2"]
        fmt=lambda n:"—" if n is None else f"{n:.3f}"
        lines.append(f"| {mode} | {p['candidate_count']} | {p['trades']} | {fmt(p['win_rate'])} | {p['net_return_pct']:+.2f}% | {fmt(p['pf'])} | {p['drawdown_closed_pct']:.2f}% | {s['net_return_pct']:+.2f}% | {fmt(p['wilson95_lower_winrate'])} |")
    lines+=["","**Tiêu chí khẳng định sơ bộ**: tối thiểu 30 lệnh trong tập kiểm tra về sau, PnL và stress spread x2 đều dương, Wilson lower 95% của p(win) >1/3, PF>1,1. Chưa tính số lệnh hòa vốn/hết giờ trong công thức ngưỡng nên phải xem cả net PnL.",
       "Nếu không vượt, quyết định NO-GO, không chỉnh thông số dựa trên kết quả kỳ kiểm tra.",
       "Giá M1 vẫn không cho biết thứ tự tick trong cùng 1 phút; kết quả **không phải thực thi broker Exness**."]
    (OUT/"BAO_CAO_M1_RECLAIM.md").write_text("\n".join(lines))
    print("M1_RECLAIM_COMPLETE",json.dumps({k:[v["performance"]["trades"],round(v["performance"]["net_return_pct"],3)] for k,v in results.items()}),flush=True)

if __name__=="__main__":main()
