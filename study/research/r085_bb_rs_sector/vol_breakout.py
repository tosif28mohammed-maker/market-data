# CH-02 (Trading Chanakya fBzl0oEzUUU, Streak): daily vol>=2x SMA20(vol), close>EMA20, close>EMA50, close>max(high prev 10d)
# buy next open; fixed SL/target 6/12, 6/18, 10/10; max hold 60d. cost 0.25%. Control: same stocks random days.
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
P=load(); a=P['a']; o,h,l,v=P['o'],P['h'],P['l'],P['v']
e20=a.ewm(span=20,adjust=False).mean(); e50=a.ewm(span=50,adjust=False).mean()
hh10=h.rolling(10).max().shift(1); vs=v.rolling(20).mean().shift(1)
sig=(v>=2*vs)&(a>e20)&(a>e50)&(a>hh10)&a.notna()
sig=sig&~sig.shift(1,fill_value=False).rolling(10).max().astype(bool)  # 10d cooldown
A=a.values;O=o.values;H=h.values;Lw=l.values; idx=a.index
def sim(S,sl,tp,hold=60):
    out=[]
    ii,jj=np.where(S.values)
    for i,j in zip(ii,jj):
        if i+1+hold>=len(idx): continue
        e=O[i+1,j]
        if not np.isfinite(e) or e<=0: continue
        s=e*(1-sl/100); t=e*(1+tp/100); r=None
        for k in range(i+1,i+1+hold):
            if not np.isfinite(Lw[k,j]): continue
            if k>i+1 and O[k,j]<=s: r=O[k,j]/e-1;w='SL';break
            if Lw[k,j]<=s: r=s/e-1;w='SL';break
            if k>i+1 and O[k,j]>=t: r=O[k,j]/e-1;w='T';break
            if H[k,j]>=t: r=t/e-1;w='T';break
        if r is None: r=A[i+hold,j]/e-1; w='time'
        out.append((idx[i],r*100-0.25,w))
    return pd.DataFrame(out,columns=['d','ret','how'])
def rep(nm,T):
    print(f"{nm}: N{len(T)} tgt%{(T.how=='T').mean()*100:.1f} win%{(T.ret>0).mean()*100:.1f} avg{T.ret.mean():+.2f} W{T.ret[T.ret>0].mean():+.2f} L{T.ret[T.ret<=0].mean():+.2f}")
    for era,(a1,b1) in {'2003-13':(2003,2013),'2014-19':(2014,2019),'2020-26':(2020,2026)}.items():
        x=T[(T.d.dt.year>=a1)&(T.d.dt.year<=b1)]; print(f"   {era} N{len(x)} tgt%{(x.how=='T').mean()*100:.0f} avg{x.ret.mean():+.2f}")
    for m in (2,4,6):
        x=T[T.d>=idx[-1]-pd.DateOffset(months=m+3)]; x=x[x.d<idx[-1]-pd.DateOffset(months=3)] if False else x
        x=T[T.d>=idx[-61]-pd.DateOffset(months=m)]; print(f"   last{m}m(+60d hold) N{len(x)} avg{x.ret.mean() if len(x) else float('nan'):+.2f}")
print('signals',int(sig.values.sum()))
rng=np.random.default_rng(3)
base=(a>e20)&(a>e50)&a.notna()
frac=sig.values.sum()/base.values.sum()
ctrl=base&pd.DataFrame(rng.random(a.shape)<frac,index=a.index,columns=a.columns)
for sl,tp in [(6,12),(6,18),(10,10)]:
    rep(f'CH-02 SL{sl}/T{tp}',sim(sig,sl,tp)); rep(f'   control(uptrend random) SL{sl}/T{tp}',sim(ctrl,sl,tp))
