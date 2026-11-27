# ROBOT
# r085 BB-01 on REAL NSE sector indices (Yahoo): close>upper BB(20,2) first time + RS126 top-4 -> buy break of signal high (5d wait),
# SL signal low -1%, target 3R (and 2R), max 4 open; cost 0.25%. Controls: all indices (no RS), random days (20 reps).
import subprocess, sys
subprocess.run([sys.executable,'-m','pip','install','-q','yfinance'],check=False)
import numpy as np, pandas as pd, yfinance as yf
T=['^NSEI','^NSEBANK','^CNXIT','^CNXPHARMA','^CNXAUTO','^CNXFMCG','^CNXMETAL','^CNXREALTY','^CNXENERGY','^CNXPSUBANK','^CNXINFRA','^CNXMEDIA','^CNXFIN','^CNXCONSUM','^CNXPSE','^CNXMNC','^CNXSERVICE','^CNXCOMMODITIES','NIFTY_PVT_BANK.NS','NIFTY_HEALTHCARE.NS','NIFTY_OIL_AND_GAS.NS','NIFTY_CONSR_DURBL.NS','^NSEMDCP50','^CNXSC']
D={}
for t in T:
    try:
        x=yf.download(t,start='2005-01-01',progress=False,auto_adjust=False)
        if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
        x=x.dropna(subset=['Close']); x=x[x.Close>0]
        if len(x)>500: D[t]=x; print(t,len(x),x.index[0].date())
        else: print(t,'short',len(x))
    except Exception as e: print(t,'fail',e)
C=pd.DataFrame({t:x.Close for t,x in D.items()}).sort_index(); H=pd.DataFrame({t:x.High for t,x in D.items()}).reindex(C.index)
Lo=pd.DataFrame({t:x.Low for t,x in D.items()}).reindex(C.index); O=pd.DataFrame({t:x.Open for t,x in D.items()}).reindex(C.index)
bad=(H<=0)|(Lo<=0)|(O<=0)|H.isna(); H=H.mask(bad,C); Lo=Lo.mask(bad,C); O=O.mask(bad,C)
H=np.maximum(H,C); Lo=np.minimum(Lo,C)
ma=C.rolling(20).mean(); sd=C.rolling(20).std(); UP=ma+2*sd
def rs_rank(look):
    ret=C/C.shift(look)-1; me=ret.groupby(C.index.to_period('M')).tail(1); rk=me.rank(axis=1,ascending=False); rk.index=rk.index.to_period('M')+1; return rk
def run(sig,look=126,topn=4,R=3,maxpos=4,wait=5,maxhold=250):
    rk=rs_rank(look); per=C.index.to_period('M'); idx=C.index; out=[]; openpos={}
    for i in range(25,len(idx)-1):
        p=per[i]
        if p not in rk.index: continue
        row=rk.loc[p]
        for j,s in enumerate(C.columns):
            if not sig.iat[i,j]: continue
            v=row.get(s,np.nan)
            if np.isnan(v) or v>topn: continue
            if openpos.get(s,-1)>=i or sum(1 for q in openpos.values() if q>=i)>=maxpos: continue
            sh=H.iat[i,j]; sl=Lo.iat[i,j]*0.99; ent=None
            for k in range(i+1,min(i+1+wait,len(idx))):
                if H.iat[k,j]>sh: ent=(k,max(O.iat[k,j],sh)); break
            if ent is None: continue
            k0,e=ent; risk=e-sl
            if not risk>0: continue
            tg=e+R*risk; res=None
            for k in range(k0,min(k0+maxhold,len(idx))):
                if k>k0 and O.iat[k,j]<=sl: res=(k,O.iat[k,j],'SL');break
                if Lo.iat[k,j]<=sl: res=(k,sl,'SL');break
                if k>k0 and O.iat[k,j]>=tg: res=(k,O.iat[k,j],'T');break
                if H.iat[k,j]>=tg: res=(k,tg,'T');break
            if res is None:
                if k0+maxhold>len(idx): continue
                k=k0+maxhold-1; res=(k,C.iat[k,j],'time')
            openpos[s]=res[0]; out.append(dict(s=s,d=idx[k0],ret=(res[1]/e-1)*100-0.25,how=res[2],risk=risk/e*100))
    return pd.DataFrame(out)
def rep(nm,X):
    if len(X)==0: print(nm,'N0'); return
    print(f"{nm}: N{len(X)} tgt%{(X.how=='T').mean()*100:.1f} avg{X.ret.mean():+.2f} W{X.ret[X.ret>0].mean():+.2f} L{X.ret[X.ret<=0].mean():+.2f} risk{X.risk.median():.1f}")
    for a1,b1 in [(2005,2013),(2014,2019),(2020,2026)]:
        y=X[(X.d.dt.year>=a1)&(X.d.dt.year<=b1)]
        if len(y): print(f"   {a1}-{b1} N{len(y)} tgt%{(y.how=='T').mean()*100:.0f} avg{y.ret.mean():+.2f}")
    for m in (2,4,6):
        y=X[X.d>=C.index[-1]-pd.DateOffset(months=m)]; print(f"   last{m}m N{len(y)} avg{y.ret.mean() if len(y) else float('nan'):+.2f}")
sig=(C>UP)&(C.shift(1)<=UP.shift(1))
rep('REAL TOP4 RS126 3R',run(sig)); rep('REAL TOP4 RS126 2R',run(sig,R=2)); rep('REAL TOP4 RS63 3R',run(sig,look=63))
rep('REAL ALL (no RS) 3R',run(sig,topn=99,maxpos=99))
rng=np.random.default_rng(7); frac=sig.values.mean(); rr=[]
for _ in range(20):
    f=pd.DataFrame(rng.random(C.shape)<frac,index=C.index,columns=C.columns)&C.notna()&UP.notna()
    X=run(f); rr.append(X.ret.mean()); 
print('RANDOM-DAY control TOP4 3R: avg %+.2f range %+.2f..%+.2f'%(np.mean(rr),min(rr),max(rr)))
print('today above upper BB:',[s for s in C.columns if C[s].iloc[-1]>UP[s].iloc[-1]], C.index[-1].date())
print('today RS126 top4:',rs_rank(126).iloc[-1].nsmallest(4).index.tolist())
