#!/usr/bin/env python3
"""Frozen A+ confluence hypothesis: real four-pair H1 bid/ask history, no live execution.

Entry criteria: long/short H1 candles, EMA trends at distinct horizons, RSI(14)
momentum, prior structure, confirmed (non-repainting) RSI pivot divergence,
ATR regime, observed spread, and session time. One first eligible trade per
ISO calendar week across ALL four symbols; NEVER fill quotas.
Uses one shared account and at most one open position at a time.
"""
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from portfolio_research import load_prices, SYMBOLS, PIPS, SPREAD_EXNESS_ASSUMPTION

START_CASH=1000.0
R_BASE_FRACTION=.01 # 1R = 1% of account equity, as an explicit convention
TRADE_R_FRACTION=.5 # 0.5R = 0.5% of account equity at designed stop
MAX_EFFECTIVE_LEVERAGE=5.0
MIN_RR_AFTER_COSTS=1.5
SCORE_MIN=7
MAX_HOLD_BARS=72
OBSERVED_SPREAD_CAP_MULTIPLIER=2.0
SLIPPAGE_PER_SIDE_PIPS=.1
WINDOWS=[('validation','2021-01-01','2023-01-01'),('holdout','2023-01-01','2026-10-30')]

def rsi(close,n=14):
    d=close.diff()
    up=d.clip(lower=0).ewm(alpha=1/n,adjust=False,min_periods=n).mean()
    down=(-d.clip(upper=0)).ewm(alpha=1/n,adjust=False,min_periods=n).mean()
    rs=up/down.replace(0,np.nan)
    return (100-100/(1+rs)).fillna(50)

def confirmed_divergences(price, r, left=3,right=3, freshness=18):
    """Divergence is recognized only AFTER 'right' future bars of the pivot close.
    Last two confirmed pivot events are compared only on the current timestamp.
    """
    n=len(price)
    long=np.zeros(n,dtype=bool);short=np.zeros(n,dtype=bool)
    low=[]; high=[]
    low_flag_until=-1;high_flag_until=-1
    for i in range(left+right,n):
        p=i-right
        if price[p]<min(price[p-left:p]) and price[p]<=min(price[p+1:p+right+1]):
            if low:
                prev=low[-1]
                if p-prev<180 and price[p]<price[prev] and r[p]>r[prev]+1.5:
                    low_flag_until=i+freshness
            low.append(p)
        if price[p]>max(price[p-left:p]) and price[p]>=max(price[p+1:p+right+1]):
            if high:
                prev=high[-1]
                if p-prev<180 and price[p]>price[prev] and r[p]<r[prev]-1.5:
                    high_flag_until=i+freshness
            high.append(p)
        long[i]=i<=low_flag_until
        short[i]=i<=high_flag_until
    return long,short

def build_features(prices):
    out={}
    for sym in SYMBOLS:
        d=prices[sym]
        close=d.close.astype(float);high=d.high.astype(float);low=d.low.astype(float);op=d.open.astype(float)
        ef=close.ewm(span=24,adjust=False,min_periods=24).mean()
        em=close.ewm(span=96,adjust=False,min_periods=96).mean()
        es=close.ewm(span=120,adjust=False,min_periods=120).mean()
        el=close.ewm(span=480,adjust=False,min_periods=480).mean()
        r=rsi(close)
        tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
        atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
        atrmed=atr.rolling(240,min_periods=240).median()
        body=(close-op).abs().clip(lower=1e-9)
        lower_wick=pd.concat([op,close],axis=1).min(axis=1)-low
        upper_wick=high-pd.concat([op,close],axis=1).max(axis=1)
        range_=(high-low).clip(lower=1e-9)
        bull_pin=(close>op)&(lower_wick>=2*body)&(lower_wick>.45*range_)&(upper_wick<=body)
        bear_pin=(close<op)&(upper_wick>=2*body)&(upper_wick>.45*range_)&(lower_wick<=body)
        bull_engulf=(close>op)&(close.shift()<op.shift())&(op<=close.shift())&(close>=op.shift())
        bear_engulf=(close<op)&(close.shift()>op.shift())&(op>=close.shift())&(close<=op.shift())
        bull_struct=(close>high.shift(1).rolling(12,min_periods=12).max()) | ((low.rolling(3).min()<=ef*1.0002)&(close>ef)&(close>close.shift()))
        bear_struct=(close<low.shift(1).rolling(12,min_periods=12).min()) | ((high.rolling(3).max()>=ef*.9998)&(close<ef)&(close<close.shift()))
        bull_div,bear_div=confirmed_divergences(low.to_numpy(float),r.to_numpy(float)),confirmed_divergences(high.to_numpy(float),r.to_numpy(float))
        # Pivot helper returns (bull, bear). For LOW data use bull; for HIGH use bear.
        bull_div=bull_div[0]
        bear_div=bear_div[1]
        strong_bull=(ef>em)&(es>el)&(close>ef)&(close>es)
        strong_bear=(ef<em)&(es<el)&(close<ef)&(close<es)
        momentum_bull=(r>=48)&(r<=72)&(r-r.shift(3)>=1.2)
        momentum_bear=(r>=28)&(r<=52)&(r-r.shift(3)<=-1.2)
        vol_good=(atr/atrmed>=.7)&(atr/atrmed<=1.9)
        spreads=pd.to_numeric(d.spread_open_pips,errors="raise")
        cost_good=(spreads>=0)&(spreads<=max(1.5,SPREAD_EXNESS_ASSUMPTION[sym]*OBSERVED_SPREAD_CAP_MULTIPLIER))
        # Trading window 07-17 UTC; no historical economic calendar available.
        session=(d.index.hour>=7)&(d.index.hour<17)&(d.index.dayofweek<5)
        score_long=(strong_bull.astype(int)*2+bull_pin.astype(int)+bull_engulf.astype(int)*0+
                   momentum_bull.astype(int)+bull_struct.astype(int)+
                   pd.Series(bull_div,index=d.index).astype(int)+vol_good.astype(int)+cost_good.astype(int)+session.astype(int))
        score_short=(strong_bear.astype(int)*2+bear_pin.astype(int)+bear_engulf.astype(int)*0+
                   momentum_bear.astype(int)+bear_struct.astype(int)+
                   pd.Series(bear_div,index=d.index).astype(int)+vol_good.astype(int)+cost_good.astype(int)+session.astype(int))
        # Candle signal accepts pin bar OR engulfing; double features never increase score.
        score_long=score_long-bull_pin.astype(int)+(bull_pin|bull_engulf).astype(int)
        score_short=score_short-bear_pin.astype(int)+(bear_pin|bear_engulf).astype(int)
        must_long=(strong_bull&momentum_bull&bull_struct&(bull_pin|bull_engulf)&vol_good&cost_good&session)
        must_short=(strong_bear&momentum_bear&bear_struct&(bear_pin|bear_engulf)&vol_good&cost_good&session)
        out[sym]=dict(open=op.to_numpy(float),hi=high.to_numpy(float),lo=low.to_numpy(float),
           close=close.to_numpy(float),atr=atr.to_numpy(float),spread=spreads.to_numpy(float),
           score_long=score_long.to_numpy(int),score_short=score_short.to_numpy(int),
           allowed_long=must_long.to_numpy(bool),allowed_short=must_short.to_numpy(bool),
           diverge_long=np.asarray(bull_div),diverge_short=np.asarray(bear_div))
    return out

def run(index,features,start,end,spread_factor=1.0):
    i0=int(index.searchsorted(pd.Timestamp(start,tz='UTC')))
    i1=int(index.searchsorted(pd.Timestamp(end,tz='UTC')))
    cash=START_CASH;pos=None; last_used_week=None;trades=[];diag=dict(candidates=0,passed_score=0,passed_rr=0,skip_min_lot=0,used_weeks=0)
    candidates=[]
    for i in range(max(i0,1600),i1):
        time=index[i];week=tuple(time.isocalendar()[:2])
        # Exit priority: close old position first; no re-entry on this same bar.
        just_exited=False
        if pos is not None:
            p=features[pos['sym']];direction=pos['direction']
            exit_price=None;reason=None
            if i-pos['i']>=MAX_HOLD_BARS and i>pos['i']:
                exit_price=p['open'][i];reason='timeout'
            if reason is None:
                if direction>0:
                    if p['lo'][i]<=pos['stop']:
                        exit_price=min(p['open'][i],pos['stop']);reason='stop'
                    elif p['hi'][i]>=pos['tp']:
                        exit_price=pos['tp'];reason='target'
                else:
                    if p['hi'][i]>=pos['stop']:
                        exit_price=max(p['open'][i],pos['stop']);reason='stop'
                    elif p['lo'][i]<=pos['tp']:
                        exit_price=pos['tp'];reason='target'
            if reason is not None:
                exit_spread=p['spread'][i]
                # Actual Dukascopy bid/ask approximate at bar OPEN, including if intrabar exit.
                actual_spread=max(pos['entry_spread'],exit_spread)*spread_factor
                cost_pips=actual_spread+2*SLIPPAGE_PER_SIDE_PIPS
                pip=PIPS[pos['sym']]
                # Cost per pip in USD for 1 lot; convert JPY quote PnL at actual close price.
                point_usd=10 if pos['sym']!='usdjpy' else 1000/max(exit_price,1)
                gross_pips=direction*(exit_price-pos['entry_mid'])/pip
                gross_usd=gross_pips*point_usd*pos['lots']
                costs_usd=cost_pips*point_usd*pos['lots']
                net=gross_usd-costs_usd
                cash+=net
                trades.append(dict(entry_time=pos['time'].isoformat(),exit_time=time.isoformat(),
                    pair=pos['sym'],direction='LONG' if direction>0 else 'SHORT',score=pos['score'],
                    divergence=pos['div'],lots=pos['lots'],entry_mid=pos['entry_mid'],
                    exit_mid=exit_price,stop=pos['stop'],target=pos['tp'],
                    designed_R_usd=pos['risk'],initial_rr_net=pos['rr'],
                    gross_pnl_usd=gross_usd,cost_usd=costs_usd,net_pnl_usd=net,
                    equity_usd=cash,exit_reason=reason))
                pos=None;just_exited=True
        if just_exited or pos is not None or last_used_week==week:
            continue
        # Candidates can only rely on i-1 completed H1 bar.
        choices=[]
        for sym in SYMBOLS:
            p=features[sym];j=i-1
            for direction,ok,score,div in (
                (1,p['allowed_long'][j],p['score_long'][j],p['diverge_long'][j]),
                (-1,p['allowed_short'][j],p['score_short'][j],p['diverge_short'][j])):
                if not ok:continue
                diag['candidates']+=1
                if score<SCORE_MIN:continue
                diag['passed_score']+=1
                pip=PIPS[sym]
                risk_price=max(1.6*p['atr'][j],5*pip)
                sl_dist_pips=risk_price/pip
                # Calculate minimum target AFTER estimated roundtrip spread/slippage
                est_spread=max(p['spread'][j],SPREAD_EXNESS_ASSUMPTION[sym])*spread_factor
                assumed_cost=est_spread+2*SLIPPAGE_PER_SIDE_PIPS
                target_dist_pips=max(2.8*p['atr'][j]/pip,1.75*sl_dist_pips)
                planned_RR=(target_dist_pips-assumed_cost)/(sl_dist_pips+assumed_cost)
                if planned_RR+1e-12<MIN_RR_AFTER_COSTS:continue
                diag['passed_rr']+=1
                # Risk budget is 0.5% equity under intended stop+cost scenario.
                dollar_per_pip=(10 if sym!='usdjpy' else 1000/p['open'][i])
                risk_lot=(sl_dist_pips+assumed_cost)*dollar_per_pip
                if risk_lot<=0:continue
                raw_lot=min(cash*R_BASE_FRACTION*TRADE_R_FRACTION/risk_lot,
                            cash*MAX_EFFECTIVE_LEVERAGE/(100000*(1 if sym=='usdjpy' else p['open'][i])),.5)
                lots=math.floor((raw_lot+1e-10)/.01)*.01
                if lots<.01:
                    diag['skip_min_lot']+=1;continue
                choices.append(dict(sym=sym,direction=direction,score=int(score),div=bool(div),
                    entry_mid=p['open'][i],stop=p['open'][i]-direction*risk_price,
                    tp=p['open'][i]+direction*target_dist_pips*pip,
                    entry_spread=float(p['spread'][j]),i=i,time=time,lots=round(lots,2),
                    risk=risk_lot*lots,rr=planned_RR))
        if choices:
            # At same timestamp pick highest score, then stronger RR, then alphabetic pair.
            choices.sort(key=lambda x:(-x['score'],-x['rr'],x['sym'], -x['direction']))
            pos=choices[0];last_used_week=week;diag['used_weeks']+=1
            # Intrabar stop/target on the entry candle must be handled immediately.
            # If both are hit, the stop wins. Entry itself is at the open.
            p=features[pos['sym']]
            first_stop=(p['lo'][i]<=pos['stop']) if pos['direction']>0 else (p['hi'][i]>=pos['stop'])
            first_target=(p['hi'][i]>=pos['tp']) if pos['direction']>0 else (p['lo'][i]<=pos['tp'])
            if first_stop or first_target:
                exit_mid=(min(p['open'][i],pos['stop']) if pos['direction']>0 else max(p['open'][i],pos['stop'])) if first_stop else pos['tp']
                pip=PIPS[pos['sym']]
                per_pip=10 if pos['sym']!='usdjpy' else 1000/max(exit_mid,1)
                gross=pos['direction']*(exit_mid-pos['entry_mid'])/pip*per_pip*pos['lots']
                fee=(pos['entry_spread']*spread_factor+2*SLIPPAGE_PER_SIDE_PIPS)*per_pip*pos['lots']
                cash+=gross-fee
                trades.append(dict(entry_time=time.isoformat(),exit_time=time.isoformat(),
                    pair=pos['sym'],direction='LONG' if pos['direction']>0 else 'SHORT',
                    score=pos['score'],divergence=pos['div'],lots=pos['lots'],entry_mid=pos['entry_mid'],
                    exit_mid=exit_mid,stop=pos['stop'],target=pos['tp'],designed_R_usd=pos['risk'],
                    initial_rr_net=pos['rr'],gross_pnl_usd=gross,cost_usd=fee,
                    net_pnl_usd=gross-fee,equity_usd=cash,
                    exit_reason='first_bar_stop' if first_stop else 'first_bar_target'))
                pos=None
    if pos is not None:
        # Liquidate at final market close to prevent hiding floating losses.
        p=features[pos['sym']];i=i1-1;pip=PIPS[pos['sym']]
        point_usd=10 if pos['sym']!='usdjpy' else 1000/p['close'][i]
        gross_pips=pos['direction']*(p['close'][i]-pos['entry_mid'])/pip
        cost_pips=max(pos['entry_spread'],p['spread'][i])*spread_factor+2*SLIPPAGE_PER_SIDE_PIPS
        gross=gross_pips*pos['lots']*point_usd;fee=cost_pips*pos['lots']*point_usd
        cash+=gross-fee
        trades.append(dict(entry_time=pos['time'].isoformat(),exit_time=index[i].isoformat(),
          pair=pos['sym'],direction='LONG' if pos['direction']>0 else 'SHORT',
          score=pos['score'],divergence=pos['div'],lots=pos['lots'],entry_mid=pos['entry_mid'],
          exit_mid=p['close'][i],stop=pos['stop'],target=pos['tp'],designed_R_usd=pos['risk'],
          initial_rr_net=pos['rr'],gross_pnl_usd=gross,cost_usd=fee,net_pnl_usd=gross-fee,
          equity_usd=cash,exit_reason='end_window'))
    return pd.DataFrame(trades),diag

def stats(trades,start,end):
    months=pd.period_range(start[:7],(pd.Timestamp(end)-pd.Timedelta(days=1)).strftime('%Y-%m'),freq='M')
    if trades.empty:return dict(trades=0,net_pct=0.,win_rate=None,pf=None,
       closed_trade_dd_pct=0,months_5=0,months_8=0,months_evaluated=len(months),total_cost_usd=0)
    pnl=trades.net_pnl_usd.to_numpy(float)
    balances=START_CASH+np.cumsum(pnl)
    peaks=np.maximum.accumulate(np.r_[START_CASH,balances])[1:]
    win=pnl[pnl>0].sum();loss=-pnl[pnl<0].sum()
    by_month=trades.assign(month=pd.to_datetime(trades.exit_time,utc=True).dt.strftime('%Y-%m')).groupby('month').net_pnl_usd.sum().to_dict()
    cash=START_CASH;g5=g8=0
    for m in months:
        r=100*by_month.get(str(m),0)/cash if cash>0 else -100
        g5+=r>=5;g8+=r>=8
        cash+=by_month.get(str(m),0)
    return dict(trades=len(trades),net_pct=100*(balances[-1]/START_CASH-1),
       end_cash_usd=float(balances[-1]),win_rate=float((pnl>0).mean()*100),
       pf=float(win/loss) if loss else None,closed_trade_dd_pct=float((balances/peaks-1).min()*100),
       months_5=int(g5),months_8=int(g8),months_evaluated=len(months),
       total_cost_usd=float(trades.cost_usd.sum()),
       max_designed_risk_usd=float(trades.designed_R_usd.max()),
       max_actual_loss_usd=float(-pnl.min()))

def main():
    out=Path("aplus_results");out.mkdir(exist_ok=True)
    index,data=load_prices()
    if len(index)<40000:raise ValueError('Missing verified common four-pair data')
    features=build_features(data)
    results={}
    for period,start,end in WINDOWS:
        base,diag=run(index,features,start,end,1)
        stressed,_=run(index,features,start,end,2)
        base.to_csv(out/(period+'_trades.csv'),index=False)
        stressed.to_csv(out/(period+'_spread_x2_trades.csv'),index=False)
        results[period]=dict(main=stats(base,start,end),spread_x2=stats(stressed,start,end),diagnostics=diag)
    # No tuning of thresholds by holdout results; preregistered go/no-go.
    v=results['validation']['main'];h=results['holdout']['main']
    can_proceed=bool(v['trades']>=40 and v['net_pct']>0 and (v['pf'] or 0)>1.10 and
        v['closed_trade_dd_pct']>=-15 and h['trades']>=40 and h['net_pct']>0 and
        (h['pf'] or 0)>1.10 and results['holdout']['spread_x2']['net_pct']>0 and
        h['closed_trade_dd_pct']>=-15)
    audit=dict(status='HISTORICAL_BACKTEST_ONLY',data='Dukascopy H1 bid/ask, not Exness',
       symbols=list(SYMBOLS),common_h1_bars=len(index),min_rr_net=MIN_RR_AFTER_COSTS,
       risk_fraction_per_trade=R_BASE_FRACTION*TRADE_R_FRACTION,score_threshold=SCORE_MIN,
       rule='max 1 A+ signal per ISO week across 4 pairs; no mandatory signals; 1 global position at once',
       entry='next bar open after closed signal bar; causal confirmed RSI pivots',
       no_true_volume=True,reason='Historical H1 CSV does not contain reliable traded volume; no fabricated volume signal',
       cost='Dukascopy observed spread at entry/exit proxy, 0.1 pip each side; no Exness historical execution nor swap',
       tested=results,passes_strict_gate=can_proceed,live_orders=0,
       caveats=['OHLC H1 execution approximation','No stop-loss guarantee on a gap',
           'Not all-candle or tick-level fill','Entry-bar stop-first resolution uses H1 candle high/low without exact tick sequence',
           'No historical news calendar filter','No rollover/swap modeled'])
    (out/'RESULTS_APLUS.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    lines=['# Kiểm định tín hiệu A+ 4 cặp Forex — chiến lược hội tụ nhiều yếu tố','',
           'R:R dự kiến sau phí >=1:1,5; 0,5R = 0,5% vốn mỗi lệnh, không bắt buộc có giao dịch mỗi tuần.',
           'Đây là dữ liệu H1 Dukascopy thật, KHÔNG phải tick Exness; chưa có carry/swap.',
           'Không dùng khối lượng giả: dữ liệu H1 không có volume đáng tin cậy.',
           '',
           '| Giai đoạn | Tín hiệu | Tổng lãi/lỗ | PF | Tỷ lệ thắng | DD theo lệnh đóng | Tuần có lệnh | Tháng >=5% | Tháng >=8% |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for period,_,_ in WINDOWS:
        item=results[period];t=item['main'];d=item['diagnostics']
        lines.append(f"| {period} | {t['trades']} | {t['net_pct']:.2f}% | {t['pf'] if t['pf'] is not None else '—'} | {t['win_rate'] if t['win_rate'] is not None else '—'} | {t['closed_trade_dd_pct']:.2f}% | {d['used_weeks']} | {t['months_5']} | {t['months_8']} |")
    lines+=['',f"**Kết luận:** {'Tạm đạt bộ lọc nghiên cứu, chưa được giao dịch thật' if can_proceed else 'Chưa đủ bằng chứng đạt bộ lọc nghiên cứu'}",
        '', 'Phần chi tiết gồm RESULTS_APLUS.json và sổ lệnh CSV. Các khoản lỗ thực tế có thể vượt mức rủi ro thiết kế khi giá gap hoặc thiếu thanh khoản.']
    (out/'BAO_CAO_APLUS.md').write_text('\n'.join(lines))
    print('A+ COMPLETE',json.dumps({key:{'trades':v['main']['trades'],'net_pct':round(v['main']['net_pct'],3),'weeks':v['diagnostics']['used_weeks']} for key,v in results.items()}),'gate',can_proceed,flush=True)

if __name__=='__main__':main()
