# r040 / i51: Fed hike days & hike-cycle restarts -> India sectors (rule written before results)
# Rule: start = first Indian close AFTER the FOMC announcement (US evening). Horizons 20d (each hike) and 60/120d (cycle start).
# Sector = equal-weight of u500 stocks of that industry (adj>0, |daily ret|<40%), excess vs equal-weight all.
import pandas as pd,numpy as np,glob,os
U='/home/claude/u500'
p='/home/claude/research/panel_adj.pkl'
if os.path.exists(p): A=pd.read_pickle(p)
else:
    adj={}
    for f in glob.glob(U+'/u500/daily/*.csv.gz'):
        d=pd.read_csv(f,usecols=['date','adj'],index_col='date',parse_dates=True); d=d[~d.index.duplicated()]
        adj[os.path.basename(f)[:-7]]=d.adj
    A=pd.DataFrame(adj).sort_index(); A=A[A.index>='2002-01-01']; A.to_pickle(p)
A=A.where(A>0); R=A.pct_change(fill_method=None); R=R.where(R.abs()<0.4)
ind=pd.read_csv(U+'/u1000/list1000.csv').set_index('symbol').industry.dropna()
sect={}
for s,g in ind.groupby(ind):
    cols=[c for c in g.index if c in R.columns]
    if len(cols)>=5: sect[s]=R[cols].mean(axis=1,skipna=True)
S=pd.DataFrame(sect); allew=R.mean(axis=1); ix=S.index
# need min stocks alive: start 2004 fine for big sectors
hikes=['2004-06-30','2004-08-10','2004-09-21','2004-11-10','2004-12-14','2005-02-02','2005-03-22','2005-05-03','2005-06-30','2005-08-09','2005-09-20','2005-11-01','2005-12-13','2006-01-31','2006-03-28','2006-05-10','2006-06-29',
'2015-12-16','2016-12-14','2017-03-15','2017-06-14','2017-12-13','2018-03-21','2018-06-13','2018-09-26','2018-12-19',
'2022-03-16','2022-05-04','2022-06-15','2022-07-27','2022-09-21','2022-11-02','2022-12-14','2023-02-01','2023-03-22','2023-05-03','2023-07-26']
starts=['2004-06-30','2015-12-16','2022-03-16']
def nextday(d): return ix[ix>pd.Timestamp(d)][0]
LS=np.log1p(S.fillna(0)).cumsum(); LA=np.log1p(allew.fillna(0)).cumsum()
def fwd(d0,h):
    i=ix.get_loc(d0); j=min(i+h,len(ix)-1)
    ex=(LS.iloc[j]-LS.iloc[i])-(LA.iloc[j]-LA.iloc[i]); return np.expm1(ex)*100, np.expm1(LA.iloc[j]-LA.iloc[i])*100
H=[nextday(d) for d in hikes]
X=pd.DataFrame({d:fwd(d,20)[0] for d in H}).T
mk=pd.Series({d:fwd(d,20)[1] for d in H})
X['cycle']=np.where(X.index<'2010','2004-06',np.where(X.index<'2020','2015-18','2022-23'))
key=['Financial Services','Information Technology','Metals & Mining','Realty','Automobile and Auto Components','Fast Moving Consumer Goods','Healthcare','Capital Goods','Oil Gas & Consumable Fuels','Power']
print('Market (EW all) 20d after hike: mean %.2f%%, up %.0f%% (n %d)'%(mk.mean(),(mk>0).mean()*100,len(mk)))
print('base 20d any day: %.2f%%'%(np.expm1(LA.shift(-20)-LA).dropna().mean()*100))
print('\nSector 20d excess after each hike, by cycle:')
print(X.groupby('cycle')[key].mean().round(2).T)
# chance: random dates, same count, from 2004-2024
rng=np.random.default_rng(7); pool=ix[(ix>='2004-01-01')&(ix<='2024-12-31')]
obs=X[key].mean(); sims=[]
for k in range(1000):
    ds=rng.choice(len(pool),len(H),replace=False)
    sims.append(pd.DataFrame({pool[i]:fwd(pool[i],20)[0] for i in ds}).T[key].mean())
sims=pd.DataFrame(sims)
pv=pd.Series({k:(np.mean(sims[k]>=obs[k]) if obs[k]>0 else np.mean(sims[k]<=obs[k])) for k in key})
print('\nall-hike mean excess and one-sided chance p:'); print(pd.DataFrame({'mean':obs.round(2),'p':pv.round(3),'cycles_same_sign':[(np.sign(X.groupby('cycle')[k].mean())==np.sign(obs[k])).sum() for k in key]}))
print('\nCycle starts 60d / 120d excess:')
for h in (60,120):
    Y=pd.DataFrame({nextday(d):fwd(nextday(d),h)[0] for d in starts}).T[key].round(1); Y['MKT']=[fwd(nextday(d),h)[1] for d in starts]
    print(h); print(Y.T.round(1))
X.to_csv('r040_hikes.csv')
