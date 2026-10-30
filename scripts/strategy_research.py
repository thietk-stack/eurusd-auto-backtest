#!/usr/bin/env python3
"""Fixed, bounded FX strategy comparison: no fitting on the final holdout."""
import json, math, sys, argparse
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from real_backtest import load_data

START=1000.0
PIP=0.0001
COSTS={"base_0p8":.8,"stress_1p2":1.2,"stress_2p0":2.0}
WINDOWS=[
  ("development","2015-01-01","2019-01-01"),
  ("validation","2019-01-01","2023-01-01"),
  ("holdout","2023-01-01","2026-10-30"),
]
CONFIG={
"donchian_baseline": dict(stop=1.9,target=2.8,ttl=48),
"trend_filter": dict(stop=1.7,target=3.0,ttl=48),
"mean_reversion": dict(stop=1.5,target=1.5,ttl=18),
"session_breakout": dict(stop=1.4,target=2.0,ttl=14)
}

def rsi_wilder(close,period=14):
    delta=close.diff()
    up=delta.clip(lower=0).ewm(alpha=1/period,adjust=False,min_periods=period).mean()
    dn=(-delta.clip(upper=0)).ewm(alpha=1/period,adjust=False,min_periods=period).mean()
    ratio=up/dn.replace(0,np.nan)
    r=100-100/(1+ratio)
    return r.fillna(50)

def indicators(d):
    c=d.close;h=d.high;l=d.low
    prev=c.shift(1)
    tr=pd.concat([h-l,(h-prev).abs(),(l-prev).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    up=h.diff(); down=-l.diff()
    plus=np.where((up>down)&(up>0),up,0.)
    minus=np.where((down>up)&(down>0),down,0.)
    plus_di=100*pd.Series(plus).ewm(alpha=1/14,adjust=False,min_periods=14).mean()/atr.replace(0,np.nan)
    minus_di=100*pd.Series(minus).ewm(alpha=1/14,adjust=False,min_periods=14).mean()/atr.replace(0,np.nan)
    dx=100*(plus_di-minus_di).abs()/(plus_di+minus_di).replace(0,np.nan)
    adx=dx.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    em20=c.ewm(span=20,adjust=False,min_periods=20).mean()
    em100=c.ewm(span=100,adjust=False,min_periods=100).mean()
    mean=c.rolling(20,min_periods=20).mean()
    std=c.rolling(20,min_periods=20).std()
    upper20=h.shift(1).rolling(20,min_periods=20).max()
    lower20=l.shift(1).rolling(20,min_periods=20).min()
    upper18=h.shift(1).rolling(18,min_periods=18).max()
    lower18=l.shift(1).rolling(18,min_periods=18).min()
    signals={}
    signals["donchian_baseline"]=np.where(c>upper18,1,np.where(c<lower18,-1,0))
    signals["trend_filter"]=np.where((c>upper20)&(em20>em100)&(adx>23),1,
                            np.where((c<lower20)&(em20<em100)&(adx>23),-1,0))
    rs=rsi_wilder(c)
    signals["mean_reversion"]=np.where((c<(mean-2*std))&(rs<32)&(adx<25),1,
                              np.where((c>(mean+2*std))&(rs>68)&(adx<25),-1,0))
    # 00:00--06:00 UTC inclusive; the 07:00 completed candle can break that range,
    # at 08:00 enter using only prior bars. Fixed UTC avoids hidden DST assumptions.
    day=d.timestamp.dt.strftime('%Y-%m-%d')
    early=d.timestamp.dt.hour<=6
    early_h=h.where(early).groupby(day).transform('max')
    early_l=l.where(early).groupby(day).transform('min')
    at7=d.timestamp.dt.hour==7
    signals["session_breakout"]=np.where(at7&(c>early_h),1,np.where(at7&(c<early_l),-1,0))
    for k,v in signals.items():
        x=np.asarray(v,dtype=np.int8)
        x[:150]=0
        signals[k]=x
    return signals,atr.to_numpy(float)

def simulate(d,signals,atr,kind,begin,end,spread=.8):
    cfg=CONFIG[kind]
    t=d.timestamp
    first=int(t.searchsorted(pd.Timestamp(begin,tz='UTC')))
    last=int(t.searchsorted(pd.Timestamp(end,tz='UTC')))
    o=d.open.to_numpy(float); h=d.high.to_numpy(float);l=d.low.to_numpy(float)
    signal=signals[kind]
    # Cost scenario: fixed broker spread on mid, 0.1 pip slippage on each side.
    side_cost=(spread/2+.1)*PIP
    cash=START;pos=0;entry=exitstop=exittarget=qty=0.;entry_idx=0
    rows=[]
    equity=[START]
    def exit_trade(i,mid,why):
        nonlocal cash,pos,entry,qty
        fill=mid-side_cost*pos
        gross=pos*(mid-entry)*100000*qty
        fees=(spread+2*.1)*10*qty
        net=gross-fees
        cash+=net
        rows.append(dict(entry_time=t.iloc[entry_idx].isoformat(),exit_time=t.iloc[i].isoformat(),
          side="LONG" if pos==1 else "SHORT",lots=qty,entry_mid=entry,exit_mid=mid,
          gross_usd=gross,spread_usd=spread*10*qty,slippage_usd=.2*10*qty,
          net_usd=net,cash=cash,exit_reason=why))
        pos=0
    for i in range(max(150,first),last):
        opened_at=i
        closed_this_bar=False
        if pos and i>entry_idx:
            if i-entry_idx>=cfg["ttl"]:
                exit_trade(i,o[i],"time");closed_this_bar=True
            elif kind=="mean_reversion" and ((pos==1 and o[i]>=d.close.iloc[i-1:].head(1).iloc[0]) if False else False):
                pass
        if pos and i>entry_idx and not closed_this_bar:
            if kind!="session_breakout" and signal[i-1]==-pos:
                exit_trade(i,o[i],"reverse");closed_this_bar=True
        # Enter strictly on next bar open, and only at allowed UTC hours.
        hour=t.iloc[i].hour
        allowed=(kind=="session_breakout" and hour==8) or (kind!="session_breakout" and 7<=hour<19)
        if not pos and not closed_this_bar and allowed and t.iloc[i].weekday()<5 and cash>=100:
            direction=int(signal[i-1])
            a=atr[i-1]
            if direction and np.isfinite(a) and a>0:
                distance=max(cfg["stop"]*a, 4*PIP)
                target_dist=max(cfg["target"]*a,4*PIP)
                estimated_risk_per_lot=(distance/PIP+spread+.2)*10
                by_risk=cash*.005/estimated_risk_per_lot
                by_notional=cash*5/(100000*o[i])
                lots=math.floor((min(by_risk,by_notional,.5)+1e-12)/.01)*.01
                if lots>=.01:
                    pos=direction;entry=o[i];qty=lots;entry_idx=i
                    exitstop=entry-pos*distance
                    exittarget=entry+pos*target_dist
        if pos:
            # Conservative same-bar rule. Adverse gap exits at actual opening price.
            if pos>0:
                if l[i]<=exitstop:
                    exit_trade(i,min(o[i],exitstop),"stop")
                elif h[i]>=exittarget:
                    exit_trade(i,exittarget,"target")
            else:
                if h[i]>=exitstop:
                    exit_trade(i,max(o[i],exitstop),"stop")
                elif l[i]<=exittarget:
                    exit_trade(i,exittarget,"target")
        equity.append(cash)
    # Every independent window has no trade carried outside: close at end boundary.
    if pos:
        i=last-1
        exit_trade(i,d.close.iloc[i],"window_end")
    return pd.DataFrame(rows)

def stats(trades,begin,end):
    yearmonth=pd.period_range(begin[:7],(pd.Timestamp(end)-pd.Timedelta(days=1)).strftime("%Y-%m"),freq="M")
    if trades.empty:
        return dict(trades=0,net_pct=0.,max_drawdown_pct=0.,profit_factor=None,
           win_rate_pct=None,positive_years=0,years=len(set(x.year for x in yearmonth)),
           months_ge_5pct=0,months_ge_8pct=0,monthly_returns={str(m):0. for m in yearmonth})
    pnl=trades.net_usd.to_numpy(float)
    end_bal=START+np.cumsum(pnl)
    peaks=np.maximum.accumulate(np.r_[START,end_bal])[1:]
    dd=100*np.min(end_bal/peaks-1)
    profit=pnl[pnl>0].sum();loss=-pnl[pnl<0].sum()
    months={str(x):0. for x in yearmonth}
    keys=pd.to_datetime(trades.exit_time,utc=True).dt.strftime("%Y-%m")
    for key,net in zip(keys,pnl):
        if key in months:months[key]+=float(net)
    balance=START;monthly={}
    for key,net in months.items():
        monthly[key]=100*net/balance if balance>0 else None
        balance+=net
    years={y:sum(net for key,net in months.items() if key.startswith(str(y))) for y in set(x.year for x in yearmonth)}
    pf=float(profit/loss) if loss>0 else None
    return dict(trades=len(trades),net_pct=100*(end_bal[-1]/START-1),
       end_cash_usd=float(end_bal[-1]),max_drawdown_pct=float(dd),
       profit_factor=pf,win_rate_pct=float((pnl>0).mean()*100),
       positive_years=sum(v>0 for v in years.values()),years=len(years),
       months_ge_5pct=sum(v is not None and v>=5 for v in monthly.values()),
       months_ge_8pct=sum(v is not None and v>=8 for v in monthly.values()),
       monthly_returns=monthly)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data-dir',default="data")
    p.add_argument('--out',default="research_results")
    args=p.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    data=load_data(Path(args.data_dir),"2010-01-01","2026-10-30")
    if len(data)<90000:raise ValueError("Dataset coverage below 90,000 hourly candles")
    signs,atr=indicators(data)
    results={}
    for name in CONFIG:
        results[name]={}
        for stage,begin,end in WINDOWS:
            tr=simulate(data,signs,atr,name,begin,end,.8)
            results[name][stage]=stats(tr,begin,end)
            tr.to_csv(out/(name+"_"+stage+".csv"),index=False)
    eligible=[]
    for name,item in results.items():
        v=item["validation"]
        if v["trades"]>=40 and v["net_pct"]>0 and (v["profit_factor"] or 0)>1.05 and v["max_drawdown_pct"]>=-20:
            eligible.append(name)
    # Holdout is evaluated for audit, but NOT used for selecting the finalist.
    selection=sorted(eligible,key=lambda n:(-results[n]["validation"]["net_pct"],-results[n]["validation"]["profit_factor"],n))
    winner=selection[0] if selection else None
    stress={}
    if winner:
        for label,sp in COSTS.items():
            stress[label]={}
            for stage,begin,end in WINDOWS[1:]:
                tr=simulate(data,signs,atr,winner,begin,end,sp)
                stress[label][stage]=stats(tr,begin,end)
    final=results[winner]["holdout"] if winner else None
    # Strict go/no-go: not a promise of 5-8% monthly.
    approved=bool(winner and final["trades"]>=40 and final["net_pct"]>0 and
        (final["profit_factor"] or 0)>=1.10 and final["max_drawdown_pct"]>=-20 and
        final["positive_years"]>=2 and stress["stress_1p2"]["holdout"]["net_pct"]>0)
    report=dict(source="Dukascopy real EURUSD H1 via verified cache",candles=len(data),cost_scenario="0.8 pip spread fixed + 0.1 pip slippage per side; swap assumed 0",
        fixed_windows={k:[b,e] for k,b,e in WINDOWS},num_predeclared_rules=len(CONFIG),
        selection_rule="validation only: >=40 trades, positive net, PF>1.05, DD>=-20%, select highest validation return",
        winner_from_validation=winner,eligible=eligible,
        passed_strict_holdout=approved,approved_for_live_trading=False,
        important="No Kronos model was executed; this is an exploratory fixed-rule study. Backtest alone does not authorize real orders.",
        models=results,stress=stress)
    (out/"RESULTS_RESEARCH.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    lines=["# EUR/USD — nghiên cứu vòng 2 (dữ liệu lịch sử thực)",
           "", "**Kết luận theo tiêu chí:** "+("Có tín hiệu đáng kiểm định tiếp (chưa được giao dịch thật)" if approved else "CHƯA XÁC NHẬN ĐƯỢC LỢI THẾ BỀN VỮNG"),
           "", "Dữ liệu: Dukascopy EUR/USD H1, 0,8 pip spread giả định Exness Standard và 0,1 pip trượt giá mỗi chiều. Chưa có swap, dữ liệu tick của Exness hay Kronos AI.",
           "", "| Chiến lược | Xác nhận 2019–22: lệnh | Lãi/lỗ | PF | DD | Kiểm tra 2023–26: lệnh | Lãi/lỗ | PF | DD |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name,rs in results.items():
        a,b=rs["validation"],rs["holdout"]
        fmt=lambda v:"—" if v is None else f"{v:.3f}"
        lines.append(f"| {name} | {a['trades']} | {a['net_pct']:.2f}% | {fmt(a['profit_factor'])} | {a['max_drawdown_pct']:.2f}% | {b['trades']} | {b['net_pct']:.2f}% | {fmt(b['profit_factor'])} | {b['max_drawdown_pct']:.2f}% |")
    lines.extend(["",f"**Được chọn theo giai đoạn xác nhận (không nhìn kết quả 2023–26):** {winner or 'Không có chiến lược nào đủ điều kiện'}.",
        f"**Kết luận kiểm định cuối:** {'Qua bộ tiêu chí nghiên cứu, nhưng cần kiểm định tiếp' if approved else 'Không đạt bộ tiêu chí nghiêm ngặt'}.",
        "", "Không chọn chiến lược dựa trên lợi nhuận giai đoạn cuối; đó sẽ là rò rỉ dữ liệu. Lãi/lỗ tháng ở đây tính theo lệnh đã đóng; có những tháng không giao dịch. Mức DD theo vốn đã hiện thực hóa, chưa gồm floating drawdown.",
        "", "Không hứa hẹn 5–8%/tháng. Cần dữ liệu bid/ask Exness tick thực, swap, spread động, kiểm tra thời gian news và forward demo trước khi giao dịch tiền thật."])
    (out/"BAO_CAO_VONG_2.md").write_text("\n".join(lines))
    print("RESEARCH COMPLETE",json.dumps({x:{s:round(v["net_pct"],3) for s,v in y.items()} for x,y in results.items()}),winner,"passed",approved,flush=True)
if __name__=="__main__": main()
