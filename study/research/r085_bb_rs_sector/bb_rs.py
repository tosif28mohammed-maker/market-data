# BB-01 (Trading Chanakya qlhjUR62fpU): sector index close > upper BB(20,2) + sector top-4 relative strength
# entry = break of signal-candle high (next days, max 5 days wait), SL = signal low -1%, target = 3x risk; max 4 open.
# Proxy: equal-weight sector indices from universe (info.csv sectors, >=8 stocks). Costs 0.25% round trip.
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
I=pd.read_csv('/home/claude/market-data/data/fund/info.csv').set_index('symbol')
P=load(); a=P['a']; prev=a.shift(1)
r=(a/prev-1); ok=r.abs()<0.5
sec=I.sector.reindex(a.columns)
L={};H={};Lo={};O={}
for s in sec.dropna().unique():
    c=sec[sec==s].index; n=ok[c].sum(axis=1)
    rr=r[c].where(ok[c]).mean(axis=1).where(n>=8)
    hh=(P['h'][c]/prev[c]-1).where(ok[c]).mean(axis=1); ll=(P['l'][c]/prev[c]-1).where(ok[c]).mean(axis=1)
    oo=(P['o'][c]/prev[c]-1).where(ok[c]).mean(axis=1)
    lev=(1+rr.fillna(0)).cumprod(); lp=lev.shift(1)
    L[s]=lev.where(n>=8); H[s]=(lp*(1+hh)).where(n>=8); Lo[s]=(lp*(1+ll)).where(n>=8); O[s]=(lp*(1+oo)).where(n>=8)
C=pd.DataFrame(L).loc['2004':]; H=pd.DataFrame(H).reindex(C.index); Lo=pd.DataFrame(Lo).reindex(C.index); O=pd.DataFrame(O).reindex(C.index)
H=np.maximum(H,C); Lo=np.minimum(Lo,C)
ma=C.rolling(20).mean(); sd=C.rolling(20).std(); up=ma+2*sd
COST=0.25
def rs_rank(look):
    ret=C/C.shift(look)-1
    # monthly ranking (month-end), applied to next month
    me=ret.groupby(C.index.to_period('M')).tail(1)
    rk=me.rank(axis=1,ascending=False)
    rk.index=rk.index.to_period('M')+1
    return rk
def run(look=126, topn=4, R=3, sel='top', maxpos=4, maxhold=250, wait=5):
    rk=rs_rank(look); per=C.index.to_period('M')
    sig=(C>up)&(C.shift(1)<=up.shift(1))
    trades=[]; openpos={}  # sec -> exit index
    idx=C.index
    for i in range(25,len(idx)-1):
        d=idx[i]; p=per[i]
        if p not in rk.index: continue
        row=rk.loc[p]
        for s in C.columns:
            if not sig.iat[i, C.columns.get_loc(s)]: continue
            rkv=row.get(s,np.nan)
            if np.isnan(rkv): continue
            nsec=row.notna().sum()
            if sel=='top' and rkv>topn: continue
            if sel=='bottom' and rkv<=nsec-topn: continue
            if s in openpos and openpos[s]>=i: continue
            if sum(1 for v in openpos.values() if v>=i)>=maxpos: continue
            j=C.columns.get_loc(s); sh=H.iat[i,j]; sl=Lo.iat[i,j]*0.99
            ent=None
            for k in range(i+1,min(i+1+wait,len(idx))):
                if H.iat[k,j]>sh: ent=(k,max(O.iat[k,j],sh)); break
            if ent is None: continue
            k0,e=ent; risk=e-sl
            if risk<=0: continue
            tgt=e+R*risk; out=None
            for k in range(k0,min(k0+maxhold,len(idx))):
                lo=Lo.iat[k,j]; hi=H.iat[k,j]
                if k>k0 and O.iat[k,j]<=sl: out=(k,O.iat[k,j],'SL'); break
                if lo<=sl: out=(k,sl,'SL'); break
                if k>k0 and O.iat[k,j]>=tgt: out=(k,O.iat[k,j],'T'); break
                if hi>=tgt: out=(k,tgt,'T'); break
            if out is None:
                k=min(k0+maxhold,len(idx))-1
                if k0+maxhold>len(idx): continue  # still open
                out=(k,C.iat[k,j],'time')
            openpos[s]=out[0]
            trades.append(dict(sec=s,d=idx[k0],x=idx[out[0]],ret=(out[1]/e-1)*100-COST,how=out[2],risk=risk/e*100,days=out[0]-k0))
    return pd.DataFrame(trades)
def rep(name,T):
    if len(T)==0: print(name,'N0'); return
    w=T[T.ret>0]; l=T[T.ret<=0]
    print(f"{name}: N{len(T)} tgt%{(T.how=='T').mean()*100:.1f} win%{(T.ret>0).mean()*100:.1f} avg{T.ret.mean():+.2f} avgW{w.ret.mean():+.2f} avgL{l.ret.mean():+.2f} risk%{T.risk.median():.1f} days{T.days.median():.0f}")
    for era,(a1,b1) in {'2004-13':(2004,2013),'2014-19':(2014,2019),'2020-26':(2020,2026)}.items():
        x=T[(T.d.dt.year>=a1)&(T.d.dt.year<=b1)]
        if len(x): print(f"   {era} N{len(x)} tgt%{(x.how=='T').mean()*100:.0f} avg{x.ret.mean():+.2f}")
    for m in (2,4,6):
        x=T[T.d>=C.index[-1]-pd.DateOffset(months=m)]
        print(f"   last{m}m N{len(x)} avg{x.ret.mean() if len(x) else float('nan'):+.2f}")
print('sectors',C.shape[1],C.index[0].date(),C.index[-1].date())
for look in (63,126):
    rep(f'TOP4 RS{look} 3R',run(look,4,3,'top'))
rep('TOP4 RS126 2R',run(126,4,2,'top'))
rep('ALL sectors (no RS) 3R',run(126,99,3,'all',maxpos=99))
rep('BOTTOM4 RS126 3R (placebo)',run(126,4,3,'bottom'))
# baseline: same entries ignoring BB signal? random-day control: entry on every 20th day in top4
T=run(126,4,3,'top'); T.to_csv('/home/claude/market-data/study/research/r085_bb_rs_sector/trades_top4_rs126.csv',index=False)
# simple portfolio CAGR approx: each trade 25% of capital
if len(T):
    eq=1.0
    for _,t in T.sort_values('x').iterrows(): eq*=1+0.25*t.ret/100
    yrs=(T.x.max()-T.d.min()).days/365.25; print('approx CAGR (25%/trade, sequential)',round((eq**(1/yrs)-1)*100,1),'% yrs',round(yrs,1))
# today
print('today above upper BB:', [s for s in C.columns if C[s].iloc[-1]>up[s].iloc[-1]])
print('today RS126 top4:', rs_rank(126).iloc[-1].nsmallest(4).index.tolist())
# CONTROL: random signal days (same count freq) instead of BB breakout, same entry/SL/target rules
rng=np.random.default_rng(7)
real_sig=((C>up)&(C.shift(1)<=up.shift(1)))
frac=real_sig.values.mean()
res=[]
for rep_i in range(20):
    fake=pd.DataFrame(rng.random(C.shape)<frac,index=C.index,columns=C.columns)&C.notna()&up.notna()
    g=globals(); orig=g['up']
    # monkeypatch: make sig = fake by setting up so that condition equals fake
    def run_fake(look=126,topn=4,R=3,sel='top'):
        global up
        up2=pd.DataFrame(np.where(fake,-np.inf,np.inf),index=C.index,columns=C.columns)
        # sig=(C>up)&(C.shift(1)<=up.shift(1)) -> need prev day up=+inf: use fake & ~fake.shift
        up=up2; T=run(look,topn,R,sel); up=orig; return T
    T=run_fake(); res.append((len(T),(T.how=='T').mean()*100,T.ret.mean()))
res=np.array(res); print('RANDOM-DAY control top4 RS126 3R (20 reps): N~%.0f tgt%% %.1f avg %+.2f (range %+.2f..%+.2f)'%(res[:,0].mean(),res[:,1].mean(),res[:,2].mean(),res[:,2].min(),res[:,2].max()))
