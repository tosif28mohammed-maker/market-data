import pandas as pd,numpy as np
exec(open('r040_fed.py').read().split("print('Market (EW all)")[0])
win=[('2004-01-01','2006-12-31'),('2015-06-01','2019-06-30'),('2021-09-01','2024-01-31')]
pool=ix[np.any([(ix>=a)&(ix<=b) for a,b in win],axis=0)]
obs=X[key].mean(); rng=np.random.default_rng(3); sims=[]
# sample per cycle same count, from its own window (regime-matched)
cnt=X.groupby('cycle').size()
wins=dict(zip(['2004-06','2015-18','2022-23'],win))
for k in range(800):
    ds=[]
    for cy,n in cnt.items():
        a,b=wins[cy]; pl=ix[(ix>=a)&(ix<=b)]; ds+=list(pl[rng.choice(len(pl),n,replace=False)])
    sims.append(pd.DataFrame({d:fwd(d,20)[0] for d in ds}).T[key].mean())
sims=pd.DataFrame(sims)
pv={k:(np.mean(sims[k]>=obs[k]) if obs[k]>0 else np.mean(sims[k]<=obs[k])) for k in key}
print(pd.DataFrame({'obs':obs.round(2),'regime_mean':sims.mean().round(2),'p_regime':pd.Series(pv).round(3)}))
# Capital goods: per-hike win rate and by first vs later hikes; also 5d
cg=X['Capital Goods']; print('CG win%% %.0f; first 3 hikes of each cycle %.2f, rest %.2f'%((cg>0).mean()*100, cg.groupby(X.cycle).head(3).mean(), cg.drop(cg.groupby(X.cycle).head(3).index).mean()))
X5=pd.DataFrame({d:fwd(d,5)[0] for d in H}).T
print('5d excess CG %.2f IT %.2f HC %.2f'%(X5['Capital Goods'].mean(),X5['Information Technology'].mean(),X5['Healthcare'].mean()))
