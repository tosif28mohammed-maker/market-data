import pandas as pd, numpy as np, sys
sys.path.insert(0,'study'); import ni_common as nc
n=pd.read_csv('data/NIFTY.csv',parse_dates=['date']).set_index('date').close
m=n.resample('ME').last().pct_change().dropna()*100
m=m[m.index<'2026-11-01']
ms=m.index.month.isin([2,5,8,11])
def s(x): return f"N{len(x)} mean {x.mean():.2f} med {x.median():.2f} up {100*(x>0).mean():.0f}%"
print('Nifty MSCI months',s(m[ms]),'| others',s(m[~ms]))
for a,b in [('2007','2012'),('2013','2020'),('2021','2026')]:
    k=m[a:b]; mk=k.index.month.isin([2,5,8,11]); print(a,b,'msci',round(k[mk].mean(),2),'other',round(k[~mk].mean(),2))
# placebo: all 4-month sets spaced 3 apart
for st in (1,2,3):
    mm=m.index.month.isin([st,st+3,st+6,st+9]); print('set',[st,st+3,st+6,st+9],round(m[mm].mean(),2))
# by month
print(m.groupby(m.index.month).mean().round(2).to_dict())
# large vs rest in panel: top100 by 60d turnover at month start
P=nc.load(); a=P['a']; tv=(P['c']*P['v']).rolling(60).mean()
r=a.resample('ME').last().pct_change(fill_method=None)*100
tvm=tv.resample('ME').last().shift(1)
rows=[]
for d in r.index[1:]:
    if d>pd.Timestamp('2026-10-31'): break
    t=tvm.loc[d].dropna(); rr=r.loc[d]
    big=t.nlargest(100).index; rest=t.index.difference(big)
    x=rr[big].clip(-60,100).mean(); y=rr[rest].clip(-60,100).mean()
    if np.isfinite(x) and np.isfinite(y): rows.append((d,x-y))
s2=pd.Series(dict(rows)); k=s2.index.month.isin([2,5,8,11])
print('Large-minus-rest MSCI months',s(s2[k]),'| others',s(s2[~k]))
for a_,b_ in [('2003','2012'),('2013','2020'),('2021','2026')]:
    q=s2[a_:b_]; kk=q.index.month.isin([2,5,8,11]); print(a_,b_,round(q[kk].mean(),2),round(q[~kk].mean(),2))
print('last 6m',s2[-6:].round(2).to_dict())
