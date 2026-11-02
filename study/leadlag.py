"""Leaders (Nifty, BankNifty, Sensex, and ~80 global series) vs every Indian stock (user, 2 Nov 2026).
For each Indian trading day D, a leader's 'last finished session before India opens on D':
  US / Europe / commodities / FX / ADRs / ETFs: their session on the calendar day before D (latest date < D).
  Asia (Japan, China, HK, Korea, Taiwan, Singapore) and Indian indices: their previous trading day (latest date < D).
Leader facts: move (close->close), body (open->close), closepos (where it closed in its day range).
Indian outcomes on D: gap (open vs prev close), oc (open->close), cc (close->close), hi (high vs open), lo (low vs open), nxt (D+1 close->close).
Per stock and period: correlations, and the rates after the leader's top-10% / bottom-10% move days (thresholds from 2013-20).
Control: the same with the leader's dates shifted by 250 trading days (link broken).
python study/leadlag.py out.pkl dir1 [dir2]  (env CHUNK=k/N, env MARKETONLY=1 for Nifty/BankNifty as followers)"""
import sys, os, glob, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
if os.environ.get('CHUNK'): k_, n_ = map(int, os.environ['CHUNK'].split('/')); files = files[k_::n_]
CR = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
def load(f):
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').set_index('date').sort_index()
    return d[d.close > 0]
leaders = {}
for f in sorted(glob.glob(os.path.join(ROOT, 'data/global/*.csv'))):
    n = os.path.basename(f)[:-4]
    if n in ('IN_GIFT_NIFTY_PROXY_INDA',): continue
    leaders[n] = load(f)
for n in ('NIFTY', 'BANKNIFTY'): leaders['IN_' + n] = load(os.path.join(ROOT, f'data/{n}.csv'))
nf = leaders['IN_NIFTY']; idx = nf.index[nf.index >= '2003-01-01']
LF = {}
for n, d in leaders.items():
    mv = d.close.pct_change(); mv[mv.abs() > 0.25] = np.nan
    has = d[['open', 'high', 'low']].notna().all(1) & (d.high > d.low)
    body = (d.close / d.open - 1).where(has); cp = ((d.close - d.low) / (d.high - d.low)).where(has)
    f = pd.DataFrame({'move': mv, 'body': body, 'cp': cp})
    pos = d.index.searchsorted(idx) - 1          # latest leader date strictly before D
    ok = pos >= 0; v = f.iloc[np.clip(pos, 0, None)].values.copy(); v[~ok] = np.nan
    lag = (idx - d.index[np.clip(pos, 0, None)]).days.values.astype(float); v[lag > 5] = np.nan   # stale (leader closed long before)
    LF[n] = pd.DataFrame(v, index=idx, columns=['move', 'body', 'cp'])
LM = pd.DataFrame({n: x.move for n, x in LF.items()}); LB = pd.DataFrame({n: x.body for n, x in LF.items()}); LC = pd.DataFrame({n: x.cp for n, x in LF.items()})
era = pd.Series(np.select([idx < '2013-01-01', idx < '2021-01-01'], ['2003-12', '2013-20'], '2021-26'), index=idx)
cr = pd.Series(False, index=idx)
for a, b in CR: cr |= (idx >= a) & (idx <= b)
n23 = pd.Series(idx >= '2023-11-01', index=idx)
PER = {'2013-20x': (era == '2013-20') & ~cr, '2021-26': era == '2021-26', 'Nov23': n23, '2003-12x': (era == '2003-12') & ~cr}
thr = {}
for n in LM:
    x = LM[n][PER['2013-20x']].dropna()
    thr[n] = (x.quantile(0.1), x.quantile(0.9)) if len(x) > 300 else (np.nan, np.nan)
def follower(d):
    d = d.reindex(idx); pc = d.close.shift()
    o = pd.DataFrame({'gap': d.open / pc - 1, 'oc': d.close / d.open - 1, 'cc': d.close / pc - 1, 'hi': d.high / d.open - 1, 'lo': d.low / d.open - 1})
    bad = (d.open == pc) | (o.cc.abs() > 0.2) | (o.gap.abs() > 0.15)
    o[bad] = np.nan; o['nxt'] = o.cc.shift(-1); return o
def analyse(name, d):
    Y = follower(d); rows = []
    for ctrl in (False, True):
        M = LM.shift(250) if ctrl else LM
        for pn, pm in PER.items():
            Yp = Y[pm]; Mp = M[pm]
            for n in M.columns:
                if n == 'IN_' + name: continue
                x = Mp[n]; lo_, hi_ = thr[n]
                if np.isnan(lo_): continue
                ok = x.notna() & Yp.cc.notna()
                if ok.sum() < 150: continue
                xs = x[ok]; ys = Yp[ok]
                r = {f'corr_{k}': np.corrcoef(xs, ys[k].fillna(ys[k].mean()))[0, 1] for k in ('gap', 'oc', 'cc', 'nxt')}
                up = xs >= hi_; dn = xs <= lo_
                for side, m in (('top', up), ('bot', dn)):
                    z = ys[m]
                    r.update({f'{side}_n': int(m.sum()), f'{side}_gapup': (z.gap > 0).mean(), f'{side}_green': (z.oc > 0).mean(), f'{side}_up': (z.cc > 0).mean(), f'{side}_nxtup': (z.nxt > 0).mean(),
                              f'{side}_gap': z.gap.mean(), f'{side}_oc': z.oc.mean(), f'{side}_cc': z.cc.mean(), f'{side}_nxt': z.nxt.mean(), f'{side}_hi': z.hi.mean(), f'{side}_lo': z.lo.mean()})
                r.update(base_gapup=(ys.gap > 0).mean(), base_green=(ys.oc > 0).mean(), base_up=(ys.cc > 0).mean(), base_nxtup=(ys.nxt > 0).mean(), base_oc=ys.oc.mean(), base_cc=ys.cc.mean(), n=int(ok.sum()))
                rows.append(dict(stock=name, leader=n, period=pn, ctrl=ctrl, **r))
    return rows
rows = []
if os.environ.get('MARKETONLY'):
    for n in ('NIFTY', 'BANKNIFTY'): rows += analyse(n, load(os.path.join(ROOT, f'data/{n}.csv')))
else:
    for f in files:
        s = os.path.basename(f)[:-7]; d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').set_index('date').sort_index()
        if len(d) < 600: continue
        rows += analyse(s, d); print(s, flush=True)
R = pd.DataFrame(rows)
for c in R.columns:
    if R[c].dtype == 'float64': R[c] = R[c].astype('float32')
R.to_pickle(OUT); print('done', len(R))
