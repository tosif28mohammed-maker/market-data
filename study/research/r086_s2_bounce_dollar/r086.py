"""r086 (27 Nov 2026, gold watch daily test): S2 'first bounce' while the dollar is still strong — does it hold?
RULES WRITTEN BEFORE RESULTS (data/global CMD_GOLD/CMD_SILVER futures, weekly W-FRI closes; INR = x FX_USDINR, KWD = x FX_USDKWD):
 Zone: weekly close >= 20% (gold) / 35% (silver) below running peak of weekly closes.
 Event (S2): in zone AND weekly close >= 1.08 x lowest weekly close of the last 13 weeks; first in 8 weeks.
 Split (scenario): DXY 20-day change at event > 0 ('dollar still strong', like now) vs <= 0 ('dollar easing').
 Outcome: next 4/13/26-week return; 'retest' = a later weekly close below that 13-week low within 13 weeks.
 Chance: all in-zone weeks (same asset, same era). Eras 2000-14 vs 2015-26. Bootstrap p (5000 draws).
"""
import numpy as np, pandas as pd
R='/home/claude/market-data'
def g(f):
    s=pd.read_csv(f'{R}/data/global/{f}.csv',parse_dates=['date']).set_index('date').close
    s=s[~s.index.duplicated()].dropna(); return s[s>0]
G,S,I,K,D=g('CMD_GOLD'),g('CMD_SILVER'),g('FX_USDINR'),g('FX_USDKWD'),g('FX_DOLLAR_INDEX')
d20=D/D.shift(20)-1
rng=np.random.default_rng(86)
ser={'GOLD_USD':(G,.20),'SILVER_USD':(S,.35),'GOLD_INR':((G*I.reindex(G.index).ffill()).dropna(),.15),
     'SILVER_INR':((S*I.reindex(S.index).ffill()).dropna(),.30),'GOLD_KWD':((G*K.reindex(G.index).ffill()).dropna(),.20),
     'SILVER_KWD':((S*K.reindex(S.index).ffill()).dropna(),.35)}
out=[]
for nm,(s,th) in ser.items():
    w=s.resample('W-FRI').last().dropna(); pk=w.cummax(); zone=w<=pk*(1-th)
    lo13=w.rolling(13).min(); ev=[]; last=None
    for i,d in enumerate(w.index):
        if zone.iloc[i] and w.iloc[i]>=1.08*lo13.iloc[i] and (last is None or i-last>=8): ev.append(i); last=i
    fwd={h:(w.shift(-h)/w-1)*100 for h in (4,13,26)}
    print(f'\n== {nm} zone {th*100:.0f}%: events {len(ev)}')
    for era,(a,b) in {'2000-14':('2000','2014'),'2015-26':('2015','2026')}.items():
        for sp in ('dollar_up','dollar_down','all'):
            idx=[i for i in ev if a<=str(w.index[i].year)<=b]
            if sp!='all':
                idx=[i for i in idx if (d20.asof(w.index[i])>0)==(sp=='dollar_up')]
            row={'series':nm,'era':era,'split':sp,'n':len(idx)}
            base=w.index[zone&(w.index.year>=int(a))&(w.index.year<=int(b))]
            for h in (4,13,26):
                x=fwd[h].iloc[idx].dropna(); c=fwd[h].reindex(base).dropna()
                if len(x)==0 or len(c)<10: row[f'w{h}']=np.nan; continue
                sims=np.array([rng.choice(c.values,len(x)).mean() for _ in range(3000)])
                row[f'w{h}']=round(x.mean(),2); row[f'ch{h}']=round(c.mean(),2); row[f'p{h}']=round((sims>=x.mean()).mean(),2)
                row[f'up{h}']=round(100*(x>0).mean())
            rt=[]
            for i in idx:
                fut=w.iloc[i+1:i+14]
                if len(fut): rt.append(bool((fut<lo13.iloc[i]).any()))
            row['retest%']=round(100*np.mean(rt)) if rt else np.nan
            out.append(row)
    print('  dates:',[f"{w.index[i].date()} dxy20 {d20.asof(w.index[i])*100:+.1f}" for i in ev][-12:])
T=pd.DataFrame(out); pd.set_option('display.width',250)
print(T.to_string(index=False))
T.to_csv(f'{R}/study/research/r086_s2_bounce_dollar/r086.csv',index=False)
# live check (last full weekly bar + DXY now)
for nm in ('GOLD_USD','SILVER_USD'):
    s,th=ser[nm]; w=s.resample('W-FRI').last().dropna()
    print('LIVE',nm,'last',w.index[-1].date(),round(w.iloc[-1],2),'13w low',round(w.rolling(13).min().iloc[-1],2),'x1.08',round(1.08*w.rolling(13).min().iloc[-1],2),'dd',round((w.iloc[-1]/w.cummax().iloc[-1]-1)*100,1),'DXY20',round(d20.iloc[-1]*100,2))
