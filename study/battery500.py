"""Full study battery for a chunk of the Nifty 500 (runs on GitHub Actions).
Usage: python study/battery500.py <u500_dir> <master_dates.csv> <chunk> <n_chunks> <out.csv>
For every stock (real data AND once on shuffled daily moves = chance control):
  calendar  hold-out: Gregorian/Hijri date, weekday, month, week (single + pairs) found in first 2/3 (|z|>=2.5, n>=30)
            must point the same way in the last 1/3 (z>=1.3); 30 shuffles -> p. Same for eras 2013-20 -> 2021-26 and 2021-Oct23 -> Nov23-now.
  MA trend  4 types (SMA, EMA, WMA, HMA) x 71 lengths (2-320): 'above MA = hold'; best in train (smoothed over nearby lengths) -> test.
  MA return buy far below MA (train 10% lowest distance) -> sell at MA touch or 60 days; short mirror.
  Pairs train->test: first 60% -> last 40%; 2013-20 -> 2021-26; 2021-Oct23 -> Nov23-now.
Costs: 0.05% per switch (trend), 0.1% per trade (return)."""
import sys, os, math, itertools, numpy as np, pandas as pd
U, MASTER, K, N, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
L = pd.read_csv(os.path.join(U, 'nifty500.csv')); master = pd.to_datetime(pd.read_csv(MASTER).date)
HJ = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hijri_tbla.csv'), parse_dates=['date']).set_index('date').hijri
TYPES = ['SMA', 'EMA', 'WMA', 'HMA']
LENS = np.r_[np.arange(2, 21), np.arange(22, 61, 2), np.arange(65, 121, 5), np.arange(130, 321, 10)]
SEG = {'E3': ('2013-01-01', '2020-12-31'), 'E4': ('2021-01-01', '2030-01-01'), 'R1': ('2021-01-01', '2023-10-31'), 'R2': ('2023-11-01', '2030-01-01')}
PAIRS = ['split', 'E3E4', 'R1R2']
rng = np.random.default_rng(1000 + K)
def clean(s):
    f = os.path.join(U, 'daily', f'{s}.csv.gz')
    if not os.path.exists(f): return None
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close'])
    d = d[d.date.isin(master) & (d.close > 0)].drop_duplicates('date').sort_values('date').reset_index(drop=True)
    if len(d) < 800: return None
    d['pct'] = d.close.pct_change() * 100
    bad = d.pct.abs() > 20; d = d[~(bad | bad.shift(1, fill_value=False))]
    d['y'] = d.date.dt.year; flat = d.groupby('y').pct.apply(lambda x: (x == 0).mean()); d = d[d.y.isin(flat[flat <= 0.2].index)]
    d = d.dropna(subset=['pct']).reset_index(drop=True)
    if len(d) < 800: return None
    h = HJ.reindex(d.date).values; ok = pd.notna(h); d = d[ok].reset_index(drop=True); h = h[ok]
    d['hm'] = [int(x[5:7]) for x in h]; d['hd'] = [int(x[8:]) for x in h]; d['hwk'] = (d.hd - 1) // 7 + 1
    d['wd'] = d.date.dt.dayofweek + 1; d['gd'] = d.date.dt.day; d['gm'] = d.date.dt.month; d['gwk'] = (d.gd - 1) // 7 + 1
    d['up'] = (d.pct > 0).astype(float); return d
COMB = []
for ds in (['wd', 'gm', 'gd', 'gwk'], ['wd', 'hm', 'hd', 'hwk']):
    for k in (1, 2): COMB += [c for c in itertools.combinations(ds, k) if set(c) not in ({'gd', 'gwk'}, {'hd', 'hwk'})]
COMB = list(dict.fromkeys(COMB))
WDN = {1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri'}
def scan(up, codes, tr, te, nmin, keep=False):
    P1 = up[tr].mean(); P2 = up[te].mean(); out = []
    for ci, c in enumerate(codes):
        mx = c.max() + 1
        n1 = np.bincount(c[tr], minlength=mx); k1 = np.bincount(c[tr], weights=up[tr], minlength=mx)
        n2 = np.bincount(c[te], minlength=mx); k2 = np.bincount(c[te], weights=up[te], minlength=mx)
        with np.errstate(all='ignore'):
            z1 = (k1 - n1 * P1) / np.sqrt(n1 * P1 * (1 - P1)); z2 = (k2 - n2 * P2) / np.sqrt(n2 * P2 * (1 - P2))
        g = np.flatnonzero((n1 >= nmin) & (np.abs(z1) >= 2.5) & (n2 >= 10) & (np.sign(z2) == np.sign(z1)) & (np.abs(z2) >= 1.3))
        if keep: out += [(ci, int(x), z1[x], k2[x] / max(n2[x], 1), P2, z2[x]) for x in g]
        else: out.append(len(g))
    return out if keep else sum(out)
def calendar(d):
    up = d.up.values; codes = [d.groupby(list(c)).ngroup().values for c in COMB]; res = {}
    n = len(d); masks = {'cal_holdout': (np.arange(n) < n * 2 // 3, np.arange(n) >= n * 2 // 3, 30)}
    for nm, (a, b) in (('cal_E3E4', ('E3', 'E4')), ('cal_R1R2', ('R1', 'R2'))):
        tr = ((d.date >= SEG[a][0]) & (d.date <= SEG[a][1])).values; te = ((d.date >= SEG[b][0]) & (d.date <= SEG[b][1])).values
        if tr.sum() >= 500 and te.sum() >= 500: masks[nm] = (tr, te, 30 if nm == 'cal_E3E4' else 20)
    for nm, (tr, te, nmin) in masks.items():
        real = scan(up, codes, tr, te, nmin, keep=True); sh = []
        for _ in range(30):
            u = up.copy(); u[tr] = rng.permutation(u[tr]); u[te] = rng.permutation(u[te]); sh.append(scan(u, codes, tr, te, nmin))
        rules = []
        for (ci, x, z1, upn, P2, z2) in sorted(real, key=lambda r: -abs(r[5]))[:4]:
            i = np.flatnonzero(codes[ci] == x)[0]; parts = []
            for k in COMB[ci]:
                v = int(d.loc[i, k]); parts.append({'wd': WDN.get(v, v), 'gm': f'M{v}', 'gd': f'D{v}', 'gwk': f'W{v}', 'hm': f'HM{v}', 'hd': f'H{v}', 'hwk': f'HW{v}'}[k])
            rules.append(f"{'+'.join(parts)} {'Up' if z1 > 0 else 'Down'} {upn:.0%}")
        res[nm] = len(real); res[nm + '_chance'] = round(float(np.mean(sh)), 2); res[nm + '_p'] = round(float(np.mean(np.array(sh) >= len(real))), 3) if real else 1.0
        res[nm + '_rules'] = '; '.join(rules)
    return res
def wma(p, n):
    w = np.arange(1, n + 1, dtype=float); o = np.full(len(p), np.nan)
    if len(p) >= n: o[n - 1:] = np.convolve(p, w[::-1], 'valid') / w.sum()
    return o
def mas(p, n):
    e = pd.Series(p).ewm(span=n, adjust=False).mean().to_numpy(copy=True); e[:n] = np.nan
    h = wma(2 * np.nan_to_num(wma(p, max(n // 2, 1)), nan=p[0]) - np.nan_to_num(wma(p, n), nan=p[0]), max(int(round(np.sqrt(n))), 1)); h[:n] = np.nan
    return {'SMA': pd.Series(p).rolling(n).mean().to_numpy(copy=True), 'EMA': e, 'WMA': wma(p, n), 'HMA': h}
def smooth_best(a):
    if np.all(np.isnan(a)): return None
    o = np.full_like(a, np.nan)
    for j, Lj in enumerate(LENS):
        w = (LENS >= Lj * 0.85) & (LENS <= Lj * 1.15)
        with np.errstate(all='ignore'): o[:, j] = np.nanmean(a[:, w], axis=1)
    o[np.isnan(a)] = np.nan
    return np.unravel_index(np.nanargmax(o), o.shape) if not np.all(np.isnan(o)) else None
def tsh(a, r):
    if len(r) < 250 or a.sum() < 20 or (1 - a).sum() < 20: return np.nan
    ch = np.abs(np.diff(np.r_[a[0], a])); x = a * r - 0.0005 * ch; return x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan
def trades(p, m, ent, side, a, b, drift):
    hit = np.flatnonzero((p >= m) if side > 0 else (p <= m)); E = np.flatnonzero(ent[a:b]) + a; out = []; cur = a
    while True:
        k = np.searchsorted(E, cur)
        if k >= len(E): break
        t = E[k]; j = np.searchsorted(hit, t + 1); e = hit[j] if j < len(hit) else 10 ** 9
        touched = e <= t + 60 and e < b
        if not touched: e = min(t + 60, b - 1)
        if e <= t: break
        r = side * (p[e] / p[t] - 1) - 0.001; out.append((r, r - side * drift * (e - t))); cur = e + 1
    return np.array(out) if out else np.zeros((0, 2))
def ma_study(d, r):
    p = np.cumprod(1 + r) * 100; n = len(p); nxt = np.r_[r[1:], np.nan]; dt = d.date.values
    def rng_of(name):
        if name == 'old': return 0, int(n * 0.6)
        if name == 'new': return int(n * 0.6), n
        a, b = SEG[name]; return int(np.searchsorted(dt, np.datetime64(a))), int(np.searchsorted(dt, np.datetime64(b), side='right'))
    segs = {s: rng_of(s) for s in ('old', 'new', 'E3', 'E4', 'R1', 'R2')}
    okseg = {s: (b - a) >= 500 for s, (a, b) in segs.items()}
    drift = {s: (np.exp(np.log(p[b - 1] / p[a]) / (b - a)) - 1 if okseg[s] else np.nan) for s, (a, b) in segs.items()}
    pairs = {'split': ('old', 'new'), 'E3E4': ('E3', 'E4'), 'R1R2': ('R1', 'R2')}
    T = {s: np.full((len(TYPES), len(LENS)), np.nan) for s in segs}
    RV = {(pn, side, h): np.full((len(TYPES), len(LENS), 5), np.nan) for pn in pairs for side in (0, 1) for h in (0, 1)}
    for j, Lj in enumerate(LENS):
        M = mas(p, int(Lj))
        for i, ty in enumerate(TYPES):
            m = M[ty]; ok = np.isfinite(m) & np.isfinite(nxt); a_ = (p > m).astype(float); dist = np.where(np.isfinite(m), p / m - 1, np.nan); prev = np.r_[np.nan, dist[:-1]]
            for s, (a, b) in segs.items():
                if okseg[s]:
                    z = np.zeros(n, bool); z[a:b] = True; z &= ok; T[s][i, j] = tsh(a_[z], nxt[z])
            for pn, (tr, te) in pairs.items():
                if not (okseg[tr] and okseg[te]): continue
                a, b = segs[tr]; x = dist[a:b]; x = x[np.isfinite(x)]
                if len(x) < 300: continue
                ql, qh = np.percentile(x, [10, 90]); el = (dist <= ql) & (prev > ql); es = (dist >= qh) & (prev < qh)
                for h, sg in enumerate((tr, te)):
                    a, b = segs[sg]
                    for side, ent in ((0, el), (1, es)):
                        Tt = trades(p, m, ent, 1 if side == 0 else -1, a, b, drift[sg]); k = len(Tt)
                        if k >= 5:
                            sd = Tt[:, 1].std(); RV[(pn, side, h)][i, j] = [k, Tt[:, 0].mean() * 100, Tt[:, 1].mean() * 100, Tt[:, 1].mean() / (sd / np.sqrt(k)) if sd > 0 else np.nan, (Tt[:, 0] > 0).mean()]
                        else: RV[(pn, side, h)][i, j, 0] = k
    out = {}
    for pn, (tr, te) in pairs.items():
        if not (okseg[tr] and okseg[te]): continue
        bh = lambda s: (lambda rr: rr.mean() / rr.std() * np.sqrt(252))(nxt[segs[s][0]:segs[s][1]][np.isfinite(nxt[segs[s][0]:segs[s][1]])])
        b = smooth_best(T[tr])
        if b:
            i, j = b; te_ = T[te]; okk = np.isfinite(te_); hold = bh(te)
            pct = float((te_[okk] < te_[i, j]).mean()) if okk.any() else np.nan
            out.update({f'trend_{pn}_MA': f'{TYPES[i]} {LENS[j]}', f'trend_{pn}_train': T[tr][i, j], f'trend_{pn}_test': te_[i, j], f'trend_{pn}_hold': hold, f'trend_{pn}_rank': pct,
                        f'trend_{pn}_pass': bool(te_[i, j] > hold and pct >= 0.75)})
        for side, nm in ((0, 'buy'), (1, 'sell')):
            tt = RV[(pn, side, 0)][:, :, 3].copy(); tt[~(RV[(pn, side, 0)][:, :, 0] >= 8)] = np.nan; b = smooth_best(tt)
            if b:
                i, j = b; x = RV[(pn, side, 1)][i, j]
                out.update({f'{nm}_{pn}_MA': f'{TYPES[i]} {LENS[j]}', f'{nm}_{pn}_n': x[0], f'{nm}_{pn}_ret': x[1], f'{nm}_{pn}_t': x[3], f'{nm}_{pn}_win': x[4],
                            f'{nm}_{pn}_pass': bool(x[0] >= 5 and x[2] > 0 and x[3] >= 1.65)})
    return out
rows = []
syms = L.symbol.tolist()[K::N]
for s in syms:
    d = clean(s)
    if d is None: print(s, 'skip'); continue
    rec = dict(symbol=s, company=L.set_index('symbol').company.get(s), industry=L.set_index('symbol').industry.get(s), start=str(d.date.min().date()), days=len(d))
    rec.update(calendar(d))
    r = d.pct.values / 100; rec.update(ma_study(d, r))
    sh = ma_study(d, rng.permutation(r)); rec.update({f'shuf_{k}': v for k, v in sh.items() if k.endswith('_pass')})
    rows.append(rec); print(s, 'done', flush=True)
pd.DataFrame(rows).to_csv(OUT, index=False)
