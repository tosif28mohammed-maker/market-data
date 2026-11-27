import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
a=load()['a']; N=pd.read_csv('/home/claude/market-data/data/NIFTY.csv',parse_dates=['date']).set_index('date').close
it=[s for s in ['TCS','INFY','HCLTECH','WIPRO','TECHM','LTIM'] if s in a]
r=a[it].pct_change(fill_method=None).where(lambda x:x.abs()<0.4).mean(axis=1)
nr=N.pct_change().reindex(r.index)
ex=(np.log1p(r.fillna(0))-np.log1p(nr.fillna(0))).cumsum()
d1=ex.diff()*100; e126=(ex-ex.shift(126))*100
rows=[];last=None
for d in d1.index[(d1>=2.5)&(e126<=-10)]:
    if last is not None and (d-last).days<30: continue
    last=d; i=ex.index.get_loc(d)
    rows.append({'d':d.date(),'bd':round(d1[d],2),'lag':round(e126[d],1),**{h:round((ex.iloc[i+h]-ex.iloc[i])*100,2) if i+h<len(ex) else np.nan for h in (5,20,60)}})
R=pd.DataFrame(rows); print(it); print(R.to_string()); print(R[[5,20,60]].mean().round(2).to_dict())
base=[]; 
lagd=e126[e126<=-10].index
print('lag baseline 20d', round(np.nanmean([(ex.shift(-20)-ex)[d]*100 for d in lagd]),2), '60d', round(np.nanmean([(ex.shift(-60)-ex)[d]*100 for d in lagd]),2))
print('last', d1.index[-1].date(), round(d1.iloc[-2],2), round(d1.iloc[-1],2), 'lag126', round(e126.iloc[-1],1))
