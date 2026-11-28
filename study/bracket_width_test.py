"""DHAN-06b (28 Nov): 'bracket width' (R1/S1 pivots + PDH/PDL) narrow -> trend day? wide -> sideways?
Bracket upper = max(R1, PDH), lower = min(S1, PDL) from previous day. Width % of prev close.
Outcome today: trendness = |close-open|/(high-low); range%; 'trend day' = trendness>=0.6.
Bucket = width percentile vs past 250 days (no look-ahead). Eras. Shuffle control = buckets compared to all days."""
import pandas as pd, numpy as np, sys
for sym in ["NIFTY","BANKNIFTY"]:
    d=pd.read_csv(f"data/{sym}.csv",parse_dates=["date"]).dropna(subset=["open","high","low","close"])
    d=d[(d.high>d.low)&(d.open>0)].reset_index(drop=True)
    H,L,C=d.high.shift(),d.low.shift(),d.close.shift()
    P=(H+L+C)/3; R1=2*P-L; S1=2*P-H
    up=np.maximum(R1,H); lo=np.minimum(S1,L)
    d["w"]=(up-lo)/C*100
    d["wp"]=d.w.rolling(250,min_periods=120).apply(lambda x:(x[:-1]<x[-1]).mean() if len(x)>1 else np.nan,raw=True)
    d["trend"]=(d.close-d.open).abs()/(d.high-d.low)
    d["rng"]=(d.high-d.low)/C*100
    d["gap"]=(d.open/C-1).abs()*100
    d=d.dropna(subset=["wp"]); d=d[d.gap<1]   # video: bade gap din chhodo
    d["b"]=pd.cut(d.wp,[-.01,.2,.4,.6,.8,1.0],labels=["1 narrow","2","3","4","5 wide"])
    d["era"]=pd.cut(d.date.dt.year,[2006,2012,2020,2023,2026],labels=["2007-12","2013-20","2021-23","2024-26"])
    print(f"\n=== {sym}  days={len(d)}  base trend-day%={(d.trend>=.6).mean()*100:.1f}  base range%={d.rng.mean():.2f}")
    t=d.groupby(["era","b"],observed=True).agg(n=("trend","size"),trend_day_pct=("trend",lambda x:(x>=.6).mean()*100),
         avg_trend=("trend","mean"),range_pct=("rng","mean"),range_vs_prevwidth=("rng",lambda x:np.nan)).drop(columns="range_vs_prevwidth")
    print(t.round(2).to_string())
