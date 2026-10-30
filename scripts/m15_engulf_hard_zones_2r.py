#!/usr/bin/env python3
"""Strong M15 price action at PREVIOUSLY VERIFIED H4/D1 four-rejection zones.

M15 body engulf >=2x previous M15 body, EACH wick <=5% M15 High-Low.
Order at 50% signal M15, VALID ONLY DURING IMMEDIATELY NEXT 15-MINUTE
CANDLE. Stop beyond signal M15 extreme by one pip, target 2R NET projected.
Actual Dukascopy BID+ASK OHLC for limit, stop and TP; no generated M15 bars.
No real trades, Exness broker integration, swap, volume, or economic calendar.
"""
import gzip, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from portfolio_research import SYMBOLS, PIPS
from htf_limit_mid_yearly import historical_prices
from htf_hard_zones_engulf import build_all, CFG
from htf_engulf_body2x_wick5 import is_strong_body_engulfing

YEARS=tuple(range(2019,2026))
MODES=("H4_same","H4_flip","D1_same","D1_flip")
START=1000.
RISK=.005
MAX_LEVERAGE=5.
MIN_NET_RR=2.
BUFFER_PIPS=1.
SLIPPAGE_PIPS=.1
MAX_POSITION_HOURS=96
OUT=Path("m15_strong_price_action_results")
M15_COLUMNS=["timestamp","open","high","low","close","bid_open","bid_high","bid_low","bid_close","ask_open","ask_high","ask_low","ask_close","spread_open_pips"]

def load_m15():
    raw={}
    months=[str(x) for x in pd.period_range("2019-01","2025-12",freq="M")]
    manifest_audit={}
    for sym in SYMBOLS:
        frames=[]
        count=0
        for month in months:
            f=Path("m15_market")/sym/(month+".csv.gz")
            mf=Path(str(f)+".source.json")
            if not f.is_file() or not mf.is_file():
                raise RuntimeError("NO_SYNTHETIC_DATA: missing Dukascopy M15 "+str(f))
            meta=json.loads(mf.read_text())
            if (meta.get("source")!="dukascopy-node" or meta.get("timeframe")!="m15"
                    or meta.get("symbol")!=sym
                    or hashlib.sha256(f.read_bytes()).hexdigest()!=meta.get("sha256")):
                raise ValueError("M15 source/hash mismatch: "+str(f))
            tab=pd.read_csv(f,compression="gzip")
            if not set(M15_COLUMNS).issubset(tab.columns):raise ValueError("Missing quote columns")
            if len(tab)!=meta["candles"]:raise ValueError("Wrong M15 candle count")
            frames.append(tab[M15_COLUMNS]);count+=len(tab)
        df=pd.concat(frames,ignore_index=True)
        ts=pd.to_datetime(df.timestamp,utc=True,errors="raise")
        if ts.duplicated().any():raise ValueError("Duplicate M15 quotes "+sym)
        df.index=ts
        if not df.index.is_monotonic_increasing:df=df.sort_index()
        vals=df[M15_COLUMNS[1:]].to_numpy(float)
        if not np.isfinite(vals).all():raise ValueError("Nonfinite M15 quote "+sym)
        if (df.ask_open<df.bid_open-1e-9).any():raise ValueError("Inverted Bid Ask "+sym)
        raw[sym]=df
        manifest_audit[sym]=dict(months=len(frames),m15_candles=count)
    return raw,manifest_audit

def signal_indices(data):
    o=data.open.to_numpy(float);c=data.close.to_numpy(float)
    h=data.high.to_numpy(float);l=data.low.to_numpy(float)
    n=len(data)
    pb=np.r_[False,c[:-1]<o[:-1]]
    ps=np.r_[False,c[:-1]>o[:-1]]
    prev_c=np.r_[np.nan,c[:-1]]
    prev_o=np.r_[np.nan,o[:-1]]
    bullish=(c>o)&pb&(o<=prev_c)&(c>=prev_o)
    bearish=(c<o)&ps&(o>=prev_c)&(c<=prev_o)
    body=np.abs(c-o)
    prev_body=np.r_[np.nan,body[:-1]]
    span=h-l
    w_up=h-np.maximum(o,c)
    w_low=np.minimum(o,c)-l
    shape=(prev_body>1e-8)&(body+1e-8>=2*prev_body)&(span>0)&(
          w_up<=span*.05+1e-8)&(w_low<=span*.05+1e-8)&(
          w_up>=-1e-8)&(w_low>=-1e-8)
    idx=np.flatnonzero(shape&(bullish|bearish))
    all_engulf=int((bullish|bearish).sum())
    # Ensure both prior candle and immediate next (fill) are REAL consecutive M15.
    time=data.index.asi8
    good=(idx>0)&(idx<n-1)
    idx=idx[good]
    good=(time[idx]-time[idx-1]==900000000000)&(
         time[idx+1]-time[idx]==900000000000)
    idx=idx[good]
    sides=np.where(bullish[idx],1,-1)
    return idx,sides,dict(engulf_all=all_engulf,strong_complete_next=len(idx))

def precompute_candidates(m15,htf,mode,summary):
    # Every zone snapshot is pre-existing at the close of the SIGNAL M15 candle.
    # No future pivot lookahead, no choosing best fill later in the week.
    candidates=[]
    for sym in SYMBOLS:
        d=m15[sym]; idx,sides,s=signal_indices(d)
        summary[sym]=s
        ts=d.index
        ev=htf[sym][mode]
        available=np.array([int(z["available"].value) for z in ev],dtype=np.int64)
        lo=d.low.to_numpy(float);hi=d.high.to_numpy(float)
        close=d.close.to_numpy(float)
        pip=PIPS[sym]
        for j,side in zip(idx,sides):
            next_ts=ts[j+1]
            if next_ts.weekday()>4 or not 7<=next_ts.hour<19:continue
            now=int(next_ts.value)
            k=int(np.searchsorted(available,now,side="right"))
            if not k:continue
            age=CFG[mode[:2]]["age_hours"]*3600*1000000000
            touched=[]
            for z in ev[max(0,k-250):k]:
                if now-int(z["available"].value)>age:continue
                if z["role"]!=("support" if side==1 else "resistance"):continue
                if not (lo[j]<=z["center"]+z["half_width"] and hi[j]>=z["center"]-z["half_width"]):
                    continue
                if side*(close[j]-z["center"])<=0:continue
                touched.append(z)
            if not touched:continue
            touched.sort(key=lambda z:(-z["touches"],z["half_width"],-int(z["available"].value)))
            z=touched[0]
            limit=(lo[j]+hi[j])/2
            if side*(close[j]-limit)<=0:continue
            stop=lo[j]-pip*BUFFER_PIPS if side==1 else hi[j]+pip*BUFFER_PIPS
            stopdist=side*(limit-stop)/pip
            if not (2<=stopdist<=160):continue
            # At entry price LIMIT (ask for BUY or bid for SELL),
            # risk includes 0.1 pip per side; 2R target includes projected slips.
            projected_target=limit+side*(2*stopdist+6*SLIPPAGE_PIPS)*pip
            # Existing confirmed HTF zone on opposite side vetoes 2R target.
            blocked=False
            for opp in ev[max(0,k-250):k]:
                if now-int(opp["available"].value)>age or opp["role"]==z["role"]:continue
                near=(opp["center"]-opp["half_width"]-pip if side==1 else
                      opp["center"]+opp["half_width"]+pip)
                if (side==1 and limit<near<=projected_target) or (side==-1 and projected_target<=near<limit):
                    blocked=True;break
            if blocked:continue
            candidates.append(dict(timestamp=next_ts,entry_idx=j+1,signal_idx=j,
                sym=sym,side=int(side),signal_time=ts[j],zone=z["center"],
                touches=z["touches"],width=z["half_width"],limit=limit,stop=stop,
                sig_low=lo[j],sig_high=hi[j]))
    candidates.sort(key=lambda v:(v["timestamp"],-v["touches"],v["width"],v["sym"]))
    return candidates

def try_fill(d,i,signal):
    # Limit refers to real executable quote: ask LOW for BUY, bid HIGH for SELL.
    f=d.iloc[i];limit=signal["limit"];side=signal["side"];stop=signal["stop"]
    if side==1:
        if f.ask_open<=stop:return None
        if f.ask_open<=limit:return float(f.ask_open)
        if f.ask_low<=limit:return float(limit)
        return None
    if f.bid_open>=stop:return None
    if f.bid_open>=limit:return float(f.bid_open)
    if f.bid_high>=limit:return float(limit)
    return None

def replay_year(m15,events,mode,year,stress_multiplier=1.):
    events=[e for e in events if e["timestamp"].year==year]
    cash=START
    pos=None;last_week=None;orders=0;fills=0;expired=0;reject_rr=0;reject_lot=0;ledger=[]
    # Chronological *one-portfolio* simulation across all four pairs.
    # Each accepted pending limit is live during only its one next M15 bar.
    def exit_position(p,exit_bar_idx,exit_price,reason):
        nonlocal cash,pos
        d=m15[p["sym"]];side=p["side"];pip=PIPS[p["sym"]]
        point=10. if p["sym"]!="usdjpy" else 1000/max(exit_price,1)
        quote_pips=side*(exit_price-p["fill_price"])/pip
        gross_usd=quote_pips*point*p["lots"]  # BID/ASK market spread already in prices
        # Explicit 0.1 pip each-side slippage. Never charge spread twice.
        slippage_usd=2*SLIPPAGE_PIPS*point*p["lots"]
        net=gross_usd-slippage_usd;cash+=net
        ledger.append(dict(year=year,mode=mode,pair=p["sym"],
            signal_tf="M15",signal_time=p["signal_time"].isoformat(),
            order_time=p["entry_time"].isoformat(),entry_time=p["entry_time"].isoformat(),
            exit_time=d.index[exit_bar_idx].isoformat(),
            side="BUY" if side==1 else "SELL",touch_count=p["touches"],
            engulf_high=p["sig_high"],engulf_low=p["sig_low"],
            limit_requested=p["limit"],entry_executable=p["fill_price"],
            stop=p["stop"],target=p["tp"],lots=p["lots"],
            designed_net_rr=p["netrr"],designed_risk_usd=p["designed_risk"],
            quote_pnl_usd=gross_usd,slippage_usd=slippage_usd,
            net_pnl_usd=net,equity_usd=cash,exit_reason=reason))
        pos=None
    for event in events:
        i=event["entry_idx"];ts=event["timestamp"];week=(ts.isocalendar().year,ts.isocalendar().week)
        if pos is not None:
            p=pos;f=m15[p["sym"]]
            # Stop/TP search on actual M15 BID/ASK per side, not synthetic H1.
            i_end=int(f.index.searchsorted(ts))
            close_idx=None;price=None;reason=None
            for q in range(p["fill_idx"],min(i_end,len(f))):
                # Fill M15 bar was already handled conservatively at entry;
                # do not generate a same-bar take profit.
                if q==p["fill_idx"]:continue
                v=f.iloc[q]
                if f.index[q]-p["entry_time"]>=pd.Timedelta(hours=MAX_POSITION_HOURS):
                    price=float(v.bid_open if p["side"]==1 else v.ask_open);reason="timeout"
                elif p["side"]==1:
                    if v.bid_low<=p["stop"]:
                        price=min(float(v.bid_open),p["stop"]);reason="stop"
                    elif v.bid_high>=p["tp"]:
                        price=p["tp"];reason="target_2R"
                else:
                    if v.ask_high>=p["stop"]:
                        price=max(float(v.ask_open),p["stop"]);reason="stop"
                    elif v.ask_low<=p["tp"]:
                        price=p["tp"];reason="target_2R"
                if reason is not None:
                    close_idx=q;break
            if close_idx is not None:exit_position(p,close_idx,price,reason)
        if pos is not None or last_week==week:continue
        # Don't submit competing orders in the same M15 to cherry-pick
        # which one later fills. First ranked event at this timestamp wins.
        orders+=1;d=m15[event["sym"]]
        entry=try_fill(d,i,event)
        if entry is None:
            expired+=1;continue
        pip=PIPS[event["sym"]];side=event["side"]
        dist=side*(entry-event["stop"])/pip
        if not(2<=dist<=160):reject_rr+=1;continue
        # Target must achieve NET +2R after assumed 0.1pip slippage each side,
        # with risk at the actual executable fill quote.
        target=entry+side*(2*dist+6*SLIPPAGE_PIPS)*pip
        riskp=dist+2*SLIPPAGE_PIPS
        rewardp=side*(target-entry)/pip-2*SLIPPAGE_PIPS
        rr=rewardp/riskp
        if rr<MIN_NET_RR-1e-10:raise AssertionError("Not net 2R")
        point=10. if event["sym"]!="usdjpy" else 1000./entry
        max_risk_lots=cash*RISK/(riskp*point)
        max_lev_lots=cash*MAX_LEVERAGE/(100000*(1 if event["sym"]=="usdjpy" else entry))
        lots=math.floor((min(max_risk_lots,max_lev_lots,.5)+1e-10)/.01)*.01
        if lots<.01:reject_lot+=1;continue
        designed=riskp*point*lots
        if designed>cash*RISK+1e-7:raise AssertionError("Excessive modeled risk")
        # Important: when a M15 bar both fills LIMIT and hits SL,
        # record the stop loss immediately (worst case for unknown tick order).
        p=dict(event,entry_time=ts,fill_idx=i,fill_price=entry,tp=target,
               lots=round(lots,2),designed_risk=designed,netrr=rr)
        pos=p;fills+=1;last_week=week
        bar=d.iloc[i]
        stop_hit=(bar.bid_low<=event["stop"] if side==1 else bar.ask_high>=event["stop"])
        if stop_hit:
            price=min(float(bar.bid_open),event["stop"]) if side==1 else max(float(bar.ask_open),event["stop"])
            exit_position(p,i,price,"same_bar_fill_and_stop")
    if pos is not None:
        p=pos
        df=m15[p["sym"]]
        end_year=pd.Timestamp(f"{year+1}-01-01",tz="UTC")
        last=int(df.index.searchsorted(end_year))-1
        # Close on actual last observed BID or ASK of calendar year.
        value=float(df.bid_close.iloc[last] if p["side"]==1 else df.ask_close.iloc[last])
        exit_position(p,last,value,"annual_end")
    return pd.DataFrame(ledger),dict(limit_placed=orders,limit_filled=fills,
        no_fill=expired,rejected_at_fill_rr=reject_rr,rejected_minlot=reject_lot)

def metrics(ledger,stats):
    if ledger.empty:return dict(orders=stats["limit_placed"],fills=0,
        unfilled=stats["no_fill"],net_pct=0,win_pct=None,pf=None,dd_closed_pct=0,
        modeled_cost_usd=0,max_designed_risk=0)
    pnl=ledger.net_pnl_usd.to_numpy(float)
    balance=START+np.cumsum(pnl)
    peaks=np.maximum.accumulate(np.r_[START,balance])[1:]
    gains=float(pnl[pnl>0].sum());loss=float(-pnl[pnl<0].sum())
    return dict(orders=stats["limit_placed"],fills=len(ledger),
        unfilled=stats["no_fill"],net_pct=100*(balance[-1]/START-1),
        win_pct=float(np.mean(pnl>0)*100),pf=gains/loss if loss else None,
        dd_closed_pct=float(np.min((balance/peaks-1)*100)),
        modeled_cost_usd=float(ledger.slippage_usd.sum()),
        max_designed_risk=float(ledger.designed_risk_usd.max()),
        max_realized_loss=float(-pnl.min()),
        by_pair={str(k):int(v) for k,v in ledger.groupby("pair").size().items()})

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m15,source=load_m15()
    _,hour=historical_prices()
    htf,zone_meta=build_all(hour["eurusd"].index,hour)
    report={}
    for mode in MODES:
        diag={}
        cand=precompute_candidates(m15,htf,mode,diag)
        report[mode]={"candidate_count":len(cand),"candle_counts":diag,"years":{}}
        for year in YEARS:
            trades,status=replay_year(m15,cand,mode,year)
            trades.to_csv(OUT/f"M15_{mode}_{year}.csv",index=False)
            stat=metrics(trades,status)
            report[mode]["years"][str(year)]=dict(**stat,diagnostics=status)
        print("M15 BACKTEST",mode,[(y,report[mode]["years"][str(y)]["fills"],
              round(report[mode]["years"][str(y)]["net_pct"],3)) for y in YEARS],flush=True)
    result=dict(status="HISTORICAL_RESEARCH_NO_REAL_TRADES",data="Authentic Dukascopy M15 BID ASK, never synthesized from H1",
        source_audit=source,signal="M15 engulf body >=2x previous M15 body; each wick <=5% of full candle",
        entry="50% M15 full range LIMIT, LIVE ONLY DURING IMMEDIATELY NEXT M15 candle",
        stop="BUY M15 engulf Low -1pip; SELL High +1pip",
        tp="Fixed projected NET 2R; no profit target reduced for opposing HTF zone; veto if blocking",
        zones="4 confirmed H4/D1 rejections, same role or role flip",
        risk_fraction=.005,max_leverage=5,lot_step=.01,one_filled_trade_per_week=True,
        years=YEARS,yearly_initial_cash=START,results=report,zone_meta=zone_meta,
        note="Bid/ask M15 quote path, slippage estimated 0.1pip each side; no Exness real swap or tick order; conservative same-bar stop first",
        no_genuine_unseen_holdout=True)
    (OUT/"RESULTS_M15_YEARLY.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    lines=["# M15 Engulfing mạnh — vùng cứng H4/D1, LIMIT nến kế tiếp, chốt 2R net",
      "", "Dữ liệu M15 Bid/Ask thật từ Dukascopy; không nội suy H1 thành M15. Giá H1 cũ chỉ dùng xây dựng vùng H4/D1 đã xác nhận.",
      "Điều kiện mới: thân engulfing M15 >=2x thân nến M15 trước, mỗi râu <=5%; chờ đúng **nến M15 kế tiếp** khớp tại 50% High-Low.",
      "SL 1 pip ngoài râu. Mục tiêu chốt theo **2R ròng dự kiến sau trượt giá**; nếu vùng cản HTF phía trước target thì bỏ lệnh, không chốt sớm.",
      "0,5% vốn rủi ro thiết kế mỗi lệnh, tối đa một lệnh khớp/tuần cả 4 cặp, 1.000 USD reset từng năm.",
      "", "| Vùng | Năm | Limit | Khớp | Lãi ròng | Tỷ lệ thắng | PF | DD sau lệnh đóng |",
      "|---|---|---:|---:|---:|---:|---:|---:|"]
    for mode in MODES:
        for y in YEARS:
            s=report[mode]["years"][str(y)]
            pf="—" if s["pf"] is None else f"{s['pf']:.2f}"
            wr="—" if s["win_pct"] is None else f"{s['win_pct']:.1f}%"
            lines.append(f"| {mode} | {y} | {s['orders']} | {s['fills']} | {s['net_pct']:+.2f}% | {wr} | {pf} | {s['dd_closed_pct']:.2f}% |")
    lines+=["","**Hạn chế:** Chưa có thứ tự tick trong mỗi M15; một nến vừa khớp Limit vừa chạm SL được coi SL trước (bảo thủ). Không có phí qua đêm, swap hay giá khớp Exness thực tế.",
       "Hiệu quả các năm 2019–2025 đã chịu chọn lọc giả thuyết qua nhiều thử nghiệm trước; chưa phải kiểm định hoàn toàn ngoài mẫu.",
       "Không đạt mục tiêu 5–8%/tháng theo mặc định. Chỉ khuyến nghị nghiên cứu/demo nếu có mẫu thống kê đủ lớn và kết quả sau phí ổn định."]
    (OUT/"BAO_CAO_M15_TUNG_NAM.md").write_text("\n".join(lines))
    print("M15 COMPLETE",len(m15["eurusd"]),json.dumps({k:{str(y):[report[k]["years"][str(y)]["fills"],round(report[k]["years"][str(y)]["net_pct"],3)] for y in YEARS} for k in MODES}),flush=True)
if __name__=="__main__":main()
