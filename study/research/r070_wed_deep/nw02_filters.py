# ROBOT
"""NW-02 आगे: Nasdaq<=-2% (पिछली रात) + Nifty gap-down<=-0.5% → open पर Nifty futures खरीद.
Cost 0.03% round trip (futures) और 0.25% (cash/ETF). Filters: Nifty prev close vs 200DMA, India VIX prev close <20 / >=20.
Exits: 5d close, और stop/target (-1.5/+1.5, -2/+3) 5 दिन में (daily high/low, stop पहले माना)."""
import pandas as pd, numpy as np
def ld(p):
    d = pd.read_csv(p, parse_dates=['date']).set_index('date').sort_index()
    return d[~d.index.duplicated()]
n = ld('data/NIFTY.csv'); q = ld('data/global/US_NASDAQ.csv'); vx = ld('data/INDIAVIX.csv')
n = n[(n.open > 0) & (n.close > 0)].copy()
n['pc'] = n.close.shift(1); n['gap'] = n.open / n.pc - 1
n['o5'] = n.close.shift(-5) / n.open - 1
n['ma200'] = n.close.rolling(200).mean().shift(1)
n['bull'] = n.pc > n.ma200
n['vix'] = vx.close.reindex(n.index).shift(1)
n['us'] = q.close.pct_change().reindex(n.index - pd.Timedelta(days=1), method='ffill').values
n = n.dropna(subset=['gap', 'us', 'ma200'])
n = n[n.gap.abs() > 1e-6]
O, H, L, C = n.open.values, n.high.values, n.low.values, n.close.values
def st(i, sl, tp, hold=5):
    e = O[i]
    for k in range(i, min(i + hold, len(O))):
        if L[k] / e - 1 <= sl: return sl
        if H[k] / e - 1 >= tp: return tp
    k = min(i + hold - 1, len(O) - 1)
    return C[k] / e - 1
pos = {d: i for i, d in enumerate(n.index)}
def era(y): return '2007-12' if y <= 2012 else ('2013-20' if y <= 2020 else '2021-26')
sig = (n.us <= -0.02) & (n.gap <= -0.005)
base = n.o5.mean()
def show(m, name):
    s = n[m].dropna(subset=['o5'])
    if len(s) < 5: print(name, 'N', len(s)); return
    r = s.o5 * 100
    line = f'{name:38s} N={len(s):3d} o5 {r.mean():+.2f} (सब {base*100:+.2f}) win {(r>0.03).mean()*100:.0f}% net fut {r.mean()-0.03:+.2f} cash {r.mean()-0.25:+.2f}'
    eras = s.groupby([era(d.year) for d in s.index]).o5.mean().mul(100).round(2).to_dict()
    print(line, '| दौर', eras)
    for sl, tp in ((-0.015, 0.015), (-0.02, 0.03)):
        x = pd.Series([st(pos[d], sl, tp) for d in s.index]) * 100 - 0.03
        hit = (x >= tp * 100 - 0.04).mean() * 100
        print(f'      SL{sl*100:.1f}/TP+{tp*100:.1f}: target {hit:.0f}% win {(x>0).mean()*100:.0f}% avg win {x[x>0].mean():+.2f} loss {x[x<=0].mean():+.2f} exp {x.mean():+.2f}')
show(sig, 'signal (all)')
show(sig & n.bull, 'signal + Nifty>200DMA')
show(sig & ~n.bull, 'signal + Nifty<200DMA')
show(sig & (n.vix < 20), 'signal + VIX<20')
show(sig & (n.vix >= 20), 'signal + VIX>=20')
show(sig & n.bull & (n.vix < 20), 'signal + bull + VIX<20')
show((n.us >= 0.02) & (n.gap >= 0.005), 'placebo Nasdaq>=+2% & gap-up')
show((n.gap <= -0.005) & (n.us > -0.01), 'control gap-down w/o US crash')
print('last signals:', [str(d.date()) for d in n[sig].index[-6:]])
