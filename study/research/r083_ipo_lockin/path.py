import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
P=load(); a=P['a']; r1=a.pct_change(fill_method=None); r1=r1.where(r1.abs()<0.4); mkt=r1.mean(axis=1)
ex=np.log1p(r1.fillna(0)).cumsum().sub(np.log1p(mkt.fillna(0)).cumsum(),axis=0); idx=a.index
first=a.apply(lambda s: s.first_valid_index()); first=first[first>=pd.Timestamp('2005-01-01')]
def path(K, lo=-20, hi=10, since=None, until=None):
    rows={}
    for s,f in first.items():
        j=idx.searchsorted(f+pd.Timedelta(days=K))
        if j+hi>=len(idx) or j+lo<1: continue
        d=idx[j]
        if since and d<pd.Timestamp(since): continue
        if until and d>pd.Timestamp(until): continue
        base=ex[s].iloc[j+lo-1]
        if pd.isna(a[s].iloc[j+lo-1]): continue
        rows[(s,d)]=[(ex[s].iloc[j+k]-base)*100 for k in range(lo,hi+1)]
    D=pd.DataFrame(rows,index=range(lo,hi+1)).T
    return D
for lab,since,until in [('anchor-90 rule era (listing>=Apr22)','2022-07-01',None),('before rule 2013-22','2013-01-01','2022-06-30'),('2005-12','2005-01-01','2012-12-31')]:
    D=path(90,since=since,until=until)
    print(lab,'N',len(D),'cum excess from day -20:', D.mean().iloc[[0,5,10,15,19,20,21,25,30]].round(2).to_dict())
# per year consistency for pre window [-10,-1] at K=90
D=path(90,lo=-10,hi=5)
D['yr']=[d.year for s,d in D.index]
pre=D[-1]; post=D[5]-D[-1]
g=pd.DataFrame({'pre':pre,'post5':post,'yr':D.yr}).groupby('yr').agg(['count','mean']).round(2)
print(g.loc[2013:].to_string())
# 2022+ K offsets 70..110 pre windows: where is the minimum? (does dip align to 90?)
for K in (60,70,80,85,90,95,100,110,120):
    D=path(K,lo=-10,hi=0,since='2022-07-01'); print('K',K,'pre10',round(D[-1].mean(),2),'N',len(D))
