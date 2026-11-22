"""r053 (22 Nov 2026, gold watch day 1): gold after the dollar index made 8+ straight up days.
RULE WRITTEN BEFORE RESULTS: FX_DOLLAR_INDEX daily close up vs previous close; event = the day the up-streak reaches 8
(new event only if >20 trading days after the previous one). Gold (CMD_GOLD, USD) forward 5/20/60 trading days from the
event close, vs all days (chance); p_hi by 5000 random draws of same n. Also: did the dollar keep rising (DXY 20d fwd),
and gold's max extra fall within 20 days. PASS = gold 20d mean > chance with p<=0.10 (i.e. dollar streak exhausts / gold bounces);
FAIL = below chance; else UNCLEAR. Also report the signals S1/S2 for the watch."""
import numpy as np, pandas as pd
R='/home/claude/market-data'
def g(f):
    s=pd.read_csv(f'{R}/data/global/{f}.csv',parse_dates=['date']).set_index('date').close
    s=s[~s.index.duplicated()].dropna(); return s[s>0]
G,D,S=g('CMD_GOLD'),g('FX_DOLLAR_INDEX'),g('CMD_SILVER')
up=(D.diff()>0).astype(int); st=up.groupby((up==0).cumsum()).cumsum()
ev=[];last=-999
for i,(d,v) in enumerate(st.items()):
    if v==8 and i-last>20: ev.append(d); last=i
print('DXY streak before last day', int(st.iloc[-2]), 'events', len(ev)); print('DXY current streak', int(st.iloc[-1]), 'as of', D.index[-1].date(), 'max streak ever', int(st.max()))
Gd=G.reindex(G.index.union(D.index)).ffill()
rng=np.random.default_rng(53); rows=[]
for d in ev:
    if d<G.index[0]: continue
    if d not in G.index: d=G.index[G.index.searchsorted(d)] if G.index.searchsorted(d)<len(G) else None
    if d is None: continue
    i=G.index.get_loc(d); r={'date':d.date(),'gold':G.iloc[i]}
    for h in (5,20,60): r[f'g{h}']=(G.iloc[i+h]/G.iloc[i]-1)*100 if i+h<len(G) else np.nan
    r['maxfall20']=(G.iloc[i:i+21].min()/G.iloc[i]-1)*100
    j=D.index.searchsorted(d); r['dxy20']=(D.iloc[j+20]/D.iloc[j]-1)*100 if j+20<len(D) else np.nan
    rows.append(r)
E=pd.DataFrame(rows); print(E.round(2).to_string())
for h in (5,20,60):
    x=E[f'g{h}'].dropna(); a=((G.shift(-h)/G-1)*100).dropna()
    sims=np.array([rng.choice(a.values,len(x)).mean() for _ in range(5000)])
    print(f'g{h}: {x.mean():+.2f}% up {100*(x>0).mean():.0f}% n{len(x)} vs all {a.mean():+.2f} ({100*(a>0).mean():.0f}%) p_hi {(sims>=x.mean()).mean():.2f}')
print('maxfall20 median', round(E.maxfall20.median(),1), 'dxy20 mean', round(E.dxy20.mean(),2))
# watch signals
low20=G.iloc[-20:].min(); m50=G.rolling(50).mean().iloc[-1]; m20=G.rolling(20).mean().iloc[-1]
print('S1 gold new 20d low:', G.iloc[-1]<=low20, 'DXY 5d chg', round((D.iloc[-1]/D.iloc[-6]-1)*100,2))
print('gold last', G.iloc[-1], 'post-crash low', G.min() if False else G.loc['2026-10-01':].min(), '50DMA', round(m50,1), '20DMA', round(m20,1))
print('silver last', S.iloc[-1], 'silver 50DMA', round(S.rolling(50).mean().iloc[-1],2), 'ratio', round(G.iloc[-1]/S.iloc[-1],1))
w=G.resample('W-FRI').last(); print('gold weekly last 3', w.tail(3).round(1).to_dict())
