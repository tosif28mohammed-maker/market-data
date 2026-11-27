import pandas as pd, numpy as np
ALL=pd.read_pickle('events.pkl'); M=pd.read_csv('offset_events.csv.gz',parse_dates=['d'])
M['era']=pd.cut(M.d.dt.year,[2004,2012,2020,2026],labels=['05-12','13-20','21-26'])
print('baseline (all offsets 60-600) d0_20 by era:', M.groupby('era',observed=True).d0_20.mean().round(2).to_dict(), 'pre', M.groupby('era',observed=True)['pre-10_-1'].mean().round(2).to_dict())
# 2022+ anchor 90d: compare pre-window vs near offsets in same era
for K in (30,90,180):
    R=ALL[K]; x=R[R.d>='2022-06-01']
    near=M[(M.d>='2022-06-01')&(M.K.isin([K-20,K+20,K+40]) if K>30 else M.K.isin([60,80]))]
    print(f'K{K} 2022+ N{len(x)} pre {x["pre-10_-1"].mean():.2f} d0_5 {x.d0_5.mean():.2f} d0_20 {x.d0_20.mean():.2f} | near offsets N{len(near)} pre {near["pre-10_-1"].mean():.2f} d0_5 {near.d0_5.mean():.2f} d0_20 {near.d0_20.mean():.2f}')
# shuffle check K=90 2022+ pre: draw same N from near-offset pool
rng=np.random.default_rng(1)
x=ALL[90]; x=x[x.d>='2022-06-01']; pool=M[(M.d>='2022-06-01')&(M.K.between(60,200))]['pre-10_-1'].dropna().values
sims=[rng.choice(pool,len(x)).mean() for _ in range(3000)]
print('K90 pre shuffle p(sim<=obs)=',np.mean(np.array(sims)<=x['pre-10_-1'].mean()).round(3))
print('\n--- scenarios (all eras) d0_20 by run-up since listing (excess), volume on expiry, Nifty regime')
for K in (30,90,180,365,540):
    R=ALL[K].dropna(subset=['d0_20']).copy()
    R['run']=pd.qcut(R.runup,3,labels=['losers','mid','winners'])
    R['vol']=np.where(R.volx>=2,'vol>=2x','vol<2x')
    a=R.groupby('run',observed=True).d0_20.agg(['count','mean']).round(2).to_dict('index')
    b=R.groupby('vol').d0_20.agg(['count','mean']).round(2).to_dict('index')
    c=R.groupby('bull').d0_20.agg(['count','mean']).round(2).to_dict('index')
    print(f'K{K} run {a}\n     vol {b}\n     bull {c}')
# same split on baseline pool for comparison
M2=M.dropna(subset=['d0_20','runup']).copy(); M2['run']=pd.qcut(M2.runup,3,labels=['losers','mid','winners'])
print('baseline run', M2.groupby('run',observed=True).d0_20.mean().round(2).to_dict(), ' vol>=2x', M2[M2.volx>=2].d0_20.mean().round(2), 'N',(M2.volx>=2).sum(), '<2x', M2[M2.volx<2].d0_20.mean().round(2))
# practical: cumulative excess of a new listing from day 20 to day 250 (survivors) by era
print('\n hold IPO from listing+30d for 1 year: mean excess per K=30 d0..d250?')
