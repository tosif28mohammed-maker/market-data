"""Claim tests LM-01 and MC-01 (news, Nov 2026).
LM-01 (LiveMint 'Nifty posts longest weekly winning streak in 5 months'): after N>=4 consecutive up weeks, does Nifty keep rising?
MC-01 (Moneycontrol: 'India VIX fell 18%... easing volatility to support bull trend'): after a big 1-day VIX fall (<=-10%, <=-15%), Nifty next 5/20 days.
RULES BEFORE RESULTS: weekly = Friday close (W-FRI last). Forward 1/4/8 weeks vs all weeks. VIX: forward 5/20 trading days vs all days.
Data: data/NIFTY.csv (2007-), data/INDIAVIX.csv (2008-). Index only, no costs (direction study).
"""
import pandas as pd, numpy as np, os
R = os.path.dirname(os.path.abspath(__file__)) + '/../../../data/'
n = pd.read_csv(R + 'NIFTY.csv', parse_dates=['date']).set_index('date').close
w = n.resample('W-FRI').last().dropna()
wr = w.pct_change()
up = (wr > 0).astype(int)
streak = up.groupby((up != up.shift()).cumsum()).cumsum() * up
out = []
def row(name, mask, ser_f, eras=(('ALL','2007','2026'),('2007-15','2007','2015'),('2016-26','2016','2026'),('last2y','2024-11','2026'))):
    for e,a,b in eras:
        m = mask[a:b]; f = ser_f[a:b]
        s = f[m].dropna(); base = f.dropna()
        if len(s) < 5: continue
        out.append(dict(test=name, era=e, n=len(s), avg=round(s.mean()*100,2), up_pct=round((s>0).mean()*100,1), base_avg=round(base.mean()*100,2), base_up=round((base>0).mean()*100,1)))
for h in (1,4,8):
    f = w.shift(-h)/w - 1
    for k in (3,4,5):
        row(f'LM-01 streak=={k} fwd{h}w', streak == k, f)
    row(f'LM-01 streak>=4 fwd{h}w', streak >= 4, f)
v = pd.read_csv(R + 'INDIAVIX.csv', parse_dates=['date']).set_index('date').close
v = v[v > 0]; vr = v.pct_change()
df = pd.concat([n, vr.rename('vr')], axis=1).dropna()
for h in (1,5,20):
    f = df.close.shift(-h)/df.close - 1
    for th in (-0.10, -0.15):
        row(f'MC-01 VIX<= {int(th*100)}% fwd{h}d', df.vr <= th, f)
    row(f'MC-01 placebo VIX>=+10% fwd{h}d', df.vr >= 0.10, f)
pd.set_option('display.width', 200)
print(pd.DataFrame(out).to_string(index=False))

# Robustness for MC-01 (added same run): crisis removed (2008-01..2009-06, 2020-02-15..2020-06), events de-clustered (>=5 days apart),
# and split by VIX level before the fall (<15, 15-20, >20).
print('\nMC-01 robustness')
crisis = ((df.index >= '2008-01-01') & (df.index <= '2009-06-30')) | ((df.index >= '2020-02-15') & (df.index <= '2020-06-30'))
lvl = v.reindex(df.index).shift(1)
f5 = df.close.shift(-5)/df.close - 1; f20 = df.close.shift(-20)/df.close - 1
ev = df.index[(df.vr <= -0.10) & ~crisis]
keep, last = [], None
for d in ev:
    if last is None or (df.index.get_loc(d) - df.index.get_loc(last)) >= 5: keep.append(d); last = d
base5, base20 = f5[~crisis].mean()*100, f20[~crisis].mean()*100
for nm, sel in [('noCrisis declustered', keep), ('VIXprev<15', [d for d in keep if lvl[d] < 15]), ('VIXprev15-20', [d for d in keep if 15 <= lvl[d] < 20]), ('VIXprev>=20', [d for d in keep if lvl[d] >= 20])]:
    a, b = f5[sel].dropna(), f20[sel].dropna()
    print(f'{nm:22s} n={len(a):3d} fwd5 {a.mean()*100:+.2f}% up {(a>0).mean()*100:.0f}% | fwd20 {b.mean()*100:+.2f}% up {(b>0).mean()*100:.0f}% | base5 {base5:+.2f} base20 {base20:+.2f}')
print('recent events:', [str(d.date()) for d in keep[-8:]])
