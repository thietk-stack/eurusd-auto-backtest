#!/usr/bin/env python3
"""Frozen 15-year EconEdge weekly-reversal extension, 2010 warmup + 2011–2025.

All 192 authentic monthly EURUSD GBPUSD AUDUSD USDJPY source files MUST be
present and hashed before any backtest; no interpolation. 2011–17 previously
unexamined period is an EARLIER retrospective extension, not forward OOS.

Side by side: (a) post-hoc untradeable pip directional diagnostic and
(b) exactly same pre-existing $1000 account risk/lot/stop rule. No retuning.
"""
import json
import math
from pathlib import Path
import pandas as pd
import numpy as np
from portfolio_research import SYMBOLS,PIPS,verify_month
import econedge_weekly_trend as base
import econedge_directional_diagnostic as dirtest

ROOT=Path(".")
OUT=Path("econedge_15year_results")
FIRST_MONTH="2010-01"
FINAL_MONTH="2025-12"
PERIODS={
    "new_2011_2017":(2011,2018),
    "reused_2018_2025":(2018,2026),
    "all_2011_2025":(2011,2026),
    "regime_2011_2014":(2011,2015),
    "regime_2015_2017":(2015,2018),
    "regime_2018_2021":(2018,2022),
    "regime_2022_2025":(2022,2026)
}

def verified_16_year_data(root=ROOT):
    months=[str(x) for x in pd.period_range(FIRST_MONTH,FINAL_MONTH,freq="M")]
    assert len(months)==192
    result={};source={}
    for sym in SYMBOLS:
        folder=(root/"data") if sym=="eurusd" else root/"portfolio_data"/sym
        frames=[verify_month(folder,m,sym) for m in months] # SHA256 checks every month
        df=pd.concat(frames,ignore_index=True)
        df["timestamp"]=pd.to_datetime(df.timestamp,utc=True,errors="raise")
        if df.timestamp.duplicated().any():raise ValueError("Duplicate H1 "+sym)
        df=df.sort_values("timestamp").set_index("timestamp")
        if (df.ask_open<df.bid_open).any():raise ValueError("Inverted quotes "+sym)
        if len(df)<90000:raise ValueError("Insufficient long history "+sym)
        result[sym]=df
        source[sym]=dict(months=len(frames),H1_bar_count=len(df),
              first_date=df.index[0].isoformat(),last_date=df.index[-1].isoformat())
    common=result[SYMBOLS[0]].index
    for sym in SYMBOLS[1:]:
        common=common.intersection(result[sym].index)
    common=common.sort_values()
    if len(common)<90000:raise ValueError("Incomplete 4-pair common H1 timeline")
    return common,{sym:result[sym].loc[common].copy() for sym in SYMBOLS},source

def direction_rows(events,index,prices):
    rows=[]
    for ev in events:
        if not ev["qualifies"]:continue
        side=-ev["momentum_direction"]
        reverse,gross,entry_spread,exit_spread=dirtest.move_for_week(ev,prices,index,side)
        trend,_,_,_=dirtest.move_for_week(ev,prices,index,-side)
        rows.append(dict(time=ev["time"].isoformat(),year=int(ev["time"].year),
            pair=ev["sym"],z_momentum=ev["z"],
            side="BUY" if side==1 else "SELL",
            stop_signal_pips=ev["stop_pips"],
            reverse_net_pips=reverse,trend_net_pips=trend,
            reverse_is_positive=reverse>0,
            entry_spread_pips=entry_spread,exit_spread_pips=exit_spread,
            no_viable_original_stop=ev["stop_pips"]>base.STOP_MAX_PIPS))
    return pd.DataFrame(rows)

def directional_metrics(frame):
    if frame.empty:return dict(n=0,mean_reverse_net_pips=None)
    a=frame.reverse_net_pips.to_numpy(float)
    b=frame.trend_net_pips.to_numpy(float)
    return dict(n=int(len(a)),reverse_win_pct=float(np.mean(a>0)*100),
        reverse_mean_net_pips=float(a.mean()),
        trend_mean_net_pips=float(b.mean()),
        paired_advantage_pips=float(np.mean(a-b)),
        lower_bootstrap_reverse_pips=base.block_bootstrap_lower(a),
        lower_bootstrap_paired_advantage_pips=base.block_bootstrap_lower(a-b),
        mean_cost_pips=float((frame.entry_spread_pips+frame.exit_spread_pips).mean()/2+2*base.SLIPPAGE_PIPS),
        stop_too_wide_candidates=int(frame.no_viable_original_stop.sum()),
        pair_breakdown={sym:dict(n=int((frame.pair==sym).sum()),
                   reverse_mean_pips=float(frame.loc[frame.pair==sym,"reverse_net_pips"].mean()))
              for sym in SYMBOLS if (frame.pair==sym).any()})

def main():
    OUT.mkdir(exist_ok=True)
    ix,prices,source=verified_16_year_data()
    events=base.build_weekly_events(ix,prices,first_year=2011,last_year=2025)
    signals=direction_rows(events,ix,prices)
    signals.to_csv(OUT/"ALL_WEEKLY_DIRECTION_SIGNALS_2011_2025.csv",index=False)
    if len(signals)<450:raise RuntimeError("Too few qualifying long-run signals")
    if signals.year.min()!=2011 or signals.year.max()!=2025:
        raise RuntimeError("Incomplete 2011–2025 event observation")
    output={}
    for name,(start,end) in PERIODS.items():
        subset=signals[(signals.year>=start)&(signals.year<end)]
        diag=directional_metrics(subset)
        part=dict(years=f"{start}–{end-1}",direction_only=diag,executable={})
        for model in ("opposite_control","trend"):
            trades,count,decisions=base.weekly_replay(events,prices,start,end,model)
            base.audit(trades)
            trmetrics=base.metrics(trades,count,events,start,end)
            part["executable"][model]=trmetrics
            trades.to_csv(OUT/(name+"_"+model+"_TRADES.csv"),index=False)
            decisions.to_csv(OUT/(name+"_"+model+"_DECISIONS.csv"),index=False)
        output[name]=part
        rev=part["executable"]["opposite_control"]
        print("LONG_HISTORY",name,"signals",diag["n"],"mean_reversal_pips",
            round(diag["reverse_mean_net_pips"],3),"bootstrap_low",
            round(diag["lower_bootstrap_reverse_pips"],3),
            "realistic_fills",rev["entered"],"simUSD",round(rev["net_usd"],3),flush=True)
    early=output["new_2011_2017"]["direction_only"]
    later=output["reused_2018_2025"]["direction_only"]
    regimes=[output[name]["direction_only"] for name in (
      "regime_2011_2014","regime_2015_2017",
      "regime_2018_2021","regime_2022_2025")]
    direction_gate=(early["n"]>=100 and later["n"]>=100
      and early["reverse_mean_net_pips"]>0 and later["reverse_mean_net_pips"]>0
      and (early["lower_bootstrap_reverse_pips"] or -1)<=0 is False
      and (later["lower_bootstrap_reverse_pips"] or -1)<=0 is False
      and sum(d["reverse_mean_net_pips"]>0 for d in regimes)>=3)
    # Equivalent straightforward gating, avoiding Python's odd chained booleans.
    direction_gate=bool(early["n"]>=100 and later["n"]>=100 and
        early["reverse_mean_net_pips"]>0 and later["reverse_mean_net_pips"]>0 and
        early["lower_bootstrap_reverse_pips"]>0 and later["lower_bootstrap_reverse_pips"]>0 and
        sum(d["reverse_mean_net_pips"]>0 for d in regimes)>=3)
    a=output["new_2011_2017"]["executable"]["opposite_control"]
    b=output["reused_2018_2025"]["executable"]["opposite_control"]
    execution_gate=bool(direction_gate and a["entered"]>=30 and b["entered"]>=30
        and a["net_usd"]>0 and b["net_usd"]>0
        and a["spread_x2_net_usd"]>0 and b["spread_x2_net_usd"]>0
        and (a["pf"] or 0)>1.1 and (b["pf"] or 0)>1.1
        and a["bootstrap_lower_mean_week_usd"]>0
        and b["bootstrap_lower_mean_week_usd"]>0)
    summary=dict(name="EconEdge 2011–2025 no retuning, 2010 H1 warmup",
      data_provenance="Dukascopy genuine H1 BID and ASK OPEN quotes; complete 192 months and SHA256 manifests per pair",
      data_source=source,common_H1_bars=len(ix),weekly_decisions=len(events),
      actual_trade_years=15,year_2010_is_warmup=True,
      original_momentum_window_H1=base.HISTORY_BARS,
      original_z_threshold=base.MIN_TREND_Z,
      original_stop_multiplier=base.STOP_ATR_MULT,
      original_risk_fraction=.005,original_min_lot=.01,original_leverage=5,
      signal_direction="Against prior four-week momentum; matched same-week momentum trend control",
      caveats=["2011-2017 is RETROSPECTIVE earlier history, not forward out-of-sample",
         "2018–2025 previously seen in other studies",
         "Directional pip diagnostic ignores trade lot, slippage of gaps, stop and financing; NOT executable PnL",
         "Simulated execution H1 uses observed BID ASK OPEN and approximate intrabar spread on stop",
         "Swap/overnight financing Exness and tick order omitted; cannot claim historical broker profits",
         "Risk cap 0.5% is planned stop risk not absolute loss bound"],
      results=output,directional_gate=direction_gate,executable_gate=execution_gate,
      verdict="NO_GO" if not execution_gate else "NEEDS_FORWARD_DEMO_AND_SWAP_TICK_VERIFICATION",
      place_real_orders=False)
    (OUT/"ECONEDGE_15Y_RESULTS.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str))
    lines=["# EconEdge — 15 năm kiểm định hồi quy về trung bình sau xu hướng bốn tuần (2011–2025)",
      "",f"**Có dữ liệu thật {len(ix):,} nến H1 giao nhau, 192 tháng/4 cặp, được kiểm tra SHA-256.** 2010 warmup; 2011–2025 là 15 năm thử nghiệm; không có lệnh thật.",
      "Ngưỡng |z|≥0,8 từ 480 H1 đã đóng, thứ Hai 08 UTC, giữ đến thứ Sáu 20 UTC, đối chứng cùng cặp cùng tuần thuận xu hướng. Không thay tham số theo dữ liệu mới.",
      "", "## A. KHẢ NĂNG DỰ BÁO HƯỚNG: pip ròng, CHƯA phải lợi nhuận giao dịch",
      "", "| Giai đoạn | Tuần đủ điều kiện | Hồi quy pip trung bình | Theo xu hướng pip trung bình | Tỷ lệ tuần đảo chiều có lãi | Bootstrap lower 95% hồi quy pip |",
      "|---|---:|---:|---:|---:|---:|"]
    for name in PERIODS:
        d=output[name]["direction_only"]
        lines.append(f"| {name} | {d['n']} | {d['reverse_mean_net_pips']:+.2f} | {d['trend_mean_net_pips']:+.2f} | {d['reverse_win_pct']:.1f}% | {d['lower_bootstrap_reverse_pips']:+.2f} |")
    lines+=["","## B. KHẢ THI VỚI TÀI KHOẢN 1.000 USD, 0,5% RỦI RO, MIN 0,01 LOT",
        "", "| Giai đoạn | Chính sách | Lệnh đặt được | Bỏ vì min lot | Lãi/lỗ USD | PF | Spread x2 USD | Bootstrap lower $/tuần |",
        "|---|---|---:|---:|---:|---:|---:|---:|"]
    for name in PERIODS:
        for mode in ("opposite_control","trend"):
            d=output[name]["executable"][mode]
            fmt=lambda a:"—" if a is None else f"{a:.2f}"
            lines.append(f"| {name} | {mode} | {d['entered']} | {d['rejected_min_lot']} | {d['net_usd']:+.2f} | {fmt(d['pf'])} | {d['spread_x2_net_usd']:+.2f} | {fmt(d['bootstrap_lower_mean_week_usd'])} |")
    lines+=["", f"**Cổng dự báo hướng:** {direction_gate}. **Cổng giao dịch khả thi:** {execution_gate}.",
      f"**Quyết định: {summary['verdict']}.** Lãi/lỗ cả kỳ reset vốn 1.000 USD theo từng nghiên cứu, không cộng phần trăm kỳ thành lãi kép.",
      "Dữ liệu 2010–2017 mới bổ sung là kiểm định hồi cứu lịch sử cũ (một trạng thái thị trường khác), không phải forward mới. Không có swap, giá chạm stop H1 theo proxy mid ±0,5 spread open, không có tick nội nến hay Exness khớp thật. Phân tích pip không có Stop Loss/lot; không đánh đồng với kết quả tài khoản.",
      "Cần dữ liệu lịch sử carry, swap broker, hoặc forward demo có tick nếu muốn kiểm định lợi nhuận thực tế."]
    (OUT/"BAO_CAO_ECONEDGE_15_NAM.md").write_text("\n".join(lines))
    print("ECONEDGE_15YR_DONE",len(ix),"signals",len(signals),"gates",direction_gate,execution_gate,flush=True)

if __name__=="__main__":main()
