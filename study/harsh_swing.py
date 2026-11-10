"""Harsh Singh podcast (user 10 Nov 2026): VCP breakout, IPO base breakout, 10% max stop, monthly ROC(18) market cycle,
21 EMA trailing exit. 1,500 shares 2003-26; excess vs all shares after 0.25% cost; eras; exits compared."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); MD = []
def md(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); MD.append(s)
P = nc.load(); A, O, H, L, C, V = (P[k] for k in ('a', 'o', 'h', 'l', 'c', 'v'))
A = A.loc[:, A.notna().sum() > 120]; cols = A.columns; O, H, L, C, V = (x[cols] for x in (O, H, L, C, V))
adj = A / C; Ha, La, Oa = H * adj, L * adj, O * adj; ok = (H - L) > 0.002 * C
v50 = V.rolling(50, min_periods=30).mean().shift(1); idx = A.index
fx = {}
for h in (20, 60):
    f = (A.shift(-h) / A - 1).clip(-0.7, 2.0); fx[h] = f.sub(f.mean(axis=1), axis=0)
ERAS = [('2003-12', '2003', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'), ('Nov23-ab', '2023-11', '2026')]
ema21 = A.ewm(span=21, adjust=False).mean()
def excess(sig, name):
    n = int(sig.values.sum()); md(f'\n### {name}: {n} signal')
    for h in (20, 60):
        s = (fx[h].where(sig).mean(axis=1) * 100 - 0.25).dropna()
        if len(s) < 20: continue
        parts = [f'{nm} {s[a:b].mean():+.2f}% (t {s[a:b].mean() / s[a:b].std() * np.sqrt(len(s[a:b])):.1f})' for nm, a, b in ERAS if len(s[a:b]) > 10]
        md(f'- {h} din bazaar se: {s.mean():+.2f}% (t {s.mean() / s.std() * np.sqrt(len(s)):.1f}) | ' + ' | '.join(parts))
def trades(sig, stop_pct=0.10):
    ii, jj = np.where(sig.values); Av, Lv, Ov, Ev = A.values, La.values, Oa.values, ema21.values; out = []
    for i, j in zip(ii, jj):
        e = Av[i, j]
        if not np.isfinite(e) or i + 121 >= len(Av): continue
        st = e * (1 - stop_pct); r = {}
        # exit A: stop or 60 days
        x = np.nan
        for k in range(i + 1, i + 61):
            if np.isfinite(Lv[k, j]) and Lv[k, j] <= st: x = min(st, Ov[k, j]) if np.isfinite(Ov[k, j]) else st; break
        if not np.isfinite(x): x = Av[i + 60, j]
        r['fixed60'] = x / e - 1 - 0.0025
        # exit B: stop, or 2 consecutive closes below 21 EMA (max 120 days)
        x = np.nan; below = 0; held = 120
        for k in range(i + 1, i + 121):
            if np.isfinite(Lv[k, j]) and Lv[k, j] <= st: x = min(st, Ov[k, j]) if np.isfinite(Ov[k, j]) else st; held = k - i; break
            c = Av[k, j]
            if np.isfinite(c):
                below = below + 1 if c < Ev[k, j] else 0
                if below >= 2: x = c; held = k - i; break
        if not np.isfinite(x): x = Av[i + 120, j]
        r['ema21'] = x / e - 1 - 0.0025; r['held'] = held; r['date'] = idx[i]
        if np.isfinite(r['fixed60']) and np.isfinite(r['ema21']): out.append(r)
    return pd.DataFrame(out).set_index('date').sort_index() if out else pd.DataFrame()
def show_tr(T, lab):
    if len(T) < 30: md(f'- {lab}: bahut kam trade'); return
    for k, nm in (('fixed60', '10% stop + 60 din'), ('ema21', '10% stop + 21 EMA trailing (2 close neeche)')):
        x = T[k] * 100
        md(f'- {lab} | {nm}: {len(x)} trade, jeet {(x > 0).mean() * 100:.0f}%, ausat {x.mean():+.1f}%, jeet par {x[x > 0].mean():+.1f}%, haar par {x[x <= 0].mean():+.1f}%' + (f', ausat {T.held.mean():.0f} din' if k == 'ema21' else '')
           + ' | ' + ' | '.join(f'{n_} {x[a:b].mean():+.1f}%' for n_, a, b in ERAS if len(x[a:b]) > 15))
md('# Harsh Singh ki swing strategies — jaanch')
# ---- 1. VCP ----
def rngp(s): return Ha.rolling(10).max().shift(s) / La.rolling(10).min().shift(s) - 1
r3, r2, r1 = rngp(1), rngp(11), rngp(21)   # latest, middle, oldest 10-day windows
pivot = Ha.rolling(10).max().shift(1)
up = (A > A.rolling(200, min_periods=160).mean()) & (A.rolling(50).mean() > A.rolling(200, min_periods=160).mean()) & (A >= Ha.rolling(250, min_periods=200).max() * 0.75)
vdry = V.rolling(10).mean().shift(1) < V.rolling(10).mean().shift(21)
brk = (A > pivot) & ~(A.shift(1) > pivot.shift(1)) & (V >= 1.5 * v50) & ok
vcp = brk & up & (r1 > r2) & (r2 > r3) & (r3 <= 0.08) & (r1 >= 0.12) & vdry
excess(vcp, 'VCP: 3 sikudti range (10-10 din), aakhri <= 8%, volume sookha, uptrend, pivot ke upar volume breakout'); show_tr(trades(vcp), 'VCP')
ctrl = brk & up
excess(ctrl, 'CONTROL: wahi breakout uptrend mein, sikudan ke bina')
# ---- 2. IPO base breakout ----
first = A.apply(pd.Series.first_valid_index); start = idx[0]
ipo = [c for c in cols if pd.notna(first[c]) and first[c] > start + pd.Timedelta(days=400)]
sig = pd.DataFrame(False, index=idx, columns=cols)
for c in ipo:
    i0 = idx.get_loc(first[c]); a = A[c].values; h = Ha[c].values; v = V[c].values
    lh = np.nanmax(h[i0:i0 + 3]); run = lh; last_high = i0
    for k in range(i0 + 3, min(i0 + 250, len(a))):
        if not np.isfinite(a[k]): continue
        if a[k] > run:
            if k - last_high >= 15 and a[k] > lh and np.isfinite(v[k]) and v[k] >= 1.3 * np.nanmean(v[max(i0, k - 20):k]) and ok[c].values[k]: sig.iat[k, cols.get_loc(c)] = True
            last_high = k
        if np.isfinite(h[k]) and h[k] > run: run = h[k]; 
md(f'\n(IPO = jin shares ka data 2004 ke baad shuru hota hai: {len(ipo)} shares; listing = data ka pehla din)')
excess(sig, 'IPO base breakout: listing ke 1 saal ke andar, 15+ din ke base ke baad listing-high ke upar naya high, volume 1.3x'); show_tr(trades(sig), 'IPO')
anyipo = pd.DataFrame(False, index=idx, columns=cols)
for c in ipo:
    i0 = idx.get_loc(first[c])
    if i0 + 20 < len(idx): anyipo.iat[i0 + 20, cols.get_loc(c)] = True
excess(anyipo, 'CONTROL: har IPO listing ke 20 din baad khareedna')
# ---- 3. ROC(18) monthly ----
md('\n## Monthly ROC(18): 18 mahine ka badlaav -> agle 12 mahine')
def ix(n):
    d = pd.read_csv(os.path.join(R, 'data', 'global', f'{n}.csv'), parse_dates=['date']).set_index('date').close.dropna(); return d[~d.index.duplicated()].sort_index()
small = (1 + A.pct_change(fill_method=None).clip(-0.4, 0.4).mean(axis=1).fillna(0)).cumprod()
for nm, s, bins in (('Sensex 1997-2026', ix('IN_SENSEX'), [-100, -10, 10, 25, 45, 1000]), ('S&P 500 1928-2026', ix('US_SP500'), [-100, -10, 10, 25, 45, 1000]),
                    ('India sab shares ka ausat 2003-26', small, [-100, 0, 30, 60, 100, 5000])):
    m = s.resample('ME').last(); roc = (m / m.shift(18) - 1) * 100; f12 = (m.shift(-12) / m - 1) * 100; f6 = (m.shift(-6) / m - 1) * 100
    g = pd.cut(roc, bins); half = m.index[len(m) // 2]
    md(f'- **{nm}** (ROC abhi {roc.iloc[-1]:+.0f}):')
    for b, x in f12.groupby(g, observed=True):
        y = x.dropna()
        if len(y) < 6: continue
        md(f'  - ROC {b}: {len(y)} mahine, agle 12 mahine {y.mean():+.1f}% ({(y > 0).mean() * 100:.0f}% upar; pehla aadha {y[y.index < half].mean():+.1f}, doosra {y[y.index >= half].mean():+.1f}), agle 6 mahine {f6[x.index].mean():+.1f}%, sabse bura {y.min():+.0f}%')
open(os.path.join(R, 'study', 'results', 'harsh_swing.md'), 'w').write('\n'.join(MD) + '\n')
