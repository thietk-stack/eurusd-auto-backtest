#!/usr/bin/env python3
"""WINNERFX v1: test a market-risk-premium / positive-skew trading mindset.

Price-only approximation: 55D close breakout + EMA20/100 confirmation, 3x
ATR20 protective trailing stop that NEVER widens, hold up to 90 D1 bars.
NO profit target; asymmetric wins vs small losses. Data: 4-pair SHA verified
Dukascopy H1, 2010 warmup, 2011-25; no swap, no tick, no live trades.
Frozen BEFORE this particular strategy's initial performance inspection.
"""
import json,math
from pathlib import Path
import numpy as np
import pandas as pd
from portfolio_research import PIPS,SYMBOLS
from econedge_long_2011_2025 import verified_16_year_data
from econedge_weekly_trend import block_bootstrap_lower

OUT=Path("winnerfx_v1_results")
START=1000.
RISK=.005
MAX_LEV=5.
LOT_STEPS=(.001,.01)
SLIP=.1
BREAK_DAYS=55
EMA_FAST=20
EMA_SLOW=100
ATR_DAYS=20
STOP_ATR=3.
MIN_STOP_PIPS=15.
MAX_STOP_PIPS=400.
MAX_HOLD_TRADING_DAYS=90
MAX_SPREAD_PIPS=10.
ERAS={"historic_2011_2017":(2011,2018),
      "reused_2018_2025":(2018,2026),
      "continuous_2011_2025":(2011,2026)}

def build_daily(index,quotes):
    """Only actual common H1 observations; never synthesize intraday quotes."""
    dindex=index.floor("D")
    uniq,initial,number=np.unique(dindex.values,return_index=True,return_counts=True)
    valid=np.flatnonzero(number>=16)
    day_index=pd.DatetimeIndex(uniq[valid]).tz_localize("UTC")
    offsets=initial[valid]
    stops=offsets+number[valid]
    daily={};hourly={}
    for sym in SYMBOLS:
        p=quotes[sym]
        h=p.high.to_numpy(float)
        low=p.low.to_numpy(float)
        close=p.close.to_numpy(float)
        op=p.open.to_numpy(float)
        row=[]
        for a,b in zip(offsets,stops):
            row.append([op[a],np.max(h[a:b]),np.min(low[a:b]),close[b-1]])
        bars=pd.DataFrame(row,index=day_index,columns=["open","high","low","close"])
        prev=bars.close.shift(1)
        tr=pd.concat([bars.high-bars.low,
             (bars.high-prev).abs(),(bars.low-prev).abs()],axis=1).max(axis=1)
        bars["atr"]=tr.rolling(ATR_DAYS,min_periods=ATR_DAYS).mean()
        bars["ema_fast"]=bars.close.ewm(span=EMA_FAST,adjust=False).mean()
        bars["ema_slow"]=bars.close.ewm(span=EMA_SLOW,adjust=False).mean()
        bars["prev55hi"]=bars.close.shift(1).rolling(BREAK_DAYS,min_periods=BREAK_DAYS).max()
        bars["prev55lo"]=bars.close.shift(1).rolling(BREAK_DAYS,min_periods=BREAK_DAYS).min()
        daily[sym]=bars
        hourly[sym]=dict(high=h,low=low,bid=p.bid_open.to_numpy(float),
            ask=p.ask_open.to_numpy(float),open=op)
    if len(day_index)<3900:raise ValueError("Missing 2010–25 genuine daily windows")
    return day_index,offsets,stops,daily,hourly

def selection(day_idx,daily):
    """Read CLOSED day t-1 only. No today high, close, ATR or spread."""
    j=day_idx-1
    if j<max(EMA_SLOW+20,BREAK_DAYS+1):return None
    opportunities=[]
    for sym in SYMBOLS:
        b=daily[sym].iloc[j]
        c=float(b["close"]);atr=float(b["atr"])
        if not np.isfinite(c) or not np.isfinite(atr) or atr<=0:continue
        if c>b.prev55hi and b.ema_fast>b.ema_slow:
            opportunities.append((float((c-b.prev55hi)/atr),sym,1,atr))
        elif c<b.prev55lo and b.ema_fast<b.ema_slow:
            opportunities.append((float((b.prev55lo-c)/atr),sym,-1,atr))
    if not opportunities:return None
    opportunities.sort(key=lambda x:(-x[0],x[1]))
    _,sym,side,atr=opportunities[0]
    return dict(pair=sym,trend_side=side,atr_signal=atr,
        signal_date=daily[sym].index[j])

def lot_size(equity,entry,pip,stop_pips,sym,step):
    point=10. if sym!="usdjpy" else 1000./max(entry,1.)
    usd_notional=100000. * (1. if sym=="usdjpy" else entry)
    rper_lot=(stop_pips+SLIP)*point
    maxlot=min(.5,equity*RISK/rper_lot,equity*MAX_LEV/usd_notional)
    lots=math.floor((maxlot+1e-10)/step)*step
    lots=round(lots,max(2,round(-math.log10(step))))
    if lots<step-1e-10:return None
    if (stop_pips+SLIP)*point*lots>equity*RISK+1e-6:
        raise AssertionError("Stop risk >0.5%")
    if usd_notional*lots>equity*MAX_LEV+1e-6:
        raise AssertionError("5x leverage violated")
    return lots,point,rper_lot*lots

def better_stop(old,close,atr,side):
    proposal=close-side*STOP_ATR*atr
    return max(old,proposal) if side==1 else min(old,proposal)

def exit_check(a,b,hourly,sym,side,stop,pip):
    """Quote high/low unavailable: approximate via midpoint OHLC and open spread.
    If gap through stop, execute at *worse* observed opposing bid/ask open.
    """
    h=hourly[sym];highest=h["high"];lowest=h["low"]
    for k in range(a,b):
        sp=(h["ask"][k]-h["bid"][k])/pip
        if not np.isfinite(sp) or sp<0:raise ValueError("Invalid real quote spread")
        if side==1:
            if lowest[k]-.5*sp*pip<=stop:
                return k,min(stop,h["bid"][k]-SLIP*pip),"stop"
        else:
            if highest[k]+.5*sp*pip>=stop:
                return k,max(stop,h["ask"][k]+SLIP*pip),"stop"
    return None

def select_and_replay(index,starts,ends,daily,hourly,first_year,last_year,step,mode):
    cash=START
    live=None;trades=[];decisions=[];year_hits={}
    stats=dict(days_considered=0,signals=0,no_entry_due_active=0,
        stopped=0,skip_min_lot=0,skip_stop_too_wide=0,skip_spread=0,
        entered=0,exit_time=0,stop_exits=0,close_out_at_cutoff=0)
    def finish(state,end_day,k,exitprice,reason):
        nonlocal live,cash
        sym=state["pair"];pip=PIPS[sym];side=state["side"];h=hourly[sym]
        sp_ex=(h["ask"][k]-h["bid"][k])/pip
        raw=side*(exitprice-state["entry_price"])/pip
        # 0.1pip slippage included on entry. Stop price includes assumed
        # exit slippage; for non-stop TIME exit add exit slippage here.
        pnl_pips=raw-(0 if reason=="stop" else SLIP)
        pnl=pnl_pips*state["usd_per_pip_per_lot"]*state["lots"]
        if not np.isfinite(pnl):raise AssertionError("Bad profit")
        stress_usd=.5*(state["entry_spread"]+sp_ex)*state["usd_per_pip_per_lot"]*state["lots"]
        cash+=pnl
        record=dict(entry_date=state["entry_date"].isoformat(),
             exit_date=index[end_day].isoformat(),pair=sym,
             direction="BUY" if side>0 else "SELL",mode=mode,
             lots=state["lots"],entry_price=state["entry_price"],
             entry_spread_pips=state["entry_spread"],
             exit_spread_pips=float(sp_ex),
             init_stop_pips=state["initial_stop_pips"],
             stop_at_exit=state["stop"],exit_price=float(exitprice),
             exit_reason=reason,entry_capital=state["capital_at_entry"],
             risk_usd=state["risk_usd"],max_budget_usd=state["capital_at_entry"]*RISK,
             holding_days=end_day-state["entry_day"]+1,
             pnl_pips=float(pnl_pips),pnl_usd=float(pnl),
             extra_spread_usd=stress_usd,pnl_spread_x2_usd=pnl-stress_usd,
             equity_after=float(cash))
        trades.append(record)
        stats["stop_exits" if reason=="stop" else "exit_time"]+=1
        live=None
    for day,ts in enumerate(index):
        if ts.year<first_year or ts.year>=last_year:continue
        stats["days_considered"]+=1
        a=int(starts[day]);b=int(ends[day])
        # We never open new position the day the previous position exited,
        # even when there is another signal at today's first hour.
        had_live=live is not None
        if live is not None:
            sym=live["pair"];pip=PIPS[sym]
            if day-live["entry_day"]>=MAX_HOLD_TRADING_DAYS:
                h=hourly[sym];k=a
                exitprice=(h["bid"][k] if live["side"]==1 else h["ask"][k])
                finish(live,day,k,exitprice,"max_hold")
            else:
                touched=exit_check(a,b,hourly,sym,live["side"],live["stop"],pip)
                if touched:
                    k,exitprice,reason=touched
                    finish(live,day,k,exitprice,reason)
                else:
                    current=daily[sym].iloc[day]
                    if np.isfinite(current.atr):
                        live["stop"]=better_stop(live["stop"],float(current.close),float(current.atr),live["side"])
        if had_live:
            stats["no_entry_due_active"]+=1
            continue
        if live is not None:continue
        signal=selection(day,daily)
        if signal is None:continue
        stats["signals"]+=1
        sym=signal["pair"];pip=PIPS[sym];side=signal["trend_side"] * (1 if mode=="trend" else -1)
        stop_pips=max(MIN_STOP_PIPS,STOP_ATR*signal["atr_signal"]/pip)
        if stop_pips>MAX_STOP_PIPS:
            stats["skip_stop_too_wide"]+=1
            decisions.append(dict(date=ts.isoformat(),reason="stop_too_wide",pair=sym))
            continue
        h=hourly[sym];first=a
        spread=(h["ask"][first]-h["bid"][first])/pip
        if not 0<=spread<=MAX_SPREAD_PIPS:
            stats["skip_spread"]+=1
            decisions.append(dict(date=ts.isoformat(),reason="spread",pair=sym))
            continue
        entry=float(h["ask"][first]+SLIP*pip if side>0
                    else h["bid"][first]-SLIP*pip)
        sizing=lot_size(cash,entry,pip,stop_pips,sym,step)
        if sizing is None:
            stats["skip_min_lot"]+=1
            decisions.append(dict(date=ts.isoformat(),reason="lot",pair=sym))
            continue
        lots,point,risk_usd=sizing
        live=dict(pair=sym,side=side,entry_price=entry,initial_stop_pips=stop_pips,
             stop=entry-side*stop_pips*pip,entry_spread=float(spread),
             entry_day=day,entry_date=ts,lots=lots,usd_per_pip_per_lot=point,
             capital_at_entry=cash,risk_usd=risk_usd)
        stats["entered"]+=1
        decisions.append(dict(date=ts.isoformat(),reason="entered",pair=sym))
        # Check real M1? Not available. The first H1 could hit stop; conservative
        # stop-first and no target award on the entry hour.
        touched=exit_check(a,b,hourly,sym,side,live["stop"],pip)
        if touched:
            k,exitprice,reason=touched
            finish(live,day,k,exitprice,reason)
        else:
            bar=daily[sym].iloc[day]
            if np.isfinite(bar.atr):
                live["stop"]=better_stop(live["stop"],float(bar.close),float(bar.atr),side)
    if live is not None:
        # Do not mark-to-market at an arbitrary future quote. Liquidate exactly
        # at the last observed hour of the specified research period with proxy
        # mid close and half observed OPEN spread.
        day=next(i for i,t in reversed(list(enumerate(index))) if t.year<last_year and t.year>=first_year)
        k=int(ends[day]-1);sym=live["pair"];h=hourly[sym];pip=PIPS[sym]
        sp=(h["ask"][k]-h["bid"][k])/pip
        raw_close=float(daily[sym].close.iloc[day])
        proxy=raw_close-live["side"]*.5*sp*pip
        finish(live,day,k,proxy,"period_cutoff")
        stats["close_out_at_cutoff"]+=1
    t=pd.DataFrame(trades);d=pd.DataFrame(decisions)
    if not t.empty:
        if (t.risk_usd>t.max_budget_usd+1e-6).any():raise AssertionError("Too much risk")
        if (t.pnl_spread_x2_usd>t.pnl_usd+1e-8).any():raise AssertionError("Spread stress improved PnL")
        if (t.lots+1e-9<step).any():raise AssertionError("Too-small lot")
    return t,d,stats

def performance(trades,stats,year0,year1):
    if trades.empty:
        return dict(**stats,pnl_usd=0.,return_pct=0.,pf=None,
          win_pct=None,mean_winner_usd=None,mean_loser_usd=None,
          dd_closed_pct=0.,average_hold_days=None,bootstrap_lower_week_usd=None,
          spread_x2_net_usd=0.)
    p=trades.pnl_usd.to_numpy(float)
    total=float(p.sum())
    eq=START+np.cumsum(p);peak=np.maximum.accumulate(np.r_[START,eq])[1:]
    pos=p[p>0];neg=p[p<0]
    # Build all Monday-anchored weeks, assign realized PnL by exit week.
    periods=pd.period_range(f"{year0}-01-01",f"{year1-1}-12-31",freq="W-SUN")
    weekly=pd.Series(0.,index=periods)
    for t in trades.itertuples(index=False):
        period=pd.Timestamp(t.exit_date).tz_localize(None).to_period("W-SUN")
        if period in weekly.index:weekly.loc[period]+=t.pnl_usd
    return dict(**stats,pnl_usd=total,return_pct=float(100*total/START),
        pf=(float(pos.sum()/-neg.sum()) if len(neg) else None),
        win_pct=float(100*np.mean(p>0)),
        mean_winner_usd=(float(pos.mean()) if len(pos) else None),
        mean_loser_usd=(float(neg.mean()) if len(neg) else None),
        avg_pnl_usd=float(p.mean()),
        dd_closed_pct=float(100*np.min(eq/peak-1)),
        average_hold_days=float(trades.holding_days.mean()),
        max_hold_days=int(trades.holding_days.max()),
        bootstrap_lower_week_usd=block_bootstrap_lower(weekly.to_numpy(float)),
        spread_x2_net_usd=float(trades.pnl_spread_x2_usd.sum()))

def annual_ledger(trades,start=2011,end=2026):
    rows=[];cash=START
    for year in range(start,end):
        ys=(trades[pd.to_datetime(trades.exit_date,utc=True).dt.year==year]
            if not trades.empty else trades)
        pnl=float(ys.pnl_usd.sum()) if not ys.empty else 0.
        eq=cash+pnl
        rows.append(dict(year=year,starting_equity_usd=cash,ending_equity_usd=eq,
           pnl_usd=pnl,return_pct=100*pnl/cash if cash else None,
           closed_trades=len(ys),wins=int((ys.pnl_usd>0).sum()) if not ys.empty else 0))
        cash=eq
    return pd.DataFrame(rows)

def gate(x,control):
    return (x["entered"]>=30 and x["pnl_usd"]>0 and
        x["spread_x2_net_usd"]>0 and (x["pf"] or 0)>1.1 and
        (x["bootstrap_lower_week_usd"] is not None and x["bootstrap_lower_week_usd"]>0)
        and x["pnl_usd"]>control["pnl_usd"])

def main():
    OUT.mkdir(exist_ok=True)
    ix,real,source=verified_16_year_data() # SHA256 all months×4
    days,starts,ends,daily,hourly=build_daily(ix,real)
    values={};annual=[]
    for era,(first,last) in ERAS.items():
        values[era]={}
        for step in LOT_STEPS:
            lot_key=f"minlot_{step:.3f}"
            values[era][lot_key]={}
            for direction in ("trend","inverse_control"):
                tr,decs,stats=select_and_replay(days,starts,ends,daily,hourly,first,last,step,
                       "trend" if direction=="trend" else "inverse")
                # Trading function sees 'inverse' and flips selected signal.
                tr.to_csv(OUT/f"{era}_{lot_key}_{direction}_TRADES.csv",index=False)
                decs.to_csv(OUT/f"{era}_{lot_key}_{direction}_DECISIONS.csv",index=False)
                r=performance(tr,stats,first,last)
                values[era][lot_key][direction]=r
                if era=="continuous_2011_2025":
                    an=annual_ledger(tr)
                    an["policy"]=lot_key+"_"+direction
                    annual.append(an)
                print("WINNERFX",era,lot_key,direction,"trades",r["entered"],
                  "USD",round(r["pnl_usd"],3),"PF",r["pf"],
                  "lower",r["bootstrap_lower_week_usd"],flush=True)
    pd.concat(annual,ignore_index=True).to_csv(OUT/"ANNUAL_REALIZED_PNL_2011_2025.csv",index=False)
    early=values["historic_2011_2017"]["minlot_0.001"]
    late=values["reused_2018_2025"]["minlot_0.001"]
    long=values["continuous_2011_2025"]["minlot_0.001"]["trend"]
    good=bool(gate(early["trend"],early["inverse_control"]) and
         gate(late["trend"],late["inverse_control"]) and
         long["pnl_usd"]>0 and long["spread_x2_net_usd"]>0 and
         long["dd_closed_pct"]>=-15.)
    result=dict(status="RESEARCH_ONLY_NO_BROKER_ORDERS",
       price_source="Dukascopy H1 source-authentic and SHA256 verified all 2010–2025 months / 4 pairs",
       source_info=source,joint_hourly_bars=len(ix),valid_days=len(days),
       policy="D1 close breaks previous 55D close range + EMA20/EMA100, 3ATR trailing without widening, 90D maximum, only one position across four pairs",
       variables=dict(risk_per_trade=RISK,leverage=MAX_LEV,initial_usd=START,
          lot_steps=LOT_STEPS,atr_multiple=STOP_ATR,
          stop_min=MIN_STOP_PIPS,stop_max=MAX_STOP_PIPS,
          max_hold_days=MAX_HOLD_TRADING_DAYS,slippage_pips_each_side=SLIP),
       eras=values,gate_success=good,
       verdict="FORWARD_DEMO_SWAP_CHECK_ONLY" if good else "NO_GO",
       independent_out_of_sample=False,live_orders=0,
       limitations=["These 2011–25 dates were used for many earlier studies. Positive result would be exploratory, not independent validation.",
         "No central order book, no dealer maker spread revenue can be replicated from this OHLC dataset",
         "High/Low H1 are midpoint, intrahour bid/ask high/low inferred from opening spread proxy",
         "NO overnight swap or funding for 90-day trend holding; modeled profit may be optimistic",
         "0.001 standard lot may not be available under actual broker account; no tick price execution verification",
         "Stop risk 0.5% is planned, gaps can result in greater realized loss",
         "Only four USD-involving pairs, one position at a time, not diversified multi-asset managed futures"])
    (OUT/"WINNERFX_V1_RESULTS.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    lines=["# WINNERFX v1 — Theo xu hướng lớn, cắt lỗ có kiểm soát, KHÔNG TP cố định",
      "",f"**{len(ix):,} H1 cùng thời điểm và {len(days):,} D1 ngày hợp lệ**, nguồn H1 Dukascopy SHA256 thật 2010–25. Dữ liệu 2011–25 đã được sử dụng nhiều lần: kiểm định hồi cứu thăm dò, không phải OOS nguyên vẹn.",
      "Quy tắc 55D breakout Close + EMA20/100, theo xu hướng, stop trailing 3ATR20 **không nới**, giữ tối đa 90 ngày; chỉ một vị thế trên 4 cặp; rủi ro thiết kế 0,5% equity/lệnh; không TP 2R. Chưa tính phí swap, có slippage giả định 0,1pip mỗi chiều.",
      "","| Giai đoạn độc lập | Lot min | Chính sách | Lệnh | PnL USD | PF | Thắng | DD đóng lệnh | Spread x2 USD | Bootstrap lower USD/tuần |",
      "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    for era in ERAS:
        for step in LOT_STEPS:
            lk=f"minlot_{step:.3f}"
            for direction in ("trend","inverse_control"):
                r=values[era][lk][direction]
                fmt=lambda x:"—" if x is None else f"{x:.3f}"
                lines.append(f"| {era} | {step:.3f} | {direction} | {r['entered']} | {r['pnl_usd']:+.2f} | {fmt(r['pf'])} | {fmt(r['win_pct'])}% | {r['dd_closed_pct']:.2f}% | {r['spread_x2_net_usd']:+.2f} | {fmt(r['bootstrap_lower_week_usd'])} |")
    lines+=["",f"**Cổng chất lượng đã chốt trước chạy: {good}; phán quyết: {result['verdict']}**.",
      "Vui lòng xem CSV ANNUAL_REALIZED_PNL_2011_2025.csv và toàn bộ ledger. Các nhóm có tài khoản 1.000 USD khởi tạo riêng; nhóm continuous_2011_2025 là sổ vốn riêng xuyên suốt, KHÔNG cộng nhóm thành một tài khoản.",
      "Hành vi nắm giữ xu hướng có phí swap/triple swap thực tế chưa mô phỏng, và giá stop dựa trên H1 midpoint HighLow ±nửa spread. Dù có lãi cũng KHÔNG được dùng tiền thật từ backtest này. Nên thu thập tick/swap broker và kiểm tra forward demo."
    ]
    (OUT/"BAO_CAO_WINNERFX_V1.md").write_text("\n".join(lines))
    print("WINNERFX_V1_COMPLETED",json.dumps({e:{k:{p:[v["entered"],round(v["pnl_usd"],2)] for p,v in cs.items()} for k,cs in vals.items()} for e,vals in values.items()}),
         "GATE",good,flush=True)
if __name__=="__main__":main()
