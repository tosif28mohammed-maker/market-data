"""r064 (24 Nov 2026, gold watch day 3): gold jumps while the dollar also rises, during a deep fall — a 'strong-hands' sign?
Trigger: on Mon 23 Nov gold +4.3% while DXY rose 103.81 -> 104.23 (gold rising AGAINST a rising dollar).
RULE WRITTEN BEFORE RESULTS: data/global CMD_GOLD/CMD_SILVER (USD), FX_DOLLAR_INDEX, FX_USDINR, FX_USDKWD.
 Zone: close >= 15% (gold) / 30% (silver) below its 252-day high.
 Event A (divergence): in zone, metal day >= +2% (gold) / +3% (silver) AND DXY day >= +0.2%.
 Control B: in zone, same metal day size, DXY day <= 0.
 Chance C: all in-zone days.
 One event per 10 trading days. Forward 5/20/60 days; also 'retest' = new close below the prior 20-day low within 60 days.
 Eras 2000-14 vs 2015-26; USD, INR, KWD. p_hi = random draws (5000) of same n from C.
 PASS = A beats C by >= +2% at 20d or 60d with p<=0.10 in BOTH eras and in INR; FAIL = A <= C; else UNCLEAR.
"""
import numpy as np, pandas as pd
R='/home/claude/market-data'
def g(f):
    s=pd.read_csv(f'{R}/data/global/{f}.csv',parse_dates=['date']).set_index('date').close
    s=s[~s.index.duplicated()].dropna(); return s[s>0]
D,I,K=g('FX_DOLLAR_INDEX'),g('FX_USDINR'),g('FX_USDKWD')
rng=np.random.default_rng(64)
def run(nm,s,zone,jump):
    dr=D.reindex(s.index).ffill().pct_change()*100; r=s.pct_change()*100
    hi=s.rolling(252,min_periods=120).max(); z=(s/hi-1)<=-zone
    lo20=s.rolling(20).min().shift(1)
    out={}
    for cur,mult in (('USD',None),('INR',I),('KWD',K)):
        x=s if mult is None else (s*mult.reindex(s.index).ffill()).dropna()
        f={h:(x.shift(-h)/x-1)*100 for h in (5,20,60)}
        ret=pd.Series([(x.iloc[i+1:i+61]<lo20.reindex(x.index).iloc[i]).any() if i+60<len(x) else np.nan for i in range(len(x))],index=x.index)
        for era,(a,b) in {'2000-14':('2000','2014'),'2015-26':('2015','2026')}.items():
            zz=z.reindex(x.index).fillna(False)&(x.index>=a)&(x.index<=b+'-12-31')
            rr=r.reindex(x.index); dd=dr.reindex(x.index)
            def thin(mask):
                ev=[];last=-99
                for i,v in enumerate(mask.values):
                    if v and i-last>=10: ev.append(mask.index[i]); last=i
                return ev
            A=thin(zz&(rr>=jump)&(dd>=0.2)); B=thin(zz&(rr>=jump)&(dd<=0)); C=x.index[zz]
            for h in (20,60):
                cv=f[h].reindex(C).dropna()
                for lab,ev in (('A',A),('B',B)):
                    v=f[h].reindex(ev).dropna()
                    if len(v)==0: out[(cur,era,lab,h)]=(np.nan,0,np.nan,np.nan,cv.mean());continue
                    p=(np.array([rng.choice(cv.values,len(v)).mean() for _ in range(3000)])>=v.mean()).mean()
                    rt=ret.reindex(ev).dropna().mean()*100
                    out[(cur,era,lab,h)]=(v.mean(),len(v),p,rt,cv.mean())
    print(f'\n== {nm} zone<=-{zone*100:.0f}% jump>=+{jump}%')
    for k,(m,n,p,rt,c) in out.items():
        print(f'  {k[0]} {k[1]} {k[2]} {k[3]}d: {m:+.2f}% n{n} p_hi {p:.2f} retest60 {rt:.0f}% | chance {c:+.2f}')
    return out
og=run('GOLD',g('CMD_GOLD'),0.15,2.0); os_=run('SILVER',g('CMD_SILVER'),0.30,3.0)
G=g('CMD_GOLD'); print('\nLIVE',G.index[-1].date(),'gold',G.iloc[-1],'day',round((G.iloc[-1]/G.iloc[-2]-1)*100,2),'DXY day',round((D.iloc[-1]/D.iloc[-2]-1)*100,2),'dd252',round((G.iloc[-1]/G.iloc[-252:].max()-1)*100,1))
