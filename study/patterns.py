"""Classic chart patterns tested on every stock (user, 2 Nov 2026): Head & Shoulders, Inverse H&S, Cup & Handle, Bull Flag,
Ascending / Descending / Symmetrical Triangle.
Swings come from a zigzag on the close (threshold = 3 x the stock's median daily range %, kept between 4% and 15%); a swing point is
used only after it is confirmed (no look-ahead). Signal = first close beyond the neckline / rim / flag top / triangle line.
Outcome over the next 60 trading days: did the textbook target come before the stop (pattern's other side)? Plus 10/20/60-day move
in the pattern's direction minus the stock's normal drift. Same detection on shuffled daily moves = chance level.
Usage: python study/patterns.py out.pkl dir1 [dir2 ...]   (env CHUNK=k/N to split work)"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
if os.environ.get('CHUNK'): k, n = map(int, os.environ['CHUNK'].split('/')); files = files[k::n]
rng = np.random.default_rng(42)
def era(y): return '2003-12' if y <= 2012 else '2013-20' if y <= 2020 else '2021-26'
def zigzag(c, thr):
    piv = []; mode = 0; ext_i = 0; ext_p = c[0]   # mode 1 = looking for high, -1 = looking for low
    for i in range(1, len(c)):
        p = c[i]
        if mode == 0:
            if p > ext_p and ext_p >= c[0] * (1 - thr) and False: pass
            if p >= ext_p * (1 + thr): piv.append((ext_i, ext_p, 'L', i)); mode = 1; ext_i, ext_p = i, p
            elif p <= ext_p * (1 - thr): piv.append((ext_i, ext_p, 'H', i)); mode = -1; ext_i, ext_p = i, p
            continue
        if mode == 1:
            if p > ext_p: ext_i, ext_p = i, p
            elif p <= ext_p * (1 - thr): piv.append((ext_i, ext_p, 'H', i)); mode = -1; ext_i, ext_p = i, p
        else:
            if p < ext_p: ext_i, ext_p = i, p
            elif p >= ext_p * (1 + thr): piv.append((ext_i, ext_p, 'L', i)); mode = 1; ext_i, ext_p = i, p
    return piv   # (index, price, type, confirmed_at)
def line(i1, p1, i2, p2, t): return p1 + (p2 - p1) * (t - i1) / (i2 - i1) if i2 != i1 else p1
def first_cross(c, start, end, f, above):
    for t in range(max(start, 1), min(end, len(c))):
        lv = f(t)
        if (above and c[t] > lv and c[t - 1] <= f(t - 1)) or (not above and c[t] < lv and c[t - 1] >= f(t - 1)): return t
    return None
def outcome(c, h, l, t, d, stop, target, drift):
    end = min(t + 60, len(c) - 1); res = 'none'
    for u in range(t + 1, end + 1):
        if (d > 0 and l[u] <= stop) or (d < 0 and h[u] >= stop): res = 'stop'; break
        if (d > 0 and h[u] >= target) or (d < 0 and l[u] <= target): res = 'target'; break
    r = {}
    for k in (10, 20, 60):
        r[f'm{k}'] = d * (c[t + k] / c[t] - 1) - d * drift * k if t + k < len(c) else np.nan
    return res, r
def detect(c, h, l, dates, thr):
    out = []; piv = zigzag(c, thr); n = len(c)
    lr = np.diff(np.log(c)); drift = {}
    yrs = dates.dt.year.values
    for e in ('2003-12', '2013-20', '2021-26'):
        m = np.array([era(y) for y in yrs[1:]]) == e
        drift[e] = float(np.exp(lr[m].mean()) - 1) if m.sum() > 100 else float(np.exp(lr.mean()) - 1)
    def add(kind, t, d, stop, target, extra=''):
        if t is None or t >= n - 1: return
        if (d > 0 and not (stop < c[t] < target)) or (d < 0 and not (target < c[t] < stop)): return
        e = era(dates[t].year); res, r = outcome(c, h, l, t, d, stop, target, drift[e])
        out.append(dict(kind=kind, t=t, date=dates[t], era=e, dir=d, res=res, risk=abs(c[t] / stop - 1), reward=abs(target / c[t] - 1), **r))
    P = piv
    for j in range(4, len(P)):
        a, b, cc, dd, e5 = P[j - 4], P[j - 3], P[j - 2], P[j - 1], P[j]
        # Head & Shoulders (H L H L H) and inverse (L H L H L)
        if a[2] == 'H' and e5[2] == 'H':
            H1, L1, H2, L2, H3 = a, b, cc, dd, e5
            if H2[1] > max(H1[1], H3[1]) * 1.03 and abs(H1[1] - H3[1]) / H2[1] <= 0.08 and H3[0] - H1[0] <= 250:
                nk = lambda t, L1=L1, L2=L2: line(L1[0], L1[1], L2[0], L2[1], t)
                hh = H2[1] - nk(H2[0])
                if hh / H2[1] >= thr:
                    t = first_cross(c, H3[3], H3[3] + 60, nk, above=False)
                    if t is not None and c[H3[3]:t + 1].max() < H2[1]: add('Head & Shoulders', t, -1, H3[1], nk(t) - hh)
        if a[2] == 'L' and e5[2] == 'L':
            L1, H1, L2, H2, L3 = a, b, cc, dd, e5
            if L2[1] < min(L1[1], L3[1]) / 1.03 and abs(L1[1] - L3[1]) / L2[1] <= 0.08 and L3[0] - L1[0] <= 250:
                nk = lambda t, H1=H1, H2=H2: line(H1[0], H1[1], H2[0], H2[1], t)
                hh = nk(L2[0]) - L2[1]
                if hh / L2[1] >= thr:
                    t = first_cross(c, L3[3], L3[3] + 60, nk, above=True)
                    if t is not None and c[L3[3]:t + 1].min() > L2[1]: add('Inverse H&S', t, 1, L3[1], nk(t) + hh)
    for j in range(3, len(P)):
        a, b, cc, dd = P[j - 3], P[j - 2], P[j - 1], P[j]
        # Cup & Handle: H(left rim) L(bottom) H(right rim) L(handle)
        if a[2] == 'H' and dd[2] == 'L':
            depth = (a[1] - b[1]) / a[1]
            if 0.12 <= depth <= 0.40 and abs(cc[1] / a[1] - 1) <= 0.05 and 35 <= cc[0] - a[0] <= 300:
                hd = (cc[1] - dd[1]) / cc[1]
                if hd <= 0.5 * depth and dd[1] > b[1] + 0.5 * (a[1] - b[1]) and dd[0] - cc[0] <= 0.5 * (cc[0] - a[0]):
                    rim = max(a[1], cc[1]); t = first_cross(c, dd[3], dd[3] + 40, lambda t, rim=rim: rim, above=True)
                    if t is not None: add('Cup & Handle', t, 1, dd[1], rim * (1 + depth))
    for j in range(3, len(P)):
        win = [p for p in P[max(0, j - 6):j + 1] if P[j][0] - p[0] <= 150]
        Hs = [p for p in win if p[2] == 'H']; Ls = [p for p in win if p[2] == 'L']
        if len(Hs) < 2 or len(Ls) < 2: continue
        last_conf = P[j][3]
        h1, h2 = Hs[-2], Hs[-1]; l1, l2 = Ls[-2], Ls[-1]
        flat_top = abs(h1[1] / h2[1] - 1) <= 0.02; flat_bot = abs(l1[1] / l2[1] - 1) <= 0.02
        rising = l2[1] > l1[1] * 1.01; falling = h2[1] < h1[1] / 1.01
        if flat_top and rising:
            top = max(h1[1], h2[1]); t = first_cross(c, last_conf, last_conf + 30, lambda t, top=top: top * 1.005, above=True)
            if t is not None: add('Ascending Triangle', t, 1, l2[1], top + (top - l1[1]))
        elif flat_bot and falling:
            bot = min(l1[1], l2[1]); t = first_cross(c, last_conf, last_conf + 30, lambda t, bot=bot: bot / 1.005, above=False)
            if t is not None: add('Descending Triangle', t, -1, h2[1], bot - (h1[1] - bot))
        elif falling and rising:
            up = lambda t, h1=h1, h2=h2: line(h1[0], h1[1], h2[0], h2[1], t); dn = lambda t, l1=l1, l2=l2: line(l1[0], l1[1], l2[0], l2[1], t)
            height = h1[1] - l1[1]; tu = first_cross(c, last_conf, last_conf + 30, up, above=True); td = first_cross(c, last_conf, last_conf + 30, dn, above=False)
            if tu is not None and (td is None or tu < td): add('Symmetrical Triangle (up)', tu, 1, dn(tu), c[tu] + height)
            elif td is not None: add('Symmetrical Triangle (down)', td, -1, up(td), c[td] - height)
    # Bull flag (vectorised candidates, no swing points needed)
    hs = pd.Series(h); ls = pd.Series(l); cs = pd.Series(c); last_t = -100
    for F in range(5, 21):
        fh = hs.shift(1).rolling(F).max().values; fl = ls.shift(1).rolling(F).min().values
        s = np.arange(n) - F - 1                        # pole end = bar just before the flag
        ok = s >= 16
        pole_top = np.where(ok, c[np.clip(s, 0, n - 1)], np.nan)
        pole_bot = np.where(ok, cs.rolling(15).min().values[np.clip(s, 0, n - 1)], np.nan)
        gain = pole_top / pole_bot - 1; ph = pole_top - pole_bot
        cand = ok & (gain >= 0.15) & (c > fh) & (np.r_[np.nan, c[:-1]] <= fh) & (fl >= pole_top - 0.5 * ph) & ((fh - fl) <= 0.5 * ph) & (fh <= pole_top * 1.03)
        for t in np.flatnonzero(cand):
            out.append(('flagcand', t, fl[t], ph[t]))
    flags = sorted([x for x in out if isinstance(x, tuple)], key=lambda x: x[1]); out = [x for x in out if not isinstance(x, tuple)]
    for _, t, fl_, ph_ in flags:
        if t - last_t >= 20: last_t = t; add('Bull Flag', int(t), 1, fl_, c[t] + ph_)
    return out
rows = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close', 'high', 'low']).drop_duplicates('date').sort_values('date').reset_index(drop=True)
    d = d[(d.close > 0) & (d.high >= d.low)].reset_index(drop=True); r = d.close.pct_change(); bad = np.flatnonzero((r.abs() > 0.25).values)
    if len(bad): d = d.iloc[bad[-1]:].reset_index(drop=True)
    if len(d) < 750: continue
    c = d.close.values.astype(float); h = np.maximum(d.high.values, c); l = np.minimum(d.low.values, c); dates = d.date
    rngp = np.median((h - l) / c); thr = float(np.clip(3 * rngp, 0.04, 0.15))
    for kind_data in ('real', 'shuffled'):
        cc, hh, ll = c, h, l
        if kind_data == 'shuffled':
            ret = np.r_[0, np.diff(np.log(c))]; hu = np.log(h / c); ld = np.log(l / c); idx = rng.permutation(np.arange(1, len(c)))
            lc = np.log(c[0]) + np.cumsum(np.r_[0, ret[idx]]); cc = np.exp(lc); hh = cc * np.exp(np.r_[hu[0], hu[idx]]); ll = cc * np.exp(np.r_[ld[0], ld[idx]])
        for e in detect(cc, hh, ll, dates, thr):
            e.update(stock=s, data=kind_data, half='old' if e['t'] < len(c) * 0.6 else 'new'); rows.append(e)
    print(s, flush=True)
pd.to_pickle(pd.DataFrame(rows), OUT); print('events', len(rows))
