import pandas as pd,numpy as np
exec(open('r039_futexp.py').read().split("print('== main ==')")[0])
df=pd.read_csv('r039_events.csv',index_col=0,parse_dates=True)
r1=c.pct_change(); base=pd.DataFrame({'r1':r1,'nx':nxt}).dropna(); base=base[base.index>='2019-02-14']
E2=set(df.index)
for lo,hi,lab in [(-1,-0.005,'day<-0.5%'),(0.005,1,'day>+0.5%')]:
    b=base[(base.r1>lo)&(base.r1<hi)]
    ne=b[~b.index.isin(E2)]; ex=b[b.index.isin(E2)]
    for era,m in [('2019-22',lambda x:x.index<'2023-01-01'),('2023-26',lambda x:x.index>='2023-01-01')]:
        print(lab,era,'non-expiry %.3f n%d | expiry %.3f n%d'%(ne[m(ne)].nx.mean()*100,m(ne).sum(),ex[m(ex)].nx.mean()*100,m(ex).sum()))
# monthly expiry inside weekly era = last expiry of each month
s=pd.Series(df.index,index=df.index); mon=s.groupby([s.index.year,s.index.month]).max().values
mr=nxt.reindex(mon).dropna()-cost
print('monthly expiry 2019-26 n',len(mr),'mean %.3f win %.1f'%(mr.mean()*100,(mr>0).mean()*100))
for a,b_ in [('2019','2022'),('2023','2026')]:
    x=mr[(mr.index>=a)&(mr.index<=b_+'-12-31')]; print(' ',a,b_,'%.3f n%d win %.0f'%(x.mean()*100,len(x),(x>0).mean()*100))
wk=nxt.reindex([d for d in df.index if d not in set(mon)]).dropna()-cost
print('weekly-only (non-monthly) %.3f n%d'%(wk.mean()*100,len(wk)))
# chance for monthly
allr=nxt.dropna(); allr=allr[allr.index>='2019-02-14']
sims=[allr.sample(len(mr),random_state=i).mean() for i in range(3000)]
print('p monthly',np.mean(np.array(sims)>=mr.mean()+cost))
# old monthly era chance
allo=nxt.dropna(); allo=allo[(allo.index>='2008-01-01')&(allo.index<'2019-02-01')]
mo=nxt.reindex(M).dropna()
sims=[allo.sample(len(mo),random_state=i).mean() for i in range(3000)]
print('p monthly 2008-19',np.mean(np.array(sims)>=mo.mean()), 'by halves', mo[mo.index<'2013'].mean()*100, mo[mo.index>='2013'].mean()*100)
