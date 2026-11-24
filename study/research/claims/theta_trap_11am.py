"""DHAN-08/11 '11 AM Theta Trap' premise test (Dhan transcript 1VC4j2aYINQ):
15-min ADX(14) falling and <20 around 10:30-11:00 -> market stays quiet after 11:00 -> sell options.
Test: at 11:00 (after 10:45 bar closes) classify day; measure 11:00->15:15 move |close-p11|% and range%.
Data: intraday_hist m15 NIFTY/BANKNIFTY (Aug-Nov 2026 only, ~3.5 months). Short-straddle proxy:
seller wins if |move| < X (X = median |move| of all days), i.e. premium priced on average day."""
import sys, pandas as pd, numpy as np
def adx(d, n=14):
    h, l, c = d.high, d.low, d.close
    up = h.diff(); dn = -l.diff()
    pdm = np.where((up > dn) & (up > 0), up, 0.0); ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    a = lambda x: pd.Series(x, index=d.index).ewm(alpha=1/n, adjust=False).mean()
    atr = a(tr); pdi = 100*a(pdm)/atr; ndi = 100*a(ndm)/atr
    dx = 100*(pdi-ndi).abs()/(pdi+ndi)
    return dx.ewm(alpha=1/n, adjust=False).mean()
out = []
for f in sys.argv[1:]:
    d = pd.read_csv(f, parse_dates=['time']).set_index('time')
    d['adx'] = adx(d)
    rows = []
    for day, g in d.groupby(d.index.date):
        g = g.between_time('09:15', '15:15')
        b = g.between_time('10:15', '10:45')
        if len(b) < 3 or len(g) < 20: continue
        p11 = b.close.iloc[-1]; aft = g.between_time('11:00', '15:15')
        a1 = b.adx.iloc[-1]; a0 = b.adx.iloc[0]
        rows.append(dict(day=day, adx=a1, falling=a1 < a0, move=abs(aft.close.iloc[-1]/p11-1)*100,
                         rng=(aft.high.max()-aft.low.min())/p11*100,
                         ext=max(aft.high.max()/p11-1, 1-aft.low.min()/p11)*100))
    R = pd.DataFrame(rows); thr = R.move.median(); ethr = R.ext.median()
    R['grp'] = np.where(R.falling & (R.adx < 20), 'A: falling&<20', np.where(R.falling, 'B: falling&>=20', 'C: rising'))
    out.append(f"== {f.split('/')[-1]}  days {len(R)} ({R.day.min()}..{R.day.max()})  median |move| {thr:.2f}%  median max-excursion {ethr:.2f}%")
    for gname, g in R.groupby('grp'):
        out.append(f"  {gname:16s} n{len(g):3d} |move| mean {g.move.mean():.2f}% med {g.move.median():.2f}  range med {g.rng.median():.2f}%  ext med {g.ext.median():.2f}  seller-win(|move|<med) {100*(g.move<thr).mean():.0f}%  quiet(ext<med) {100*(g.ext<ethr).mean():.0f}%")
    for lab, s in [('last 2m', R.day >= (R.day.max() - pd.Timedelta(days=61)))]:
        g = R[s & (R.grp == 'A: falling&<20')]; o = R[s & (R.grp != 'A: falling&<20')]
        out.append(f"  {lab}: A n{len(g)} |move| med {g.move.median():.2f} vs others n{len(o)} {o.move.median():.2f}")
print('\n'.join(out))
