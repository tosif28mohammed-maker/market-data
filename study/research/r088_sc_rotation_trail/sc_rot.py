# r088 AI-14BEFA: small-cap 12m outperformance vs large >17% -> rotate to large? (Yahoo ^CNXSC failed on robot)
# Proxy: point-in-time turnover rank (126d median price*volume) each month: large = top 100, small = rank 251-500.
# Equal-weight monthly-rebalanced. Survivorship: universe = today's listed stocks (bias favours small; caveat).
import sys,numpy as np,pandas as pd
sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
P=load(); a=P['a']; tv=(P['c']*P['v']).rolling(126,min_periods=100).median()
r=a.pct_change(fill_method=None); r=r.where(r.abs()<0.5)
me=a.index.to_series().groupby(a.index.to_period('M')).last()
L=[];S=[]
for i in range(len(me)-1):
    d=me.iloc[i]; rk=tv.loc[d].dropna().rank(ascending=False)
    if len(rk)<500: L.append(np.nan);S.append(np.nan);continue
    big=rk[rk<=100].index; sm=rk[(rk>250)&(rk<=500)].index
    p=a.index[(a.index>d)&(a.index<=me.iloc[i+1])]
    L.append((1+r.loc[p,big].mean(axis=1).fillna(0)).prod()-1); S.append((1+r.loc[p,sm].mean(axis=1).fillna(0)).prod()-1)
M=pd.DataFrame({'L':L,'S':S},index=me.index[1:]).dropna()
cl=(1+M).cumprod()
rel12=cl.S/cl.S.shift(12)-cl.L/cl.L.shift(12)
print('months',len(M),M.index[0],M.index[-1])
for h in (3,6,12):
    f=(cl.S.shift(-h)/cl.S)-(cl.L.shift(-h)/cl.L)
    for nm,mk in [('ALL',rel12.notna()),('rel>17',rel12>.17),('rel>25',rel12>.25),('rel<-17',rel12<-.17)]:
        x=f[mk].dropna()
        print(f'{h:2d}m {nm:8s} N{len(x):3d} small-large {x.mean()*100:+6.2f}pp small better {np.mean(x>0)*100:4.0f}%')
cross=(rel12>.17)&(rel12.shift(1)<=.17)
print('episodes:')
for d in rel12.index[cross]:
    i=cl.index.get_loc(d); j6=min(i+6,len(cl)-1); j12=min(i+12,len(cl)-1)
    f6=cl.S.iloc[j6]/cl.S.iloc[i]-cl.L.iloc[j6]/cl.L.iloc[i]; f12=cl.S.iloc[j12]/cl.S.iloc[i]-cl.L.iloc[j12]/cl.L.iloc[i]
    print(f'  {d} rel {rel12[d]*100:+.0f} -> 6m {f6*100:+.1f} 12m {f12*100:+.1f}')
print('today rel12', round(rel12.iloc[-1]*100,1), rel12.index[-1])
