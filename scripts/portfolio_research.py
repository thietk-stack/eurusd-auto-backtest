#!/usr/bin/env python3
"""Fixed four-pair FX portfolio research. Weekly rebalance, causal signals, no live orders.

Cash-balance weekly marks and turnover costs use verified historical Dukascopy H1 prices.
No carry/swap is modeled: missing historical finance data must never be synthesized.
"""
import hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd

SYMBOLS=('eurusd','gbpusd','audusd','usdjpy')
START='2020-01-01'; END='2026-10-30'
VALIDATION=('2021-01-01','2023-01-01')
HOLDOUT=('2023-01-01','2026-10-30')
SCENARIOS=('ts_momentum','cross_section','equal_weight_benchmark')
START_CAPITAL=1000.0
PIPS={'eurusd':.0001,'gbpusd':.0001,'audusd':.0001,'usdjpy':.01}
# Published as illustrative Exness Standard scenario only: NOT verified broker quotes.
SPREAD_EXNESS_ASSUMPTION={'eurusd':.8,'gbpusd':1.2,'audusd':1.5,'usdjpy':1.1}

def verify_month(folder,month,symbol):
    f=folder/(month+'.csv')
    manifest=Path(str(f)+'.source.json')
    if not f.is_file() or not manifest.is_file():
        raise ValueError('MISSING REAL HISTORICAL MONTH '+symbol+'/'+month)
    meta=json.loads(manifest.read_text())
    if meta.get('source')!='dukascopy-node':
        raise ValueError('Incorrect provenance '+str(f))
    if meta.get('instrument') not in (symbol,None):
        raise ValueError('Instrument mismatch '+str(f))
    if hashlib.sha256(f.read_bytes()).hexdigest()!=meta.get('sha256'):
        raise ValueError('Checksum mismatch '+str(f))
    frame=pd.read_csv(f)
    required=['timestamp','open','high','low','close','bid_open','ask_open','spread_open_pips']
    if not set(required).issubset(frame.columns):
        raise ValueError('Missing market columns '+str(f))
    frame=frame[required]
    return frame

def load_prices(root=Path('.')):
    months=[str(x) for x in pd.period_range(START[:7],(pd.Timestamp(END)-pd.Timedelta(days=1)).strftime('%Y-%m'),freq='M')]
    raw={}
    for sym in SYMBOLS:
        folder=root/'data' if sym=='eurusd' else root/'portfolio_data'/sym
        df=pd.concat([verify_month(folder,m,sym) for m in months],ignore_index=True)
        df['timestamp']=pd.to_datetime(df.timestamp,utc=True,errors='raise')
        df=df.sort_values('timestamp')
        if df.timestamp.duplicated().any():raise ValueError('Duplicate '+sym)
        for c in ['open','high','low','close','bid_open','ask_open','spread_open_pips']:
            df[c]=pd.to_numeric(df[c],errors='raise')
            if not np.isfinite(df[c]).all():raise ValueError('Bad value '+sym+' '+c)
        if not ((df['close']>0)&(df['open']>0)&(df['ask_open']>=df['bid_open'])).all():
            raise ValueError('Inverted market '+sym)
        raw[sym]=df.set_index('timestamp')
    # Only shared observed candles, never forward fill or synthesize missing prices.
    ix=raw[SYMBOLS[0]].index
    for sym in SYMBOLS[1:]:ix=ix.intersection(raw[sym].index)
    ix=ix[(ix>=pd.Timestamp(START,tz='UTC'))&(ix<pd.Timestamp(END,tz='UTC'))].sort_values()
    if len(ix)<26000: raise ValueError('Too few contemporaneous EUR GBP AUD JPY hourly observations '+str(len(ix)))
    common={sym:raw[sym].loc[ix].copy() for sym in SYMBOLS}
    return ix,common

def weekly_inputs(index,prices):
    # 08 UTC Monday open, signals use only earlier price (at preceding valid bar).
    positions=np.flatnonzero((index.dayofweek==0)&(index.hour==8))
    # Need ~60 trading days of warmup: >= 1440 (common) earlier observed candles.
    positions=positions[positions>=1600]
    if len(positions)<200:raise ValueError('Insufficient weekly portfolio dates')
    # We use prior H1 CLOSE as signal, then trade at this week's 08:00 OPEN.
    close=pd.DataFrame({s:prices[s]['close'].to_numpy(float) for s in SYMBOLS},index=index)
    opening=pd.DataFrame({s:prices[s]['open'].to_numpy(float) for s in SYMBOLS},index=index)
    observed=pd.DataFrame({s:prices[s]['spread_open_pips'].to_numpy(float) for s in SYMBOLS},index=index)
    # log return and realized annual volatility over past ~1 month H1, no future bars.
    logp=np.log(close)
    hv=logp.diff().rolling(480,min_periods=480).std()*math.sqrt(24*5*52)
    mom20=logp-logp.shift(480)
    mom60=logp-logp.shift(1440)
    result=[]
    for j in positions:
        prev=j-1
        signals={}
        vol=hv.iloc[prev]
        m20=mom20.iloc[prev]
        m60=mom60.iloc[prev]
        if not np.isfinite(vol).all() or not np.isfinite(m20).all() or not np.isfinite(m60).all():continue
        # Time-series momentum: 20-day and 60-day trend must agree.
        sign=np.where((m20>0)&(m60>0),1.,np.where((m20<0)&(m60<0),-1.,0.))
        target=np.zeros(len(SYMBOLS))
        active=abs(sign)>0
        if active.any():
            # Each leg targets 8%/year vol contribution before caps; correlation unmodeled.
            target[active]=sign[active]*np.minimum(.55, .08/np.maximum(vol.values[active],.035)/math.sqrt(active.sum()))
        if sum(abs(target))>1.50:target*=1.5/sum(abs(target))
        signals['ts_momentum']=target
        # Cross-sectional foreign-currency momentum; JPY strength is negative USDJPY return.
        foreign_strength=m60.to_numpy(float).copy()
        foreign_strength[SYMBOLS.index('usdjpy')]*=-1
        ranks=np.argsort(foreign_strength)
        target=np.zeros(len(SYMBOLS))
        hi,lo=int(ranks[-1]),int(ranks[0])
        target[hi]=min(.55,.08/max(vol.iloc[hi],.035))
        target[lo]=-min(.55,.08/max(vol.iloc[lo],.035))
        # Translate JPY-vs-USD exposure to USDJPY base orientation.
        target[SYMBOLS.index('usdjpy')]*=-1
        signals['cross_section']=target
        # Always-invested zero-signal reference: equal BUY exposures (not USD neutral).
        signals['equal_weight_benchmark']=np.full(len(SYMBOLS),.25)
        result.append(dict(time=index[j],entry=opening.iloc[j].to_numpy(float),
                           spreads=observed.iloc[j].to_numpy(float),weights=signals))
    return result

def simulate(weekly,strategy,begin,end,cost='dukas_observed',spread_multiplier=1):
    # All portfolios reset to $1,000 at each independent window.
    active=[row for row in weekly if pd.Timestamp(begin,tz='UTC')<=row['time']<pd.Timestamp(end,tz='UTC')]
    if len(active)<25:raise ValueError('Insufficient weekly portfolio observations')
    weights=np.zeros(len(SYMBOLS));cash=START_CAPITAL;records=[]
    for n,item in enumerate(active):
        target=item['weights'][strategy].copy()
        # Trade at week's Monday 08 open; mark to next available Monday 08 open.
        next_item=active[n+1] if n+1<len(active) else None
        # Never estimate unrealized ending week after last known Monday.
        if next_item is None:break
        prices=item['entry'];future=next_item['entry']
        if not (np.isfinite(prices).all() and np.isfinite(future).all() and (prices>0).all()):raise ValueError('Invalid observed prices')
        if cost=='dukas_observed':spreads=np.maximum(item['spreads'],0)
        elif cost=='exness_assumption':spreads=np.array([SPREAD_EXNESS_ASSUMPTION[x] for x in SYMBOLS])
        else:raise ValueError('Unknown cost scenario')
        if (spreads>100).any():raise ValueError('Impossible spreads')
        # Rebalance signed notional exposures: new target, costs per one-way turnover.
        turnover=abs(target-weights)
        tx=(spreads*spread_multiplier/2+.10)*np.array([PIPS[s] for s in SYMBOLS])/prices*turnover
        if (tx<0).any() or not np.isfinite(tx).all():raise ValueError('Transaction cost impossible')
        cost_usd=cash*tx.sum()
        pnl_by_pair={}
        for k,s in enumerate(SYMBOLS):
            # USDJPY quote is JPY; USD value of gain (JPY) converted at exit price.
            r=(future[k]-prices[k])/(future[k] if s=='usdjpy' else prices[k])
            pnl_by_pair[s]=cash*target[k]*r
        gross=sum(pnl_by_pair.values())
        opening_cash=cash
        cash+=gross-cost_usd
        if cash<=0:raise ValueError('Insolvency')
        records.append(dict(start=item['time'].isoformat(),end=next_item['time'].isoformat(),
            open_balance=opening_cash,gross_usd=gross,transaction_cost_usd=cost_usd,
            net_usd=gross-cost_usd,end_balance=cash,
            **{f'w_{s}':float(target[k]) for k,s in enumerate(SYMBOLS)},
            **{f'pnl_{s}':float(pnl_by_pair[s]) for s in SYMBOLS}))
        weights=target
    return pd.DataFrame(records)

def metrics(df,begin,end):
    if df.empty: raise ValueError('Empty trades')
    cash=df.end_balance.to_numpy(float)
    peaks=np.maximum.accumulate(np.r_[START_CAPITAL,cash])[1:]
    drawdown=100*(cash/peaks-1)
    gross=float(df.gross_usd.sum())
    net=float(df.net_usd.sum())
    # Weekly mark-to-market is NOT intraday maximum DD.
    # Monthly returns: equity from first available week close to last observed week close;
    # may not align with calendar month boundary exactly.
    months=df.assign(month=pd.to_datetime(df.end,utc=True).dt.strftime('%Y-%m')).groupby('month')
    return dict(weeks=int(len(df)),net_return_pct=net/START_CAPITAL*100,
                end_balance_usd=float(cash[-1]),gross_usd=gross,cost_usd=float(df.transaction_cost_usd.sum()),
                max_weekly_drawdown_pct=float(drawdown.min()),
                annualized_vol_pct=float(df.net_usd.div(df.open_balance).std()*np.sqrt(52)*100),
                positive_weeks=int((df.net_usd>0).sum()),
                months_ge_5=int(sum(100*g.net_usd.sum()/g.open_balance.iloc[0]>=5 for _,g in months)),
                months_ge_8=int(sum(100*g.net_usd.sum()/g.open_balance.iloc[0]>=8 for _,g in months)))

def main():
    out=Path('portfolio_results');out.mkdir(parents=True,exist_ok=True)
    idx,price=load_prices()
    rows=weekly_inputs(idx,price)
    result={}
    for strategy in SCENARIOS:
        result[strategy]={}
        for name,period in [('validation',VALIDATION),('holdout',HOLDOUT)]:
            for scenario,mult in [('dukas_observed',1),('exness_assumption',1),('exness_stress_double',2)]:
                basis='dukas_observed' if scenario=='dukas_observed' else 'exness_assumption'
                trades=simulate(rows,strategy,*period,cost=basis,spread_multiplier=mult)
                result[strategy][name+'_'+scenario]=metrics(trades,*period)
                trades.to_csv(out/(strategy+'_'+name+'_'+scenario+'.csv'),index=False)
    # Select only on 2021–22, never on holdout 2023–26.
    eligible=[]
    for strategy in ('ts_momentum','cross_section'):
        v=result[strategy]['validation_exness_assumption']
        if v['weeks']>=70 and v['net_return_pct']>0 and v['max_weekly_drawdown_pct']>=-15:
            eligible.append(strategy)
    selected=sorted(eligible,key=lambda s:-result[s]['validation_exness_assumption']['net_return_pct'])
    winner=selected[0] if selected else None
    h=result[winner]['holdout_exness_assumption'] if winner else None
    approved=bool(winner and h['net_return_pct']>0 and h['max_weekly_drawdown_pct']>=-15 and
            result[winner]['holdout_exness_stress_double']['net_return_pct']>0)
    audit=dict(status='COMPLETE_REAL_MARKET_DATA',data_source='Dukascopy H1 Bid/Ask, NOT Exness',
               symbols=SYMBOLS,common_h1_bars=len(idx),weekly_observations=len(rows),
               fixed_windows=dict(validation=VALIDATION,holdout=HOLDOUT),
               cost_model='Observed Dukascopy or assumed Exness-like fixed spreads +0.1pip per one-way notional turnover',
               extra_risk='NO swap/carry financing, NO overnight charges, NO execution delay; weekly-only mark-to-market',
               carry_strategy_implemented=False,carry_reason='No audited historical interest-rate/rollover series for all currencies',
               future_leakage='signals from previous finished H1 candle; execution at Monday 08 H1 open',
               predeclared_strategies=SCENARIOS,results=result,validation_eligible=eligible,
               selected_from_validation=winner,passes_predeclared_holdout_gate=approved,
               live_trading_enabled=False,monthly_5_8_target_guaranteed=False)
    (out/'RESULTS_PORTFOLIO.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    lines=['# Danh mục Forex 4 cặp — kiểm định dữ liệu lịch sử thật',
         '','**Không giao dịch tiền thật; không mô hình hóa carry hoặc swap vì thiếu chuỗi lãi suất lịch sử đáng tin cậy.**',
         '',f'Có {len(idx):,} nến H1 cùng thời điểm của cả bốn cặp, {len(rows):,} mốc tái cân bằng tuần.',
         '','| Chiến lược | Giai đoạn | Tuần | Lợi nhuận ròng | Phí giả định | DD theo tuần | Tháng >=5% | Tháng >=8% |',
         '|---|---|---:|---:|---:|---:|---:|---:|']
    for strategy in SCENARIOS:
        for name in ('validation','holdout'):
            v=result[strategy][name+'_exness_assumption']
            lines.append(f"| {strategy} | {name} | {v['weeks']} | {v['net_return_pct']:.2f}% | {v['cost_usd']:.2f} USD | {v['max_weekly_drawdown_pct']:.2f}% | {v['months_ge_5']} | {v['months_ge_8']} |")
    lines.extend(['',f'**Được chọn theo validation 2021–2022:** {winner or "KHÔNG CÓ PHƯƠNG ÁN ĐẠT"}',
       f'**Qua điều kiện ngoài mẫu 2023–2026:** {"CÓ, cần nghiên cứu tiếp" if approved else "KHÔNG"}',
       '', 'Các mức spread Exness được dùng như giả định nghiên cứu, không phải spread lịch sử Exness đã xác minh.',
       'Monthly returns are based on weekly close snapshots, not full calendar-month portfolio mark-to-market.',
       'Báo cáo này KHÔNG thể chứng minh lợi nhuận 5–8%/tháng ổn định; đầu tư Forex có rủi ro mất vốn.',
       'Giới hạn quan trọng: giao dịch FX dùng đòn bẩy/rollover phải tính lãi qua đêm và phí tài khoản thực; kết quả chưa tính.',
       '', 'Tất cả tín hiệu xác định trước, cùng bộ dữ liệu; giai đoạn holdout không tham gia chọn tham số.'])
    (out/'BAO_CAO_DANH_MUC_VI.md').write_text('\n'.join(lines))
    print('PORTFOLIO COMPLETED',json.dumps({k:{p:round(v[p+'_exness_assumption']['net_return_pct'],2) for p in ['validation','holdout']} for k,v in result.items()}),flush=True)
if __name__=='__main__': main()
