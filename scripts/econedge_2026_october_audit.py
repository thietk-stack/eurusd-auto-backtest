#!/usr/bin/env python3
"""EconEdge Oct 2026 chronological extension, frozen 2026 H1 EURUSD/GBPUSD policy.

Independent check:
- Pin the SHA256 manifest of all 26 original Sep 2025–Sep 2026 month files
  to the already-published 2026 Jan–Sep run artifact 13025105010.
- Reproduce original 38 weeks / original trades and PnL before seeing October.
- Add ONLY new fully observed Fri 20 UTC weeks 2026-09-28..2026-10-30.
- Reuse exact frozen 2026 signal/stop/lot/replay without retuning.
- No fabricated missing quotes, no broker swap, no live orders.
"""
from pathlib import Path
import hashlib,json
import pandas as pd
import numpy as np
import econedge_2026_eurgbp as old
from portfolio_research import verify_month

OUT=Path("econedge_2026_october_audit")
FIRST="2025-09"
LAST="2026-10"
NEW_START=pd.Timestamp("2026-09-28T00:00:00Z")
LAST_COMPLETE_FRIDAY=pd.Timestamp("2026-10-30T20:00:00Z")
BASELINE_CUTOFF=pd.Timestamp("2026-09-30T23:59:59Z")
# This is SHA256 of 26 ordered "pair,month,source SHA256" lines with final newline,
# taken directly from original 2026 Jan-Sep artifact #13025105010, not recalculated
# from newly downloaded files.
BASELINE_26_MONTH_MANIFEST_SHA256="303b518abd5600ed91a6cb68f28b8a865cc919043c15abf4e19b7876e7496829"
BASELINE_EXPECTED={
    (".001","opposite_control"):(13,17.7985),
    (".001","trend"):(13,-25.8180),
    (".01","opposite_control"):(2,-4.5350),
    (".01","trend"):(2,-7.6400),
}
BASELINE_WEEKS=38

def load_extended():
    months=[str(x) for x in pd.period_range(FIRST,LAST,freq="M")]
    if len(months)!=14:raise AssertionError("Must have exactly 14 genuine months")
    quotes={};audit=[];original_lines=[]
    for sym in old.PAIRS:
        folder=Path("data") if sym=="eurusd" else Path("portfolio_data")/sym
        frames=[]
        for month in months:
            f=folder/(month+".csv")
            manifest=Path(str(f)+".source.json")
            if not f.is_file() or not manifest.is_file():raise FileNotFoundError(f)
            meta=json.loads(manifest.read_text())
            raw=f.read_bytes()
            sha=hashlib.sha256(raw).hexdigest()
            if (meta.get("source")!="dukascopy-node" or
                meta.get("timeframe")!="h1" or
                meta.get("instrument") not in (sym,None) or
                meta.get("sha256")!=sha):
                raise ValueError("Source or SHA mismatch "+str(f))
            df=verify_month(folder,month,sym)
            actual_count=meta.get("candles",meta.get("candle_count"))
            if actual_count is None or int(actual_count)!=len(df):
                raise ValueError("Incorrect manifest candle count "+str(f))
            if df.empty:raise ValueError("Empty authentic quote month "+str(f))
            frames.append(df)
            audit.append(dict(pair=sym,month=month,source="dukascopy-node",
                              candles=len(df),sha256=sha,
                              source_from=meta.get("from"),source_to=meta.get("to_exclusive",meta.get("to"))))
            if month!="2026-10":original_lines.append(f"{sym},{month},{sha}")
        p=pd.concat(frames,ignore_index=True)
        p["timestamp"]=pd.to_datetime(p.timestamp,utc=True,errors="raise")
        if p.timestamp.duplicated().any():raise ValueError("Duplicate real H1 timestamps "+sym)
        p=p.set_index("timestamp").sort_index()
        for col in ("open","high","low","close","bid_open","ask_open","spread_open_pips"):
            p[col]=pd.to_numeric(p[col],errors="raise")
            if not np.isfinite(p[col]).all():raise ValueError("Nonfinite quote "+sym)
        if not ((p.ask_open>=p.bid_open)&(p.open>0)&(p.close>0)).all():
            raise ValueError("Crossed or invalid genuine Bid/Ask "+sym)
        quotes[sym]=p
    digest=hashlib.sha256(("\n".join(original_lines)+"\n").encode()).hexdigest()
    if digest!=BASELINE_26_MONTH_MANIFEST_SHA256:
        raise AssertionError("Baseline 26 source month hashes changed: NO comparable extension. "+digest)
    idx=quotes["eurusd"].index.intersection(quotes["gbpusd"].index).sort_values()
    if len(idx)<7200 or LAST_COMPLETE_FRIDAY not in idx:
        raise RuntimeError("October last Friday 20:00 UTC not present on BOTH sources")
    if idx[-1]>pd.Timestamp("2026-10-31T00:00:00Z"):
        raise ValueError("Unexpected quote beyond October as-of cutoff")
    return idx,{sym:quotes[sym].loc[idx].copy() for sym in old.PAIRS},audit,digest

def replay(events,quotes,lot,mode):
    trades,decisions,metrics=old.run_book(events,quotes,lot,mode)
    return trades,decisions,metrics

def main():
    OUT.mkdir(exist_ok=True)
    idx,quotes,audit,digest=load_extended()
    pd.DataFrame(audit).to_csv(OUT/"ORIGINAL_SOURCE_MONTH_SHA256.csv",index=False)
    events=old.freeze_events(idx,quotes)
    if any(e["exit_deadline"] not in idx for e in events):
        raise AssertionError("Any partial week forbidden")
    baseline=[e for e in events if e["exit_deadline"]<=BASELINE_CUTOFF]
    new=[e for e in events if e["time"]>=NEW_START and e["exit_deadline"]<=LAST_COMPLETE_FRIDAY]
    if len(baseline)!=BASELINE_WEEKS or len(new)!=5 or len(events)!=43:
        raise RuntimeError(f"Baseline 38 + 5 new full weeks required: baseline={len(baseline)} new={len(new)} total={len(events)}")
    if {str(e["time"].date()) for e in new}!={"2026-09-28","2026-10-05","2026-10-12","2026-10-19","2026-10-26"}:
        raise AssertionError("Unexpected new week date")
    pd.DataFrame([{k:str(v) if isinstance(v,pd.Timestamp) else v for k,v in e.items()} for e in new]).to_csv(
        OUT/"FROZEN_NEW_FIVE_WEEKS.csv",index=False)
    old.signals(new,idx,quotes).to_csv(OUT/"FROZEN_NEW_FIVE_WEEKS_DIRECTION.csv",index=False)
    results={}
    for lot in (.001,.01):
        key=".001" if lot==.001 else ".01"
        file_prefix="lot0001" if lot==.001 else "lot001"
        results[key]={}
        for mode in ("opposite_control","trend"):
            t0,d0,m0=replay(baseline,quotes,lot,mode)
            expected_count,expected_pnl=BASELINE_EXPECTED[(key,mode)]
            if m0["weekly_decisions"]!=BASELINE_WEEKS or m0["entered"]!=expected_count or abs(m0["net_usd"]-expected_pnl)>0.00011:
                raise AssertionError("Published original baseline not reproduced exactly "+str((key,mode,m0["entered"],m0["net_usd"])))
            tall,dall,ma=replay(events,quotes,lot,mode)
            tn,dn,mn=replay(new,quotes,lot,mode)
            t0.to_csv(OUT/f"{file_prefix}_{mode}_BASELINE_TRADES.csv",index=False)
            tall.to_csv(OUT/f"{file_prefix}_{mode}_ALL_THROUGH_OCT_TRADES.csv",index=False)
            tn.to_csv(OUT/f"{file_prefix}_{mode}_NEW_FIVE_WEEKS_ISOLATED_TRADES.csv",index=False)
            dall.to_csv(OUT/f"{file_prefix}_{mode}_ALL_DECISIONS.csv",index=False)
            dn.to_csv(OUT/f"{file_prefix}_{mode}_NEW_DECISIONS.csv",index=False)
            if len(tall) and (tall.designed_risk_usd>tall.budget_usd+1e-7).any():
                raise AssertionError("Designed risk > 0.5%")
            if ma["weekly_decisions"]!=43 or mn["weekly_decisions"]!=5:
                raise AssertionError("Incorrect weekly decision count")
            # Equity is carried from Jan to Oct in ALL; the isolated new
            # period starts at $1,000 and is NOT summed into the all-period.
            delta=float(ma["net_usd"]-m0["net_usd"])
            results[key][mode]=dict(original_JanSep=m0,
                new_five_weeks_isolated_start_1000=mn,
                full_JanOct_compounded=ma,
                incremental_pnl_full_account_usd=delta)
            print("OCT2026",key,mode,"new_fills",mn["entered"],
                "new_compounded_increment_USD",round(delta,4),
                "full_fills",ma["entered"],"full_net_USD",round(ma["net_usd"],4),flush=True)
    overall=dict(status="RESEARCH_ONLY_NO_REAL_ORDERS",source="dukascopy-node authentic H1 Bid/Ask",
        generated_asof_utc="2026-10-31",
        original_26_month_manifest_sha256=digest,
        original_artifact_id=13025105010,
        all_28_source_months=audit,
        shared_observed_H1=len(idx),
        original_complete_weeks=len(baseline),
        new_complete_weeks=len(new),
        total_complete_weeks=len(events),
        new_week_start_dates=[str(e["time"].date()) for e in new],
        frozen_params=dict(z_threshold=.8,lookback_closed_H1=480,stop_median_H1=72,
          stop_multiplier=6,stop_min_pips=8,stop_max_pips=70,
          max_leverage=5,risk_fraction=.005,slippage_pips_each_side=.1,
          weekly_open="Monday 08 UTC",exit="Friday 20 UTC or stop"),
        results=results,verdict="NO_GO_5_NEW_WEEKS_NOT_ENOUGH",
        true_broker_swap_available=False,
        historical_spread="Dukascopy OPEN bid/ask observed; not Exness spread",
        warnings=[
          "The Oct 2026 data add FIVE chronologically later full weeks; only four Monday entries occur in Oct, and Sep 28 is newly complete.",
          "Not pristine out-of-sample across project; other 2026 price data were viewed before this frozen strategy.",
          "5 new weekly decisions cannot establish statistical edge, and 43 total weeks cannot override failed 2011–25 historical robustness.",
          "No swap, triple-swap, financing, Exness tick-level stop or real execution.",
          "A designed <=0.5% stop does not guarantee realized losses <=0.5% in gaps.",
          "0.001 standard lot is hypothetical and needs broker demo contract-size verification."
        ],
        real_orders=0)
    (OUT/"EURGBP_2026_OCTOBER_AUDIT.json").write_text(json.dumps(overall,indent=2,ensure_ascii=False,default=str))
    lines=["# EconEdge EURUSD GBPUSD — kiểm toán bổ sung 5 tuần thực đến 30/10/2026",
      "",f"Đã khớp chính xác SHA256 26 tệp nguồn cũ với artifact 2026 #13025105010: `{digest}`. Tổng {len(audit)} tệp tháng/cặp, trong đó 2 tệp tháng 10 mới, {len(idx)} H1 giao nhau. **Không đổi một thông số chiến lược nào**.",
      "Đã tái lập chính xác 38 tuần và cả 4 sổ baseline Jan–Sep 2026 (lệnh và PnL). Thêm 5 tuần hoàn chỉnh có Monday 08 UTC và Friday 20 UTC từ 28/09 đến 30/10.",
      "", "| Lot tối thiểu | Hướng | Lệnh mới 5 tuần | PnL mới USD, vốn tiếp nối | Tổng lệnh Jan–Oct | PnL tổng Jan–Oct USD | PF tổng | Stress x2 tổng USD |",
      "|---|---|---:|---:|---:|---:|---:|---:|"]
    for lot in results:
        for mode in results[lot]:
            x=results[lot][mode]
            m=x["full_JanOct_compounded"];new_metrics=x["new_five_weeks_isolated_start_1000"]
            pf="—" if m["pf"] is None else f"{m['pf']:.3f}"
            lines.append(f"| {lot} | {mode} | {new_metrics['entered']} | {x['incremental_pnl_full_account_usd']:+.4f} | {m['entered']} | {m['net_usd']:+.4f} | {pf} | {m['spread_x2_net_usd']:+.4f} |")
    lines+=["", "**Kết luận:** NO-GO tiền thật, không đủ mẫu mới để khẳng định edge. Phần kết quả từ năm 2011–2025 theo đúng chính sách đã lỗ $55,57 trên $1.000 với lot 0,001 (105 lệnh), không được quên khi nhìn 2026.",
       "Swap thực của Exness và khớp lệnh tick không có; lợi nhuận chỉ là PnL mô phỏng giá Dukascopy, không phải PnL thực của tài khoản broker. Không tạo giao dịch hay thay đổi vốn.",
       "Đọc sổ lệnh, quyết định từng tuần và SHA256 nguồn kèm trong artifact để đối chiếu."]
    (OUT/"BAO_CAO_OCTOBER_2026.md").write_text("\n".join(lines))
    print("OCT2026_AUDIT_COMPLETED",len(idx),len(baseline),len(new),"NO_GO",flush=True)

if __name__=="__main__":main()
