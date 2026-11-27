# side test: नई listings की भीड़ (पिछले 3 महीने की गिनती, panel में) -> EW बाज़ार अगले 3/6 महीने (supply overhang?)
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
a=load()['a']; r1=a.pct_change(fill_method=None).where(lambda x:x.abs()<0.4); mkt=r1.mean(axis=1)
N=pd.read_csv('/home/claude/market-data/data/NIFTY.csv',parse_dates=['date']).set_index('date').close
first=a.apply(lambda s:s.first_valid_index()); first=first[first>='2005-01-01']
cnt=first.dt.to_period('M').value_counts().sort_index(); m=pd.period_range('2005-01','2026-10',freq='M'); cnt=cnt.reindex(m,fill_value=0)
c3=cnt.rolling(3).sum()
lm=np.log1p(mkt.fillna(0)).cumsum(); lmm=lm.resample('ME').last(); lmm.index=lmm.index.to_period('M')
Nm=N.resample('ME').last(); Nm.index=Nm.index.to_period('M')
df=pd.DataFrame({'c3':c3,'f3':(lmm.shift(-3)-lmm)*100,'f6':(lmm.shift(-6)-lmm)*100,'n3':(Nm.shift(-3)/Nm-1)*100,'n6':(Nm.shift(-6)/Nm-1)*100}).dropna()
df['q']=pd.qcut(df.c3.rank(method='first'),3,labels=['कम','बीच','भीड़'])
print(df.groupby('q',observed=True)[['c3','f3','f6','n3','n6']].mean().round(2))
for era in [('2005','2014'),('2015','2026')]:
    x=df[(df.index.year>=int(era[0]))&(df.index.year<=int(era[1]))].copy(); x['q']=pd.qcut(x.c3.rank(method='first'),3,labels=['कम','बीच','भीड़'])
    print(era, x.groupby('q',observed=True)[['n6','f6']].mean().round(2).to_dict())
print('last c3', c3.tail(4).to_dict())
