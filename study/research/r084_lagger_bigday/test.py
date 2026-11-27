# r084 (i119): पिछड़े sector का अचानक बड़ा दिन -> आगे? Rule पहले लिखा:
# sector EW (info.csv, >=8 stocks) daily excess vs EW market >= +3.5% (also 2.5% for sample) AND 126d excess <= -10% -> sector excess next 5/20/60d.
# Controls: same big day w/o lag (126d > -10%); lagging sectors w/o big day (baseline). Episodes 30d gap per sector. Eras + shuffle.
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
I=pd.read_csv('/home/claude/market-data/data/fund/info.csv').set_index('symbol')
a=load()['a']; r1=a.pct_change(fill_method=None); r1=r1.where(r1.abs()<0.4); mkt=r1.mean(axis=1)
sec=I.sector.reindex(a.columns); S={}
for s in sec.dropna().unique():
    c=sec[sec==s].index; n=r1[c].notna().sum(axis=1); S[s]=r1[c].mean(axis=1).where(n>=8)
S=pd.DataFrame(S); print('sectors',list(S.columns))
lS=np.log1p(S.fillna(0)).cumsum(); lM=np.log1p(mkt.fillna(0)).cumsum(); ex=lS.sub(lM,axis=0)
d1=(ex-ex.shift(1))*100; e126=(ex-ex.shift(126))*100
F={h:(ex.shift(-h)-ex)*100 for h in (5,20,60)}
def ev(cond,gap=30):
    rows=[]
    for s in S.columns:
        last=None
        for d in cond.index[cond[s].fillna(False)]:
            if last is not None and (d-last).days<gap: continue
            last=d; rows.append({'sec':s,'d':d,**{h:F[h].at[d,s] for h in F},'lag':e126.at[d,s],'bd':d1.at[d,s]})
    return pd.DataFrame(rows).dropna(subset=[20])
def show(R,lab):
    print(lab,'N',len(R),{h:round(R[h].mean(),2) for h in F},'%+20',round((R[20]>0).mean()*100),'%+60',round((R[60]>0).mean()*100) if R[60].notna().any() else '')
for thr in (3.5,2.5):
    A=ev((d1>=thr)&(e126<=-10)); show(A,f'BIG{thr}+LAG')
    for era,(y0,y1) in {'03-12':(2003,2012),'13-20':(2013,2020),'21-26':(2021,2026)}.items():
        x=A[(A.d.dt.year>=y0)&(A.d.dt.year<=y1)]; show(x,'   '+era)
    show(ev((d1>=thr)&(e126>-10)),f'BIG{thr} no lag')
base=ev(e126<=-10,gap=30); show(base,'LAG baseline (any day, 30d gap)')
# shuffle: random lagging-sector days, same N as BIG2.5+LAG
A=ev((d1>=2.5)&(e126<=-10)); rng=np.random.default_rng(0)
sims=[base.sample(len(A),replace=True,random_state=int(rng.integers(1e9)))[20].mean() for _ in range(2000)]
print('shuffle p(sim>=obs) 20d:', np.mean(np.array(sims)>=A[20].mean()).round(3))
print('IT events:'); print(ev((d1>=2.5)&(e126<=-10)).query("sec.str.contains('IT') or sec.str.contains('Tech')",engine='python').tail(12).round(2).to_string())
print('today', d1.index[-1].date(), d1.iloc[-1].round(2).to_dict()); print('126d', e126.iloc[-1].round(1).to_dict())
