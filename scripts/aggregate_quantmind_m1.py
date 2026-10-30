#!/usr/bin/env python3
"""Aggregate pre-registered 15 non-contiguous M1 research months.

All months have $1000 simulated initial capital independently.
NEVER annualize or compound these month-return percentages.
"""
import json, math
from pathlib import Path
import numpy as np
import pandas as pd

MONTHS={2022:[1,4,7,10],2023:[1,4,7,10],2024:[4,7,10],2025:[1,4,7,10]}
INPUT=Path("monthly_m1")
OUT=Path("m1_multi_month_summary")
def wilson_lower(p,n,z=1.645):
    if n==0:return None
    return (p+z*z/(2*n)-z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n)

def metrics(t):
    if t.empty:return dict(trades=0,wins=0,pnl_usd=0.,pf=None,win_pct=None,
          wilson_lower=None,extra_stress_cost_usd=0.,pnl_after_spread_x2_usd=0.)
    pnl=t.pnl_usd.to_numpy(float);win=(pnl>0)
    gain=float(pnl[win].sum());loss=float(-pnl[~win].sum())
    point=np.where(t.pair.to_numpy()=="usdjpy",
        1000/np.maximum(t.entry_executable_quote.to_numpy(float),1),10.)
    extra=t.entry_spread_pips.to_numpy(float)*point*t.lots.to_numpy(float)
    if (extra<0).any():raise AssertionError("Negative spread costs")
    return dict(trades=int(len(t)),wins=int(win.sum()),pnl_usd=float(pnl.sum()),
        pf=gain/loss if loss else None,win_pct=float(np.mean(win)*100),
        wilson_lower=float(wilson_lower(win.mean(),len(t))),
        extra_stress_cost_usd=float(extra.sum()),
        pnl_after_spread_x2_usd=float(pnl.sum()-extra.sum()))

def main():
    OUT.mkdir(exist_ok=True)
    records=[];tradefiles={"reversal":[],"continuation":[]}
    for year,months in MONTHS.items():
        for month in months:
            label=f"{year}-{month:02d}"
            folder=INPUT/("quantmind-m1-"+label)/"m1_reclaim_results"
            p=folder/"RESULTS_M1_RECLAIM.json"
            if not p.exists():raise FileNotFoundError("Cannot silently skip month: "+str(p))
            r=json.loads(p.read_text())
            start=f"{label}-01"
            if r.get("period",[None])[0]!=start:
                raise AssertionError("Wrong date period "+str(p))
            if r.get("market_source","").find("Dukascopy M1 BID ASK")<0:
                raise AssertionError("No verified quote source "+str(p))
            for sym,x in r["source_audit"].items():
                if x["months"]!=[label] or x["real_m1_bars"]<10000:
                    raise AssertionError("Missing non-synthetic monthly bars: "+label+" "+sym)
            for mode in ("reversal","continuation"):
                f=folder/(mode+"_trades.csv")
                if not f.exists():raise FileNotFoundError(str(f))
                try:
                    t=pd.read_csv(f)
                except pd.errors.EmptyDataError:
                    t=pd.DataFrame()  # zero-trade month emits an empty CSV
                if len(t)>0:
                    if t.time.str.slice(0,7).ne(label).any():raise AssertionError("Cross-period entry")
                    if (t.planned_risk_usd>t.max_planned_risk_usd+1e-6).any():
                        raise AssertionError("More than 0.5% risk")
                    if t.time.str.slice(0,10).duplicated().any():
                        pass  # daily duplicates allowed; weekly cap audited below
                    times=pd.to_datetime(t.time,utc=True)
                    if times.dt.strftime("%G-%V").duplicated().any():
                        raise AssertionError("Multiple entries in a week "+label)
                    t["month"]=label
                    t["cohort"]="discovery_2022" if year==2022 else (
                        "validation_2023" if year==2023 else "later_2024_2025")
                    tradefiles[mode].append(t)
                s=r["results"][mode]
                base=s["performance"];st=s["spread_x2"]
                if int(base["trades"])!=len(t):raise AssertionError("JSON/trade count mismatch")
                if len(t)>0 and abs(float(t.pnl_usd.sum())-base["pnl_usd"])>1e-6:
                    raise AssertionError("Monthly PnL mismatch "+label)
                if st["net_return_pct"]>base["net_return_pct"]+1e-8:
                    raise AssertionError("Spread x2 must not increase fixed-path PnL")
                records.append(dict(month=label,cohort=("discovery_2022" if year==2022
                    else "validation_2023" if year==2023 else "later_2024_2025"),
                    model=mode,candidates=base["candidate_count"],trades=base["trades"],
                    wins=int(len(t[t.pnl_usd>0])) if len(t) else 0,
                    pnl_usd=base["pnl_usd"],
                    stress_pnl_usd=st["pnl_usd"]))
    monthly=pd.DataFrame(records)
    monthly.to_csv(OUT/"ALL_MONTHLY_RESULTS.csv",index=False)
    result={}
    for mode in ("reversal","continuation"):
        t=pd.concat(tradefiles[mode],ignore_index=True) if tradefiles[mode] else pd.DataFrame()
        t.to_csv(OUT/(mode+"_ALL_15_MONTHS.csv"),index=False)
        result[mode]={}
        for cohort in ("discovery_2022","validation_2023","later_2024_2025"):
            subset=t[t.cohort==cohort] if not t.empty else t
            data=metrics(subset)
            row=monthly[(monthly.model==mode)&(monthly.cohort==cohort)]
            data["months"]=list(row.month)
            data["candidate_events"]=int(row.candidates.sum())
            data["number_of_observed_months"]=len(row)
            result[mode][cohort]=data
    validation=result["reversal"]["validation_2023"]
    later=result["reversal"]["later_2024_2025"]
    val_gate=(validation["trades"]>=15 and validation["pnl_usd"]>0 and
          validation["pnl_after_spread_x2_usd"]>0 and (validation["pf"] or 0)>1.1)
    later_gate=(later["trades"]>=30 and later["pnl_usd"]>0 and
          later["pnl_after_spread_x2_usd"]>0 and (later["pf"] or 0)>1.1 and
          (later["wilson_lower"] or 0)>1/3)
    result_obj=dict(data_source="REAL Dukascopy M1 BID ASK 2022-2025 fixed calendar months, SHA256 per month",
      periods=MONTHS,pilot_excluded="2024-01",
      capital_note="Each monthly study resets $1000. Summed USD is NOT compounded or annual profit.",
      selection_rule="Frozen 60 M1 false break and reclaim, spread compression, no HTF filters",
      risk_fraction=.005,net_rr_target=2,one_trade_per_ISO_week=True,
      mode_results=result,validation_gate=val_gate,later_gate=later_gate,
      evidence_for_real_money="NO_GO",
      caveat="M1 quote OHLC, no tick sequence/market depth/Exness swap or slippage confirmation; selected months not continuous.")
    (OUT/"AGGREGATED_M1_RECLAIM.json").write_text(json.dumps(result_obj,ensure_ascii=False,indent=2,default=str))
    lines=["# QuantMind v2 — Đối chiếu 15 tháng M1 cố định trước kiểm định",
       "", "Khám phá 2022: Jan/Apr/Jul/Oct; Validation 2023: Jan/Apr/Jul/Oct; kiểm tra sau 2024 Apr/Jul/Oct và 2025 Jan/Apr/Jul/Oct. Thí điểm 2024Jan đã xem bị LOẠI.",
       "", "**Mỗi tháng khởi tạo độc lập 1.000 USD. PnL USD cộng giữa các tháng là thống kê của nhiều phép thử, KHÔNG phải lãi gộp trong một tài khoản 2022–2025.**",
       "", "| Chiến lược | Kỳ | Số tháng | Ứng viên | Giao dịch | Tỷ lệ thắng | PnL USD cộng | PF | PnL x2 spread USD | Wilson lower 95% |",
       "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for mode in ("reversal","continuation"):
        for cohort in ("discovery_2022","validation_2023","later_2024_2025"):
            d=result[mode][cohort]
            fm=lambda x:"—" if x is None else f"{x:.3f}"
            lines.append(f"| {mode} | {cohort} | {d['number_of_observed_months']} | {d['candidate_events']} | {d['trades']} | {fm(d['win_pct'])}% | {d['pnl_usd']:+.2f} | {fm(d['pf'])} | {d['pnl_after_spread_x2_usd']:+.2f} | {fm(d['wilson_lower'])} |")
    lines+=["",f"Validation pass: **{val_gate}**; Later-period pass: **{later_gate}**",
         "", "Kết luận của cổng: **NO-GO giao dịch tiền thật** kể cả khi có kết quả mẫu tích cực. Chỉ khi cả hai cổng có đủ mẫu và lợi nhuận sau phí mới được nghiên cứu tiếp tick/forward demo.",
         "Tất cả sổ lệnh từng tháng và kiểm tra phí x2 được lưu trong artifact. Tick nội phút và swap Exness vẫn chưa có."]
    (OUT/"BAO_CAO_15_THANG_M1.md").write_text("\n".join(lines))
    print("M1_COHORTS_COMPLETE",json.dumps({m:{c:[v["trades"],round(v["pnl_usd"],3)] for c,v in cs.items()} for m,cs in result.items()}),"VAL",val_gate,"LATER",later_gate,flush=True)

if __name__=="__main__":main()
