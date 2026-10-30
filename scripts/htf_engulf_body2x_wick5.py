#!/usr/bin/env python3
"""H1 or H4 true BODY engulfing >=2x prior BODY, with EACH wick <=5% whole range.
All other locked H4/D1 four-touch zones, limit-only-next-candle, fees/risk unchanged.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import htf_engulf_next_candle as old
from portfolio_research import SYMBOLS

PRICE_EPS=1e-8

WICK_MAX_FRACTION=0.05
BODY_MULTIPLIER=2.0
OUTPUT=Path("engulf_body2x_wick5_results")

def is_strong_body_engulfing(open_,high,low,close,prev_open,prev_close,side):
    """Body is >=2x preceding same-timeframe real body; EACH wick <=5% full range.
    Only closed OHLC data, no lookahead or synthetic volume.
    """
    v=np.asarray([open_,high,low,close,prev_open,prev_close],dtype=float)
    if not np.isfinite(v).all():return False
    whole=high-low
    body=abs(close-open_)
    previous=abs(prev_close-prev_open)
    if whole<=PRICE_EPS or previous<=PRICE_EPS:return False
    if body+PRICE_EPS<BODY_MULTIPLIER*previous:return False
    if high+PRICE_EPS<max(open_,close) or low-PRICE_EPS>min(open_,close):return False
    upper=high-max(open_,close)
    lower=min(open_,close)-low
    if upper < -PRICE_EPS or lower < -PRICE_EPS:return False
    if upper>WICK_MAX_FRACTION*whole+PRICE_EPS:return False
    if lower>WICK_MAX_FRACTION*whole+PRICE_EPS:return False
    if side==1:return close>open_
    if side==-1:return close<open_
    return False

def build_strong_masks(index,prices,features,engulf):
    masks={};audit={}
    for sym in SYMBOLS:
        f=features[sym]
        n=len(index)
        h1mask=np.zeros(n,dtype=bool)
        h1total=0
        h1raw=np.asarray(f["bull"]|f["bear"],dtype=bool)
        for j in range(1,n):
            if not h1raw[j]:continue
            if index[j]-index[j-1]!=pd.Timedelta(hours=1):continue
            h1total+=1
            side=1 if f["bull"][j] else -1
            h1mask[j]=is_strong_body_engulfing(f["open"][j],f["high"][j],f["low"][j],
                 f["close"][j],f["open"][j-1],f["close"][j-1],side)
        masks[(sym,"H1")]=h1mask
        # H4 uses independently aggregated four complete historical H1 candles.
        df=prices[sym]
        grouped=df.resample("4h",label="right",closed="left")
        bars=pd.DataFrame({"open":grouped.open.first(),"high":grouped.high.max(),
            "low":grouped.low.min(),"close":grouped.close.last(),"count":grouped.close.count()}).dropna()
        valid=bars["count"].eq(4)
        h4_allowed=set()
        for at_i,sig in engulf[(sym,"H4")].items():
            t=index[at_i]
            if t not in bars.index:continue
            place=bars.index.get_loc(t)
            if not isinstance(place,(int,np.integer)) or place<1:continue
            prev=bars.iloc[place-1]
            bar=bars.iloc[place]
            if not valid.iloc[place] or not valid.iloc[place-1]:continue
            if is_strong_body_engulfing(bar.open,bar.high,bar.low,bar.close,prev.open,prev.close,sig["side"]):
                h4_allowed.add(at_i)
        masks[(sym,"H4")]=h4_allowed
        audit[sym]={"H1_engulf_before_body2x_wick5":int(h1total),
                    "H1_qualifying_body2x_wick5":int(h1mask.sum()),
                    "H4_engulf_before_body2x_wick5":int(len(engulf[(sym,"H4")])),
                    "H4_qualifying_body2x_wick5":int(len(h4_allowed))}
        yearly={}
        for year in old.YEARS:
            start=pd.Timestamp(f"{year}-01-01",tz="UTC")
            end=pd.Timestamp(f"{year+1}-01-01",tz="UTC")
            lo=int(index.searchsorted(start));hi=int(index.searchsorted(end))
            yearly[str(year)]=dict(H1=int(h1mask[lo:hi].sum()),
                H4=sum(lo<=i<hi for i in h4_allowed))
        audit[sym]["qualifying_by_year"]=yearly
    return masks,audit

def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    idx,prices=old.historical_prices()
    feat,stats=old.build_all(idx,prices)
    engulf=old.engulf_signals(prices,idx,feat)
    masks,counts=build_strong_masks(idx,prices,feat,engulf)
    old_signal=old.signal_at
    def strict_signal(index,features,engulf,sym,tf,i):
        sig=old_signal(index,features,engulf,sym,tf,i)
        if sig is None:return None
        allowed=masks[(sym,tf)]
        if tf=="H1":
            if i<1 or not allowed[i-1]:return None
        elif i not in allowed:return None
        return sig
    # Change ONLY candidate eligibility; all previous zone, limit, 1-candle
    # expiry, SL/TP and risk/fee/execution assumptions remain unaltered.
    old.signal_at=strict_signal
    results={}
    for tf in old.SIGNAL_TIMEFRAMES:
        results[tf]={}
        for mode in old.ZONE_MODES:
            results[tf][mode]={}
            for year in old.YEARS:
                trades,c=old.backtest(idx,feat,engulf,mode,tf,year)
                old.audit(trades,year)
                stress,sc=old.backtest(idx,feat,engulf,mode,tf,year,spread_mult=2)
                old.audit(stress,year)
                stat=old.metrics(trades,c)
                stat["stress_x2_pct"]=old.metrics(stress,sc)["return_pct"]
                stat["counts"]=c
                stat["year"]=year
                trades.to_csv(OUTPUT/f"{tf}_{mode}_{year}.csv",index=False)
                results[tf][mode][str(year)]=stat
            print("FILTER BODY 2X WICK <= 5%",tf,mode,
                [(year,results[tf][mode][str(year)]["filled"],
                  round(results[tf][mode][str(year)]["return_pct"],3)) for year in old.YEARS],flush=True)
    doc=dict(status="RESEARCH_ONLY_NO_LIVE_TRADES",
        source="Actual Dukascopy H1 BID/ASK verified, not Exness historical execution",
        common_hourly_candles=len(idx),years=old.YEARS,symbols=list(SYMBOLS),
        previous_reference="https://github.com/thietk-stack/eurusd-auto-backtest/blob/main/BAO_CAO_H1_H4_ENGULFING_LIMIT_1_NEN.md",
        strict_filter="Current body abs(Close-Open) >=2x preceding same-timeframe abs(Close-Open); each upper and lower wick <=5% of current whole High-Low candle. Keep regular body engulfing.",
        body_multiple=BODY_MULTIPLIER,each_wick_max_full_range_fraction=WICK_MAX_FRACTION,max_quote_rounding_epsilon=PRICE_EPS,
        timeframes=["H1","H4"],zone_models=list(old.ZONE_MODES),
        other_rules_unchanged=True,
        limit="50% of High-Low signal candle, active ONLY in next same-timeframe candle",
        stop="BUY engulfing low -1pip, SELL high +1pip",
        tp="Gross 2R capped before known opposing zone; net R:R>=1.5",
        risk_budget=.005,real_orders=0,
        qualifying_candle_counts=counts,model_results=results,
        caveat="Historical H1 OHLC cannot establish exact intrabar limit/SL sequence; missing swap/real Exness spread; 2019-25 not virgin OOS")
    (OUTPUT/"RESULTS_BODY2X_WICK5.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2))
    lines=["# Engulfing thân >=2× thân nến trước, mỗi râu <=5% High-Low — 2019–2025",
      "", "Cùng một phương pháp vùng cứng H4/D1 và Limit chỉ ở nến H1/H4 kế tiếp.",
      "", "**Bộ lọc mới duy nhất:** |Close-Open| >= 2× |Close-Open| của nến liền trước cùng khung;",
      "mỗi râu trên và dưới đều <=5% tổng High-Low nến hiện tại; sai số máy 1e-8 đơn vị giá. Không bắt buộc 0 râu.",
      "", "| Nến engulfing | Kiểu vùng | Năm | Tín hiệu đặt Limit | Lệnh khớp | Lệnh hết hạn | Lợi nhuận | PF | Tỷ lệ thắng | DD đóng lệnh | Spread x2 |",
      "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for tf in old.SIGNAL_TIMEFRAMES:
        for mode in old.ZONE_MODES:
            for year in old.YEARS:
                row=results[tf][mode][str(year)]
                pf="—" if row["pf"] is None else f"{row['pf']:.3f}"
                wr="—" if row["win_pct"] is None else f"{row['win_pct']:.1f}%"
                lines.append(f"| {tf} | {mode} | {year} | {row['submitted']} | {row['filled']} | {row['expired']} | {row['return_pct']:+.2f}% | {pf} | {wr} | {row['dd_pct']:.2f}% | {row['stress_x2_pct']:+.2f}% |")
    lines+=["", "## Số lượng nến tự thân đạt lọc (trước yêu cầu chạm vùng cứng)"]
    for sym in SYMBOLS:
        row=counts[sym]
        lines.append(f"- {sym}: H1 {row['H1_qualifying_body2x_wick5']}/{row['H1_engulf_before_body2x_wick5']}, H4 {row['H4_qualifying_body2x_wick5']}/{row['H4_engulf_before_body2x_wick5']}.")
    lines+=["", "Có thể có năm không giao dịch. Nếu số lệnh ít, không thể coi năm 0% là bằng chứng hòa vốn bền vững.",
       "Không có chuỗi giá tick Exness hay swap/rollover, giá khớp LIMIT/SL trong nến vẫn chỉ là mô hình bảo thủ.",
       "Rủi ro 0,5% equity là mức thiết kế, có thể vượt khi gap/slippage. Không giao dịch thật hoặc hứa lợi nhuận 5-8%/tháng.",
       "Giai đoạn 2019–2025 đã được dùng ở các nghiên cứu khác; đây là phép khám phá, không phải holdout mới nguyên vẹn."]
    (OUTPUT/"BAO_CAO_THAN_2X_RAU_5PT.md").write_text("\n".join(lines))
    print("STRICT FILTER COMPLETE",json.dumps(counts,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
