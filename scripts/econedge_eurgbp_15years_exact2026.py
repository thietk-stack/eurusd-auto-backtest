#!/usr/bin/env python3
"""Audit EXACT two-pair EconEdge 2026 frozen rules on earlier 2011–25 H1 quotes.

The earlier four-pair 15-year study is NOT equivalent: this selects the
largest abs momentum of EURUSD/GBPUSD only and tests micro/standard lot.
2010 is exclusively feature warm-up; no hindsight price repair or broker orders.
"""
import json,hashlib,math
from pathlib import Path
import numpy as np,pandas as pd
from portfolio_research import verify_month,PIPS
import econedge_weekly_trend as base
from econedge_directional_diagnostic import move_for_week

PAIRS=("eurusd","gbpusd")
FIRST="2010-01";LAST="2025-12"
ROOT=Path("econedge_eurgbp_15_years_results")
WINDOWS={
 "historic_2011_2017":(2011,2018),
 "reused_2018_2025":(2018,2026),
 "full_2011_2025":(2011,2026),
}
LOT_LEVELS=(.01,.001)
DIRECTIONS=("opposite_control","trend")

def load_quotes(root=Path(".")):
    months=[str(p) for p in pd.period_range(FIRST,LAST,freq="M")]
    assert len(months)==192
    frames={};metadata=[];removed=[]
    for sym in PAIRS:
        folder=(root/"data") if sym=="eurusd" else root/"portfolio_data"/sym
        bars=[]
        for month in months:
            file=folder/(month+".csv");meta=Path(str(file)+".source.json")
            if not file.is_file() or not meta.is_file():
                raise FileNotFoundError(f"Missing authentic H1 month {sym}/{month}")
            source=json.loads(meta.read_text())
            if source.get("source")!="dukascopy-node":
                raise ValueError(f"Unverified provenance: {meta}")
            if source.get("instrument") not in (sym,None):
                raise ValueError(f"Instrument mismatch: {meta}")
            digest=hashlib.sha256(file.read_bytes()).hexdigest()
            if digest!=source.get("sha256"):raise ValueError(f"Bad checksum {file}")
            part=verify_month(folder,month,sym)
            if len(part)!=int(source["candles"]):raise ValueError("Metadata count mismatch "+str(file))
            if len(part)<100:raise ValueError("Abnormally sparse month "+str(file))
            metadata.append(dict(symbol=sym,month=month,n=len(part),
                sha256=digest,removed_bad_bidask=int(source.get("rejected_inverted_spread",0))))
            bars.append(part)
        merged=pd.concat(bars,ignore_index=True)
        merged.timestamp=pd.to_datetime(merged.timestamp,utc=True,errors="raise")
        if merged.timestamp.duplicated().any():raise ValueError("Duplicate H1 timestamp "+sym)
        merged=merged.set_index("timestamp").sort_index()
        numeric=merged[["open","high","low","close","bid_open","ask_open","spread_open_pips"]].to_numpy(float)
        if not np.isfinite(numeric).all():raise ValueError("Non-finite price")
        if (merged.ask_open<merged.bid_open).any():raise ValueError("Invalid reversed spread "+sym)
        if len(merged)<90000:raise ValueError("Insufficient historical quotes "+sym)
        frames[sym]=merged
    shared=frames["eurusd"].index.intersection(frames["gbpusd"].index).sort_values()
    if len(shared)<90000:raise ValueError("Insufficient joint EURGBP historical H1")
    # Do not forward fill or interpolate missing hours in one pair.
    for sym in PAIRS:frames[sym]=frames[sym].loc[shared].copy()
    return shared,frames,pd.DataFrame(metadata)

def frozen_two_pair_events(index,prices):
    old=base.SYMBOLS
    try:
        base.SYMBOLS=PAIRS
        events=base.build_weekly_events(index,prices,first_year=2011,last_year=2025)
    finally:
        base.SYMBOLS=old
    if not events or events[0]["time"].year!=2011 or events[-1]["time"].year!=2025:
        raise RuntimeError("Historical weekly coverage incomplete")
    # Use actual complete Friday 20:00 UTC hourly open for both event arms:
    # 2026 strategy enforces it; historical must be exactly same.
    complete=[e for e in events if e["exit_deadline"] in index]
    if len(complete)<700:raise RuntimeError("Too few complete EURGBP 15-year weeks")
    return complete

def direction_diagnostics(events,index,prices):
    rows=[]
    for e in events:
        if not e["qualifies"]:continue
        reversal=-e["momentum_direction"]
        rp,gross,sp,exsp=move_for_week(e,prices,index,reversal)
        tp,_,_,_=move_for_week(e,prices,index,-reversal)
        rows.append(dict(time=e["time"].isoformat(),year=int(e["time"].year),
            week=f"{e['time'].isocalendar().year}-{e['time'].isocalendar().week:02d}",
            pair=e["sym"],z_score=e["z"],required_stop_pips=e["stop_pips"],
            reverse_pips=rp,trend_pips=tp,reverse_positive=rp>0,
            signal_entry_spread=sp,signal_exit_spread=exsp))
    return pd.DataFrame(rows)

def replay(events,prices,first,last,lotstep,mode):
    old=base.LOT_STEP
    try:
        base.LOT_STEP=lotstep
        t,c,d=base.weekly_replay(events,prices,first,last,mode)
        # Audit must run with same configured min lot as replay.
        base.audit(t)
        if not t.empty:
            if t.week.duplicated().any():raise AssertionError("More than 1 filled trade a week")
            if (t.designed_risk_usd>t.budget_usd+1e-7).any():
                raise AssertionError("Over planned 0.5% equity risk")
            if (np.abs(t.lot/lotstep-np.round(t.lot/lotstep))>1e-7).any():
                raise AssertionError("Bad .001 lot rounding")
        perf=base.metrics(t,c,events,first,last)
    finally:
        base.LOT_STEP=old
    return t,d,perf

def year_breakdown(t,decisions,first=2011,last=2026):
    # Yearly return denominator is prior Dec 31 account equity of the
    # FULL 15-year compounded replay; annual PnL must not be conflated
    # with yearly-reset simulation.
    result={}
    eq=base.START_CAPITAL
    if not t.empty:t=t.sort_values("time")
    for year in range(first,last):
        y=t[t.year==year] if not t.empty else t
        initial=eq
        pnl=float(y.pnl_usd.sum()) if not y.empty else 0.
        eq+=pnl
        result[str(year)]=dict(ending_equity_usd=float(eq),starting_equity_usd=float(initial),
            pnl_usd=pnl,return_pct=100*pnl/initial,
            filled_trades=len(y),wins=int((y.pnl_usd>0).sum()) if not y.empty else 0,
            stop_trades=int((y.exit_reason=="stop").sum()) if not y.empty else 0,
            weekly_decisions=int(decisions.time.str.slice(0,4).eq(str(year)).sum()),
            rejected_stop=int(((decisions.time.str.slice(0,4)==str(year))&
                              (decisions.reason=="stop_too_wide")).sum()),
            rejected_minlot=int(((decisions.time.str.slice(0,4)==str(year))&
                              (decisions.reason=="min_lot_incompatible_with_risk")).sum()))
    return result

def verdict(era,comparators):
    must=[]
    for name in ("historic_2011_2017","reused_2018_2025"):
        p=era[name]["hypothetical_minlot_0001"]["opposite_control"]
        c=era[name]["hypothetical_minlot_0001"]["trend"]
        must.append(p["entered"]>=30 and p["net_usd"]>0 and
            p["spread_x2_net_usd"]>0 and (p["pf"] or 0)>1.1 and
            (p["bootstrap_lower_mean_week_usd"] is not None and
             p["bootstrap_lower_mean_week_usd"]>0) and
            p["net_usd"]>c["net_usd"])
    return all(must)

def main():
    ROOT.mkdir(exist_ok=True)
    idx,prices,metadata=load_quotes()
    metadata.to_csv(ROOT/"SOURCE_192_MONTHS_2_PAIRS_SHA256.csv",index=False)
    events=frozen_two_pair_events(idx,prices)
    decisions=[]
    for e in events:
        decisions.append(dict(time=e["time"].isoformat(),pair=e["sym"],
             z=e["z"],qualifies=e["qualifies"],signal_stop_pips=e["stop_pips"]))
    pd.DataFrame(decisions).to_csv(ROOT/"ALL_MONDAY_DECISIONS_2011_2025.csv",index=False)
    signals=direction_diagnostics(events,idx,prices)
    signals.to_csv(ROOT/"ALL_QUALIFYING_DIRECTIONAL_SIGNALS.csv",index=False)
    out={};full_yearly={}
    for window,(first,last) in WINDOWS.items():
        out[window]={}
        for lot in LOT_LEVELS:
            label="standard_minlot_001" if lot==.01 else "hypothetical_minlot_0001"
            out[window][label]={}
            for direction in DIRECTIONS:
                t,d,performance=replay(events,prices,first,last,lot,direction)
                t.to_csv(ROOT/f"{window}_{label}_{direction}_trades.csv",index=False)
                d.to_csv(ROOT/f"{window}_{label}_{direction}_decisions.csv",index=False)
                out[window][label][direction]=performance
                if window=="full_2011_2025":
                    full_yearly[label+"_"+direction]=year_breakdown(t,d,first,last)
                print("EURGBP_15Y",window,label,direction,
                     "entered",performance["entered"],
                     "USD",round(performance["net_usd"],3),
                     "stressUSD",round(performance["spread_x2_net_usd"],3),
                     "bootstrap",round(performance["bootstrap_lower_mean_week_usd"],4),flush=True)
    direction_period={}
    for tag,(first,last) in WINDOWS.items():
        sub=signals[(signals.year>=first)&(signals.year<last)]
        r=sub.reverse_pips.to_numpy(float)
        direction_period[tag]=dict(n=len(sub),mean_reverse_pips=float(r.mean()),
            mean_trend_pips=float(sub.trend_pips.mean()),
            win_pct=float((r>0).mean()*100),
            bootstrap_lower_reverse_pips=base.block_bootstrap_lower(r),
            selected_pair_breakdown={p:int((sub.pair==p).sum()) for p in PAIRS})
    outcome=verdict(out,None)
    statement=dict(status="AUDITED_15_YEAR_RETROSPECTIVE_NOT_LIVE",
        source="Genuine Dukascopy H1 Bid/Ask monthly source SHA256 2010-2025",
        source_file_count=len(metadata),total_H1_joint_bars=len(idx),
        actual_years="2011-2025",warmup_year=2010,
        exact_2026_pair_selection="Max abs(z) only EURUSD/GBPUSD, Monday 08 UTC, z>=0.8",
        lots="0.01 standard-lot and 0.001 standard-lot hypothetical as in 2026",
        one_account_per_window="Each WINDOW starts $1000 separately; full_2011_2025 continuously compounds WITHIN 15 years",
        independent_holdout=False,known_selection_bias="EURGBP chosen after examining previous 15-year four-pair study",
        full_years_not_reset_inside_full_window=True,
        periods=direction_period,results=out,
        full_run_yearly_ledger=full_yearly,
        precommitted_two_era_gate=outcome,
        verdict="NO_GO" if not outcome else "FORWARD_DEMO_ONLY_NOT_REAL_MONEY",
        original_z_threshold=base.MIN_TREND_Z,
        original_max_stop=base.STOP_MAX_PIPS,original_risk_per_trade=base.RISK,
        expected_slippage_pips_each_way=base.SLIPPAGE_PIPS,
        live_orders=0,
        major_limits=["Bid/Ask true at H1 OPEN only; intrabar STOP from midpoint H/L and opening spread proxy",
           "Swap/overnight financing and Exness broker tick-execution not included",
           "Data selected retrospectively 2011–2025; statistical p-values post-selection are optimistic",
           "0.001 standard lot not verified as available in user's exact broker account",
           "Risk 0.5% is design budget, gap can breach"])
    (ROOT/"SUMMARY_15Y_EURGBP_001_vs_0001.json").write_text(json.dumps(statement,ensure_ascii=False,indent=2,default=str))
    yearly_rows=[]
    for label,years in full_yearly.items():
        for year,x in years.items():yearly_rows.append(dict(strategy=label,year=year,**x))
    pd.DataFrame(yearly_rows).to_csv(ROOT/"EACH_YEAR_CONTINUOUS_ACCOUNT.csv",index=False)
    lines=["# ECONEDGE EUR/USD + GBP/USD — CHÍNH XÁC cấu hình 2026, kiểm tra lại 2011–2025",
      "",f"Đã kiểm tra **{len(metadata)} file tháng/cặp SHA256** và **{len(idx)} nến H1 thực chung**. Vốn $1.000; không có giao dịch thật. Năm 2010 warm-up.",
      "Thứ Hai 08 UTC, momentum 480 H1, chỉ EUR/USD và GBP/USD, |z|≥0,8, đảo chiều vs xu hướng cùng cặp/tuần, stop 6×median72 H1 tối đa 70pip, đóng thứ Sáu 20 UTC, rủi ro thiết kế 0,5%, đòn bẩy 5×.",
      "", "| Nhóm (vốn reset giữa các NHÓM) | Min lot | Hướng | Lệnh | Lãi/lỗ USD | Lãi/lỗ % nhóm | PF | Stress spread ×2 USD | Bootstrap lower 95% USD/tuần |",
      "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for window in WINDOWS:
        for lot in LOT_LEVELS:
            label="standard_minlot_001" if lot==.01 else "hypothetical_minlot_0001"
            for mode in DIRECTIONS:
                m=out[window][label][mode]
                fmt=lambda x:"—" if x is None else f"{x:.3f}"
                lines.append(f"| {window} | {lot:.3f} | {mode} | {m['entered']} | {m['net_usd']:+.2f} | {m['net_return_pct']:+.2f}% | {fmt(m['pf'])} | {m['spread_x2_net_usd']:+.2f} | {fmt(m['bootstrap_lower_mean_week_usd'])} |")
    lines+=["", "## Pip không sử dụng stop/lot (chỉ khả năng dự báo hướng)",
            "", "| Nhóm | Tín hiệu | Reversal TB pip | Trend TB pip | Bootstrap lower reversal pip |",
            "|---|---:|---:|---:|---:|"]
    for window,x in direction_period.items():
        lines.append(f"| {window} | {x['n']} | {x['mean_reverse_pips']:+.2f} | {x['mean_trend_pips']:+.2f} | {x['bootstrap_lower_reverse_pips']:+.2f} |")
    lines += ["","## Kết quả theo từng năm của sổ tài khoản 2011–25 CHẠY LIÊN TỤC",
      "","| Năm | Reversal .001 USD | Trend .001 USD | Reversal .001 số lệnh |",
      "|---|---:|---:|---:|"]
    keyr="hypothetical_minlot_0001_opposite_control"
    keyt="hypothetical_minlot_0001_trend"
    for y in range(2011,2026):
        rr=full_yearly[keyr][str(y)]
        tt=full_yearly[keyt][str(y)]
        lines.append(f"| {y} | {rr['pnl_usd']:+.2f} | {tt['pnl_usd']:+.2f} | {rr['filled_trades']} |")
    lines+=["",f"**Cổng phân kỳ được khóa trước kết quả: {outcome}. Phán quyết: {statement['verdict']}**.",
     "Nhóm EUR/GBP được chọn sau khi xem các năm 2011–25: đây là **nghiên cứu hậu nghiệm, KHÔNG phải xác nhận ngoài mẫu**. 2026 đã được kiểm định riêng: chỉ 13 lệnh giả định .001, +$17.80 nhưng bootstrap dưới 0; không cộng % 2026 vào kết quả 15 năm.",
     "Không có spread/swap broker Exness hoặc tick nội nến. Lợi nhuận nếu dương vẫn không phải PnL giao dịch thật. Lot 0.001 chỉ mô phỏng tương đương khối lượng với cent-lot phù hợp nếu broker hỗ trợ.",
     "Mọi quyết định nhận lệnh/bỏ lệnh, ledger, bảng lãi từng năm và SHA256 nguồn được đính kèm artifact."]
    (ROOT/"BAO_CAO_15_NAM_EURGBP_0001.md").write_text("\n".join(lines))
    print("EURGBP_15Y_COMPLETE",len(idx),len(events),len(signals),
          "15YEAR_GATES",outcome,flush=True)
if __name__=="__main__":main()
