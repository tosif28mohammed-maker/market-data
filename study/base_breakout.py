"""Ravindra Rokade type 3-step setup (user 10 Nov 2026, podcast summary): (1) strong move on big volume (institutions),
(2) base: price rests in a tight range, volume dries up, holds the upper half of the move, (3) breakout from the base on volume.
Entry = close of breakout day (circuit-locked days skipped), stop = base low, risk 1% of capital per trade ('trade to lose').
Test: 1,500 shares 2003-26. Excess vs all shares after 0.25% cost, 20/60 days; R-multiples with the stop (exit at stop or after 60
days); eras; CONTROL = same breakout+volume without steps 1-2; variants of base length 20/30/40 days."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); MD = []
def md(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); MD.append(s)
P = nc.load(); A, O, H, L, C, V = (P[k] for k in ('a', 'o', 'h', 'l', 'c', 'v'))
A = A.loc[:, A.notna().sum() > 500]; cols = A.columns; O, H, L, C, V = (x[cols] for x in (O, H, L, C, V))
adj = A / C; Ha, La = H * adj, L * adj
v50 = V.rolling(50, min_periods=30).mean().shift(1); ok = (H - L) > 0.002 * C
f = {h: (A.shift(-h) / A - 1).clip(-0.7, 2.0) for h in (20, 60)}; fx = {h: x.sub(x.mean(axis=1), axis=0) for h, x in f.items()}
idx = A.index
ERAS = [('2003-12', '2003', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'), ('Nov23-ab', '2023-11', '2026')]
def setup(N, full=True):
    bh, bl = Ha.rolling(N).max().shift(1), La.rolling(N).min().shift(1)
    brk = (A > bh) & (V >= 1.5 * v50) & ok
    brk &= ~((A.shift(1) > bh.shift(1)))  # first close above the base
    if not full: return brk, bl
    tight = (bh / bl - 1) <= 0.15
    p0, p1 = A.shift(N + 21), A.shift(N + 1)
    move = (p1 / p0 - 1) >= 0.20
    mvol = V.rolling(20).mean().shift(N + 1) >= 1.5 * V.rolling(50).mean().shift(N + 21)
    dry = V.rolling(N).mean().shift(1) <= 0.7 * V.rolling(20).mean().shift(N + 1)
    hold = bl >= p0 + 0.5 * (p1 - p0)
    return brk & tight & move & mvol & dry & hold, bl
def report(sig, bl, name):
    n = int(sig.values.sum()); md(f'\n### {name}: {n} signal ({n / max(sig.any(axis=1).sum(), 1):.1f} prati signal-din, {sig.any(axis=1).sum()} din)')
    for h in (20, 60):
        s = (fx[h].where(sig).mean(axis=1) * 100 - 0.25).dropna()
        parts = [f'{nm} {s[a:b].mean():+.2f}% (t {s[a:b].mean() / s[a:b].std() * np.sqrt(len(s[a:b])):.1f})' for nm, a, b in ERAS if len(s[a:b]) > 10]
        md(f'- {h} din bazaar se (kharcha ghata kar): {s.mean():+.2f}% (t {s.mean() / s.std() * np.sqrt(len(s)):.1f}) | ' + ' | '.join(parts))
    # R-multiples with stop at base low
    ii, jj = np.where(sig.values); Av, Lv, Ov, blv = A.values, La.values, (O * adj).values, bl.values; rows = []
    for i, j in zip(ii, jj):
        e, st = Av[i, j], blv[i, j]
        if not np.isfinite(st) or st >= e or i + 61 >= len(Av): continue
        risk = e - st
        if risk / e > 0.20: continue
        ex = np.nan
        for k in range(i + 1, i + 61):
            lo, op = Lv[k, j], Ov[k, j]
            if np.isfinite(lo) and lo <= st: ex = min(st, op) if np.isfinite(op) else st; break
        if not np.isfinite(ex):
            ex = Av[i + 60, j]
            if not np.isfinite(ex): continue
        rows.append((idx[i], (ex - e - 0.0025 * e) / risk, risk / e))
    T = pd.DataFrame(rows, columns=['date', 'R', 'riskpct']).set_index('date').sort_index()
    if len(T) < 30: md('- R: bahut kam trade'); return T
    def rl(x): return f'{len(x)} trade, jeet {(x.R > 0).mean() * 100:.0f}%, ausat {x.R.mean():+.2f}R, jeet par {x.R[x.R > 0].mean():+.1f}R, haar par {x.R[x.R <= 0].mean():+.1f}R'
    md(f'- Stop = base ka low (ausat doori {T.riskpct.mean() * 100:.1f}%), 60 din ya stop: ' + rl(T))
    md('  - daur-war: ' + ' | '.join(f'{nm}: {rl(T[a:b])}' for nm, a, b in ERAS if len(T[a:b]) > 20))
    md(f'  - 1% jokhim prati trade ho to ausat {T.R.mean():+.2f}% capital prati trade; lagatar sabse lambi haar: {int((T.R <= 0).astype(int).groupby((T.R > 0).cumsum()).sum().max())} trade')
    return T
md('# 3-step setup: badi chaal (volume) -> base (shaant, volume sookha) -> volume ke saath breakout')
for N in (20, 30, 40):
    s, bl = setup(N); report(s, bl, f'POORA SETUP, base {N} din')
s, bl = setup(20, full=False); report(s, bl, 'CONTROL: sirf 20 din ka breakout + volume (step 1-2 ke bina)')
open(os.path.join(R, 'study', 'results', 'base_breakout.md'), 'w').write('\n'.join(MD) + '\n')
