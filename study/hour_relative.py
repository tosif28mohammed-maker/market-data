"""Stock-specific hour-of-day effect with the stock's own trend removed: x = hour return - (whole day open->close)/7.
Learn first half of days, test second half; pass = |t|>=2 in learn and same sign t>=1.65 in test. Control: random sign flips per day.
Also weekday x hour (x on that weekday minus the stock's x on other days).  python study/hour_relative.py out.pkl dir"""
import sys, os, glob, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]; files = sorted(glob.glob(os.path.join(sys.argv[2], '*.csv.gz'))); rng = np.random.default_rng(5)
SLOTS = ['09:15', '10:15', '11:15', '12:15', '13:15', '14:15', '15:15']
def tstat(x): return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)) + 1e-12)
rows = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['open', 'close']); d = d[(d.open > 0) & (d.close > 0)]
    if len(d) < 1500: continue
    d['day'] = d.time.dt.normalize(); d['slot'] = d.time.dt.strftime('%H:%M'); d = d[d.slot.isin(SLOTS)]
    O = d.pivot_table(index='day', columns='slot', values='open', aggfunc='first').reindex(columns=SLOTS)
    C = d.pivot_table(index='day', columns='slot', values='close', aggfunc='last').reindex(columns=SLOTS)
    ok = O.notna().all(1) & C.notna().all(1); O, C = O[ok], C[ok]
    H = pd.DataFrame({'h1': C['09:15'] / O['09:15'] - 1}, index=C.index)
    for i in range(1, 7): H[f'h{i + 1}'] = C[SLOTS[i]] / C[SLOTS[i - 1]] - 1
    day = C['15:15'] / O['09:15'] - 1; H = H[(day.abs() < 0.2)]; day = day[H.index]
    X = H.sub(day / 7, axis=0)
    if len(X) < 300: continue
    half = np.arange(len(X)) >= len(X) // 2; wd = X.index.dayofweek.values
    for col in X.columns:
        v = X[col].values; sg = rng.choice([-1, 1], len(v))
        a, b = v[~half], v[half]
        rows.append((s, col, 'all', len(a), a.mean(), tstat(a), b.mean(), tstat(b), (b > 0).mean(), tstat((v * sg)[~half]), tstat((v * sg)[half])))
        for w, wn in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri']):
            m = wd == w
            def ex(mask_half):
                x = v[mask_half & m]; y = v[mask_half & ~m]
                return x.mean() - y.mean(), (x.mean() - y.mean()) / np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
            perm = rng.permutation(wd) == w
            def exr(mask_half):
                x = v[mask_half & perm]; y = v[mask_half & ~perm]
                return (x.mean() - y.mean()) / np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
            ea, ta = ex(~half); eb, tb = ex(half)
            rows.append((s, col, wn, int((m & ~half).sum()), ea, ta, eb, tb, np.nan, exr(~half), exr(half)))
    print(s, flush=True)
pd.DataFrame(rows, columns=['stock', 'hour', 'cond', 'n', 'ex_learn', 't_learn', 'ex_test', 't_test', 'win_test', 'tr_learn', 'tr_test']).to_pickle(OUT)
