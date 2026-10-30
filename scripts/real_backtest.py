#!/usr/bin/env python3
"""Causal, read-only historical EURUSD H1 research. Data from Dukascopy, Exness cost scenarios."""
import argparse, json, math, hashlib, sys
from pathlib import Path
import numpy as np
import pandas as pd

PIP=.0001
START_CASH=1000.0
def load_data(folder, begin, end):
    start=pd.Timestamp(begin,tz='UTC'); stop=pd.Timestamp(end,tz='UTC')
    if not start<stop: raise ValueError('Invalid date range')
    months=pd.period_range(start.tz_localize(None).to_period('M'),(stop-pd.Timedelta(seconds=1)).tz_localize(None).to_period('M'))
    frames=[]
    for month in months:
        f=folder/(str(month)+'.csv')
        mf=Path(str(f)+'.source.json')
        if not f.exists() or not mf.exists():raise ValueError('MISSING VERIFIED REAL-DATA MONTH '+str(month))
        m=json.loads(mf.read_text())
        if m.get('source')!='dukascopy-node' or hashlib.sha256(f.read_bytes()).hexdigest()!=m.get('sha256'):
            raise ValueError('BAD SOURCE MANIFEST/CHECKSUM '+str(month))
        frames.append(pd.read_csv(f))
    if not frames:raise ValueError('No CSV files')
    data=pd.concat(frames,ignore_index=True)
    expected={'timestamp','open','high','low','close','bid_open','ask_open','spread_open_pips'}
    if not expected.issubset(data.columns):raise ValueError('Bad input columns')
    data['timestamp']=pd.to_datetime(data.timestamp,utc=True,errors='raise')
    data=data[(data.timestamp>=start)&(data.timestamp<stop)].sort_values('timestamp').reset_index(drop=True)
    if data.empty or data.timestamp.duplicated().any():raise ValueError('No or duplicated hourly data')
    for c in expected-{'timestamp'}:
        data[c]=pd.to_numeric(data[c],errors='raise')
        if not np.isfinite(data[c]).all():raise ValueError('Non-finite '+c)
    if not (data.close.between(.5,2)&data.spread_open_pips.between(0,100)).all():raise ValueError('Invalid FX prices')
    if not ((data.high>=data[['open','close']].max(axis=1))&(data.low<=data[['open','close']].min(axis=1))).all():
        raise ValueError('Invalid candle OHLC')
    return data

def backtest(d, oos, spread=.8, slip=.1):
    c=d.close; h=d.high; l=d.low
    tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False).mean().to_numpy()
    upper=h.shift(1).rolling(18).max().to_numpy()
    lower=l.shift(1).rolling(18).min().to_numpy()
    close=c.to_numpy(float); op=d.open.to_numpy(float); hi=h.to_numpy(float); lo=l.to_numpy(float)
    times=d.timestamp
    signals=np.where(close>upper,1,np.where(close<lower,-1,0))
    first=max(135,int(np.searchsorted(times.values,pd.Timestamp(oos,tz='UTC').to_datetime64())))
    cash=START_CASH;position=0;entry_i=-1;records=[]; equity=[]
    fee=(spread/2+slip)*PIP
    entry_mid=entry_fill=lots=stop=target=0.
    for i in range(first,len(d)):
        p=op[i];reason=None;exit_mid=None
        # Planned open exits cannot access the high/low from later in the same candle.
        if position and i>entry_i:
            if i-entry_i>=48:reason='time';exit_mid=p
            elif signals[i-1]==-position:reason='opposite';exit_mid=p
        if not position and 7<=times.iloc[i].hour<20 and times.iloc[i].weekday()<5 and cash>=100:
            direction=int(signals[i-1])
            a=float(atr[i-1])
            if direction and np.isfinite(a) and a>0:
                distance=max(1.9*a,4*PIP)
                total_cost_pips=spread+2*slip
                proposed=(cash*.005)/((distance/PIP+total_cost_pips)*10)
                by_leverage=cash*5/(100000*p)
                lots=math.floor((min(proposed,by_leverage,.5)+1e-12)/.01)*.01
                if lots>=.01:
                    position=direction;entry_i=i;entry_mid=p;entry_fill=p+fee*direction
                    stop=p-direction*distance
                    target=p+direction*max(2.8*a,4*PIP)
        if position and reason is None:
            # Gaps fill at actual open if worse; both stop and target touched => stop first.
            if position==1:
                if lo[i]<=stop:reason='stop';exit_mid=min(p,stop)
                elif hi[i]>=target:reason='target';exit_mid=max(p,target)
            else:
                if hi[i]>=stop:reason='stop';exit_mid=max(p,stop)
                elif lo[i]<=target:reason='target';exit_mid=min(p,target)
        if position and reason is not None:
            exit_fill=exit_mid-fee*position
            gross=position*(exit_mid-entry_mid)*100000*lots
            net=position*(exit_fill-entry_fill)*100000*lots
            cash+=net
            records.append(dict(entry_time=str(times.iloc[entry_i]),exit_time=str(times.iloc[i]),
                side='buy' if position==1 else 'sell',lots=round(lots,4),
                entry_fill=round(entry_fill,8),exit_fill=round(exit_fill,8),
                gross_usd=gross,spread_usd=spread*10*lots,slippage_usd=slip*20*lots,
                swap_usd=0,net_pnl_usd=net,balance_usd=cash,exit_reason=reason))
            position=0
        equity.append((times.iloc[i],cash+position*(close[i]-entry_fill)*100000*lots if position else cash))
    trades=pd.DataFrame(records)
    curve=pd.DataFrame(equity,columns=['time','equity'])
    return trades,curve,position!=0

def performance(trades):
    if trades.empty:return dict(trades=0)
    profits=trades.net_pnl_usd.to_numpy(float)
    eq=START_CASH+np.cumsum(profits)
    peak=np.maximum.accumulate(np.r_[START_CASH,eq])[1:]
    months=(pd.Timestamp(trades.exit_time.iloc[-1])-pd.Timestamp(trades.entry_time.iloc[0])).total_seconds()/(86400*30.436875)
    good=profits[profits>0].sum(); bad=-profits[profits<0].sum()
    finish=float(eq[-1])
    return dict(trades=len(trades),win_rate_pct=100*float(np.mean(profits>0)),
      profit_factor=float(good/bad) if bad else None,
      end_balance_usd=finish,net_return_pct=100*(finish/START_CASH-1),
      closed_trade_max_drawdown_pct=100*float(np.min(eq/peak-1)),
      monthly_compound_pct=100*((finish/START_CASH)**(1/max(months,0.001))-1) if finish>0 else None,
      total_spread_usd=float(trades.spread_usd.sum()),
      total_slippage_usd=float(trades.slippage_usd.sum()))

def monthly_results(t):
    if t.empty:return []
    t=t.copy()
    t['month']=pd.to_datetime(t.exit_time,utc=True).dt.strftime('%Y-%m')
    balance=START_CASH;out=[]
    for k,g in t.groupby('month',sort=True):
        net=float(g.net_pnl_usd.sum())
        out.append(dict(month=k,opening_balance_usd=balance,net_pnl_usd=net,
                        return_pct=100*net/balance if balance else None))
        balance+=net
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data-dir',default='data');p.add_argument('--from',dest='begin',default='2010-01-01')
    p.add_argument('--to',default='2026-10-30');p.add_argument('--oos',default='2015-01-01')
    p.add_argument('--target',type=int,default=2000);p.add_argument('--out',default='results')
    a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    if not(a.begin<a.oos<a.to):raise ValueError('OOS must be between FROM and TO')
    d=load_data(Path(a.data_dir),a.begin,a.to)
    result={}
    for label,spread in [('Exness_Standard_0p8',.8),('Spread_1p2',1.2),('Spread_2p0',2.0)]:
        trades,curve,unclosed=backtest(d,a.oos,spread)
        trades.to_csv(out/(label+'_all_OOS.csv'),index=False)
        trades.head(a.target).to_csv(out/(label+'_first_2000.csv'),index=False)
        curve.to_csv(out/(label+'_equity.csv'),index=False)
        m=monthly_results(trades)
        pd.DataFrame(m).to_csv(out/(label+'_monthly.csv'),index=False)
        result[label]=dict(all_oos=performance(trades),first_2000=performance(trades.head(a.target)),
            count=len(trades),has_unclosed_position=unclosed,monthly=m,
            months_at_least_8pct=sum(x['return_pct'] is not None and x['return_pct']>=8 for x in m))
    status='COMPLETE_2000_OOS' if result['Exness_Standard_0p8']['count']>=a.target else 'INCOMPLETE_NOT_2000'
    report=dict(status=status,source='Dukascopy via dukascopy-node H1 BID/ASK',
       broker_cost='Exness Standard fixed SPREAD SCENARIO, not actual Exness historical spread',
       period=[a.begin,a.to],oos=a.oos,total_candles=len(d),starting_capital_usd=START_CASH,
       kronos_executed=False,real_orders=0,slippage_per_side_pips=.1,commission_usd=0,
       swap='assumed zero; NOT VERIFIED',cost_sensitivity=result,
       important='Strategy Donchian18 ATR14, stop 1.9x, target 2.8x, 0.5% risk, <=5x leverage. OHLC intrabar assumption; no 8% profitability guarantee.')
    (out/'RESULTS.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    with (out/'BAO_CAO_VI.md').open('w') as f:
        f.write('# Backtest EUR/USD — dữ liệu lịch sử thực từ Dukascopy\n\n')
        f.write('**Trạng thái:** '+status+'\n\n')
        f.write('**Đây không phải dữ liệu Exness, giao dịch thực hoặc kết quả chạy Kronos.**\n\n')
        f.write('| Spread giả định | Lệnh ngoài mẫu | Lãi/lỗ ròng | Drawdown đóng lệnh | Tháng đạt 8%* |\n|---|---:|---:|---:|---:|\n')
        for k,v in result.items():
            s=v['all_oos'];f.write(f"| {k} | {v['count']} | {s.get('net_return_pct','NA')}% | {s.get('closed_trade_max_drawdown_pct','NA')}% | {v['months_at_least_8pct']} |\n")
        f.write('\n*Chỉ tháng có lệnh đóng; lợi suất dựa vào lãi/lỗ đã hiện thực hoá, không phải mark-to-market.\n')
        f.write('\n**Rủi ro:** Spread cố định không phản ánh mở rộng spread theo tin tức; swap chưa kiểm chứng; không bảo đảm 8%/tháng.\n')
        if status!='COMPLETE_2000_OOS':f.write('\n**Chưa đủ 2000 lệnh, KHÔNG công nhận kết quả là backtest 2000 lệnh.**\n')
    print(status, 'observed candles:',len(d), 'trades:',result['Exness_Standard_0p8']['count'])
    if status!='COMPLETE_2000_OOS':sys.exit(4)
if __name__=='__main__': main()
