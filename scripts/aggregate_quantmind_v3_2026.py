#!/usr/bin/env python3
"""Never silently omit unprofitable/missing months when consolidating QuantMind v3."""
import json,math
from pathlib import Path
import numpy as np
import pandas as pd

MONTHS=[f"2026-{m:02d}" for m in range(1,10)]
ROOT=Path("monthly_v3")
OUT=Path("quantmind_v3_2026_aggregate")
MODES=("control","confirmed")
def cohort(m):return "early_Jan_Apr" if int(m[-2:])<=4 else "later_May_Sep"
def wilson_one_sided95(w,n):
    if n==0:return None
    p=w/n;z=1.6448536269514722
    return float((p+z*z/(2*n)-z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n))
def trade_metrics(t):
    if t.empty:return dict(trades=0,wins=0,win_pct=None,net_usd=0.,
        spread_x2_net_usd=0.,pf=None,wilson_lower95=None,
        extra_spread_usd=0.,cross_month_duplicate_iso_weeks=0)
    pnl=t.pnl_usd.to_numpy(float);wins=int((pnl>0).sum())
    quotes=t.entry_executable_quote.to_numpy(float)
    pip_usd=np.where(t.pair.to_numpy()=="usdjpy",1000/np.maximum(quotes,1),10.)
    extra=t.entry_spread_pips.to_numpy(float)*pip_usd*t.lots.to_numpy(float)
    if (extra<-1e-6).any():raise AssertionError("Negative quote spread cost")
    week=pd.to_datetime(t.time,utc=True).dt.strftime("%G-%V")
    pf=float(pnl[pnl>0].sum()/-pnl[pnl<0].sum()) if (pnl<0).any() else None
    return dict(trades=len(t),wins=wins,win_pct=100*wins/len(t),
        net_usd=float(pnl.sum()),spread_x2_net_usd=float(pnl.sum()-extra.sum()),
        pf=pf,wilson_lower95=wilson_one_sided95(wins,len(t)),
        extra_spread_usd=float(extra.sum()),
        cross_month_duplicate_iso_weeks=int(week.duplicated().sum()))

def main():
    OUT.mkdir(exist_ok=True)
    sources=[];records=[];all_trades={mode:[] for mode in MODES}
    for month in MONTHS:
        d=ROOT/("quantmind-v3-"+month)/"v3_confirmed_reclaim_results"
        p=d/"RESULTS_V3_MONTH.json"
        if not p.exists():raise FileNotFoundError("Cannot declare completion with missing month "+month)
        raw=json.loads(p.read_text())
        if raw.get("date_from")!=month+"-01":raise AssertionError("Wrong source month")
        if "Genuine Dukascopy M1 bid and ask" not in raw.get("data_source",""):
            raise AssertionError("Not actual M1 quotes")
        for symbol,detail in raw["source_audit"].items():
            if detail["months"]!=[month] or detail["real_m1_bars"]<10000:
                raise AssertionError("Missing M1 source "+month+" "+symbol)
        sources.append(dict(month=month,
            rows=sum(x["real_m1_bars"] for x in raw["source_audit"].values())))
        for mode in MODES:
            f=d/(mode+"_trades.csv")
            if not f.exists():raise FileNotFoundError("Missing ledger "+str(f))
            try:t=pd.read_csv(f)
            except pd.errors.EmptyDataError:t=pd.DataFrame()
            base=raw["results"][mode]["base"]
            stress=raw["results"][mode]["spread_x2_same_fills"]
            if len(t)!=int(base["trades"]):raise AssertionError("Wrong trade total "+month)
            if len(t):
                if not t.time.str.startswith(month).all():raise AssertionError("Cross-month entry "+month)
                if (t.planned_risk_usd>t.max_planned_risk_usd+1e-6).any():
                    raise AssertionError("Over-budget trade")
                if pd.to_datetime(t.time,utc=True).dt.strftime("%G-%V").duplicated().any():
                    raise AssertionError("Duplicate weekly entry WITHIN month")
                t=t.copy();t["month"]=month;t["cohort"]=cohort(month)
                all_trades[mode].append(t)
                if abs(t.pnl_usd.sum()-base["pnl_usd"])>1e-5:
                    raise AssertionError("Pnl mismatch")
            if stress["pnl_usd"]>base["pnl_usd"]+1e-7:
                raise AssertionError("Bad spread stress: costs increase profit")
            records.append(dict(month=month,cohort=cohort(month),mode=mode,
                candidates=base["candidate_count"],trades=base["trades"],
                wins=int((t.pnl_usd>0).sum()) if not t.empty else 0,
                net_usd=base["pnl_usd"],spread_x2_net_usd=stress["pnl_usd"]))
    monthly=pd.DataFrame(records)
    monthly.to_csv(OUT/"V3_MONTHLY_RESULTS.csv",index=False)
    result={}
    for mode in MODES:
        t=pd.concat(all_trades[mode],ignore_index=True) if all_trades[mode] else pd.DataFrame()
        t.to_csv(OUT/(mode+"_ALL_REAL_TRADES_2026.csv"),index=False)
        result[mode]={}
        for c in ("early_Jan_Apr","later_May_Sep"):
            sub=t[t.cohort==c] if not t.empty else t
            row=monthly[(monthly["mode"]==mode)&(monthly["cohort"]==c)]
            stat=trade_metrics(sub)
            stat["candidate_events"]=int(row.candidates.sum())
            stat["months"]=list(row.month)
            if abs(stat["net_usd"]-row.net_usd.sum())>1e-5:
                raise AssertionError("Aggregate PnL inconsistent")
            if abs(stat["spread_x2_net_usd"]-row.spread_x2_net_usd.sum())>1e-4:
                raise AssertionError("Cost stress inconsistent")
            result[mode][c]=stat
    early=result["confirmed"]["early_Jan_Apr"]
    later=result["confirmed"]["later_May_Sep"]
    ctrl=result["control"]["later_May_Sep"]
    early_pass=(early["trades"]>=12 and early["net_usd"]>0 and
         (early["pf"] or 0)>1.1 and early["spread_x2_net_usd"]>0)
    later_pass=(later["trades"]>=16 and later["net_usd"]>0 and
         (later["pf"] or 0)>1.1 and later["spread_x2_net_usd"]>0 and
         (later["wilson_lower95"] or 0)>1/3 and later["net_usd"]>ctrl["net_usd"])
    outcome=dict(status="RESEARCH_NO_REAL_MONEY",
        source="Real SHA-verified Dukascopy M1 bid/ask 2026 Jan-Sep four pairs",
        no_hidden_months=len(sources)==9,source_month_rows=sources,
        period_split="2026-Jan-Apr early, May-Sep later; project previously studied 2026 H1 but not M1 v3",
        policies=dict(control="Tue-Thu 10-16 original M1 reclaim",
             confirmed="same-event completed following M1 closes >=0.25 pip further inside with no extreme retest and spread <=signal, <=1.1x historic median"),
        monthly_reset="Every calendar month separately starts $1000; USD totals are sum across independent months, NOT compounded nine-month return",
        modes=result,early_gate=early_pass,later_gate=later_pass,
        verdict="NO_GO" if not(early_pass and later_pass) else "GO_TO_FORWARD_PAPER_ONLY",
        real_orders=0,
        caveat="OHLC M1 stop-first, no Exness tick, no swap; weekly ISO rule within each month, possible cross-month duplicate weeks; no multi-trial p value correction")
    (OUT/"QUANTMIND_V3_2026_RESULTS.json").write_text(json.dumps(outcome,ensure_ascii=False,indent=2))
    lines=["# QuantMind FX v3 — M1 có xác nhận, loại thiên lệch thứ Hai",
      "", "Thử **chín tháng M1 Bid/Ask thực 01–09/2026** trên bốn cặp tiền, 2026 M1 chưa từng dùng trong các vòng v1/v2. Hai chính sách đã khóa từ trước, không chỉnh thông số theo kết quả.",
      "", "| Chính sách | Kỳ | Mẫu tháng | Tín hiệu đủ điều kiện | Lệnh khớp | Tỷ lệ thắng | Tổng PnL USD | PF | Spread x2 USD | Wilson lower 95% |",
      "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    def fmt(x):return "—" if x is None else f"{x:.3f}"
    for mode in MODES:
        for c in ("early_Jan_Apr","later_May_Sep"):
            x=result[mode][c]
            lines.append(f"| {mode} | {c} | {len(x['months'])} | {x['candidate_events']} | {x['trades']} | {fmt(x['win_pct'])}% | {x['net_usd']:+.2f} | {fmt(x['pf'])} | {x['spread_x2_net_usd']:+.2f} | {fmt(x['wilson_lower95'])} |")
    lines+=["",f"Cổng đầu 01–04: **{early_pass}**; cổng sau 05–09: **{later_pass}**; Quyết định: **{outcome['verdict']}**.",
        "", "## Lưu ý nghiên cứu",
        "Mỗi tháng reset vốn giả định 1.000 USD nên tổng USD KHÔNG phải tỷ suất lợi nhuận kép liên tục. Quy định tối đa 1 lệnh/tuần áp dụng trong mỗi tháng, không đảm bảo ở tuần vắt qua hai tháng.",
        "Các lệnh thực tế được chọn là lệnh đủ điều kiện đầu tiên trong cửa sổ Tue–Thu 10–16, chưa phải đánh giá mọi ứng viên độc lập; có thể còn thiên lệch giờ đầu phiên. Báo giá M1 không có thứ tự tick nội phút, tính SL trước khi nến chứa cả TP và SL.",
        "Không có phí swap, thị trường order book FX tập trung hay giá khớp thực Exness. Dữ liệu 2026 H1 từng được dùng ở nghiên cứu khác nên đây không phải holdout chưa từng xem ở cấp toàn dự án.",
        "Nếu đủ số lệnh mà lợi nhuận sau spread không đạt, không tối ưu sau test để tuyên bố lợi thế."]
    (OUT/"BAO_CAO_QUANTMIND_V3_2026.md").write_text("\n".join(lines))
    print("QUANTMIND_V3_2026_COMPLETE",json.dumps({m:{c:[d["trades"],round(d["net_usd"],3)] for c,d in cs.items()} for m,cs in result.items()}),
       "gates",early_pass,later_pass,"verdict",outcome["verdict"],flush=True)
if __name__=="__main__":main()
