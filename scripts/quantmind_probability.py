#!/usr/bin/env python3
"""QuantMind FX v1: causal two-brain probability-of-first-touch model.

AI model: frozen histogram boosting model + independent historical-case memory
on 2019-22 only, sigmoid calibration 2023H1, locked validation 2023H2,
HISTORICAL shadow test 2024-25. Does NOT use live ChatGPT API or place orders.
"""
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import brier_score_loss,roc_auc_score
from htf_limit_mid_yearly import historical_prices
from portfolio_research import SYMBOLS,PIPS

OUT=Path("quantmind_results")
CAPITAL=1000.;RISK=.005;MAX_LEVERAGE=5.;HORIZON=24;SLIP_PIPS=.1
CANDIDATE_HOURS=(8,12,16)
TRAIN_END="2023-01-01";CAL_END="2023-07-01";VAL_END="2024-01-01";TEST_END="2026-01-01"
MODEL_PROB_MIN=.40;MEMORY_PROB_MIN=.40;FINAL_PROB_MIN=.48
MEMORY_K=40
FEATURES=("r3","r12","r24","r72","r120","trend24","trend72","trend_ratio",
    "vol_ratio","efficiency24","efficiency72","wick_asym","body_dir",
    "breakout24","breakout72","shock","spread_ratio","market_push",
    "pair_eurusd","pair_gbpusd","pair_audusd","pair_usdjpy",
    "hour8","hour12","hour16")
MODEL_ARGS=dict(max_iter=90,max_leaf_nodes=9,max_depth=3,min_samples_leaf=140,
    learning_rate=.04,l2_regularization=12.,random_state=20261031)
# Research freeze: ONE configuration, no threshold optimization with observed results.

def data_features(index,prices):
    # Cross-pair dollar factor is normalized and calculated only from last
    # fully CLOSED hour; USDJPY foreign-currency performance has opposite sign.
    ret={}
    for sym in SYMBOLS:
        c=prices[sym].close.astype(float)
        ret[sym]=np.log(c).diff(12)
    dollar=(-ret["eurusd"]-ret["gbpusd"]-ret["audusd"]+ret["usdjpy"])/4.
    all_rows=[]
    eligible=np.flatnonzero(index.hour.isin(CANDIDATE_HOURS)&(index.dayofweek<5))
    eligible=eligible[(eligible>480)&(eligible<len(index)-HORIZON-1)]
    for sym in SYMBOLS:
        d=prices[sym];pip=PIPS[sym]
        c=d.close.to_numpy(float)
        o=d.open.to_numpy(float)
        high=d.high.to_numpy(float);low=d.low.to_numpy(float)
        hh=pd.Series(high,index=index)
        ll=pd.Series(low,index=index)
        cp=pd.Series(c,index=index)
        base=hh-ll
        median=base.rolling(48,min_periods=48).median().to_numpy(float)
        prior_spread=d.spread_open_pips.to_numpy(float)
        spread_range=np.maximum(median/pip,1)
        diff=np.r_[np.nan,np.diff(c)]
        path=pd.Series(np.abs(diff),index=index).rolling(24,min_periods=24).sum().to_numpy(float)
        path72=pd.Series(np.abs(diff),index=index).rolling(72,min_periods=72).sum().to_numpy(float)
        def shifted(x,n):return np.r_[np.full(n,np.nan),np.asarray(x)[:-n]]
        avg24=cp.rolling(24,min_periods=24).mean().to_numpy(float)
        avg72=cp.rolling(72,min_periods=72).mean().to_numpy(float)
        rollmed120=base.rolling(120,min_periods=120).median().to_numpy(float)
        max24=hh.rolling(24,min_periods=24).max().to_numpy(float)
        min24=ll.rolling(24,min_periods=24).min().to_numpy(float)
        max72=hh.rolling(72,min_periods=72).max().to_numpy(float)
        min72=ll.rolling(72,min_periods=72).min().to_numpy(float)
        market=dollar.to_numpy(float)
        for i in eligible:
            j=i-1;scale=median[j]
            if not np.isfinite(scale) or scale<=0:continue
            spread=float(prior_spread[i])
            if not np.isfinite(spread) or spread<0 or spread>8:continue
            entry=float(o[i]);riskprice=max(6*pip,1.25*scale)
            stop_pips=riskprice/pip
            if stop_pips>120:continue
            # Use the exactly observed entry OPEN quote spread, not future spread.
            costp=spread+2*SLIP_PIPS
            targetp=2*stop_pips+3*costp
            if not (np.isfinite(path[j]) and np.isfinite(path72[j]) and
                    np.isfinite(rollmed120[j]) and np.isfinite(market[j])):
                continue
            for side in (1,-1):
                z=np.array([
                    side*(c[j]-c[j-3])/scale,
                    side*(c[j]-c[j-12])/scale,
                    side*(c[j]-c[j-24])/scale,
                    side*(c[j]-c[j-72])/scale,
                    side*(c[j]-c[j-120])/scale,
                    side*(c[j]-avg24[j])/scale,
                    side*(c[j]-avg72[j])/scale,
                    side*(avg24[j]-avg72[j])/scale,
                    scale/max(rollmed120[j],1e-12),
                    abs(c[j]-c[j-24])/max(path[j],1e-12),
                    abs(c[j]-c[j-72])/max(path72[j],1e-12),
                    side*(((min(o[j],c[j])-low[j])-(high[j]-max(o[j],c[j])))/scale),
                    side*(c[j]-o[j])/scale,
                    side*(c[j]-max24[j])/scale if side==1 else side*(c[j]-min24[j])/scale,
                    side*(c[j]-max72[j])/scale if side==1 else side*(c[j]-min72[j])/scale,
                    (high[j]-low[j])/max(scale,1e-12),
                    spread/max(spread_range[j],1),
                    side*market[j]/max(scale/c[j],1e-8),
                    float(sym=="eurusd"),float(sym=="gbpusd"),
                    float(sym=="audusd"),float(sym=="usdjpy"),
                    float(index[i].hour==8),float(index[i].hour==12),float(index[i].hour==16)
                ],dtype=np.float64)
                if not np.isfinite(z).all():continue
                # Rare price extremes are clipped using fixed absolute thresholds,
                # NEVER using statistics from test years.
                z=np.clip(z,-20,20)
                res=label_first_touch(d,i,side,entry,stop_pips,targetp,costp,pip)
                all_rows.append(dict(index=i,symbol=sym,side=side,time=index[i],
                     X=z,y=int(res["target_hit"]),net_pips=res["net_pips"],
                     exit_i=res["exit_i"],exit_reason=res["reason"],
                     cost_pips=costp,risk_pips=stop_pips,
                     target_pips=targetp,spread=spread))
    frame=pd.DataFrame(all_rows)
    if len(frame)<12000:raise ValueError("Missing candidate event labels / insufficient H1")
    return frame

def label_first_touch(d,i,side,entry,stopdist,targetdist,costp,pip):
    high=d.high.to_numpy(float);low=d.low.to_numpy(float);op=d.open.to_numpy(float)
    cl=d.close.to_numpy(float)
    stop=entry-side*stopdist*pip;target=entry+side*targetdist*pip
    # Conservative stop-first when both horizontal barriers touched in a bar.
    for k in range(i,i+HORIZON):
        if side==1:
            if low[k]<=stop:
                price=min(op[k],stop)
                return dict(target_hit=False,net_pips=(price-entry)/pip-costp,
                            exit_i=k,reason="stop")
            if high[k]>=target:
                return dict(target_hit=True,net_pips=(target-entry)/pip-costp,
                            exit_i=k,reason="target")
        else:
            if high[k]>=stop:
                price=max(op[k],stop)
                return dict(target_hit=False,net_pips=(entry-price)/pip-costp,
                            exit_i=k,reason="stop")
            if low[k]<=target:
                return dict(target_hit=True,net_pips=(entry-target)/pip-costp,
                            exit_i=k,reason="target")
    k=i+HORIZON-1
    return dict(target_hit=False,net_pips=side*(cl[k]-entry)/pip-costp,
                exit_i=k,reason="time")

def split(frame):
    # Labels cannot cross any split boundary (purge = forward horizon).
    train=frame[(frame.time<TRAIN_END)&(frame.time>="2019-01-01")&
        (frame.exit_i<frame.index.map(lambda _: 10**10))].copy()
    cal=frame[(frame.time>=TRAIN_END)&(frame.time<CAL_END)].copy()
    val=frame[(frame.time>=CAL_END)&(frame.time<VAL_END)].copy()
    test=frame[(frame.time>=VAL_END)&(frame.time<TEST_END)].copy()
    # Actual time of the last future candle per event is used for embargo.
    # Index of exit alone is not sufficient: stop may trigger early, but
    # LABEL EXAMINES an entire potential 24-bar path before first-touch.
    # Purge 24 H1 observations before boundary using global index time.
    for name,part,end in (("train",train,TRAIN_END),("cal",cal,CAL_END),("validation",val,VAL_END),("holdout",test,TEST_END)):
        # Full-horizon boundary purge is applied in main() using timestamps.
        yield name,part

def probabilities(train,cal,others):
    x_train=np.vstack(train.X.values);y=train.y.to_numpy(int)
    x_cal=np.vstack(cal.X.values)
    if len(np.unique(y))<2 or len(np.unique(cal.y))<2:raise ValueError("Missing both classes")
    model=HistGradientBoostingClassifier(**MODEL_ARGS)
    model.fit(x_train,y)
    # Separate Platt-type sigmoid calibration from main training.
    base_cal=np.clip(model.predict_proba(x_cal)[:,1],.00001,.99999)
    logit_cal=np.log(base_cal/(1-base_cal)).reshape(-1,1)
    platt=LogisticRegression(C=1.,random_state=20261031)
    platt.fit(logit_cal,cal.y.to_numpy(int))
    scaler=StandardScaler().fit(x_train)
    knn=NearestNeighbors(n_neighbors=MEMORY_K,algorithm="auto",n_jobs=-1)
    knn.fit(scaler.transform(x_train))
    prior=float(y.mean())
    for name,subset in others:
        if subset.empty:
            yield name,subset.copy();continue
        x=np.vstack(subset.X.values)
        raw=np.clip(model.predict_proba(x)[:,1],.00001,.99999)
        logits=np.log(raw/(1-raw)).reshape(-1,1)
        p_model=platt.predict_proba(logits)[:,1]
        distances,neighbors=knn.kneighbors(scaler.transform(x),return_distance=True)
        wins=y[neighbors].sum(axis=1).astype(float)
        # Beta-style shrinkage avoids 40-neighbor sample probability extremes.
        p_memory=(wins+8*prior)/(MEMORY_K+8)
        combined=.65*p_model+.35*p_memory-.35*np.abs(p_model-p_memory)
        output=subset.copy()
        output["prob_ml"]=p_model
        output["prob_memory"]=p_memory
        output["prob_guarded"]=np.clip(combined,0,1)
        output["expected_net_R"]=3*output["prob_guarded"]-1
        output["analog_wins"]=wins.astype(int)
        yield name,output

def simulation(df,all_prices,spread_factor=1):
    equity=CAPITAL;trades=[];skip_to=None;last_week=None
    # NO hindsight: inspect each timestamp chronologically, then select
    # a pair/direction only among *same timestamp* candidates.
    df=df.sort_values(["time","symbol","side"],kind="stable")
    passing=df[(df.prob_ml>=MODEL_PROB_MIN)&
       (df.prob_memory>=MEMORY_PROB_MIN)&(df.prob_guarded>=FINAL_PROB_MIN)]
    grouped=passing.groupby("time",sort=True)
    for ts,rows in grouped:
        if skip_to is not None and ts<=skip_to:continue
        week=(ts.isocalendar().year,ts.isocalendar().week)
        if last_week==week:continue
        rows=rows.sort_values(["prob_guarded","prob_ml","symbol"],ascending=[False,False,True])
        chosen=None
        for row in rows.itertuples():
            sym=row.symbol;pip=PIPS[sym];px=all_prices[sym]
            spread=float(px.spread_open_pips.iloc[row.index])
            if not np.isfinite(spread) or spread<0 or spread*spread_factor>8:continue
            cost=spread*spread_factor+2*SLIP_PIPS
            stop_dist=row.risk_pips
            tp_dist=2*stop_dist+3*cost
            entry=float(px.open.iloc[row.index])
            pvalue=10 if sym!="usdjpy" else 1000/max(entry,1)
            per_lot=(stop_dist+cost)*pvalue
            lots=math.floor((min(equity*RISK/per_lot,
                    equity*MAX_LEVERAGE/(100000*(1 if sym=="usdjpy" else entry)),.5)+1e-10)/.01)*.01
            if lots<.01:continue
            # Must recalc the triple barrier at spread scenario; do NOT
            # re-use labels from a lower-spread market.
            outcome=label_first_touch(px,row.index,row.side,entry,
                  stop_dist,tp_dist,cost,pip)
            net_usd=outcome["net_pips"]*pvalue*lots
            original_equity=equity;equity+=net_usd
            chosen=dict(time=str(ts),pair=sym,side="BUY" if row.side==1 else "SELL",
                p_ml=float(row.prob_ml),p_memory=float(row.prob_memory),
                p_guarded=float(row.prob_guarded),expected_R=float(row.expected_net_R),
                analog_wins=int(row.analog_wins),risk_budget_usd=float(original_equity*RISK),
                designed_risk_usd=float((stop_dist+cost)*pvalue*lots),
                entry_mid=entry,stop_dist_pips=stop_dist,target_dist_pips=tp_dist,
                total_cost_pips=cost,lot=lots,exit_time=str(px.index[outcome["exit_i"]]),
                reason=outcome["reason"],net_pnl_usd=net_usd,equity_usd=equity)
            skip_to=px.index[outcome["exit_i"]]
            last_week=week
            break
        if chosen:trades.append(chosen)
    return pd.DataFrame(trades)

def metrics(trades):
    if trades.empty:return dict(trades=0,net_pct=0,pf=None,win_pct=None,
         closed_dd_pct=0,max_intended_risk_usd=0,monthly_5=0,months=0)
    pnl=trades.net_pnl_usd.to_numpy(float)
    b=CAPITAL+np.cumsum(pnl)
    peaks=np.maximum.accumulate(np.r_[CAPITAL,b])[1:]
    pos=pnl[pnl>0].sum();neg=-pnl[pnl<0].sum()
    by_month=trades.assign(month=pd.to_datetime(trades.time,utc=True).dt.strftime("%Y-%m"))
    monthly=by_month.groupby("month").net_pnl_usd.sum().to_numpy(float)
    return dict(trades=len(trades),net_pct=(b[-1]/CAPITAL-1)*100,
         end_cash_usd=float(b[-1]),pf=float(pos/neg) if neg else None,
         win_pct=float(np.mean(pnl>0)*100),
         closed_dd_pct=float(np.min((b/peaks-1)*100)),
         max_intended_risk_usd=float(trades.designed_risk_usd.max()),
         mean_guarded_probability=float(trades.p_guarded.mean()),
         monthly_5=int((monthly>=CAPITAL*.05).sum()),
         months=int(len(monthly)))

def predictive_quality(part,training_prior):
    if part.empty:return None
    y=part.y.to_numpy(int)
    p=part.prob_guarded.to_numpy(float)
    baseline=float(training_prior)  # fixed in 2019-22, NOT oracle test mean
    brier=brier_score_loss(y,p)
    return dict(observations=len(part),actual_win_rate=float(y.mean()),
      brier=float(brier),constant_prior_brier=float(brier_score_loss(y,np.full(len(y),baseline))),
      auc=float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
      mean_predicted_probability=float(p.mean()),
      opportunities_passing=int(((part.prob_ml>=MODEL_PROB_MIN)&
      (part.prob_memory>=MEMORY_PROB_MIN)&(part.prob_guarded>=FINAL_PROB_MIN)).sum()))

def main():
    OUT.mkdir(exist_ok=True)
    index,prices=historical_prices()
    # Every array aligned strictly to a jointly observed real H1 timestamp.
    data=data_features(index,prices)
    # purge all possible 24-bar future paths across split boundaries
    last_index=data["index"].to_numpy(int)+HORIZON-1
    endtime=index[last_index]
    data["full_horizon_end"]=endtime
    components={}
    for name,start,end in (("train","2019-01-01",TRAIN_END),
                           ("cal",TRAIN_END,CAL_END),
                           ("validation",CAL_END,VAL_END),
                           ("holdout",VAL_END,TEST_END)):
        part=data[(data.time>=start)&(data.time<end)&
                  (data.full_horizon_end<pd.Timestamp(end,tz="UTC"))].copy()
        if len(part)<1000:raise ValueError("Insufficient true observations in "+name)
        components[name]=part
    outputs=dict(probabilities(components["train"],components["cal"],
      [(k,components[k]) for k in ("cal","validation","holdout")]))
    output={}
    for name,part in outputs.items():
        quality=predictive_quality(part,float(components["train"].y.mean()))
        trades=simulation(part,prices)
        stressed=simulation(part,prices,spread_factor=2)
        if not trades.empty:
            if (trades.designed_risk_usd>trades.risk_budget_usd+1e-6).any():
                raise AssertionError("Risk budget violation")
            if (trades.p_guarded<FINAL_PROB_MIN-1e-10).any():
                raise AssertionError("Selected low confidence candidate")
            if pd.to_datetime(trades.time,utc=True).dt.strftime("%G-%V").duplicated().any():
                raise AssertionError("More than one entry/week")
        trades.to_csv(OUT/(name+"_orders.csv"),index=False)
        output[name]=dict(quality=quality,main=metrics(trades),
            spread_x2=metrics(stressed))
        print("QUANTMIND",name,"events",len(part),"trades",len(trades),
           "net_pct",round(metrics(trades)["net_pct"],4),flush=True)
    v=output["validation"];h=output["holdout"]
    validation_go=(v["main"]["trades"]>=8 and v["main"]["net_pct"]>0 and
         (v["main"]["pf"] or 0)>1.05 and
         v["quality"]["brier"]<v["quality"]["constant_prior_brier"])
    holdout_go=(validation_go and h["main"]["trades"]>=30 and h["main"]["net_pct"]>0 and
         (h["main"]["pf"] or 0)>1.1 and h["main"]["closed_dd_pct"]>=-15
         and h["spread_x2"]["net_pct"]>0)
    result=dict(status="HISTORICAL_RESEARCH_NOT_LIVE",
      algorithms="Histogram gradient boosting + held-out sigmoid calibration + kNN case memory; probability-disagreement veto",
      model_arguments=MODEL_ARGS,training_counts={k:len(v) for k,v in components.items()},
      periods=dict(train="2019-2022",calibration="2023H1",validation="2023H2",holdout="2024-2025"),
      risk_per_trade_equity=.005,risk_reward_after_costs=2.0,
      horizon_h1_bars=HORIZON,no_more_than_one_entry_per_week=True,
      probability_thresholds=dict(ml=MODEL_PROB_MIN,memory=MEMORY_PROB_MIN,guarded=FINAL_PROB_MIN),
      actual_data="Verified historical Dukascopy H1 Bid/Ask (mid-OHLC approximates intrabar fills)",
      label_first_touch_stop_first_if_ambiguous=True,
      market_data_n= len(index),symbols=list(SYMBOLS),features=list(FEATURES),
      output=output,validation_go=validation_go,holdout_go=holdout_go,
      verdict="NO_GO" if not holdout_go else "PAPER_ONLY_MORE_TESTS_NEEDED",
      live_orders=0,caveats=["No real Exness ticks/swap/macro calendar/latency",
         "No live ChatGPT model called on individual historic events; code implements researched deterministic probability policy",
         "No untouched domain-level holdout: 2024-25 were studied with OTHER strategies earlier",
         "Simulated signal/limit/outcomes use H1 mid-OHLC; cannot know true intrabar quote sequence",
         "Drawdown only after closed trades; gaps can exceed intended 0.5% stop risk"])
    (OUT/"QUANTMIND_RESULTS.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    lines=["# QuantMind FX v1 — xác suất TP 2R trước SL 1R với tự phản biện",
      "", "Mô hình học máy + trí nhớ 40 tình huống thị trường gần nhất trong bộ huấn luyện; không dùng tín hiệu từ RSI/Engulfing như điều kiện bắt buộc.",
      "2019-22 train, 2023H1 hiệu chỉnh, 2023H2 kiểm định/điều kiện NO-GO, 2024-25 báo cáo kỳ sau. Chưa có hồi kiểm thử trên tick Exness.",
      "", "| Giai đoạn | Quan sát dự báo | Brier | Baseline Brier | AUC | Số giao dịch | Lợi nhuận sau phí | Profit Factor | DD | Spread x2 |",
      "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for k in ("cal","validation","holdout"):
        row=output[k];q=row["quality"];p=row["main"];sp=row["spread_x2"]
        fmt=lambda v:"—" if v is None else f"{v:.3f}"
        lines.append(f"| {k} | {q['observations']} | {q['brier']:.4f} | {q['constant_prior_brier']:.4f} | {fmt(q['auc'])} | {p['trades']} | {p['net_pct']:+.2f}% | {fmt(p['pf'])} | {p['closed_dd_pct']:.2f}% | {sp['net_pct']:+.2f}% |")
    lines+=["",f"Validation gate: **{validation_go}**. Holdout gate: **{holdout_go}**.",
      "**Kết luận:** "+result["verdict"]+". Không có hệ thống tự giao dịch thật; AI hiện tham gia thiết kế, mã đánh giá mọi snapshot lịch sử và đưa ra xác suất, nhưng không gọi ChatGPT API cho từng nến.",
      "Brier nhỏ hơn tốt hơn; AUC≈0,5 giống xếp hạng ngẫu nhiên. Phí swap chưa tính. Nghiên cứu cũ đã nhìn 2024–25, do đó báo cáo holdout chỉ mang tính thời gian ngoài mẫu cho mô hình này, không phải holdout nguyên vẹn cho toàn dự án.",
      "Nhật ký từng giao dịch, xác suất từng nguồn và lịch sử học được xuất kèm JSON/CSV."]
    (OUT/"BAO_CAO_QUANTMIND.md").write_text("\n".join(lines))
    print("QUANTMIND COMPLETE",json.dumps({k:[v["main"]["trades"],round(v["main"]["net_pct"],3)] for k,v in output.items()}),
      "validation_go",validation_go,"holdout_go",holdout_go,flush=True)

if __name__=="__main__":main()
