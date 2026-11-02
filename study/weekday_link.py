"""Weekday -> weekday and week -> week links (user, 2 Nov 2026).
Day level: for day A (weekday a, k-th such weekday of the month, return bucket) -> day B later in the same week or in the next week:
  B's own return (up / flat / down, mean) and the hold return from A's close to B's close.
Week level: week of month k (by the week's first trading day), weekly return bucket -> each of the next 1..8 weeks.
Control: the same counts with B taken from a randomly re-ordered week (link broken, weekday structure kept).
Output: aggregated counts per stock (also '_NIFTY' and '_BASKET' = equal-weight all stocks, added by the caller).
python study/weekday_link.py out.pkl dir1 [dir2]   (env CHUNK=k/N; env BASKET=1 to also build the basket)"""
import sys, os, glob, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
if os.environ.get('CHUNK'): k_, n_ = map(int, os.environ['CHUNK'].split('/')); files = files[k_::n_]
rng = np.random.default_rng(17)
CR = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
EDGES = [-np.inf, -0.02, -0.005, 0.005, 0.02, np.inf]; BL = ['1 2%+ नीचे', '2 0.5-2% नीचे', '3 सपाट', '4 0.5-2% ऊपर', '5 2%+ ऊपर']
WEDGES = [-np.inf, -0.03, -0.01, 0.01, 0.03, np.inf]; WL = ['1 3%+ नीचे', '2 1-3% नीचे', '3 सपाट (±1%)', '4 1-3% ऊपर', '5 3%+ ऊपर']
def lab_period(d):
    d = pd.DatetimeIndex(d); era = np.select([d < '2013-01-01', d < '2021-01-01'], ['2003-12', '2013-20'], '2021-26')
    cr = np.zeros(len(d), bool)
    for a, b in CR: cr |= (d >= a) & (d <= b)
    return era, cr, d >= '2023-11-01'
def analyse(c, name):
    c = c[c.index >= '2003-01-01']; r = c.pct_change(); r[r.abs() > 0.2] = np.nan
    df = pd.DataFrame({'c': c, 'r': r}).dropna()
    if len(df) < 500: return []
    df['wd'] = df.index.dayofweek; df['wk'] = df.index.to_period('W-SUN').start_time
    C = df.pivot_table(index='wk', columns='wd', values='c'); R = df.pivot_table(index='wk', columns='wd', values='r')
    C = C.reindex(columns=range(5)); R = R.reindex(columns=range(5))
    weeks = C.index; nW = len(weeks); perm = rng.permutation(nW)
    out = []
    for ctrl in (False, True):
        for a in range(5):
            A = R[a].values; Ac = C[a].values; Ad = weeks + pd.Timedelta(days=a)
            kth = ((Ad.day - 1) // 7 + 1).values
            era, cr, n23 = lab_period(Ad); bk = pd.cut(A, EDGES, labels=False)
            for off in (0, 1):
                for b in range(5):
                    if off == 0 and b <= a: continue
                    src = perm if ctrl else np.arange(nW)
                    j = src + off; ok = j < nW; jj = np.where(ok, j, 0)
                    B = np.where(ok, R[b].values[jj], np.nan); Bc = np.where(ok, C[b].values[jj], np.nan)
                    hold = Bc / Ac - 1 if not ctrl else np.where(ok, (C[b].values[jj] / C[a].values[jj] - 1) if off == 0 else np.nan, np.nan)
                    m = ~np.isnan(A) & ~np.isnan(B)
                    if m.sum() == 0: continue
                    T = pd.DataFrame({'era': era[m], 'cr': cr[m], 'n23': n23[m], 'kth': kth[m], 'bk': bk[m], 'B': B[m], 'H': hold[m]})
                    T['up'] = T.B > 0.005; T['dn'] = T.B < -0.005; T['pos'] = T.B > 0; T['B2'] = T.B ** 2
                    g = T.groupby(['era', 'cr', 'n23', 'kth', 'bk']).agg(n=('B', 'size'), up=('up', 'sum'), dn=('dn', 'sum'), pos=('pos', 'sum'), sB=('B', 'sum'), sB2=('B2', 'sum'), sH=('H', 'sum'), nH=('H', 'count')).reset_index()
                    g['a'] = a; g['b'] = b; g['off'] = off; g['ctrl'] = ctrl; g['lvl'] = 'day'; out.append(g)
        # week level
        wc = C.ffill(axis=1).iloc[:, -1]; wc = wc.dropna(); wr = wc.pct_change(); wr[wr.abs() > 0.4] = np.nan
        fd = pd.Series(df.index, index=df.index).groupby(df.wk).min(); fd = fd.reindex(wc.index)
        k = ((pd.DatetimeIndex(fd).day - 1) // 7 + 1).values; era, cr, n23 = lab_period(pd.DatetimeIndex(fd)); bk = pd.cut(wr.values, WEDGES, labels=False)
        n = len(wr); pm = rng.permutation(n) if ctrl else np.arange(n)
        for h in range(1, 9):
            j = pm + h; ok = j < n; jj = np.where(ok, j, 0); Bv = np.where(ok, wr.values[jj], np.nan)
            m = ~np.isnan(wr.values) & ~np.isnan(Bv)
            T = pd.DataFrame({'era': era[m], 'cr': cr[m], 'n23': n23[m], 'kth': k[m], 'bk': bk[m], 'B': Bv[m]})
            T['up'] = T.B > 0.01; T['dn'] = T.B < -0.01; T['pos'] = T.B > 0; T['B2'] = T.B ** 2
            g = T.groupby(['era', 'cr', 'n23', 'kth', 'bk']).agg(n=('B', 'size'), up=('up', 'sum'), dn=('dn', 'sum'), pos=('pos', 'sum'), sB=('B', 'sum'), sB2=('B2', 'sum')).reset_index()
            g['a'] = -1; g['b'] = h; g['off'] = h; g['ctrl'] = ctrl; g['lvl'] = 'week'; g['sH'] = np.nan; g['nH'] = 0; out.append(g)
    res = pd.concat(out)
    if os.environ.get('NOKTH'):
        res = res.groupby(['lvl', 'ctrl', 'a', 'b', 'off', 'era', 'cr', 'n23', 'bk'], as_index=False)[['n', 'up', 'dn', 'pos', 'sB', 'sB2', 'sH', 'nH']].sum(min_count=1); res['kth'] = 0
    for c_ in ('n', 'up', 'dn', 'pos', 'nH'): res[c_] = res[c_].astype('int32')
    for c_ in ('sB', 'sB2', 'sH'): res[c_] = res[c_].astype('float32')
    res['stock'] = name; return [res]
rows = []
if os.environ.get('MARKET'):
    nf = pd.read_csv(os.path.join(ROOT, 'data/NIFTY.csv'), parse_dates=['date']).drop_duplicates('date').set_index('date').close.sort_index()
    rows += analyse(nf, '_NIFTY')
    rets = []
    for f in files:
        d = pd.read_csv(f, parse_dates=['date'], usecols=['date', 'close']).dropna().drop_duplicates('date').set_index('date').close.sort_index()
        x = d.pct_change(); x[x.abs() > 0.2] = np.nan; rets.append(x.rename(f))
    P = pd.concat(rets, axis=1); cnt = P.notna().sum(1); br = P.mean(1)[cnt >= 30]
    rows += analyse((1 + br.fillna(0)).cumprod(), '_BASKET')
else:
    for f in files:
        s = os.path.basename(f)[:-7]
        d = pd.read_csv(f, parse_dates=['date'], usecols=['date', 'close']).dropna().drop_duplicates('date').set_index('date').close.sort_index()
        d = d[d > 0]; rows += analyse(d, s); print(s, flush=True)
pd.concat(rows).to_pickle(OUT); print('done')
