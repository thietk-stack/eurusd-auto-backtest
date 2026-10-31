#!/usr/bin/env python3
"""EconEdge: five-country 3m interbank rate differential predicts FX spot price?

This is a PRICE ONLY direction diagnostic (NOT carry profit, swap, OIS, or
tradable strategy). OECD 3M interbank rates via FRED public data CSV, with
reference month m withheld until 2 calendar months later. Data may be revised.
"""
import urllib.request,urllib.parse,hashlib,json,csv,io,math
from pathlib import Path
import pandas as pd,numpy as np
from econedge_long_2011_2025 import verified_16_year_data
from portfolio_research import PIPS
from econedge_macro_cftc_v1 import PAIRS

OUT=Path("econedge_macro_rates_v1_results")
RATE_SERIES={
 "usd":"IR3TIB01USM156N",
 "eurusd":"IR3TIB01EZM156N",
 "gbpusd":"IR3TIB01GBM156N",
 "audusd":"IR3TIB01AUM156N",
 "usdjpy":"IR3TIB01JPM156N",
}
FRED="https://fred.stlouisfed.org/graph/fredgraph.csv"
REFERENCE_LAG_MONTHS=2
BOOTSTRAP_BLOCK_MONTHS=6
SEED=20261031

def get_rates():
    OUT.mkdir(exist_ok=True)
    path=OUT/"FRED_OECD_3MONTH_REAL_SOURCE.csv"
    if path.exists():
        buf=path.read_bytes()
    else:
        query=urllib.parse.urlencode({"id":",".join(RATE_SERIES.values()),"cosd":"2009-01-01","coed":"2025-12-31"})
        url=FRED+"?"+query
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (EconEdge FX historical research; no resale)","Accept":"text/csv,*/*"})
        with urllib.request.urlopen(req,timeout=90) as response:
            buf=response.read()
        if len(buf)<8000:raise ValueError("FRED real 5-country source too small")
        path.write_bytes(buf)
    sha=hashlib.sha256(buf).hexdigest()
    df=pd.read_csv(io.BytesIO(buf))
    df.columns=[c.strip() for c in df.columns]
    datecol=next((c for c in ("observation_date","DATE","date") if c in df.columns),None)
    if datecol is None:raise ValueError("FRED date missing")
    df["reference_month"]=pd.to_datetime(df[datecol],utc=True,errors="raise").dt.to_period("M")
    if df["reference_month"].duplicated().any():raise ValueError("Duplicate OECD rate months")
    for sym,series in RATE_SERIES.items():
        if series not in df.columns:raise ValueError("Missing actual OECD 3month rate "+series)
        df[series]=pd.to_numeric(df[series].replace(".",np.nan),errors="coerce")
    df=df.set_index("reference_month").sort_index()
    counts={s:int(df[name].notna().sum()) for s,name in RATE_SERIES.items()}
    if counts["usd"]<135:raise RuntimeError("Too few observed USD rate months "+str(counts))
    return df,dict(sha256=sha,source=FRED,
       series=RATE_SERIES,nonmissing_month_counts=counts,
       raw_file=str(path),rate_frequency="MONTHLY",income_paid_to_spot_broker=0)

def block_boot_lower(values):
    x=np.asarray(values,float)
    if len(x)<15:return None
    n=len(x);b=min(BOOTSTRAP_BLOCK_MONTHS,n)
    rng=np.random.default_rng(SEED);samples=[]
    for _ in range(2500):
        start=rng.integers(0,n,size=math.ceil(n/b))
        y=np.concatenate([x[(np.arange(i,i+b))%n] for i in start])[:n]
        samples.append(y.mean())
    return float(np.percentile(samples,5))

def signal_monthly(idx,quotes,rates):
    # First actual MON 08 UTC for each month. Keep positions from this
    # first weekly bar until next month's first MON 08 UTC, with no stop.
    monday=np.flatnonzero((idx.dayofweek==0)&(idx.hour==8))
    ref={}
    for i in monday:
        month=idx[i].to_period("M")
        if month not in ref:ref[month]=i
    results=[]
    for month,i in sorted(ref.items()):
        if month.year<2011 or month.year>2025:continue
        target=month-REFERENCE_LAG_MONTHS
        nextmonth=month+1
        if target not in rates.index or nextmonth not in ref:continue
        j=ref[nextmonth]
        usd=float(rates.loc[target,RATE_SERIES["usd"]])
        if not np.isfinite(usd):continue
        options=[]
        for sym in PAIRS:
            fc=float(rates.loc[target,RATE_SERIES[sym]])
            if np.isfinite(fc):
                diff=fc-usd
                options.append(dict(pair=sym,rate_diff=diff,month_ref=str(target)))
        if len(options)!=4:continue
        options.sort(key=lambda e:(-abs(e["rate_diff"]),e["pair"]))
        x=options[0]
        if abs(x["rate_diff"])<1e-12:continue
        sym=x["pair"];p=quotes[sym]
        # Positive interest differential long FOREIGN currency, not
        # necessarily profitable because depreciation can overwhelm carry.
        buy_foreign=1 if x["rate_diff"]>0 else -1
        side=(buy_foreign if sym!="usdjpy" else -buy_foreign)
        start_ask=float(p.ask_open.iloc[i]);start_bid=float(p.bid_open.iloc[i])
        end_ask=float(p.ask_open.iloc[j]);end_bid=float(p.bid_open.iloc[j])
        pip=PIPS[sym]
        def bps(s):
            entry=start_ask+.1*pip if s==1 else start_bid-.1*pip
            exitp=end_bid-.1*pip if s==1 else end_ask+.1*pip
            return s*(exitp-entry)/entry*10000
        r=bps(side);op=bps(-side)
        results.append(dict(entry_time=idx[i].isoformat(),exit_time=idx[j].isoformat(),
            observed_rate_month=str(target),selected_pair=sym,
            interest_rate_foreign_minus_usd_pct=x["rate_diff"],
            high_rate_foreign_signal=buy_foreign,
            high_interest_proxy_price_bps=r,
            opposite_price_bps=op,months_held=1,
            not_forward_points_or_swaps=True))
    if len(results)<110:raise RuntimeError("Not enough actual rate-aligned months to claim completed study")
    return pd.DataFrame(results)

def summary(df):
    groups={"older_2011_2017":(2011,2018),"newer_2018_2025":(2018,2026),
        "entire_2011_2025":(2011,2026)}
    result={}
    years=pd.to_datetime(df.entry_time,utc=True).dt.year
    for name,(a,b) in groups.items():
        sub=df[(years>=a)&(years<b)]
        x=sub.high_interest_proxy_price_bps.to_numpy(float)
        ctrl=sub.opposite_price_bps.to_numpy(float)
        result[name]=dict(n=len(x),mean_spot_bps=float(x.mean()),
            winrate=float((x>0).mean()),mean_opposite_spot_bps=float(ctrl.mean()),
            lower95_6month_block_spot_bps=block_boot_lower(x),
            lower95_difference_vs_opposite=block_boot_lower(x-ctrl))
    return result

def main():
    rates,source=get_rates()
    idx,quotes,source_fx=verified_16_year_data()
    events=signal_monthly(idx,quotes,rates)
    events.to_csv(OUT/"MONTHLY_INTERBANK_RATE_SPOT_PRICE_DIRECTIONS.csv",index=False)
    results=summary(events)
    a=results["older_2011_2017"];b=results["newer_2018_2025"]
    gate=bool(a["n"]>=60 and b["n"]>=72 and
        a["mean_spot_bps"]>0 and b["mean_spot_bps"]>0 and
        a["lower95_6month_block_spot_bps"]>0 and b["lower95_6month_block_spot_bps"]>0)
    o=dict(source=source,fx_source=source_fx,
        critical="PRICE ONLY. Interest differential is used only as sign/selector: NO interest revenue or swap added to PnL",
        two_month_information_lag=REFERENCE_LAG_MONTHS,
        price_only_months=len(events),real_orders=0,
        results=results,gate=gate,verdict="RESEARCH_NO_GO" if not gate else "SIGNAL_ONLY_NEEDS_BROKER_FORWARD_SWAP",
        limitations=["OECD rate observation vintages may be revised. Two-month lag does not guarantee true as-published vintages.",
          "Interest rate differential 3M is NOT earnable carry, currency forward discount, nor Exness daily swap",
          "NO stop-loss or money management: these are bps of SPOT PRICE, not broker USD profits",
          "Historical pair choice is post hoc relative to other hypotheses already tried; no pristine 2011-25 OOS",
          "Broker tick costs, spreads, liquidity and swap require separate validated data"])
    (OUT/"MACRO_RATE_PROXY_RESULTS.json").write_text(json.dumps(o,ensure_ascii=False,indent=2,default=str))
    lines=["# OECD/FRED lãi suất liên ngân hàng 3 tháng — KHÔNG phải carry có thể nhận từ broker",
      "",f"Tải dữ liệu FRED thật, SHA256: {source['sha256']}. Số tháng có đủ dữ liệu: {len(events)}. Có lùi **hai tháng lịch** trước mỗi quyết định.",
      "Chọn cặp giữa EURUSD GBPUSD AUDUSD USDJPY có |lãi suất foreign-USD| cao nhất; đi theo đồng tiền có lãi suất 3m cao hơn. Đo CHỈ biến động giá spot sau Bid/Ask và 0,1pip slippage mỗi chiều; **không cộng lãi suất hoặc swap**.",
      "", "| Giai đoạn | Tháng có dữ liệu | Theo tiền lãi suất cao: bps spot TB | Đối chứng ngược: bps spot TB | Bootstrap lower 95% bps tháng |",
      "|---|---:|---:|---:|---:|"]
    for name,x in results.items():
        lines.append(f"| {name} | {x['n']} | {x['mean_spot_bps']:+.2f} | {x['mean_opposite_spot_bps']:+.2f} | {x['lower95_6month_block_spot_bps']:+.2f} |")
    lines+=["",f"**Cổng thử nghiệm có bằng chứng: {gate}. Phán quyết: {o['verdict']}.**",
       "Ngay cả một kết quả bps giá dương cũng chưa phải kiếm được carry. Để backtest vốn thật phải có **forward/swap rates lịch sử theo broker**, funding, phí và 0.5% stop. Không được giả lập khoản thu nhập chắc chắn từ rate differential." ]
    (OUT/"BAO_CAO_INTERBANK_RATE_PREDICTION.md").write_text("\n".join(lines))
    print("MACRO_FRED_RATES_COMPLETE",len(events),results,"gate",gate,flush=True)
if __name__=="__main__":main()
