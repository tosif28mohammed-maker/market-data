"""r050 (22 Nov 2026) i01: Results-day surprise drift (PEAD, price-based proxy) on all stocks 2003-2026.
RULES WRITTEN BEFORE RESULTS:
 results window = trading days from day 15 to day 60 after a quarter end (Jul15-Aug29, Oct15-Nov29, Jan15-Feb28, Apr15-May30).
 EVENT_UP  = day excess return vs equal-weight market >= +5% AND volume >= 3x its 50-day median (announcement proxy),
             first such day per stock per window. EVENT_DN = same with <= -5%.
 CONTROL   = same rule on days OUTSIDE the results windows (non-results news shocks).
 trade: buy next day OPEN; A) hold 20 / 60 trading days, excess vs market (same span), cost 0.25%;
        B) stop = event-day low (skip if risk >10% or <1.5%), target 2R, max 60 days, stop first if same bar, cost 0.25%.
 eras 2003-12 / 2013-20 / 2021-26 + last 24/12/6/4/2 months; liquidity D dropped (ni_common).
 scenarios: winners vs losers by market vs 200DMA, stock prior 60d return, close-location on event day, gap size,
            size (traded value rank), and a chance check = control events.
"""
import os, sys, numpy as np, pandas as pd
R = '/home/claude/market-data'; sys.path.insert(0, f'{R}/study')
from ni_common import load
P = load(); A, C, O, H, L, V = P['a'], P['c'], P['o'], P['h'], P['l'], P['v']
ret = A.pct_change(fill_method=None); ret = ret.where(ret.abs() < 0.4)
mkt = ret.mean(axis=1)
ex = ret.sub(mkt, axis=0)
vmed = V.rolling(50, min_periods=30).median().shift(1)
vr = V / vmed
idx = A.index
q = idx.to_period('Q')
qend = (q - 1).end_time.normalize()  # previous quarter end
dsq = np.asarray((idx - qend).days)
inwin = pd.Series((dsq >= 15) & (dsq <= 60), index=idx)
winid = pd.Series(np.where(inwin, (idx.year * 10 + idx.quarter), -1), index=idx)
nif = pd.read_csv(f'{R}/data/NIFTY.csv', parse_dates=['date']).set_index('date').close
mk_idx = (1 + mkt.fillna(0)).cumprod()
mk200 = (mk_idx / mk_idx.rolling(200).mean() - 1).reindex(idx)
tvrank = (C * V).rolling(126, min_periods=60).median().rank(axis=1, ascending=False)
p60 = A / A.shift(60) - 1
clv = ((C - L * C / C) - (L)) / (H - L)  # placeholder overwritten below
clv = (P['a'] - L) / (H - L)  # adj close inside adj range
gap = O / A.shift(1) - 1
up_sig = (ex >= 0.05) & (vr >= 3)
dn_sig = (ex <= -0.05) & (vr >= 3)
Av, Ov, Hv, Lv = A.values, O.values, H.values, L.values
mkv = mk_idx.values
rows = []
def collect(sig, kind):
    S = sig.values
    for j, s in enumerate(A.columns):
        ii = np.where(S[:, j])[0]
        seen = set()
        for i in ii:
            if i + 61 >= len(idx): continue
            w = winid.iloc[i]
            iswin = inwin.iloc[i]
            key = (w if iswin else ('out', idx[i].year, idx[i].month))
            if key in seen: continue
            seen.add(key)
            e = Ov[i + 1, j]
            if not np.isfinite(e) or e <= 0: continue
            rec = dict(sym=s, date=idx[i], kind=kind, win=bool(iswin), mk200=mk200.iloc[i], p60=p60.iat[i, j], clv=clv.iat[i, j],
                       gap=gap.iat[i, j], ex0=ex.iat[i, j], rank=tvrank.iat[i, j])
            for h in (20, 60):
                x = Av[i + h, j]
                if np.isfinite(x):
                    rec[f'x{h}'] = ((x / e - 1) - (mkv[i + h] / mkv[i] - 1)) * 100 - 0.25
            # B: stop/target (long for UP, short for DN)
            lo, hi = Lv[i, j], Hv[i, j]
            if kind == 'UP':
                risk = (e - lo) / e
                if 0.015 <= risk <= 0.10:
                    tgt = e * (1 + 2 * risk); stp = lo; res = None
                    for k in range(i + 1, i + 61):
                        if Lv[k, j] <= stp: res = (stp / e - 1); break
                        if Hv[k, j] >= tgt: res = 2 * risk; break
                    if res is None: res = Av[i + 60, j] / e - 1; hit = 'time'
                    else: hit = 'tgt' if res > 0 else 'stop'
                    rec.update(B=res * 100 - 0.25, Bhit=hit, risk=risk * 100)
            else:
                risk = (hi - e) / e
                if 0.015 <= risk <= 0.10:
                    tgt = e * (1 - 2 * risk); stp = hi; res = None
                    for k in range(i + 1, i + 61):
                        if Hv[k, j] >= stp: res = -(stp / e - 1); break
                        if Lv[k, j] <= tgt: res = 2 * risk; break
                    if res is None: res = -(Av[i + 60, j] / e - 1); hit = 'time'
                    else: hit = 'tgt' if res > 0 else 'stop'
                    rec.update(B=res * 100 - 0.25, Bhit=hit, risk=risk * 100)
            rows.append(rec)
collect(up_sig, 'UP'); collect(dn_sig, 'DN')
E = pd.DataFrame(rows); E.to_csv(f'{R}/study/research/pead_events.csv', index=False)
last = E.date.max()
def summ(d, lab):
    b = d.dropna(subset=['B'])
    hit = (b.Bhit == 'tgt').mean() * 100 if len(b) else np.nan
    w = b.B[b.B > 0].mean(); l = b.B[b.B <= 0].mean()
    print(f'{lab:28s} n{len(d):6d} x20 {d.x20.mean():+.2f} x60 {d.x60.mean():+.2f} (x60>0 {100*(d.x60>0).mean():.0f}%) | B n{len(b)} tgt {hit:.1f}% win {100*(b.B>0).mean():.0f}% avgW {w:+.2f} avgL {l:+.2f} ratio {abs(w/l) if l else np.nan:.2f} net {b.B.mean():+.2f}')
for kind in ['UP', 'DN']:
    print(f'\n===== {kind} (DN = x is long-side excess; B is SHORT trade) =====')
    for win in [True, False]:
        d = E[(E.kind == kind) & (E.win == win)]
        summ(d, f'{"RESULTS" if win else "CONTROL"} ALL')
        if win:
            for era, a, b in [('2003-12', '2003', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026')]:
                summ(d[(d.date >= a) & (d.date <= b + '-12-31')], f'  {era}')
            for mths in [24, 12, 6, 4]:
                summ(d[d.date >= last - pd.DateOffset(months=mths)], f'  last {mths}m')
    d = E[(E.kind == kind) & E.win]
    print('  -- scenarios (RESULTS events) --')
    d = d.assign(mk=np.where(d.mk200 > 0, 'mkt>200', 'mkt<200'), pri=pd.qcut(d.p60, 3, labels=['p60 low', 'p60 mid', 'p60 high']),
                 cl=pd.cut(d.clv, [-1, .5, .8, 2], labels=['close weak', 'close mid', 'close near high']),
                 gp=pd.cut(d.gap, [-1, -0.02, 0.02, 0.05, 5], labels=['gap<-2', 'gap~0', 'gap2-5', 'gap>5']),
                 sz=pd.cut(d['rank'], [0, 200, 600, 5000], labels=['top200', '200-600', 'small']))
    for c in ['mk', 'pri', 'cl', 'gp', 'sz']:
        for k, g in d.groupby(c, observed=True):
            summ(g, f'    {c}={k}')
