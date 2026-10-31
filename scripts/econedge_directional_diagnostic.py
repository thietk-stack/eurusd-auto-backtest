#!/usr/bin/env python3
"""After-the-fact, NON-TRADABLE directional diagnostic of ECONEDGE signals.

No lot filters/stops or position sizing, signals (and pairs) are exactly the
ones locked in the existing weekly four-week trend hypothesis. Measure
close-to-Friday 20 UTC net price movement in PIPS and opposite control on
the SAME pair and week. This is NOT a new deployable portfolio or pristine
unseen holdout, and is labeled explicitly post-hoc.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from htf_limit_mid_yearly import historical_prices
from portfolio_research import PIPS
import econedge_weekly_trend as base

OUT=Path("econedge_signal_diagnostic_results")
def move_for_week(event,prices,index,side):
    sym=event["sym"];p=prices[sym];pip=PIPS[sym]
    i=event["entry_idx"];k=event["end_idx"]
    spr=base.quote_spread(p,i,pip)
    exit_spr=base.quote_spread(p,k,pip)
    entry=float(p.ask_open.iloc[i]) if side==1 else float(p.bid_open.iloc[i])
    if index[k]==event["exit_deadline"]:
        exit_px=float(p.bid_open.iloc[k]) if side==1 else float(p.ask_open.iloc[k])
    else:
        exit_px=float(p.close.iloc[k])-side*.5*exit_spr*pip
    netpips=side*(exit_px-entry)/pip-2*base.SLIPPAGE_PIPS
    raw_mid=(float(p.open.iloc[k]) if index[k]==event["exit_deadline"] else float(p.close.iloc[k]))
    gross_direction_pips=side*(raw_mid-float(p.open.iloc[i]))/pip
    return float(netpips),float(gross_direction_pips),float(spr),float(exit_spr)

def quality(vals):
    if not len(vals):
        return dict(n=0,avg_net_pips=None,winrate=None,
            bootstrap_lower_mean_net_pips=None,avg_gross_direction_pips=None)
    a=np.array([v["trend_net_pips"] for v in vals],float)
    ctrl=np.array([v["opposite_net_pips"] for v in vals],float)
    gross=np.array([v["gross_move_pips"] for v in vals],float)
    return dict(n=len(a),avg_net_pips=float(a.mean()),
        winrate=float((a>0).mean()),
        avg_gross_direction_pips=float(gross.mean()),
        opposite_avg_net_pips=float(ctrl.mean()),
        strategy_vs_control_mean_pips=float((a-ctrl).mean()),
        bootstrap_lower_mean_net_pips=base.block_bootstrap_lower(a),
        bootstrap_lower_trend_minus_opposite=base.block_bootstrap_lower(a-ctrl),
        pct_weeks_cost_over_move=float(np.mean(np.abs(gross)<=.5*np.abs(a+ctrl))) )

def main():
    OUT.mkdir(exist_ok=True)
    idx,prices=historical_prices()
    events=base.build_weekly_events(idx,prices)
    rows=[]
    for event in events:
        if not event["qualifies"]:continue
        side=event["momentum_direction"]
        tr,gross,sp,so=move_for_week(event,prices,idx,side)
        ant,_,_,_=move_for_week(event,prices,idx,-side)
        rows.append(dict(time=event["time"].isoformat(),year=event["time"].year,
            pair=event["sym"],zscore=event["z"],trend_net_pips=tr,
            opposite_net_pips=ant,gross_move_pips=gross,
            entry_spread_pips=sp,exit_spread_pips=so,
            stop_forbidden=event["stop_pips"]>base.STOP_MAX_PIPS))
    df=pd.DataFrame(rows)
    df.to_csv(OUT/"WEEKLY_ALL_CANDIDATE_SIGNALS.csv",index=False)
    result={}
    for name,(a,b) in base.PERIODS.items():
        s=df[(df.year>=a)&(df.year<b)]
        report=quality(s.to_dict("records"))
        report["years"]={str(y):quality(s[s.year==y].to_dict("records")) for y in range(a,b)}
        report["stop_too_wide_weeks"]=int(s.stop_forbidden.sum())
        result[name]=report
        print("DIRECTIONAL",name,report["n"],round(report["avg_net_pips"],3),
            round(report["strategy_vs_control_mean_pips"],3),
            round(report["bootstrap_lower_mean_net_pips"],3),flush=True)
    doc=dict(status="READ_ONLY_POST_HOC_DIAGNOSTIC_NOT_BROKER_STRATEGY",
        method="Identical Monday selected pair and frozen |4-week momentum Z| >=0.8 signal, measured through Friday 20 UTC without ANY stop/lot/risk sizing",
        future_used_for_signals=False,history="Real 2018-2025 Dukascopy H1 BID ASK verified",
        beta="Pips ignoring sizing, 5x leverage, micro-lot availability, emergency stops and overnight financing; never interpret as executable PnL",
        results=result,actual_trades=0,real_orders=0)
    (OUT/"DIRECTIONAL_DIAGNOSTIC.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2))
    lines=["# Chẩn đoán HẬU NGHIỆM tín hiệu theo xu hướng (KHÔNG phải backtest chiến lược khả thi)",
      "", "Cùng lịch thứ Hai 08 và cùng cặp được chọn theo |z| của EconEdge, nhưng **không áp dụng SL, lot tối thiểu, hạn mức rủi ro** để hỏi một câu duy nhất: giá có tiếp diễn theo hướng đã hình thành hay không, trước khi tính khả năng triển khai.",
      "**Báo cáo đơn vị pip**, không phải USD của tài khoản $1000. Không mô phỏng phí swap/financing, tick hay thị trường thay đổi trong tuần. Không được thực thi từ kết quả này.",
      "", "| Kỳ | Tuần đủ tín hiệu | Hướng đúng sau chi phí | Pip TB sau quote spread/slippage | Pip TB đối chứng ngược | Bootstrap lower mean pip/tuần | Cận dưới chênh lệch vs đối chứng |",
      "|---|---:|---:|---:|---:|---:|---:|"]
    for name,rr in result.items():
        fmt=lambda x:"—" if x is None else f"{x:.3f}"
        lines.append(f"| {name} | {rr['n']} | {100*rr['winrate']:.1f}% | {fmt(rr['avg_net_pips'])} | {fmt(rr['opposite_avg_net_pips'])} | {fmt(rr['bootstrap_lower_mean_net_pips'])} | {fmt(rr['bootstrap_lower_trend_minus_opposite'])} |")
    lines+=["", "Đây là một phép đánh giá được thêm **sau khi đã thấy** backtest chính, nên không được gọi kết quả confirmatory hay holdout nguyên vẹn.",
      "Dù tín hiệu có dự báo tốt hơn 0, nó vẫn chưa thể giao dịch theo giới hạn 0,01 lot, 0,5%/lệnh, 5× đòn bẩy nếu Stop Loss cần rộng hơn 70 pip. Ngược lại, nếu pip TB thấp hơn 0 thì việc tối ưu lot sẽ không tạo edge."]
    (OUT/"BAO_CAO_DIAGNOSTIC_XU_HUONG.md").write_text("\n".join(lines))
    print("ECONEDGE_DIRECTIONAL_DIAGNOSTIC_COMPLETE",flush=True)
if __name__=="__main__":main()
