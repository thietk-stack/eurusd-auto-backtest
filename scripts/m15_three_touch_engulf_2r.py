#!/usr/bin/env python3
"""Pure M15 price action: THREE touches of the same price area with at most
TEN M15 candles between consecutive touches; third touch is a fully closed
strong M15 body engulfing. No H4 or D1 zones (removed by user).

Each first/second touch: confirmed M15 pivot reacting away in its following
closed candle, causal (no repaint). Third touch: M15 engulfing wick returns
to the SAME zone and closes away. Real price quotes, one-candle limit, net TP
2R, designed risk 0.5% equity. No live trades or fabricated lower TF.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
import m15_engulf_hard_zones_2r as old
from portfolio_research import SYMBOLS,PIPS

YEAR_LIST=old.YEARS
OUT=Path("m15_three_touch_results")
TOUCH_MAX_BARS=10
TOUCH_MIN_BARS=2
PIVOT_LEFT=2
PIVOT_RIGHT=1
MIN_REACTION_MEDIAN_CANDLE_FRACTION=.4
ZONE_WIDTH_MIN_PIPS=2.0
ZONE_WIDTH_MEDIAN_CANDLE_FRACTION=.35

def pivot_reactions(d,pip):
    """Return independent pivots where first reaction is already CLOSED.
    At signal candle j, pivot p must obey p+1 < j (seen before j).
    """
    h=d.high.to_numpy(float);l=d.low.to_numpy(float)
    c=d.close.to_numpy(float)
    n=len(d)
    median=pd.Series(h-l).rolling(40,min_periods=10).median().to_numpy(float)
    support=np.zeros(n,dtype=bool)
    resist=np.zeros(n,dtype=bool)
    for p in range(PIVOT_LEFT,n-PIVOT_RIGHT):
        m=median[p]
        if not np.isfinite(m) or m<=0:continue
        support[p]=(l[p]<min(l[p-2:p]) and l[p]<l[p+1] and
                    c[p+1]-l[p]>=MIN_REACTION_MEDIAN_CANDLE_FRACTION*m)
        resist[p]=(h[p]>max(h[p-2:p]) and h[p]>h[p+1] and
                   h[p]-c[p+1]>=MIN_REACTION_MEDIAN_CANDLE_FRACTION*m)
    return support,resist,median

def three_touch_signal(j,side,lo,hi,close,pivots,median,pip):
    """Choose exactly 2 earlier independent pivot points then current engulfing
    = third touch. Each gap 2–10 candles, with zone co-location.
    Third point does not need 1 additional future pivot confirmation,
    because the finished engulfing itself is the reversal evidence.
    """
    if j<10:return None
    pivots_prev,_,_=pivots if side>0 else (pivots[1],None,None)
    px=lo[j] if side>0 else hi[j]
    med=median[j]
    if not np.isfinite(med):return None
    width=max(ZONE_WIDTH_MIN_PIPS*pip,ZONE_WIDTH_MEDIAN_CANDLE_FRACTION*med)
    for p2 in range(j-TOUCH_MIN_BARS,j-TOUCH_MAX_BARS-1,-1):
        if p2<2 or not pivots_prev[p2]:continue
        if abs((lo[p2] if side>0 else hi[p2])-px)>width:continue
        for p1 in range(p2-TOUCH_MIN_BARS,p2-TOUCH_MAX_BARS-1,-1):
            if p1<2 or not pivots_prev[p1]:continue
            v1=lo[p1] if side>0 else hi[p1]
            v2=lo[p2] if side>0 else hi[p2]
            if abs(v1-px)>width or abs(v1-v2)>width:continue
            center=float(np.median([v1,v2,px]))
            if side*(close[j]-center)<=0:continue
            return dict(prior_pivot_1=p1,prior_pivot_2=p2,signal_idx=j,
                        gap_12=p2-p1,gap_23=j-p2,
                        zone_center=center,zone_half_width=width,
                        prices=[float(v1),float(v2),float(px)])
    return None

def candidates_all(m15):
    candidates=[]
    count={}
    for sym in SYMBOLS:
        d=m15[sym]
        idx,sides,base=old.signal_indices(d)
        support,resist,median=pivot_reactions(d,PIPS[sym])
        h=d.high.to_numpy(float);l=d.low.to_numpy(float)
        c=d.close.to_numpy(float)
        count[sym]=dict(strong_engulf_m15=base["strong_complete_next"],
            independent_confirmed_support_pivots=int(support.sum()),
            independent_confirmed_resistance_pivots=int(resist.sum()),
            three_touch_confirmed=0)
        for j,side in zip(idx,sides):
            i=j+1
            now=d.index[i]
            if now.dayofweek>4 or not 7<=now.hour<19:continue
            match=three_touch_signal(int(j),int(side),l,h,c,
                       (support,resist,median),median,PIPS[sym])
            if match is None:continue
            count[sym]["three_touch_confirmed"]+=1
            midpoint=float((h[j]+l[j])/2)
            if side*(c[j]-midpoint)<=0:continue
            stop=float(l[j]-PIPS[sym] if side>0 else h[j]+PIPS[sym])
            distance=side*(midpoint-stop)/PIPS[sym]
            if not 2<=distance<=160:continue
            # Existing two confirmed pivot reactions + current finished signal.
            candidates.append(dict(timestamp=now,entry_idx=int(i),signal_idx=int(j),
                sym=sym,side=int(side),signal_time=d.index[j],
                zone=match["zone_center"],touches=3,width=match["zone_half_width"],
                limit=midpoint,stop=stop,sig_low=float(l[j]),sig_high=float(h[j]),
                touch_gap_12=match["gap_12"],touch_gap_23=match["gap_23"],
                pivot_1=match["prior_pivot_1"],pivot_2=match["prior_pivot_2"],
                touch_prices=match["prices"]))
    # Deterministic chronological ordering; if multiple pairs have same next
    # candle, submit only one limit to avoid hindsight-based selection.
    candidates.sort(key=lambda x:(x["timestamp"],x["width"],x["sym"]))
    unique=[];last_ts=None
    for c in candidates:
        if c["timestamp"]==last_ts:continue
        unique.append(c);last_ts=c["timestamp"]
    return unique,count

def audit(trades,year):
    if trades.empty:return
    if not (trades.touch_count==3).all():raise AssertionError("Not three touches")
    if not (trades.designed_net_rr>=2-1e-9).all():raise AssertionError("RR below net 2")
    if not ((trades.quote_pnl_usd-trades.slippage_usd-trades.net_pnl_usd).abs()<1e-7).all():
        raise AssertionError("P&L inconsistent")
    if pd.to_datetime(trades.entry_time,utc=True).dt.strftime("%G-%V").duplicated().any():
        raise AssertionError("More than one fill in ISO week")
    cash=old.START
    for row in trades.itertuples(index=False):
        pip=PIPS[row.pair]
        if abs(row.limit_requested-(row.engulf_low+row.engulf_high)/2)>1e-7:
            raise AssertionError("Incorrect midpoint limit")
        stop=row.engulf_low-pip if row.side=="BUY" else row.engulf_high+pip
        if abs(row.stop-stop)>1e-7:raise AssertionError("Incorrect SL")
        if row.designed_risk_usd>cash*.005+1e-6:
            raise AssertionError("Risk above 0.5%")
        if abs(row.equity_usd-(cash+row.net_pnl_usd))>1e-6:
            raise AssertionError("Discontinuous account balance")
        cash=row.equity_usd

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m15,sources=old.load_m15()
    candidate,counts=candidates_all(m15)
    result={}
    for year in YEAR_LIST:
        rows,stats=old.replay_year(m15,candidate,"M15_three_touch",year)
        audit(rows,year)
        rows.to_csv(OUT/f"M15_three_touch_{year}.csv",index=False)
        result[str(year)]=dict(**old.metrics(rows,stats),diagnostics=stats)
        print("M15 3TOUCH YEAR",year,"orders",stats["limit_placed"],
            "fills",stats["limit_filled"],"net_pct",round(result[str(year)]["net_pct"],4),flush=True)
    summary=dict(source="Verified real Dukascopy 15min BID ASK; no H1 interpolation",
        source_sha_audit=sources,
        years=YEAR_LIST,signals_by_pair=counts,all_candidates=len(candidate),
        zone="ONLY M15 three touches: two confirmed pivots + finished M15 strong engulfing as third reversal",
        timeframe="M15 only; no H4/D1 zones or checks",
        max_gap_between_consecutive_touches_m15=TOUCH_MAX_BARS,
        minimum_independent_gap_m15=TOUCH_MIN_BARS,
        pivot_confirmation="1 following closed 15-minute candle for first 2 touches; third is engulfing",
        same_price_zone_tolerance=f"max({ZONE_WIDTH_MIN_PIPS}pip, {ZONE_WIDTH_MEDIAN_CANDLE_FRACTION} * rolling median M15 range 40)",
        strong_engulf="body >=2x previous M15 body, both wicks <=5% whole M15 candle",
        limit="50% full M15 engulfing High–Low, ONLY next 15-minute candle",
        stop="BUY engulfing low -1pip, SELL high +1pip",
        tp="projected net RR 2.0 inclusive quote spread and 0.1pip each way slippage",
        initial_cash_each_year=1000,planned_risk_fraction=.005,
        max_one_filled_trade_per_ISO_week_across_four_pairs=True,
        scenario="HISTORICAL_RESEARCH_ONLY_NOT_BROKER_EXECUTION",
        real_orders=0,results=result,
        caveats=["M15 candle OHLC does not determine intrabar order of fill vs SL/TP; conservative same-bar stop",
        "Swap/rollover excluded and Exness price/real latency not represented",
        "Each year resets account balance; do not sum percentages as compounded seven-year return",
        "2019–25 used previously, so not an untouched final holdout",
        "0.5% stop risk design can be exceeded by gaps/slippage"])
    (OUT/"RESULTS_M15_THREE_TOUCH_2R.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    lines=["# Chỉ M15: 3 chạm cùng vùng giá, mỗi lần cách nhau tối đa 10 nến, TP chốt 2R",
        "", "Hai lần đầu là pivot M15 đã xác nhận đảo chiều (chỉ 1 nến tương lai được dùng **sau khi nó đã đóng**); lần thứ ba là chính nến M15 Engulfing mạnh đã đóng tại cùng vùng, không cần dữ liệu tương lai.",
        "Khoảng cách giữa các điểm chạm liên tiếp **2 đến 10 nến M15**, độ rộng vùng = max(2 pip, 0,35 x median biên độ 40 nến M15).",
        "Không sử dụng vùng H4, D1. Giữ thân Engulfing >=2x thân trước, từng râu <=5%; limit tại midpoint, chỉ nến M15 kế tiếp, SL qua wick 1 pip, TP dự kiến ròng đúng 2R, 0,5% vốn theo stop.",
        "", "| Năm | Limit được xét | Lệnh khớp | Không khớp | Lợi nhuận ròng | Tỷ lệ thắng | PF | DD sau đóng lệnh |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for yr in YEAR_LIST:
        r=result[str(yr)]
        wr="—" if r["win_pct"] is None else f"{r['win_pct']:.1f}%"
        pf="—" if r["pf"] is None else f"{r['pf']:.2f}"
        lines.append(f"| {yr} | {r['orders']} | {r['fills']} | {r['unfilled']} | {r['net_pct']:+.2f}% | {wr} | {pf} | {r['dd_closed_pct']:.2f}% |")
    lines+=["","Giá M15 Dukascopy Bid/Ask thật, không dựng M15 từ H1. Sổ lệnh CSV và JSON kiểm toán được xuất kèm.",
       "**Hạn chế:** Chưa có tick nội nến hay phí qua đêm thực tế. Nếu Limit và SL cùng nằm trong một nến, stop được ưu tiên. Không khẳng định đạt 5–8%/tháng khi chưa có kết quả đáng tin cậy."]
    (OUT/"BAO_CAO_M15_3_CHAM_2R.md").write_text("\n".join(lines))
    print("M15 THREE-TOUCH FINISHED",json.dumps({y:[r['fills'],round(r['net_pct'],3)] for y,r in result.items()}),flush=True)

if __name__=="__main__":main()
