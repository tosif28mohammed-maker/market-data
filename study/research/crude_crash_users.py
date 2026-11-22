"""r051 (22 Nov 2026) value chain (A) input cost, reverse of r042: Brent CRASH -> crude users.
RULES WRITTEN BEFORE RESULTS: event E20 = Brent 20-day return <= -15% (first in 40 days); E5 = Brent 5-day <= -8% (first in 28 days).
start = next Indian close. Groups EW: OMC (BPCL,HINDPETRO,IOC), Aviation (INDIGO), Paints (ASIANPAINT,BERGEPAINT,KANSAINER,INDIGOPNTS),
Tyres (MRF,APOLLOTYRE,CEATLTD,JKTYRE,BALKRISIND), Upstream (ONGC,OIL). Excess vs EW all stocks (ni_common panel); 5/20/60d; eras 2004-12/2013-26;
chance = 600 random-date sets; scenario: crash with world risk-off (S&P 20d <= -5%) vs calm.
Live case: Brent 28 Oct -> 20 Nov 2026 = -22%.
"""
import sys, numpy as np, pandas as pd
R0='/home/claude/market-data'; sys.path.insert(0,f'{R0}/study')
from ni_common import load
A=load()['a']; R=A.pct_change(fill_method=None); R=R.where(R.abs()<0.4); ew=R.mean(axis=1); ix=R.index
g=lambda f: (lambda s: s[~s.index.duplicated()].dropna())(pd.read_csv(f'{R0}/data/global/{f}.csv',index_col='date',parse_dates=True).close)
br=g('CMD_BRENT'); spx=g('US_SP500'); s20=spx/spx.shift(20)-1
G={'OMC':['BPCL','HINDPETRO','IOC'],'Aviation':['INDIGO'],'Paints':['ASIANPAINT','BERGEPAINT','KANSAINER','INDIGOPNTS'],'Tyres':['MRF','APOLLOTYRE','CEATLTD','JKTYRE','BALKRISIND'],'Upstream':['ONGC','OIL']}
G={k:[s for s in v if s in R.columns] for k,v in G.items()}; print(G)
LG={k:np.log1p(R[v].mean(axis=1).fillna(0)).cumsum() for k,v in G.items()}; LE=np.log1p(ew.fillna(0)).cumsum()
def events(ret,th,gap):
    ev=[];last=None
    for d in ret.index:
        if ret[d]<=th and (last is None or (d-last).days>gap): ev.append(d); last=d
    return [(d,ix[ix>d][0]) for d in ev if d>=pd.Timestamp('2004-01-01') and len(ix[ix>d])>60]
def fx(i,h,k): return float(np.expm1((LG[k].iloc[i+h]-LG[k].iloc[i])-(LE.iloc[i+h]-LE.iloc[i]))*100)
rng=np.random.default_rng(51); pool=np.arange(ix.get_loc(ix[ix>='2004-02-01'][0]),len(ix)-61)
for lab,ret,th,gap in [('E20',br/br.shift(20)-1,-0.15,40),('E5',br/br.shift(5)-1,-0.08,28)]:
    ev=events(ret,th,gap); rows=[]
    for d0,d in ev:
        i=ix.get_loc(d); row={'date':d,'riskoff':bool(s20.asof(d0)<=-0.05)}
        for k in G:
            row[k+'_d0']=float(np.expm1((LG[k].iloc[i]-LG[k].iloc[i-1])-(LE.iloc[i]-LE.iloc[i-1]))*100)
            for h in (5,20,60): row[f'{k}_{h}']=fx(i,h,k)
        rows.append(row)
    E=pd.DataFrame(rows).set_index('date'); E['era']=np.where(E.index<'2013','2004-12','2013-26')
    print(f'\n==== {lab} events {len(E)} (2004-12 {sum(E.era=="2004-12")}, 2013-26 {sum(E.era=="2013-26")}), riskoff {E.riskoff.sum()}')
    cols=[c for c in E.columns if c not in('era','riskoff')]
    print(E.groupby('era')[cols].mean().round(2).T.assign(riskoff=E[E.riskoff][cols].mean().round(2),calm=E[~E.riskoff][cols].mean().round(2)).to_string())
    sims=[]
    for s in range(600):
        ii=rng.choice(pool,len(E),replace=False); sims.append({f'{k}_{h}':np.mean([fx(i,h,k) for i in ii]) for k in G for h in (5,20,60)})
    sims=pd.DataFrame(sims)
    for c in sims.columns:
        o=E[c].mean(); p=np.mean(sims[c]<=o) if o<0 else np.mean(sims[c]>=o)
        print(f'{c:14s} obs {o:+.2f} chance {sims[c].mean():+.2f} p {p:.3f} win {np.mean(E[c]>0)*100:.0f}%')
    E.to_csv(f'{R0}/study/research/crude_crash_{lab}.csv'); print('last events', [str(x.date()) for x in E.index[-5:]])
