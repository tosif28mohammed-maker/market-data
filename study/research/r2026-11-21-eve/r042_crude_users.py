# r042 value chain (A) input cost: Brent spike -> crude USERS. Rule fixed first:
# event = Brent 5-day return >= +8% (first in 20 days); India start = next Indian close after the US/London day.
# Groups: OMC (BPCL,HINDPETRO,IOC), Aviation (INDIGO), Paints (ASIANPAINT,BERGEPAINT,KANSAINER,INDIGOPNTS), Tyres (MRF,APOLLOTYRE,CEATLTD,JKTYRE,BALKRISIND),
# Upstream (ONGC,OIL) as contrast. Excess vs EW all u500, 5d/20d/60d; eras; chance = random dates.
import pandas as pd,numpy as np
A=pd.read_pickle('/home/claude/research/panel_adj.pkl'); A=A.where(A>0)
R=A.pct_change(fill_method=None); R=R.where(R.abs()<0.4); ew=R.mean(axis=1); ix=R.index
br=pd.read_csv('/home/claude/market-data/data/global/CMD_BRENT.csv',index_col='date',parse_dates=True).close; br=br[~br.index.duplicated()].dropna()
b5=br/br.shift(5)-1
G={'OMC':['BPCL','HINDPETRO','IOC'],'Aviation':['INDIGO'],'Paints':['ASIANPAINT','BERGEPAINT','KANSAINER','INDIGOPNTS'],'Tyres':['MRF','APOLLOTYRE','CEATLTD','JKTYRE','BALKRISIND'],'Upstream':['ONGC','OIL']}
G={k:[s for s in v if s in R.columns] for k,v in G.items()}; print(G)
LG={k:np.log1p(R[v].mean(axis=1).fillna(0)).cumsum() for k,v in G.items()}; LE=np.log1p(ew.fillna(0)).cumsum()
ev=[];last=None
for d in b5.index:
    if b5[d]>=0.08 and (last is None or (d-last).days>28):
        ev.append(d); last=d
ev=[ix[ix>d][0] for d in ev if d>=pd.Timestamp('2004-01-01') and len(ix[ix>d])>60]
def fx(d,h,k):
    i=ix.get_loc(d); return float(np.expm1((LG[k].iloc[i+h]-LG[k].iloc[i])-(LE.iloc[i+h]-LE.iloc[i]))*100)
# day0 reaction too (close before -> start close)
out=[]
for d in ev:
    i=ix.get_loc(d)
    row={'date':d}
    for k in G:
        row[k+'_d0']=float(np.expm1((LG[k].iloc[i]-LG[k].iloc[i-1])-(LE.iloc[i]-LE.iloc[i-1]))*100)
        for h in (5,20,60): row[f'{k}_{h}']=fx(d,h,k)
    out.append(row)
E=pd.DataFrame(out).set_index('date'); E['era']=np.where(E.index<'2013','2004-12','2013-26')
print('events',len(E)); cols=[c for c in E.columns if c!='era']
print(E.groupby('era')[cols].mean().round(2).T)
rng=np.random.default_rng(2); pool=ix[(ix>='2004-02-01')&(ix<ix[-61])]
sims=[]
for s in range(600):
    ds=pool[rng.choice(len(pool),len(E),replace=False)]
    sims.append({f'{k}_{h}':np.mean([fx(d,h,k) for d in ds]) for k in G for h in (5,20,60)})
sims=pd.DataFrame(sims)
for c in sims.columns:
    o=E[c].mean(); p=np.mean(sims[c]<=o) if o<0 else np.mean(sims[c]>=o)
    print(f'{c:14s} obs {o:+.2f}  chance-mean {sims[c].mean():+.2f}  p {p:.3f}  win {np.mean(E[c]>0)*100:.0f}%')
E.to_csv('r042_events.csv')
