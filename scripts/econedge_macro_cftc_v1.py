#!/usr/bin/env python3
"""EconEdge Macro v1: as-published CFTC TFF flow proxies, full audit, no fake data.

A) Official CFTC Socrata dataset (gpe5-46if), with annual ZIP fallback from
CFTC.gov. Both are primary government sources. Every bytestring SHA256.
B) Use Tuesday positions only at >=13 calendar-day lag on Monday 08 UTC.
C) Map futures base FX (JPY inverted) to Dukascopy spot. Compare fund-net
4-report change follow-vs-reverse under original weekly stop/risk rules.
D) Explicitly NOT cross-border capital flows or tradeable carry.
"""
import csv,io,json,hashlib,os,zipfile,urllib.request,urllib.parse,time
from pathlib import Path
from collections import defaultdict
import pandas as pd
import numpy as np
from econedge_long_2011_2025 import verified_16_year_data
import econedge_weekly_trend as base
from portfolio_research import PIPS

OUT=Path("econedge_macro_cot_v1_results")
BASE_COT="https://publicreporting.cftc.gov/resource/gpe5-46if.csv"
CFTC_OLD="https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
PAIRS=("eurusd","gbpusd","audusd","usdjpy")
PAIR_NAME=dict(eurusd="EURO FX",gbpusd="BRITISH POUND",
   audusd="AUSTRALIAN DOLLAR",usdjpy="JAPANESE YEN")
YEARS=list(range(2010,2026))
PERIODS={"historic_2011_2017":(2011,2018),
         "reused_2018_2025":(2018,2026),
         "full_2011_2025":(2011,2026)}
MIN_PUBLICATION_LAG_CALENDAR_DAYS=13
MAX_REPORT_AGE_DAYS=35
LOT_STEP=.001
STOP_BASE_MIN=base.STOP_MIN_PIPS
STOP_BASE_MAX=base.STOP_MAX_PIPS

def download_primary(url,timeout=120):
    req=urllib.request.Request(url,headers={"User-Agent":"EconEdgeResearch/1.0 (public historical CFTC academic dataset; no scraping)","Accept":"text/csv, application/zip, */*"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        data=r.read()
        if len(data)<5000:raise ValueError("Unexpectedly tiny CFTC response "+url)
        if len(data)>150_000_000:raise ValueError("Download too large")
        return data

def fetch_raw():
    OUT.mkdir(exist_ok=True)
    cache=OUT/"CFTC_OFFICIAL_ORIGINAL.csv"
    if cache.exists() and cache.stat().st_size>100_000:
        raw=cache.read_bytes()
        return raw,dict(method="local_in_this_job",sha256=hashlib.sha256(raw).hexdigest())
    query=urllib.parse.urlencode({"$where":
       "report_date_as_yyyy_mm_dd >= '2010-01-01T00:00:00' AND report_date_as_yyyy_mm_dd < '2026-01-01T00:00:00'",
       "$limit":"50000"})
    url=BASE_COT+"?"+query
    failures=[]
    try:
        raw=download_primary(url)
        if not raw.startswith((b'"',b'id,',b'ID,')):
            # Many CSV columns will begin with ID; robust check by CSV header.
            header=next(csv.reader(io.StringIO(raw[:15000].decode("utf-8-sig",errors="replace"))))
            if "market_and_exchange_names" not in [h.strip().lower() for h in header]:
                raise ValueError("Not the CFTC TFF CSV data")
        cache.write_bytes(raw)
        return raw,dict(method="official_CFTC_TFF_Socrata",url=BASE_COT,
           query=query,sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))
    except Exception as e:
        failures.append("Official CFTC API: "+repr(e))
    # Fallback annual official compressed files ONLY; never substitute 3rd-party mirrors.
    result=[]
    try:
        for y in YEARS:
            original=download_primary(CFTC_OLD.format(year=y),timeout=60)
            fname=OUT/f"CFTC_SOURCE_{y}.zip"
            fname.write_bytes(original)
            with zipfile.ZipFile(io.BytesIO(original)) as z:
                names=[n for n in z.namelist() if n.lower().endswith((".txt",".csv"))]
                if not names:raise ValueError("No source CSV in CFTC ZIP year "+str(y))
                blob=z.read(names[0]).decode("utf-8-sig",errors="replace")
                result.extend(list(csv.DictReader(io.StringIO(blob))))
        if not result:raise ValueError("No historical positions in CFTC ZIP archives")
        cols=sorted({k for row in result for k in row})
        buf=io.StringIO()
        writer=csv.DictWriter(buf,fieldnames=cols);writer.writeheader();writer.writerows(result)
        raw=buf.getvalue().encode("utf-8")
        cache.write_bytes(raw)
        return raw,dict(method="official_CFTC_TFF_annual_ZIP",url_template=CFTC_OLD,
           years=YEARS,sha256=hashlib.sha256(raw).hexdigest(),
           archive_sha256={str(y):hashlib.sha256((OUT/f"CFTC_SOURCE_{y}.zip").read_bytes()).hexdigest() for y in YEARS})
    except Exception as e:
        failures.append("Official CFTC ZIP: "+repr(e))
        raise RuntimeError("CFTC primary source unavailable or invalid; no simulated flow results. "+" | ".join(failures))

def sanitize_field(k):
    return k.strip().lower().replace(" ","_").replace("-","_").replace("__","_")

def lookup(row,*starts):
    for prefix in starts:
        keys=[k for k in row if k==prefix or k.startswith(prefix)]
        if keys:
            keys.sort(key=len)
            v=row[keys[0]]
            if v is not None and str(v).strip() not in ("","-",".","nan"):
                return v
    return None

def classify(name):
    text=str(name).upper().strip()
    if "CHICAGO MERCANTILE EXCHANGE" not in text:
        return None
    if any(t in text for t in ("MICRO","MINI","CROSS","/"," - ICE")):return None
    match=[sym for sym,word in PAIR_NAME.items() if text.startswith(word)]
    return match[0] if len(match)==1 else None

def parse_positions(raw):
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig",errors="replace")))
    if not reader.fieldnames:raise ValueError("Missing CFTC CSV header")
    records=[];unexpected=defaultdict(int)
    for original in reader:
        row={sanitize_field(k):v for k,v in original.items() if k is not None}
        name=lookup(row,"market_and_exchange_names")
        sym=classify(name)
        if not sym:continue
        date_str=lookup(row,"report_date_as_yyyy_mm_dd","report_date_as_mm_dd_yyyy","as_of_date_in_form_yymmdd")
        if date_str is None:raise ValueError("CFTC contract lacks Tuesday report date")
        d=pd.to_datetime(str(date_str).strip(),utc=True,errors="coerce")
        if pd.isna(d):raise ValueError("Bad CFTC report date "+str(date_str))
        longv=lookup(row,"asset_mgr_positions_long")
        shortv=lookup(row,"asset_mgr_positions_short")
        openint=lookup(row,"open_interest_all")
        leveraged_long=lookup(row,"lev_money_positions_long")
        leveraged_short=lookup(row,"lev_money_positions_short")
        if any(v is None for v in (longv,shortv,openint)):
            raise ValueError("Actual CFTC asset-manager positions unavailable")
        l=float(str(longv).replace(",",""));s=float(str(shortv).replace(",",""))
        oi=float(str(openint).replace(",",""))
        if not (np.isfinite(oi) and oi>0 and l>=0 and s>=0):
            raise ValueError("Invalid CFTC long short open interest")
        records.append(dict(tuesday=d,report_market=name,pair=sym,
             contract_code=str(lookup(row,"cftc_contract_market_code")),
             open_interest=oi,asset_long=l,asset_short=s,
             leveraged_long=float(leveraged_long) if leveraged_long else np.nan,
             leveraged_short=float(leveraged_short) if leveraged_short else np.nan,
             net_ratio=(l-s)/oi,
             available_at=d+pd.Timedelta(days=MIN_PUBLICATION_LAG_CALENDAR_DAYS)))
    df=pd.DataFrame(records)
    if len(df)<1500:
        raise RuntimeError("CFTC real TFF FX rows insufficient: "+str(len(df)))
    if df.duplicated(["pair","tuesday"]).any():
        duplicates=df[df.duplicated(["pair","tuesday"],keep=False)]
        raise RuntimeError("Ambiguous same-pair CFTC TFF report, fail closed: "+str(duplicates[["pair","tuesday","report_market","contract_code"]].head(15)))
    for sym in PAIRS:
        rows=df[df.pair==sym].sort_values("tuesday")
        if len(rows)<500:raise RuntimeError("Missing historical CFTC weeks for "+sym)
        print("COT_REAL_MARKET",sym,len(rows),rows.report_market.iloc[0],rows.contract_code.iloc[0],flush=True)
    return df.sort_values(["pair","tuesday"]).reset_index(drop=True)

def add_available_fourweek_change(df):
    new=[]
    for sym in PAIRS:
        g=df[df.pair==sym].sort_values("tuesday").copy()
        # Require no larger gaps: past four reports span normally 28 days.
        four=g.net_ratio.shift(4)
        d4=(g.tuesday-g.tuesday.shift(4)).dt.days
        g["delta4"]=np.where(d4.between(21,40),g.net_ratio-four,np.nan)
        new.append(g)
    return pd.concat(new,ignore_index=True)

def events(index,prices,cot):
    monday=np.flatnonzero((index.dayofweek==0)&(index.hour==8))
    book={}
    for sym in PAIRS:
        f=cot[cot.pair==sym].sort_values("available_at").dropna(subset=["delta4"])
        book[sym]=dict(dates=f.available_at.to_numpy(dtype="datetime64[ns]"),rows=f.reset_index(drop=True))
    med={}
    for sym in PAIRS:
        p=prices[sym];pip=PIPS[sym]
        med[sym]=pd.Series((p.high.to_numpy(float)-p.low.to_numpy(float))/pip).rolling(
          base.STOP_MEDIAN_BARS,min_periods=base.STOP_MEDIAN_BARS).median().to_numpy(float)
    es=[]
    for i in monday:
        ts=index[i];j=i-1
        if ts.year<2011 or ts.year>2025 or j<480:continue
        cutoff=ts.normalize()+pd.Timedelta(days=4,hours=20)
        end=int(index.searchsorted(cutoff,side="right")-1)
        if end<=i or index[end].isocalendar().week!=ts.isocalendar().week:continue
        opportunities=[]
        for sym in PAIRS:
            b=book[sym]
            if not len(b["dates"]):continue
            last=int(np.searchsorted(b["dates"],np.datetime64(ts.tz_localize(None)),side="right")-1)
            if last<0:continue
            row=b["rows"].iloc[last]
            age=(ts-row.tuesday).days
            if not (MIN_PUBLICATION_LAG_CALENDAR_DAYS<=age<=MAX_REPORT_AGE_DAYS):
                continue
            if not np.isfinite(med[sym][j]):continue
            score=float(row.delta4)
            if abs(score)<1e-12:continue
            stop=max(base.STOP_MIN_PIPS,6*float(med[sym][j]))
            opportunities.append(dict(pair=sym,delta=score,report_ts=row.tuesday,
                 stop_pips=stop,age_days=age))
        if not opportunities:continue
        opportunities.sort(key=lambda e:(-abs(e["delta"]),e["pair"]))
        best=opportunities[0];sym=best["pair"]
        # JPY futures are quoted as JPY/USD: reverse direction to USDJPY spot.
        side=(1 if best["delta"]>0 else -1)*(-1 if sym=="usdjpy" else 1)
        es.append(dict(entry_idx=int(i),end_idx=int(end),time=ts,
            exit_deadline=cutoff,sym=sym,z=best["delta"],
            stop_pips=best["stop_pips"],momentum_direction=side,qualifies=True,
            cftc_tuesday=str(best["report_ts"]),cftc_age_days=best["age_days"]))
    if len(es)<400:raise RuntimeError("Too few authentic COT weeks")
    return es

def run():
    OUT.mkdir(exist_ok=True)
    original,meta=fetch_raw()
    df=add_available_fourweek_change(parse_positions(original))
    df.to_csv(OUT/"CFTC_ALL_FOUR_FX_SNAPSHOTS.csv",index=False)
    idx,prices,quote_meta=verified_16_year_data()
    ev=events(idx,prices,df)
    pd.DataFrame(ev).to_csv(OUT/"ALL_COT_SIGNALS_USED.csv",index=False)
    result={}
    original_lot=base.LOT_STEP
    try:
        base.LOT_STEP=LOT_STEP
        for group,(start,end) in PERIODS.items():
            result[group]={}
            for mode in ("trend","opposite_control"):
                t,counts,d=base.weekly_replay(ev,prices,start,end,mode)
                base.audit(t)
                performance=base.metrics(t,counts,ev,start,end)
                result[group][mode]=performance
                t.to_csv(OUT/f"{group}_{mode}_TRADES.csv",index=False)
                d.to_csv(OUT/f"{group}_{mode}_DECISIONS.csv",index=False)
                print("COT_FLOW_RESULT",group,mode,"trades",performance["entered"],
                    "USD",round(performance["net_usd"],4),
                    "PF",performance["pf"],
                    "block_lb",performance["bootstrap_lower_mean_week_usd"],flush=True)
    finally:
        base.LOT_STEP=original_lot
    def passes(period):
        x=result[period]["trend"]
        y=result[period]["opposite_control"]
        return (x["entered"]>=35 and x["net_usd"]>0 and
            x["spread_x2_net_usd"]>0 and (x["pf"] or 0)>1.1 and
            (x["bootstrap_lower_mean_week_usd"] is not None and
             x["bootstrap_lower_mean_week_usd"]>0) and x["net_usd"]>y["net_usd"])
    good=(passes("historic_2011_2017") and passes("reused_2018_2025") and
          result["full_2011_2025"]["trend"]["dd_closed_pct"]>=-15)
    outcome=dict(research="CFTC official as-of Tuesday delayed >=13 days, Asset Manager 4-report net position delta, single top absolute USD FX future",
      fetched_source=meta,cot_fx_rows=len(df),cot_signal_weeks=len(ev),
      H1_shared_bars=len(idx),separate_carry_interest_income_modeled=False,
      spot_quote_source=quote_meta,
      forex_jpy_signal_inverted=True,delayed_COT_days=MIN_PUBLICATION_LAG_CALENDAR_DAYS,
      results=result,gate_pass=bool(good),verdict="NO_GO" if not good else "FORWARD_DEMO_ONLY",
      no_live_orders=True,limitations=[
       "CFTC TFF futures-only is not actual spot FX capital flows and positions may reflect hedging/reclassification.",
       "Historical report release dates can be holiday-delayed; 13-day delay used to reduce lookahead; special delays not individually audited.",
       "2011–25 has been viewed many times for other strategy research; not untouched holdout.",
       "H1 candle midpoint extremes and opening spread proxy are not real tick fill prices.",
       "No true carry interest, futures roll PnL or broker financing/swap included.",
       "Historical minimum .001 standard lot is hypothetical and requires broker contract verification."
      ])
    (OUT/"CFTC_MACRO_V1_RESULTS.json").write_text(json.dumps(outcome,ensure_ascii=False,indent=2,default=str))
    lines=["# ECONEDGE MACRO v1 — Dòng vị thế CFTC và kết quả H1 Forex 2011–2025",
       "",f"Nguồn CFTC official: {meta.get('method')} sha256 {meta.get('sha256')}. Có {len(df)} bản ghi của bốn hợp đồng forex futures và {len(ev)} tuần giao dịch có báo cáo đủ trễ.",
       "LƯU Ý: CFTC vị thế là futures, **không phải luồng vốn Forex spot**. Tín hiệu từ vị thế thứ Ba chỉ được dùng từ thứ Hai ≥13 ngày sau. **Không cộng lãi suất/forward/swap vào USD PnL**.",
       "", "| Kỳ (vốn reset mỗi kỳ) | Chính sách | Lệnh | PnL USD | PF | Stress spread×2 | Bootstrap LB 95% USD/tuần |",
       "|---|---|---:|---:|---:|---:|---:|"]
    for name,records in result.items():
        for mode,x in records.items():
            fmt=lambda a:"—" if a is None else f"{a:.3f}"
            lines.append(f"| {name} | {mode} | {x['entered']} | {x['net_usd']:+.2f} | {fmt(x['pf'])} | {x['spread_x2_net_usd']:+.2f} | {fmt(x['bootstrap_lower_mean_week_usd'])} |")
    lines+=["",f"**Cổng chất lượng đạt:** {good}. **Kết luận: {outcome['verdict']}**.",
      "Không có lệnh thật, giá tick broker hay swap. Dữ liệu 2011–25 dùng nhiều lần trong nghiên cứu trước: **không được gọi là kiểm định ngoài mẫu nguyên vẹn**.",
      "Quy trình kiểm tra dữ liệu và lệnh ở file CFTC_ALL_FOUR_FX_SNAPSHOTS.csv, ALL_COT_SIGNALS_USED.csv, sổ khớp/bỏ lệnh từng kỳ."]
    (OUT/"BAO_CAO_CFTC_MACRO.md").write_text("\n".join(lines))
    print("CFTC_MACRO_COMPLETED",len(df),len(ev),"gate",good,flush=True)

if __name__=="__main__":
    run()
