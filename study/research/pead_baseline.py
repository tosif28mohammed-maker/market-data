"""r050 extra: baseline (random stock-days, same windows, next-open entry) + combined scenario for PEAD events; chance by shuffling dates."""
import sys, numpy as np, pandas as pd
R='/home/claude/market-data'; sys.path.insert(0,f'{R}/study')
from ni_common import load
P=load(); A,O=P['a'],P['o']
ret=A.pct_change(fill_method=None); ret=ret.where(ret.abs()<0.4); mk=(1+ret.mean(axis=1).fillna(0)).cumprod()
idx=A.index; q=idx.to_period('Q'); dsq=np.asarray((idx-(q-1).end_time.normalize()).days); inw=(dsq>=15)&(dsq<=60)
rng=np.random.default_rng(50)
Av,Ov,mv=A.values,O.values,mk.values
ii=np.arange(len(idx)-61)
out={True:[],False:[]}
for i in ii[::5]:
    for h in (60,):
        x=(Av[i+h]/Ov[i+1]-1)-(mv[i+h]/mv[i]-1)
        x=x[np.isfinite(x)&(np.abs(x)<5)]
        out[bool(inw[i])].append((idx[i], np.nanmean(x)*100-0.25, np.nanmean(x>0)*100))
for k,v in out.items():
    d=pd.DataFrame(v,columns=['d','x60','pos']); print('baseline', 'results-window' if k else 'outside', 'x60', round(d.x60.mean(),2),'pos%',round(d.pos.mean(),1))
    for a,b in [('2003','2012'),('2013','2020'),('2021','2026')]:
        s=d[(d.d>=a)&(d.d<=b+'-12-31')]; print('   ',a,b,round(s.x60.mean(),2))
E=pd.read_csv(f'{R}/study/research/pead_events.csv',parse_dates=['date'])
U=E[(E.kind=='UP')&E.win]
best=U[(U.mk200>0)&(U.p60>U.p60.quantile(2/3))&(U.clv>0.8)]
def s(d,l):
    b=d.dropna(subset=['B']); w=b.B[b.B>0].mean(); L=b.B[b.B<=0].mean()
    print(f'{l:30s} n{len(d)} x60 {d.x60.mean():+.2f} | tgt {100*(b.Bhit=="tgt").mean():.1f}% ratio {abs(w/L):.2f} net {b.B.mean():+.2f}')
s(best,'UP mkt>200 & p60 high & close-high')
for a,b in [('2003','2012'),('2013','2020'),('2021','2026'),('2024-11','2026')]:
    s(best[(best.date>=a)&(best.date<=b+'-12-31')],'   '+a)
C=E[(E.kind=='UP')&~E.win]; cb=C[(C.mk200>0)&(C.p60>U.p60.quantile(2/3))&(C.clv>0.8)]; s(cb,'CONTROL same filter')
# year-by-year relative: results UP minus control UP x60; results DN minus control DN
E['y']=E.date.dt.year
t=E.groupby(['y','kind','win']).x60.mean().unstack(['kind','win'])
t['UPdiff']=t[('UP',True)]-t[('UP',False)]; t['DNdiff']=t[('DN',True)]-t[('DN',False)]
print(t[['UPdiff','DNdiff']].round(2).T.to_string())
print('UPdiff>0 years',(t.UPdiff>0).sum(),'/',t.UPdiff.notna().sum(),' DNdiff<0 years',(t.DNdiff<0).sum(),'/',t.DNdiff.notna().sum())
