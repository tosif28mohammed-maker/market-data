# ROBOT
"""AI-062853 Hurst filter (trend vs mean-reversion) + AI-9197A2 (5y price CAGR > market 5y CAGR).
Monthly starts 2004-2026. Hurst via variance ratio on last 250 daily log returns (q=10):
H = 0.5 + 0.5*log(VR)/log(q). Inside H-high (>0.55) group: buy 6m winners (trend); inside H-low (<0.45): buy 1m losers (reversion).
Forward 1m (and 12m for CAGR rule) excess vs equal-weight all stocks, costs 0.25% per trade. Universe = current u1000/u2000 (survivorship note)."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, REPO
P = load(); a = P['a']
lr = np.log(a).diff().where(lambda x: x.abs() < 0.4)
me = a.resample('ME').last()
dates = [d for d in me.index if d.year >= 2004]
q = 10
out = []
for i, d in enumerate(dates[:-1]):
    w = lr.loc[:d].iloc[-250:]
    ok = w.notna().sum() >= 230
    w = w.loc[:, ok]
    v1 = w.var()
    vq = w.rolling(q).sum().iloc[q-1::q].var()
    H = 0.5 + 0.5*np.log((vq/(q*v1)).clip(lower=1e-6))/np.log(q)
    p = me.loc[:d]
    r6 = (p.iloc[-1]/p.iloc[-7]-1) if len(p) > 7 else None
    r1 = p.iloc[-1]/p.iloc[-2]-1
    nxt = dates[i+1]
    f1 = (me.loc[nxt]/me.loc[d]-1).where(lambda x: x.abs() < 3)
    cols = H.index.intersection(f1.dropna().index)
    if len(cols) < 150 or r6 is None: continue
    m = f1[cols].mean()
    H = H[cols]; r6c = r6[cols]; r1c = r1[cols]
    hi, lo = H[H > 0.55].index, H[H < 0.45].index
    def ex(ix): return (f1[ix].mean()-m)*100 if len(ix) >= 10 else np.nan
    trend_hi = r6c[hi][r6c[hi] > r6c[hi].quantile(0.7)].index
    trend_lo = r6c[lo][r6c[lo] > r6c[lo].quantile(0.7)].index
    rev_lo = r1c[lo][r1c[lo] < r1c[lo].quantile(0.3)].index
    rev_hi = r1c[hi][r1c[hi] < r1c[hi].quantile(0.3)].index
    trend_all = r6c[r6c > r6c.quantile(0.7)].index
    rev_all = r1c[r1c < r1c.quantile(0.3)].index
    out.append(dict(date=d, H_med=H.median(), trend_Hhi=ex(trend_hi), trend_Hlo=ex(trend_lo), trend_all=ex(trend_all),
                    rev_Hlo=ex(rev_lo), rev_Hhi=ex(rev_hi), rev_all=ex(rev_all), Hhi=ex(hi), Hlo=ex(lo)))
R = pd.DataFrame(out).set_index('date')
def era(d): return '2004-12' if d.year <= 2012 else ('2013-20' if d.year <= 2020 else '2021-26')
L = [f"Hurst (VR q=10, 250d) median H across months {R.H_med.median():.3f}; months {len(R)}",
     "1m excess vs EW market (before cost; trade cost 0.25%/month if fully rotated):"]
for c in ['trend_Hhi','trend_all','trend_Hlo','rev_Hlo','rev_all','rev_Hhi','Hhi','Hlo']:
    s = R[c].dropna()
    L.append(f"  {c:10s} mean {s.mean():+.2f}% median {s.median():+.2f}% beat {100*(s>0).mean():.0f}% n={len(s)} | " +
             ' '.join(f"{e} {y.mean():+.2f}" for e, y in s.groupby(s.index.map(era))) +
             ' | last6m ' + f"{s.iloc[-6:].mean():+.2f} last4m {s.iloc[-4:].mean():+.2f} last2m {s.iloc[-2:].mean():+.2f}")
# AI-9197A2: 5y price CAGR > EW market 5y CAGR -> next 12m
out2 = []
for d in dates:
    if d.year < 2008: continue
    p = me.loc[:d]
    if len(p) < 61: continue
    c5 = (p.iloc[-1]/p.iloc[-61]-1).where(lambda x: x.abs() < 50)
    j = me.index.get_loc(d)
    if j+12 >= len(me): continue
    f12 = (me.iloc[j+12]/me.loc[d]-1).where(lambda x: x.abs() < 20)
    cols = c5.dropna().index.intersection(f12.dropna().index)
    if len(cols) < 150: continue
    m = f12[cols].mean(); mc = c5[cols].mean()  # EW benchmark proxy
    ins = cols[c5[cols] > c5[cols].median()]; rest = cols.difference(ins)
    top = cols[c5[cols] > c5[cols].quantile(0.9)]
    out2.append(dict(date=d, beat=(f12[ins].mean()-f12[rest].mean())*100, top10=(f12[top].mean()-m)*100,
                     hit=(f12[ins] > m).mean()*100))
R2 = pd.DataFrame(out2).set_index('date')
L.append("AI-9197A2: 5y price CAGR above median (EW mkt proxy) -> next 12m:")
for c in ['beat','top10']:
    s = R2[c]
    L.append(f"  {c}: mean {s.mean():+.1f}% median {s.median():+.1f}% starts>0 {100*(s>0).mean():.0f}% | " +
             ' '.join(f"{e} {y.mean():+.1f}" for e, y in s.groupby(s.index.map(era))))
L.append(f"  stock hit (above-median group beating mkt) {R2.hit.mean():.0f}%")
txt = '\n'.join(L); print(txt)
od = f'{REPO}/study/research/r058_hurst_5ycagr'; os.makedirs(od, exist_ok=True)
open(f'{od}/result.txt', 'w').write(txt + '\n')
