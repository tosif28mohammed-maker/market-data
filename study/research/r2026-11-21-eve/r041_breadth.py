# r041 / i28: stock-level breadth thrust. Rule (fixed before results): B = share of alive u500 stocks (>=200 alive) with 10d return >= +7%.
# Event = B crosses above its threshold T (T = 90th/95th pct of 2003-2012 history, learned on first era) after being below for 20 days; events >= 60d apart.
# Outcome: equal-weight all-stock and Nifty 20/60d forward; compare base, eras, chance (random dates, cluster = 1 per event).
import pandas as pd,numpy as np
A=pd.read_pickle('/home/claude/research/panel_adj.pkl'); A=A.where(A>0)
R=A.pct_change(fill_method=None); R=R.where(R.abs()<0.4)
L=np.log1p(R.fillna(0)).cumsum().where(A.notna())
r10=np.expm1(L-L.shift(10)); alive=r10.notna().sum(axis=1)
B=((r10>=0.07).sum(axis=1)/alive).where(alive>=200)
ew=R.mean(axis=1); LE=np.log1p(ew.fillna(0)).cumsum()
n=pd.read_csv('/home/claude/market-data/data/NIFTY.csv',index_col='date',parse_dates=True).close; n=n[~n.index.duplicated()]
sx=pd.read_csv('/home/claude/market-data/data/global/IN_SENSEX.csv',index_col='date',parse_dates=True).close; sx=sx[~sx.index.duplicated()]
ix=B.dropna().index
idx=sx.reindex(ix,method='ffill')
def f(s,h): return (s.shift(-h)/s-1)*100
F={'ew20':np.expm1(LE.shift(-20)-LE).reindex(ix)*100,'ew60':np.expm1(LE.shift(-60)-LE).reindex(ix)*100,'sx20':f(idx,20),'sx60':f(idx,60)}
F=pd.DataFrame(F)
learn=B[(B.index<'2013-01-01')].dropna()
for q in (0.90,0.95):
    T=learn.quantile(q); ev=[]; last=None
    below=(B<T).rolling(20).sum()==20
    for d in ix[1:]:
        if B[d]>=T and below.shift(1).get(d,False) and (last is None or (ix.get_loc(d)-ix.get_loc(last))>=60):
            ev.append(d); last=d
    E=F.reindex(ev)
    E['era']=np.where(E.index<'2013','2003-12',np.where(E.index<'2021','2013-20','2021-26'))
    print(f'\n== threshold {q:.0%} of 2003-12 = {T*100:.1f}% stocks up >=7% in 10d; events {len(ev)} ==')
    print(E.groupby('era').agg(['mean','count']).round(2).iloc[:,[0,1,2,4,6]])
    print('all events', E.drop(columns='era').mean().round(2).to_dict(), ' base', F.mean().round(2).to_dict())
    print('win sx60 %.0f%%  base %.0f%%'%((E.sx60>0).mean()*100,(F.sx60>0).mean()*100))
    rng=np.random.default_rng(5); sims=[F.dropna().sample(len(E.dropna()),random_state=k).mean() for k in range(3000)]
    sims=pd.DataFrame(sims); print('chance p (>= obs):', {c:round(float(np.mean(sims[c]>=E[c].mean())),3) for c in F.columns})
    print('dates:',[str(d.date()) for d in ev][-12:])
print('\ncurrent B (last date %s) = %.1f%%'%(B.dropna().index[-1].date(),B.dropna().iloc[-1]*100))
B.to_csv('r041_breadth_series.csv')
