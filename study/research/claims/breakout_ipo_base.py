"""Base-breakout (Setup A) + IPO-base (Setup B) backtest — rules from friend's-Claude spec (O'Neil/Minervini), 26 Nov 2026.
Rules fixed BEFORE results:
 Trend Template (Minervini 8): C>SMA150&SMA200, SMA150>SMA200, SMA200>SMA200[-21], SMA50>SMA150&SMA200, C>SMA50,
   C>=1.30*min(L,252), C>=0.75*max(H,252), RS>=70 (RS = pct rank of 0.4R63+0.2R126+0.2R189+0.2R252).
 Base (A): base_high = max(H over previous N days, N in 25/50/100), base_low = min(L same days), depth=(bh-bl)/bh <= D (15/25/35).
   Breakout day: C > bh*1.001 and C <= bh*1.05 (not extended). Optional: V >= 1.4*SMA50(V); dry-up mean(V prev 10d) < 0.8*SMA50(V).
   Market filter optional: Nifty > SMA200 and SMA200 rising (21d).
 Setup B (IPO): first trade date >= 2004-01 (proxy listing). Signal day 10..60 after listing: C > max(H since listing excl. today)*1.001,
   depth since listing <= 30% (alt 50), V >= 1.5*mean(V from day 3); listing day excluded from base.
 Entry: signal-day close (= our 2:15-3:25 buy). Costs 0.25% + slippage 0.10%.
 Exits: X1 = stop -8% (fill min(open,stop)), target +25%, failed (close < pivot*0.97 within 10d), trail close<SMA50, max 120d.
        X2 = stop -8%, failed rule, trail close<SMA50 only (no target), max 250d.
 One open trade per stock per config. Compare: same exits on random Trend-Template days (placebo).
"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
import ni_common as nc
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.environ.get('OUT', os.path.join(REPO, 'study', 'results'))
CST = 0.35
P = nc.load()
c = P['a']; o = P['o']; h = P['h']; l = P['l']; v = P['v']
dates = c.index; syms = c.columns
s50, s150, s200 = [c.rolling(n, min_periods=n).mean() for n in (50, 150, 200)]
v50 = v.rolling(50, min_periods=40).mean()
R = lambda n: c / c.shift(n) - 1
score = 0.4 * R(63) + 0.2 * R(126) + 0.2 * R(189) + 0.2 * R(252)
rs = score.rank(axis=1, pct=True) * 100
tt = ((c > s150) & (c > s200) & (s150 > s200) & (s200 > s200.shift(21)) & (s50 > s150) & (s50 > s200) & (c > s50)
      & (c >= 1.3 * l.rolling(252, min_periods=252).min()) & (c >= 0.75 * h.rolling(252, min_periods=252).max()) & (rs >= 70))
nf = pd.read_csv(os.path.join(REPO, 'data', 'NIFTY.csv'), parse_dates=[0], index_col=0).iloc[:, 3].reindex(dates).ffill()
n200 = nf.rolling(200).mean(); mkt_ok = ((nf > n200) & (n200 > n200.shift(21))).values
volr = (v / v50).values; dry = (v.shift(1).rolling(10).mean() / v50).values
C, O, H, L, S50 = c.values, o.values, h.values, l.values, s50.values
T, N = C.shape


def sim(i, j, pivot, mode):
    e = C[i, j]; stop = e * 0.92; tgt = e * 1.25; maxd = 120 if mode == 1 else 250
    for k in range(i + 1, min(i + maxd + 1, T)):
        if np.isnan(C[k, j]):
            continue
        if L[k, j] <= stop:
            return min(O[k, j], stop) / e - 1, k, 'stop'
        if mode == 1 and H[k, j] >= tgt:
            return max(O[k, j], tgt) / e - 1, k, 'target'
        if k - i <= 10 and C[k, j] < pivot * 0.97:
            return C[k, j] / e - 1, k, 'failed'
        if C[k, j] < S50[k, j]:
            return C[k, j] / e - 1, k, 'trail'
    k = min(i + maxd, T - 1)
    while k > i and np.isnan(C[k, j]):
        k -= 1
    return C[k, j] / e - 1, k, 'time'


def run(sig, piv, name, feats):
    rows = []
    for mode in (1, 2):
        for j in range(N):
            idx = np.flatnonzero(sig[:, j]); busy = -1
            for i in idx:
                if i <= busy or i >= T - 2:
                    continue
                r, k, why = sim(i, j, piv[i, j], mode)
                busy = k
                d = dict(setup=name, exit=f'X{mode}', sym=syms[j], date=dates[i], ret=r * 100 - CST, days=k - i, why=why)
                for fk, fv in feats.items():
                    d[fk] = fv[i, j] if fv.ndim == 2 else fv[i]
                rows.append(d)
    return rows


ttv = tt.values
rows = []
for Nb in (25, 50, 100):
    bh = h.shift(1).rolling(Nb, min_periods=Nb).max().values
    bl = l.shift(1).rolling(Nb, min_periods=Nb).min().values
    depth = (bh - bl) / bh * 100
    sig = ttv & (C > bh * 1.001) & (C <= bh * 1.05) & (depth <= 35)
    rows += run(sig, bh, f'A_N{Nb}', dict(depth=depth, volr=volr, dry=dry, mkt=mkt_ok.astype(float)))
# placebo: random TT days (5% sample), same exits
rng = np.random.default_rng(0)
plc = ttv & (rng.random(ttv.shape) < 0.05)
plc_all = ~np.isnan(C) & ~np.isnan(S50) & (rng.random(ttv.shape) < 0.01)
rows += run(plc_all, C * 1.0, 'PLACEBO_ALL', dict(depth=np.zeros_like(C), volr=volr, dry=dry, mkt=mkt_ok.astype(float)))
rows += run(plc, C * 1.0, 'PLACEBO_TT', dict(depth=np.zeros_like(C), volr=volr, dry=dry, mkt=mkt_ok.astype(float)))
# Setup B IPO base
first = c.apply(lambda s: s.first_valid_index())
ipo = first[first >= pd.Timestamp('2004-01-01')]
sigB = np.zeros_like(ttv); pivB = np.full(C.shape, np.nan); depB = np.full(C.shape, np.nan); vB = np.full(C.shape, np.nan); ageB = np.full(C.shape, np.nan)
for s, d0 in ipo.items():
    j = syms.get_loc(s); i0 = dates.get_loc(d0)
    for i in range(i0 + 10, min(i0 + 61, T)):
        hh = np.nanmax(H[i0 + 1:i, j]); ll = np.nanmin(L[i0 + 1:i, j])
        if np.isnan(hh) or np.isnan(C[i, j]):
            continue
        mv = np.nanmean(v.values[i0 + 2:i, j])
        if C[i, j] > hh * 1.001 and C[i, j] <= hh * 1.05:
            sigB[i, j] = True; pivB[i, j] = hh; depB[i, j] = (hh - ll) / hh * 100
            vB[i, j] = v.values[i, j] / mv if mv > 0 else np.nan; ageB[i, j] = i - i0
            break  # first breakout only
rows += run(sigB, pivB, 'B_IPO', dict(depth=depB, volr=vB, dry=dry, mkt=mkt_ok.astype(float), age=ageB))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, 'breakout_ipo_trades.csv.gz'), index=False)


def era(d):
    return np.where(d < '2013-01-01', '2003-12', np.where(d < '2021-01-01', '2013-20', '2021-26'))


def summ(g):
    w = g.ret > 0
    aw = g.ret[w].mean(); al = -g.ret[~w].mean()
    return pd.Series(dict(n=len(g), win=round(w.mean() * 100, 1), tgt_hit=round((g.why == 'target').mean() * 100, 1),
                          avg=round(g.ret.mean(), 2), med=round(g.ret.median(), 2), avg_win=round(aw, 2), avg_loss=round(al, 2),
                          wl=round(aw / al, 2) if al > 0 else np.nan, days=round(g.days.mean(), 1)))


df['era'] = era(df.date.values.astype('datetime64[D]').astype(str))
res = []
for (setup, ex), g in df.groupby(['setup', 'exit']):
    variants = {'base': g}
    if setup.startswith('A'):
        for D in (15, 25):
            variants[f'depth<={D}'] = g[g.depth <= D]
        variants['vol1.4'] = g[g.volr >= 1.4]
        variants['vol1.4+dry'] = g[(g.volr >= 1.4) & (g.dry < 0.8)]
        variants['vol1.4+mkt'] = g[(g.volr >= 1.4) & (g.mkt == 1)]
        variants['d25+vol1.4+dry+mkt'] = g[(g.depth <= 25) & (g.volr >= 1.4) & (g.dry < 0.8) & (g.mkt == 1)]
        variants['mkt'] = g[g.mkt == 1]
    if setup == 'B_IPO':
        variants['d30+vol1.5'] = g[(g.depth <= 30) & (g.volr >= 1.5)]
        variants['d30+vol1.5+mkt'] = g[(g.depth <= 30) & (g.volr >= 1.5) & (g.mkt == 1)]
        variants['mkt'] = g[g.mkt == 1]
    if setup.startswith('PLACEBO'):
        variants['mkt'] = g[g.mkt == 1]
    for vn, gg in variants.items():
        if len(gg) < 30:
            continue
        s = summ(gg); s['setup'] = setup; s['exit'] = ex; s['variant'] = vn; s['era'] = 'ALL'; res.append(s)
        for e, ge in gg.groupby('era'):
            if len(ge) >= 20:
                s = summ(ge); s['setup'] = setup; s['exit'] = ex; s['variant'] = vn; s['era'] = e; res.append(s)
R_ = pd.DataFrame(res)[['setup', 'exit', 'variant', 'era', 'n', 'win', 'tgt_hit', 'avg', 'med', 'avg_win', 'avg_loss', 'wl', 'days']]
R_.to_csv(os.path.join(OUT, 'breakout_ipo_summary.csv'), index=False)
pd.set_option('display.width', 220); pd.set_option('display.max_rows', 500)
print(R_.to_string(index=False))
