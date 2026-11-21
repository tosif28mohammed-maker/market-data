# r039 / i38: FUT_EXP — Nifty long at weekly-expiry close -> next close. Rule written before results.
import pandas as pd, numpy as np
D='/home/claude/market-data/data/'
n=pd.read_csv(D+'NIFTY.csv',index_col='date',parse_dates=True); n=n[~n.index.duplicated()]
v=pd.read_csv(D+'INDIAVIX.csv',index_col='date',parse_dates=True).close
sp=pd.read_csv(D+'global/US_SP500.csv',index_col='date',parse_dates=True).close
c=n.close; o=n.open; ix=c.index
nxt=c.shift(-1)/c-1; ovn=o.shift(-1)/c-1; intr=c.shift(-1)/o.shift(-1)-1
def expiries(start,end,wd):
    out=[]
    for d in pd.date_range(start,end,freq='D'):
        if d.weekday()==wd:
            t=ix[ix<=d]
            if len(t) and (d-t[-1]).days<4: out.append(t[-1])
    return sorted(set(out))
E=expiries('2019-02-14','2025-08-28',3)+expiries('2025-09-02','2026-11-20',1)
# monthly expiry era (last Thursday) 2008-2019 for out-of-sample angle
M=[]
for (y,m),g in pd.Series(ix,index=ix)[(ix>='2008-01-01')&(ix<'2019-02-01')].groupby([ix[(ix>='2008-01-01')&(ix<'2019-02-01')].year,ix[(ix>='2008-01-01')&(ix<'2019-02-01')].month]):
    th=[d for d in pd.date_range(f'{y}-{m:02d}-01',periods=31) if d.month==m and d.weekday()==3][-1]
    t=ix[ix<=th]; M.append(t[-1])
cost=0.0001
def st(sel,name):
    r=nxt.reindex(sel).dropna()-cost
    base=nxt.dropna()
    print(f'{name:38s} n={len(r):4d} mean={r.mean()*100:+.3f}% win={(r>0).mean()*100:4.1f}%  (all days {base.mean()*100:+.3f}%)')
    return r
print('== main ==')
w=st(E,'weekly expiry 2019-26 (all)')
st([d for d in E if d<pd.Timestamp('2025-09-01')],'  Thursday era 2019-Aug25')
st([d for d in E if d>=pd.Timestamp('2025-09-01')],'  Tuesday era Sep25-Nov26')
for y in range(2019,2027): st([d for d in E if d.year==y],f'  {y}')
st(M,'monthly expiry 2008-Jan19 (OOS angle)')
# chance: shuffle — random same-count days in same years
rng=np.random.default_rng(1); allr=nxt.dropna(); allr=allr[allr.index>='2019-02-14']
sims=[allr.sample(len(w),random_state=i).mean() for i in range(2000)]
print('chance p(random >= expiry mean)=',np.mean(np.array(sims)>=w.mean()+cost))
# split overnight vs next-day intraday
print('overnight part %.3f%%  next-day intraday part %.3f%%'%(ovn.reindex(E).mean()*100,intr.reindex(E).mean()*100))
# scenarios: what circumstances on expiry day
df=pd.DataFrame(index=pd.DatetimeIndex(E))
df['r']=nxt.reindex(df.index)-cost
df['prior2']=(c/c.shift(2)-1).reindex(df.index)
df['expday']=(c/c.shift(1)-1).reindex(df.index)
df['vix']=v.reindex(ix,method='ffill').reindex(df.index)
df['above200']=(c>c.rolling(200).mean()).reindex(df.index)
spr=sp.pct_change(); spr.index=spr.index+pd.Timedelta(days=1)  # US day t closes before India t+1 open
df['us_next']=spr.reindex(ix,method=None).shift(-1).reindex(df.index)
df=df.dropna(subset=['r'])
df['era']=np.where(df.index<'2023-01-01','2019-22','2023-26')
print('\n== scenarios (mean next-day %, n) by era ==')
def sc(col,bins,labels):
    df['b']=pd.cut(df[col],bins,labels=labels)
    print(col); print((df.groupby(['b','era'],observed=True).r.agg(['mean','count']).assign(mean=lambda x:(x['mean']*100).round(3))).unstack())
sc('prior2',[-1,-0.01,0.01,1],['2d<-1%','flat','2d>+1%'])
sc('expday',[-1,-0.005,0.005,1],['exp<-0.5','flat','exp>+0.5'])
sc('vix',[0,13,18,100],['vix<13','13-18','>18'])
print(df.groupby(['above200','era']).r.agg(['mean','count']))
# outcome split: winners vs losers circumstances
df['win']=df.r>0
print('\nwinners vs losers: mean prior2, expday, vix');print(df.groupby('win')[['prior2','expday','vix']].mean())
df.to_csv('r039_events.csv')
