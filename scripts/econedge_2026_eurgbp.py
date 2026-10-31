#!/usr/bin/env python3
"""Research-only, frozen EURUSD+GBPUSD weekly reversal vs trend, real 2026 H1.

Data: genuine Dukascopy BID/ASK open quotes SHA256 checked monthly from
2025-09 to 2026-09. NO fabricated data, live order submission or optimizer.
Known limitation: min .001 lot is a hypothetical broker configuration.
"""
import os,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import econedge_weekly_trend as base
from portfolio_research import verify_month,PIPS

ROOT=Path("econedge_2026_eurgbp_results")
PAIRS=("eurusd","gbpusd")
FIRST="2025-09";LAST="2026-09"
YEAR=2026
def load_data():
    months=[str(x) for x in pd.period_range(FIRST,LAST,freq="M")]
    if len(months)!=13:raise AssertionError("Expected Sep 2025–Sep 2026")
    data={};audit=[]
    for sym in PAIRS:
        folder=Path("data") if sym=="eurusd" else Path("portfolio_data")/sym
        tables=[]
        for m in months:
            f=folder/(m+".csv");j=Path(str(f)+".source.json")
            if not f.exists() or not j.exists():raise FileNotFoundError(f)
            metadata=json.loads(j.read_text());raw=f.read_bytes()
            if metadata.get("source")!="dukascopy-node" or metadata.get("timeframe")!="h1" or metadata.get("instrument") not in (None,sym):
                raise ValueError("Wrong data provenance: "+str(f))
            if hashlib.sha256(raw).hexdigest()!=metadata.get("sha256"):raise ValueError("SHA256 "+str(f))
            df=verify_month(folder,m,sym)
            if int(metadata.get("candles",len(df)))!=len(df):raise ValueError("Wrong monthly bar count "+str(f))
            if df.empty:raise ValueError("Empty month "+str(f))
            tables.append(df)
            audit.append(dict(pair=sym,month=m,hourly_bars=len(df),sha256=metadata["sha256"]))
        x=pd.concat(tables,ignore_index=True)
        x["timestamp"]=pd.to_datetime(x["timestamp"],utc=True,errors="raise")
        if x.timestamp.duplicated().any():raise ValueError("Duplicate quote timestamp "+sym)
        x=x.set_index("timestamp").sort_index()
        if not(x.ask_open>=x.bid_open).all():raise ValueError("Crossed BID ASK "+sym)
        data[sym]=x
    idx=data["eurusd"].index.intersection(data["gbpusd"].index).sort_values()
    if len(idx)<6500:raise ValueError("Not enough real shared H1 quotes")
    return idx,{s:data[s].loc[idx].copy() for s in PAIRS},audit

def freeze_events(index,prices):
    old=base.SYMBOLS
    try:
        base.SYMBOLS=PAIRS
        raw=base.build_weekly_events(index,prices,first_year=YEAR,last_year=YEAR)
    finally:
        base.SYMBOLS=old
    # Only complete weeks with the true original Friday 20:00 H1 OPEN.
    events=[e for e in raw if e["exit_deadline"] in index and
            e["time"].year==YEAR and e["exit_deadline"]<=index[-1]]
    if len(events)<20:raise ValueError("Too few complete 2026 weeks")
    return events

def signals(events,index,prices):
    data=[]
    for e in events:
        if not e["qualifies"]:continue
        sym=e["sym"];p=prices[sym];pip=PIPS[sym];i=e["entry_idx"];k=e["end_idx"]
        if index[k]!=e["exit_deadline"]:raise AssertionError("Partial week")
        side=-e["momentum_direction"]
        open_reverse=(float(p.ask_open.iloc[i]) if side==1 else float(p.bid_open.iloc[i]))
        close_reverse=(float(p.bid_open.iloc[k]) if side==1 else float(p.ask_open.iloc[k]))
        other=-side
        open_trend=(float(p.ask_open.iloc[i]) if other==1 else float(p.bid_open.iloc[i]))
        close_trend=(float(p.bid_open.iloc[k]) if other==1 else float(p.ask_open.iloc[k]))
        data.append(dict(time=str(e["time"]),week=f"{e['time'].isocalendar().year}-{e['time'].isocalendar().week:02d}",
                         pair=sym,zscore=e["z"],planned_stop_pips=e["stop_pips"],
                         reversal_pips=side*(close_reverse-open_reverse)/pip-2*base.SLIPPAGE_PIPS,
                         trend_pips=other*(close_trend-open_trend)/pip-2*base.SLIPPAGE_PIPS))
    return pd.DataFrame(data)

def run_book(events,prices,minimum_lot,mode):
    old=base.LOT_STEP
    try:
        base.LOT_STEP=minimum_lot
        t,counts,decisions=base.weekly_replay(events,prices,YEAR,YEAR+1,mode)
        if len(t):
            if (t.designed_risk_usd>t.budget_usd+1e-7).any():raise AssertionError("Risk >0.5%")
            if (t.lot<minimum_lot-1e-10).any():raise AssertionError("Below lot step")
            if t.week.duplicated().any():raise AssertionError("More than 1 filled/ISO week")
            if (t.pnl_x2_usd>t.pnl_usd+1e-8).any():raise AssertionError("Stress increases PnL")
            if (t.lot.div(minimum_lot).sub(t.lot.div(minimum_lot).round()).abs()>1e-7).any():
                raise AssertionError("Not multiple of configured lot step")
        result=base.metrics(t,counts,events,YEAR,YEAR+1)
    finally:
        base.LOT_STEP=old
    return t,decisions,result

def main():
    ROOT.mkdir(exist_ok=True)
    idx,prices,audit=load_data()
    events=freeze_events(idx,prices)
    obs=signals(events,idx,prices)
    obs.to_csv(ROOT/"FROZEN_2026_WEEKLY_DIRECTION.csv",index=False)
    results={}
    for lot in (.01,.001):
        label="standard_minlot_001" if lot==.01 else "hypothetical_minlot_0001"
        results[label]={}
        for mode in ("opposite_control","trend"):
            t,d,metrics=run_book(events,prices,lot,mode)
            t.to_csv(ROOT/(label+"_"+mode+"_TRADES.csv"),index=False)
            d.to_csv(ROOT/(label+"_"+mode+"_DECISIONS.csv"),index=False)
            results[label][mode]=metrics
            print("EURGBP_2026",label,mode,"fills",metrics["entered"],
                "net_USD",round(metrics["net_usd"],3),flush=True)
    rev=obs.reversal_pips.to_numpy(float) if not obs.empty else np.array([])
    guard=(len(rev)>=20 and base.block_bootstrap_lower(rev) is not None and
           base.block_bootstrap_lower(rev)>0)
    usable=results["standard_minlot_001"]["opposite_control"]
    good=bool(guard and usable["entered"]>=15 and usable["net_usd"]>0 and
       usable["spread_x2_net_usd"]>0 and (usable["pf"] or 0)>1.1 and
       (usable["bootstrap_lower_mean_week_usd"] or -1)<=0 is False)
    output=dict(status="RESEARCH_ONLY_NO_REAL_BROKER_ORDERS",
        data="Authentic Dukascopy H1 BID ASK OPEN 2025-09 through 2026-09, SHA256 by source month",
        provenance=audit,common_H1=len(idx),realized_year=YEAR,
        full_weeks=len(events),weekly_signals=len(obs),
        fixed_480H_z_threshold=base.MIN_TREND_Z,
        sign="Reverse of four-week trend; matched same-week opposite benchmark",
        2026_mean_reversal_pips=float(rev.mean()) if len(rev) else None,
        2026_mean_trend_pips=float(obs.trend_pips.mean()) if len(obs) else None,
        2026_bootstrap_8week_lower_pips=base.block_bootstrap_lower(rev),
        risk_fraction=.005,cap_lev=5.,trade_accounts_start_usd=1000,
        lot_variants="0.01 standard; 0.001 HYPOTHETICAL and broker support not verified",
        books=results,preregistered_gate_pass=bool(good),
        verdict="INSUFFICIENT_OR_NO_GO" if not good else "REQUIRES_FORWARD_TICKS_SWAP_DEMO",
        cautions=["2026 H1 calendar price previously appeared in other project research, not pristine multi-trial OOS",
                 "No historical Exness swap/tick level, expected prices not guaranteed fills",
                 "Trailing Friday 20:00 quote must exist, partial weeks excluded",
                 "Original H1 stop uses midpoint High/Low and opening-spread proxy, not true tick bid ask",
                 "No real order submission"],
        real_orders=0)
    (ROOT/"EURGBP_2026_RESULTS.json").write_text(json.dumps(output,ensure_ascii=False,indent=2,default=str))
    lines=["# EUR/USD + GBP/USD — nghiên cứu kiểm định giá H1 thật năm 2026",
      "",f"{len(events)} tuần hoàn chỉnh, {len(obs)} tuần đủ tín hiệu. Nguồn {len(audit)} tệp tháng Bid/Ask đã kiểm tra SHA-256.",
      "",f"Đảo chiều: pip TB **{output['2026_mean_reversal_pips']}**; Cận dưới bootstrap 95% **{output['2026_bootstrap_8week_lower_pips']}**.",
      "", "| Lot tối thiểu | Chính sách | Giao dịch | PnL USD | PF | Stress x2 spread USD | DD đóng lệnh |",
      "|---|---|---:|---:|---:|---:|---:|"]
    for a in results:
        for b,r in results[a].items():
            fmt=lambda x:"—" if x is None else f"{x:.3f}"
            lines.append(f"| {a} | {b} | {r['entered']} | {r['net_usd']:+.2f} | {fmt(r['pf'])} | {r['spread_x2_net_usd']:+.2f} | {r['dd_closed_pct']:.2f}% |")
    lines.extend(["",f"**Phán quyết:** {output['verdict']}.",
      "Ghi chú: 0.001 lot chỉ giả định. Phân tích chưa có swap, execution tick Exness, financing và giá đóng thật của H1; không đủ điều kiện cho giao dịch tiền thật."])
    (ROOT/"BAO_CAO_EURGBP_2026.md").write_text("\n".join(lines))
    print("EURGBP_2026_FINISHED",len(events),len(obs),output["verdict"],flush=True)
if __name__=="__main__":main()
