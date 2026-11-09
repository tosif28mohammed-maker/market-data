"""Period-START study (user 9 Nov 2026: 'ritu jis din/hafte shuru hui — Somvaar? pehla hafta upar ya neeche? — poori ritu kaisi rahi').
Same deep test for every period type: 6 ritu, mahina, timahi, saal. Markets: Sensex 1997-, sab shares ka ausat 2003-, S&P 1928-,
Nikkei, DAX, FTSE, Hang Seng. Rules: (1) weekday on which the period started -> whole period; (2) first day up/down -> rest;
(3) first 5 trading days up/down -> rest of period (first 5 days excluded = tradable); (4) first week big (top/bottom third);
(5) per ritu separately. 'Rest' compared with the same market's normal rest-of-period; strongest rule per family vs 1000 shuffles."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); rng = np.random.default_rng(5); MD = []
def md(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); MD.append(s)
RN = ['Vasant', 'Grishma', 'Varsha', 'Sharad', 'Hemant', 'Shishir']; WD = ['Som', 'Mangal', 'Budh', 'Guru', 'Shukra']
def ritu_key(d):
    m = d.month * 100 + d.day
    k = 0 if 315 <= m < 515 else 1 if 515 <= m < 715 else 2 if 715 <= m < 915 else 3 if 915 <= m < 1115 else 4 if (m >= 1115 or m < 115) else 5
    return (d.year if m >= 315 else d.year - 1) * 10 + k
KEYS = {'ritu': ritu_key, 'mahina': lambda d: d.year * 100 + d.month, 'timahi': lambda d: d.year * 10 + (d.month - 1) // 3, 'saal': lambda d: d.year}
def ix(n):
    d = pd.read_csv(os.path.join(R, 'data', 'global', f'{n}.csv'), parse_dates=['date']).set_index('date').close.dropna()
    return d[~d.index.duplicated()].sort_index()
MK = {'Sensex': ix('IN_SENSEX'), 'S&P 500': ix('US_SP500'), 'Nikkei': ix('JP_NIKKEI'), 'DAX': ix('EU_DAX'), 'FTSE': ix('EU_FTSE'), 'Hang Seng': ix('HK_HANGSENG')}
ra = nc.load()['a'].pct_change(fill_method=None).clip(-0.4, 0.4).mean(axis=1).dropna(); MK['India sab shares'] = (1 + ra).cumprod()
def table(close, kind):
    r = np.log(close).diff().dropna() * 100; key = pd.Series([KEYS[kind](d) for d in r.index], index=r.index)
    rows = []
    for k, x in r.groupby(key.values):
        n = len(x)
        if n < {'ritu': 30, 'mahina': 15, 'timahi': 50, 'saal': 200}[kind]: continue
        rows.append(dict(key=k, wd=x.index[0].dayofweek, d1=x.iloc[0], w1=x.iloc[:5].sum(), rest1=x.iloc[1:].sum(), rest5=x.iloc[5:].sum(), full=x.sum(),
                         sub=(k % 10 if kind == 'ritu' else (k % 100 if kind == 'mahina' else 0))))
    return pd.DataFrame(rows)
def t2(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if len(a) < 8 or len(b) < 8: return np.nan
    return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
md('# Shuruaat se poora daur: ritu / mahina / timahi / saal')
md('"baaki" = pehle 5 din chhod kar daur ka baaki hissa (yani 5ve din ke close par khareed sakte the).')
SUM = []
for kind in ('ritu', 'mahina', 'timahi', 'saal'):
    md(f'\n## {kind.upper()}')
    for nm, c in MK.items():
        T = table(c, kind)
        if len(T) < 20: continue
        up, dn = T[T.w1 > 0], T[T.w1 <= 0]; t_w = t2(up.rest5, dn.rest5)
        q1, q3 = T.w1.quantile(1 / 3), T.w1.quantile(2 / 3); hi, lo = T[T.w1 >= q3], T[T.w1 <= q1]
        d_up, d_dn = T[T.d1 > 0], T[T.d1 <= 0]
        # weekday of start: strongest weekday vs rest, adjusted by shuffle
        tw = {w: t2(T[T.wd == w].full, T[T.wd != w].full) for w in range(5)}; bw = max(tw, key=lambda w: abs(tw[w]) if np.isfinite(tw[w]) else 0)
        mx = []
        for _ in range(500):
            f = rng.permutation(T.full.values); mx.append(np.nanmax([abs(t2(f[T.wd.values == w], f[T.wd.values != w])) for w in range(5)]))
        pw = np.mean(np.array(mx) >= abs(tw[bw]))
        half = len(T) // 2; A_, B_ = T.iloc[:half], T.iloc[half:]
        th = [t2(X[X.w1 > 0].rest5, X[X.w1 <= 0].rest5) for X in (A_, B_)]
        md(f'- **{nm}** ({len(T)} {kind}): pehla hafta UPAR -> baaki {up.rest5.mean():+.1f}% ({(up.rest5 > 0).mean() * 100:.0f}% upar, {len(up)}) | NEECHE -> baaki {dn.rest5.mean():+.1f}% ({(dn.rest5 > 0).mean() * 100:.0f}% upar, {len(dn)}) | fark t {t_w:+.1f} (pehla aadha {th[0]:+.1f}, doosra {th[1]:+.1f})')
        md(f'  - pehla hafta bahut achha (top tihaai) -> baaki {hi.rest5.mean():+.1f}% | bahut bura -> baaki {lo.rest5.mean():+.1f}% | pehla DIN upar -> baaki {d_up.rest1.mean():+.1f}%, neeche -> {d_dn.rest1.mean():+.1f}% (t {t2(d_up.rest1, d_dn.rest1):+.1f})')
        md(f'  - shuruaat ka din: sabse alag {WD[bw]} se shuru ({int((T.wd == bw).sum())} baar) -> poora daur {T[T.wd == bw].full.mean():+.1f}% vs baaki {T[T.wd != bw].full.mean():+.1f}% (t {tw[bw]:+.1f}); kismat se chance {pw * 100:.0f}%')
        SUM.append(dict(kind=kind, market=nm, n=len(T), t_week=round(t_w, 2), t_h1=round(th[0], 2), t_h2=round(th[1], 2), p_weekday=round(pw, 2)))
    if kind == 'ritu':
        md('\n### Har ritu alag (Sensex aur India sab shares): pehla hafta upar vs neeche -> us ritu ka baaki hissa')
        for nm in ('Sensex', 'India sab shares'):
            T = table(MK[nm], 'ritu'); ts = {}
            for k in range(6):
                x = T[T['sub'] == k]; u, d_ = x[x.w1 > 0], x[x.w1 <= 0]
                ts[k] = (u.rest5.mean() if len(u) else np.nan, d_.rest5.mean() if len(d_) else np.nan, len(u), len(d_), (u.rest5.mean() - d_.rest5.mean()) / np.sqrt(u.rest5.var() / max(len(u), 1) + d_.rest5.var() / max(len(d_), 1)) if len(u) > 3 and len(d_) > 3 else np.nan)
            best = max(ts, key=lambda k: abs(ts[k][4]) if np.isfinite(ts[k][4]) else 0); mx = []
            for _ in range(1000):
                m_ = 0
                for k in range(6):
                    x = T[T['sub'] == k]; f = rng.permutation(x.rest5.values); u, d_ = f[x.w1.values > 0], f[x.w1.values <= 0]
                    if len(u) > 3 and len(d_) > 3: m_ = max(m_, abs((u.mean() - d_.mean()) / np.sqrt(u.var(ddof=1) / len(u) + d_.var(ddof=1) / len(d_))))
                mx.append(m_)
            md(f'- {nm}: ' + '; '.join(f'{RN[k]}: upar->{v[0]:+.1f}% ({v[2]}), neeche->{v[1]:+.1f}% ({v[3]}), t {v[4]:+.1f}' for k, v in ts.items()))
            md(f'  - sabse mazboot {RN[best]} (t {ts[best][4]:+.1f}); 6 ritu mein kismat se itna milne ka chance {np.mean(np.array(mx) >= abs(ts[best][4])) * 100:.0f}%')
pd.DataFrame(SUM).to_csv(os.path.join(R, 'study', 'results', 'period_start.csv'), index=False)
open(os.path.join(R, 'study', 'results', 'period_start.md'), 'w').write('\n'.join(MD) + '\n')
