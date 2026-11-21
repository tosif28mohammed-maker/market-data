import pandas as pd,numpy as np
exec(open('r039_futexp.py').read().split("print('== main ==')")[0])
df=pd.read_csv('r039_events.csv',index_col=0,parse_dates=True)
r1=c.pct_change(); base=pd.DataFrame({'r1':r1,'nx':nxt}).dropna(); base=base[base.index>='2019-02-14']
dn=base[base.r1<-0.005]; ex=dn[dn.index.isin(df.index)]
sims=[dn.nx.sample(len(ex),random_state=i).mean() for i in range(5000)]
print('expiry-down n',len(ex),'mean %.3f win %.1f p %.4f'%(ex.nx.mean()*100,(ex.nx>0).mean()*100,np.mean(np.array(sims)>=ex.nx.mean())))
print('per year');print((ex.nx.groupby(ex.index.year).agg(['mean','count'])).assign(mean=lambda x:(x['mean']*100).round(2)).T)
# rupee-ish P&L per lot at 65 & Nifty 25000, cost 100
pl=ex.nx*25800*65-100; print('per trade Rs %.0f; avg win %.0f avg loss %.0f; win%% %.1f'%(pl.mean(),pl[pl>0].mean(),pl[pl<0].mean(),(pl>0).mean()*100))
# overnight vs intraday for this subset
print('ovn %.3f intr %.3f'%(ovn.reindex(ex.index).mean()*100,intr.reindex(ex.index).mean()*100))
# Tuesday era subset
t=ex[ex.index>='2025-09-01']; print('Tuesday era n',len(t),'mean %.3f'%(t.nx.mean()*100))
# non-down expiry days (what paper rule would skip)
nd=df[~df.index.isin(ex.index)]; print('skipped expiry days n',len(nd),'mean %.3f'%(nd.r.mean()*100))
