#!/usr/bin/env python3
"""Pure price-action H1 support/resistance backtest (two preregistered zone definitions).

All zone construction is causal. A pivot at p becomes known at p+3 only.
Real FX market observations downloaded independently from Dukascopy. No real orders.
"""
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from portfolio_research import load_prices, SYMBOLS, PIPS

START_CASH=1000.
RISK_FRACTION=.005
MIN_NET_RR=1.5
LEVERAGE_CAP=5.
MAX_HOLD=72
MIN_TOUCH_SEPARATION=24   # separate reactions >= 24 valid H1 candles
ZONE_HISTORY=24*180       # look back 180 days for 4 separate reactions
ZONE_VALIDITY=24*90       # no trading stale zone older than ~90 days
PIVOT_LEFT=PIVOT_RIGHT=3
SCENARIOS=('four_same_role','four_mixed_roles')
WINDOWS=(('validation','2021-01-01','2023-01-01'),
         ('holdout','2023-01-01','2026-10-30'))
SLIPPAGE_PIPS=.1
# Only completed price bars and patterns: no RSI, EMA, ATR, ADX, volume, news.

def detect_pivots(d):
    low=d.low.to_numpy(float); high=d.high.to_numpy(float)
    close=d.close.to_numpy(float)
    n=len(d)
    rng=pd.Series(high-low).rolling(240,min_periods=100).median().to_numpy(float)
    islow=np.zeros(n,dtype=bool); ishigh=np.zeros(n,dtype=bool)
    lo=low[PIVOT_LEFT:n-PIVOT_RIGHT];hi=high[PIVOT_LEFT:n-PIVOT_RIGHT]
    lower=np.ones(len(lo),bool);higher=np.ones(len(hi),bool)
    for offset in range(1,PIVOT_LEFT+1):
        lower&=(lo<low[PIVOT_LEFT-offset:n-PIVOT_RIGHT-offset])
        higher&=(hi>high[PIVOT_LEFT-offset:n-PIVOT_RIGHT-offset])
    for offset in range(1,PIVOT_RIGHT+1):
        lower&=(lo<=low[PIVOT_LEFT+offset:n-PIVOT_RIGHT+offset])
        higher&=(hi>=high[PIVOT_LEFT+offset:n-PIVOT_RIGHT+offset])
    islow[PIVOT_LEFT:n-PIVOT_RIGHT]=lower
    ishigh[PIVOT_LEFT:n-PIVOT_RIGHT]=higher
    # Nontrivial reaction must already have occurred in the three confirmation bars.
    pivots=[]
    for p in range(250,n-PIVOT_RIGHT):
        typical=rng[p]
        if not np.isfinite(typical) or typical<=0:continue
        if islow[p] and np.max(close[p+1:p+4])-low[p]>=1.2*typical:
            pivots.append((p+PIVOT_RIGHT,p,'support',low[p]))
        if ishigh[p] and high[p]-np.min(close[p+1:p+4])>=1.2*typical:
            pivots.append((p+PIVOT_RIGHT,p,'resistance',high[p]))
    pivots.sort(key=lambda e:(e[0],e[1],e[2]))
    return pivots,rng

def nearby_cluster(events, pivot, tolerance, history):
    recent=[x for x in events if 0<=pivot[1]-x[1]<=history and abs(x[3]-pivot[3])<=tolerance]
    # Distinct touches: a multi-bar oscillation inside one day counts only once.
    selected=[]
    for x in reversed(recent):
        if all(abs(x[1]-y[1])>=MIN_TOUCH_SEPARATION for y in selected):
            selected.append(x)
    return list(reversed(selected))

def qualified(cluster, kind, last):
    if len(cluster)<4:return False
    roles=[x[2] for x in cluster]
    if kind=='four_same_role':
        return roles.count(last[2])>=4
    if kind=='four_mixed_roles':
        return ('support' in roles and 'resistance' in roles and
                any(a!=b for a,b in zip(roles,roles[1:])))
    raise ValueError(kind)

def build_zone_snapshots(prices):
    """For each symbol, produce actual causal hard zone activation/update events.
    Not based on future bars, and not optimized over final returns.
    """
    result={}
    for sym in SYMBOLS:
        d=prices[sym]
        pivots,rng=detect_pivots(d)
        pip=PIPS[sym]
        seen=[]
        activated={x:[] for x in SCENARIOS}
        for event in pivots:
            confirmed,p,role,price=event
            seen.append(event)
            # Drop pivots older than the stated 4320 observed H1 bar lookback.
            # These pivots cannot belong to any new cohort, so no signal changes.
            while seen and p-seen[0][1]>ZONE_HISTORY:
                seen.pop(0)
            # Zone half-width: 6 pips or 0.75 x median observed H1 candle range,
            # computed from past bars only. 4-touch cohort must fit within +/- width.
            width=max(6*pip, .75*rng[confirmed])
            cohort=nearby_cluster(seen,event,width,ZONE_HISTORY)
            for kind in SCENARIOS:
                use=( [z for z in cohort if z[2]==role] if kind=='four_same_role' else cohort )
                if not qualified(use,kind,event):continue
                if not all(x[0]<=confirmed for x in use):raise AssertionError('Future pivot leaked')
                center=float(np.median([x[3] for x in use]))
                activated[kind].append(dict(active_i=confirmed,center=center,width=width,
                                  role=role,touches=len(use),last_p=p,
                                  cluster_first_i=use[0][0],cluster_last_i=use[-1][0]))
        result[sym]=dict(activations=activated,pip=pip,
            open=d.open.to_numpy(float),hi=d.high.to_numpy(float),
            lo=d.low.to_numpy(float),close=d.close.to_numpy(float),
            bid=d.bid_open.to_numpy(float),ask=d.ask_open.to_numpy(float),
            rng=rng)
    return result

def rejection(f,j,z):
    """Candle j must retest zone and turn away on its finished candle.
    Signal accepted at j close; next candle j+1 OPEN is executable.
    """
    center=z['center'];w=z['width']
    op=f['open'][j];cl=f['close'][j];lo=f['lo'][j];hi=f['hi'][j]
    body=max(abs(cl-op),f['pip']*.1)
    touched=lo<=center+w and hi>=center-w
    if not touched:return False
    if z['role']=='support':
        lower_wick=min(op,cl)-lo
        return cl>center+w and cl>op and (lower_wick>=.55*body or
                (cl>f['hi'][j-1] and lo< f['lo'][j-1]))
    upper_wick=hi-max(op,cl)
    return cl<center-w and cl<op and (upper_wick>=.55*body or
            (cl<f['lo'][j-1] and hi>f['hi'][j-1]))

def min_cost_pips(sym,observed_spread,stress):
    # Whole spread plus 0.1 pip slippage each side (roundtrip).
    if not (0<=observed_spread<=100):return None
    return observed_spread*stress+2*SLIPPAGE_PIPS

def simulate(index,features,kind,start,end,stress=1):
    i0=int(index.searchsorted(pd.Timestamp(start,tz='UTC')))
    i1=int(index.searchsorted(pd.Timestamp(end,tz='UTC')))
    active={s:[] for s in SYMBOLS}
    cursors={s:0 for s in SYMBOLS}
    cash=START_CASH;pos=None;last_week=None
    trades=[];weeks=set()
    diagnostics=dict(pivots_activated=0,retest_candidates=0,
        rejects_stop_position=0,rejects_rr=0,rejects_lot=0,eligible=0)
    # Entries must be selected chronologically, NOT the best signal found later in the week.
    for i in range(max(300,i0),i1):
        ts=index[i];week=(ts.isocalendar().year,ts.isocalendar().week)
        for sym in SYMBOLS:
            evs=features[sym]['activations'][kind]
            while cursors[sym]<len(evs) and evs[cursors[sym]]['active_i']<=i-1:
                z=evs[cursors[sym]];active[sym].append(z);cursors[sym]+=1
                diagnostics['pivots_activated']+=1
            active[sym]=[x for x in active[sym] if i-x['active_i']<=ZONE_VALIDITY]
        just_exited=False
        if pos is not None:
            f=features[pos['sym']]
            mid=None;reason=None
            if i-pos['i']>=MAX_HOLD and i>pos['i']:
                mid=f['open'][i];reason='time'
            if reason is None:
                if pos['direction']>0:
                    if f['lo'][i]<=pos['stop']:mid=min(f['open'][i],pos['stop']);reason='SL'
                    elif f['hi'][i]>=pos['target']:mid=pos['target'];reason='TP'
                else:
                    if f['hi'][i]>=pos['stop']:mid=max(f['open'][i],pos['stop']);reason='SL'
                    elif f['lo'][i]<=pos['target']:mid=pos['target'];reason='TP'
            if reason is not None:
                pip=f['pip']
                point_usd=10 if pos['sym']!='usdjpy' else 1000/mid
                gross_pips=pos['direction']*(mid-pos['entry'])/pip
                gross=gross_pips*point_usd*pos['lot']
                cost_pips=min_cost_pips(pos['sym'],max(pos['spread_open'],(f['ask'][i]-f['bid'][i])/pip),stress)
                if cost_pips is None:raise ValueError('Bad exit spread')
                costs=point_usd*pos['lot']*cost_pips
                net=gross-costs
                cash+=net
                trades.append(dict(entry_time=pos['time'].isoformat(),exit_time=ts.isoformat(),
                    pair=pos['sym'],mode=kind,direction=pos['direction'],touch_count=pos['touches'],
                    zone_center=pos['zone_center'],zone_width_pips=pos['zone_width']/pip,
                    stop=pos['stop'],target=pos['target'],entry_mid=pos['entry'],exit_mid=mid,
                    lots=pos['lot'],initial_net_rr=pos['rr'],
                    intended_risk_usd=pos['risk'],gross_usd=gross,cost_usd=costs,
                    net_usd=net,balance_usd=cash,exit_reason=reason))
                pos=None;just_exited=True
        if pos is not None or just_exited or last_week==week or cash<100:continue
        # Price-only entry window: London/NY overlap 07:00–19:00 UTC.
        if ts.weekday()>4 or ts.hour<7 or ts.hour>=19:continue
        possibilities=[]
        for sym in SYMBOLS:
            f=features[sym];pip=f['pip'];j=i-1
            observed=(f['ask'][i]-f['bid'][i])/pip
            costp=min_cost_pips(sym,observed,stress)
            if costp is None or costp>12:continue
            # Most recent zones first; duplicate price bands de-duplicated per hour.
            used_centers=[]
            for z in reversed(active[sym]):
                if any(abs(z['center']-c)<=z['width'] for c in used_centers):continue
                used_centers.append(z['center'])
                if not rejection(f,j,z):continue
                diagnostics['retest_candidates']+=1
                side=1 if z['role']=='support' else -1
                entry=f['open'][i]
                buffer=max(1.5*pip,.20*z['width'])
                stop=(z['center']-z['width']-buffer) if side==1 else (z['center']+z['width']+buffer)
                dist=side*(entry-stop)
                if dist<=0 or dist/pip<5 or dist/pip>90:
                    diagnostics['rejects_stop_position']+=1;continue
                # Take profit 2.0 gross risk, require net R:R >=1.5 after observed spread.
                target=entry+side*2*dist
                netrr=(2*dist/pip-costp)/(dist/pip+costp)
                if netrr<MIN_NET_RR:
                    diagnostics['rejects_rr']+=1;continue
                # Veto an opposing confirmed hard level that blocks our 2R target.
                blocked=False
                for opposing in active[sym]:
                    if opposing['role']==z['role']:continue
                    v=opposing['center']
                    if (side==1 and entry<v<target) or (side==-1 and target<v<entry):
                        blocked=True;break
                if blocked:
                    diagnostics['rejects_rr']+=1;continue
                point_usd=10 if sym!='usdjpy' else 1000/entry
                per_lot_risk=(dist/pip+costp)*point_usd
                by_risk=cash*RISK_FRACTION/per_lot_risk
                by_leverage=cash*LEVERAGE_CAP/(100000*(1 if sym=='usdjpy' else entry))
                lot=math.floor((min(by_risk,by_leverage,.5)+1e-9)/.01)*.01
                if lot<.01:
                    diagnostics['rejects_lot']+=1;continue
                risk=per_lot_risk*lot
                if risk>cash*RISK_FRACTION+1e-8:raise AssertionError('Risk exceeds 0.5R')
                diagnostics['eligible']+=1
                possibilities.append(dict(sym=sym,direction=side,score=z['touches'],p=z['last_p'],
                    entry=entry,stop=stop,target=target,lot=round(lot,2),risk=risk,
                    rr=netrr,i=i,time=ts,spread_open=observed,zone_center=z['center'],
                    zone_width=z['width'],touches=z['touches']))
        if not possibilities:continue
        # Same-clock candidates: more distinct reactions, then narrower zone; name tie-break.
        possibilities.sort(key=lambda x:(-x['touches'],x['zone_width'],x['sym']))
        pos=possibilities[0]
        last_week=week
        weeks.add(week)
        # Enforce first-candle stop-first rule right after entering at open.
        f=features[pos['sym']]
        hit_sl=(f['lo'][i]<=pos['stop']) if pos['direction']==1 else (f['hi'][i]>=pos['stop'])
        hit_tp=(f['hi'][i]>=pos['target']) if pos['direction']==1 else (f['lo'][i]<=pos['target'])
        if hit_sl or hit_tp:
            mid=(min(f['open'][i],pos['stop']) if pos['direction']==1 else max(f['open'][i],pos['stop'])) if hit_sl else pos['target']
            per_pip=10 if pos['sym']!='usdjpy' else 1000/mid
            gross=pos['direction']*(mid-pos['entry'])/f['pip']*per_pip*pos['lot']
            fee=(pos['spread_open']*stress+2*SLIPPAGE_PIPS)*per_pip*pos['lot']
            net=gross-fee
            cash+=net
            trades.append(dict(entry_time=ts.isoformat(),exit_time=ts.isoformat(),pair=pos['sym'],mode=kind,
                direction=pos['direction'],touch_count=pos['touches'],zone_center=pos['zone_center'],
                zone_width_pips=pos['zone_width']/f['pip'],stop=pos['stop'],target=pos['target'],
                entry_mid=pos['entry'],exit_mid=mid,lots=pos['lot'],initial_net_rr=pos['rr'],
                intended_risk_usd=pos['risk'],gross_usd=gross,cost_usd=fee,net_usd=net,
                balance_usd=cash,exit_reason='ENTRY_BAR_SL' if hit_sl else 'ENTRY_BAR_TP'))
            pos=None
    if pos is not None:
        # Liquidate remaining open trade rather than hiding unrealized loss at the boundary.
        f=features[pos['sym']];i=i1-1;mid=f['close'][i];pip=f['pip']
        point_usd=10 if pos['sym']!='usdjpy' else 1000/mid
        gross=pos['direction']*(mid-pos['entry'])/pip*point_usd*pos['lot']
        fee=(pos['spread_open']*stress+2*SLIPPAGE_PIPS)*point_usd*pos['lot']
        cash+=gross-fee
        trades.append(dict(entry_time=pos['time'].isoformat(),exit_time=index[i].isoformat(),
            pair=pos['sym'],mode=kind,direction=pos['direction'],touch_count=pos['touches'],
            zone_center=pos['zone_center'],zone_width_pips=pos['zone_width']/pip,
            stop=pos['stop'],target=pos['target'],entry_mid=pos['entry'],exit_mid=mid,
            lots=pos['lot'],initial_net_rr=pos['rr'],intended_risk_usd=pos['risk'],
            gross_usd=gross,cost_usd=fee,net_usd=gross-fee,balance_usd=cash,
            exit_reason='END_PERIOD'))
    return pd.DataFrame(trades),dict(diagnostics,distinct_entry_weeks=len(weeks))

def metrics(df,begin,end):
    n_months=len(pd.period_range(begin[:7],(pd.Timestamp(end)-pd.Timedelta(days=1)).strftime('%Y-%m'),freq='M'))
    if df.empty:return dict(trades=0,net_return_pct=0.,win_rate_pct=None,pf=None,
            max_closed_drawdown_pct=0.,months_ge_5pct=0,months_ge_8pct=0,
            months=n_months,min_rr_net=None,max_realized_loss_usd=0.,cost_usd=0.,pairs={})
    pnl=df.net_usd.to_numpy(float)
    balance=START_CASH+np.cumsum(pnl)
    peak=np.maximum.accumulate(np.r_[START_CASH,balance])[1:]
    profits=pnl[pnl>0].sum();loss=-pnl[pnl<0].sum()
    groups=df.assign(month=pd.to_datetime(df.exit_time,utc=True).dt.strftime('%Y-%m')).groupby('month').net_usd.sum().to_dict()
    now=START_CASH;n5=n8=0
    for month in pd.period_range(begin[:7],(pd.Timestamp(end)-pd.Timedelta(days=1)).strftime('%Y-%m'),freq='M'):
        value=groups.get(str(month),0)
        pct=100*value/now if now>0 else -100
        n5+=pct>=5;n8+=pct>=8
        now+=value
    return dict(trades=int(len(df)),net_return_pct=float((balance[-1]/START_CASH-1)*100),
       ending_cash_usd=float(balance[-1]),win_rate_pct=float(np.mean(pnl>0)*100),
       pf=float(profits/loss) if loss else None,
       max_closed_drawdown_pct=float(np.min((balance/peak-1)*100)),
       months_ge_5pct=int(n5),months_ge_8pct=int(n8),months=n_months,
       min_rr_net=float(df.initial_net_rr.min()),max_realized_loss_usd=float(-pnl.min()),
       max_intended_risk_usd=float(df.intended_risk_usd.max()),
       cost_usd=float(df.cost_usd.sum()),
       pairs={str(k):int(v) for k,v in df.groupby('pair').size().items()})

def main():
    out=Path('price_action_results');out.mkdir(exist_ok=True)
    idx,prices=load_prices()
    if len(idx)<40000:raise ValueError('Missing common historical H1 data')
    feat=build_zone_snapshots(prices)
    results={}
    for mode in SCENARIOS:
        results[mode]={}
        for phase,begin,end in WINDOWS:
            ledger,diag=simulate(idx,feat,mode,begin,end)
            stress,stressdiag=simulate(idx,feat,mode,begin,end,stress=2)
            ledger.to_csv(out/(mode+'_'+phase+'.csv'),index=False)
            stress.to_csv(out/(mode+'_'+phase+'_spread_x2.csv'),index=False)
            results[mode][phase]=dict(base=metrics(ledger,begin,end),
                                       stress=metrics(stress,begin,end),
                                       diagnostics=diag)
    eligible=[]
    for mode in SCENARIOS:
        val=results[mode]['validation']['base']
        if val['trades']>=25 and val['net_return_pct']>0 and (val['pf'] or 0)>=1.1 and val['max_closed_drawdown_pct']>=-15:
            eligible.append(mode)
    winner=sorted(eligible,key=lambda mode:-results[mode]['validation']['base']['net_return_pct'])
    candidate=winner[0] if winner else None
    verdict=False
    if candidate:
        h=results[candidate]['holdout']
        verdict=(h['base']['trades']>=25 and h['base']['net_return_pct']>0 and
                 (h['base']['pf'] or 0)>=1.1 and h['base']['max_closed_drawdown_pct']>=-15 and
                 h['stress']['net_return_pct']>0)
    audit=dict(status='RESEARCH_NOT_LIVE',source='Verified Dukascopy H1 bid/ask, not Exness',
        four_pairs=list(SYMBOLS),common_bars=len(idx),
        no_indicators='No RSI EMA ATR trend volume news or ML in price-action signals',
        pivot_confirmation_bars=PIVOT_RIGHT,required_distinct_pivot_rejections=4,
        min_touch_distance_h1=MIN_TOUCH_SEPARATION,zone_width='max(6 pips,0.75 x trailing 240 bar median range)',
        two_rules=list(SCENARIOS),rule_summary=dict(
            four_same_role='At least four separate confirmed pivot lows (support) OR highs (resistance), with price rejection',
            four_mixed_roles='At least four separate confirmed pivots in same zone, including both support and resistance roles'),
        entered='Next H1 open after confirmed price-only rejection; max one position/week across all pairs',
        risk_per_trade_equity_fraction=RISK_FRACTION,minimum_after_cost_rr=MIN_NET_RR,
        risk_caveat='0.5% risk is an estimated stop+cost budget, not a hard limit against gaps',
        cost='Dukascopy observed bid/ask spread at open/exit proxy plus 0.1 pip slippage each side; no Exness historical swap',
        validation_only_eligible=eligible,selected_on_validation=candidate,
        passed_holdout_gate=verdict,live_orders=0,backtests=results,
        limitations=['H1 intrabar ordering not known, stop-first on dual touches',
                     'No historical swap, macro news, order book or Exness tick spreads',
                     'A support/resistance pivot is known only 3 bars after reversal',
                     'No 5-8% monthly profitability guarantee'])
    (out/'RESULTS_PRICE_ACTION.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    lines=['# Backtest price action: Vùng hỗ trợ/kháng cự cứng ≥4 lần chạm','',
           'Không dùng EMA, RSI, ATR hay volume, không bù dữ liệu giả. Giá Dukascopy H1 Bid/Ask, không phải dữ liệu Exness.',
           'R:R dự kiến sau phí >= 1:1,5, mỗi lệnh rủi ro thiết kế 0,5% vốn (0,5R), tối đa một giao dịch/tuần trên bốn cặp.',
           'Vùng chỉ hình thành sau 4 pivot được xác nhận sau 3 nến, các lần chạm cách nhau tối thiểu 24 nến.',
           '','| Định nghĩa vùng | Giai đoạn | Lệnh | Lãi ròng | PF | Tỷ lệ thắng | DD lệnh đóng | R:R dự kiến thấp nhất | Spread x2 | Tháng >=5% |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mode in SCENARIOS:
        for phase,_,_ in WINDOWS:
            b=results[mode][phase]['base'];stress=results[mode][phase]['stress']
            pf='—' if b['pf'] is None else f"{b['pf']:.2f}"
            wr='—' if b['win_rate_pct'] is None else f"{b['win_rate_pct']:.1f}%"
            rr='—' if b['min_rr_net'] is None else f"{b['min_rr_net']:.3f}"
            lines.append(f"| {mode} | {phase} | {b['trades']} | {b['net_return_pct']:+.2f}% | {pf} | {wr} | {b['max_closed_drawdown_pct']:.2f}% | {rr} | {stress['net_return_pct']:+.2f}% | {b['months_ge_5pct']} |")
    lines+=['',f"**Được chọn trên validation mà không nhìn holdout:** {candidate or 'Không phương án nào đạt điều kiện'}",
            f"**Đạt tiêu chuẩn nghiên cứu cuối:** {'CÓ, cần kiểm tra forward demo tiếp' if verdict else 'KHÔNG'}",
            '', 'Sổ lệnh và diagnostics nằm trong ZIP artifact. Drawdown dựa trên số dư sau khi đóng lệnh, không gồm floating losses.',
            'Không đảm bảo 0,5% giới hạn lỗ trong trường hợp gap hoặc khớp giá xấu. Không có giao dịch tiền thật.']
    (out/'BAO_CAO_VUNG_CUNG.md').write_text('\n'.join(lines))
    print('PRICE ACTION COMPLETE',json.dumps({m:{p:{'trades':v[p]['base']['trades'],'net_pct':round(v[p]['base']['net_return_pct'],3)} for p,_,_ in WINDOWS} for m,v in results.items()}),'winner',candidate,'gate',verdict,flush=True)

if __name__=='__main__':main()
