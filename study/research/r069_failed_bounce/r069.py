"""r069 (25 Nov 2026) Failed bounce in a deep fall: what came next for gold/silver?
Rule written before looking: Zone = close >=15% (gold) / >=30% (silver) below 252-day high.
Event A: in zone, within the last 10 days the close rose >= +3.5% gold / +5% silver above the
then 20-day low close (a bounce), and today closes at a NEW 20-day closing low (bounce failed).
One event per 15 days. Chance C = all zone days. Forward 20/60 days; worst further fall in 60d.
Eras 2000-14 vs 2015-26; USD, INR (x USDINR), KWD (x USDKWD).
PASS (long) = A beats C by >=+2% at 60d with p<=0.10 in both eras and INR agrees. Same for SHORT (A worse by 2%).
"""
import pandas as pd, numpy as np, sys
from scipy import stats
G='data/global/'
def rd(f):
    d=pd.read_csv(G+f+'.csv',parse_dates=[0],index_col=0).iloc[:,3]; return d[~d.index.duplicated()].dropna()
inr=rd('FX_USDINR'); kwd=rd('FX_USDKWD')
out=[]
for m,zone,bnc in [('GOLD',.15,.035),('SILVER',.30,.05)]:
    usd=rd('CMD_'+m)
    for ccy in ['USD','INR','KWD']:
        s=usd if ccy=='USD' else (usd*(inr if ccy=='INR' else kwd)).dropna()
        s=s[s>0]
        hi=s.rolling(252,min_periods=200).max(); dd=1-s/hi; inzone=dd>=zone
        low20=s.rolling(20).min()
        newlow=s<=s.shift(1).rolling(19).min()
        bounce=(s/low20.shift(0)-1).rolling(10).max().shift(1)>=bnc
        ev=inzone&newlow&bounce
        f20=s.shift(-20)/s-1; f60=s.shift(-60)/s-1
        mn60=s[::-1].rolling(60,min_periods=1).min()[::-1].shift(-1)/s-1
        last=-999; idx=[]
        for i,(t,v) in enumerate(ev.items()):
            if v and i-last>=15: idx.append(t); last=i
        idx=pd.DatetimeIndex(idx)
        for era,a,b in [('2000-14','2000','2014'),('2015-26','2015','2026')]:
            A=idx[(idx>=a)&(idx<=b+'-12-31')]
            C=inzone[a:b][inzone[a:b]].index
            for h,fr in [(20,f20),(60,f60)]:
                xa=fr.reindex(A).dropna(); xc=fr.reindex(C).dropna()
                p=stats.ttest_ind(xa,xc,equal_var=False).pvalue if len(xa)>2 else np.nan
                out.append(dict(m=m,ccy=ccy,era=era,h=h,nA=len(xa),A=round(xa.mean()*100,1) if len(xa) else np.nan,upA=round((xa>0).mean()*100) if len(xa) else np.nan,C=round(xc.mean()*100,1),p=round(p,2) if p==p else np.nan,worst60=round(mn60.reindex(A).median()*100,1) if len(A) else np.nan))
        if ccy=='USD': print(m,'events',list(idx.strftime('%Y-%m-%d')))
r=pd.DataFrame(out); print(r.to_string())
