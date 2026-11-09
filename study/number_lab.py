"""NUMBER LAB (user 9 Nov 2026: 'hypothetical / ajeeb tareeke ki study — 19 jaise numbers, bade events se +-k din, guna/bhaag,
apni dheemi chadhaai (trend line) se upar/neeche kitna; sab shares par; 2-4 pakki pakad wale shares bhi mil gaye to kaam ho gaya').
1,500 shares 2002-26 (liquidity D removed, adj close, circuit-locked days removed). Every part does the same honest thing:
   pick the best pattern PER SHARE on 2003-2014, test it on 2015-2026, and ALSO on 2023-11..now;
   count how many shares 'pass' and compare with a PLACEBO run where the dates are scrambled (circular shift) —
   if real passes ~= placebo passes, the pattern is luck. Only shares passing all three (and beating placebo) are listed.
Parts:
  trend   : distance from own trend line (rolling 120-day straight line on log price, only past data) in sigma units ->
            next 5 / 20 days vs market. Pooled + per share.
  lag     : does a share repeat itself every k days (k = 2..60)? autocorrelation per share.
  event   : after big market days (all-share average move >= 2%): which day +k (1..30) the share moves, per share.
  numbers : date numbers — day of month divisible by n with remainder r (n = 2..31, e.g. 19), trading-day-of-year mod n,
            per share best (n, r).
Excess = share return minus the average of all shares that day. Cost not deducted per day (patterns are 1-day);
a pattern must earn > 0.25% per trade to be worth anything — shown.
"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(R, 'study', 'results')
part = sys.argv[1] if len(sys.argv) > 1 else 'trend'
MD = []
def md(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); MD.append(s)

P = nc.load()
A = P['a'].astype('float64'); H, L, C = P['h'], P['l'], P['c']
A = A.loc[:, A.notna().sum() > 1000]; cols = A.columns; H, L, C = H[cols], L[cols], C[cols]
r = A.pct_change(fill_method=None).clip(-0.4, 0.4)
r = r.where((H - L) > 0.002 * C)  # circuit-locked days out
ex = r.sub(r.mean(axis=1), axis=0)  # excess vs average share that day
idx = r.index
H1 = (idx >= '2003-01-01') & (idx < '2015-01-01'); H2 = idx >= '2015-01-01'; H3 = idx >= '2023-11-01'
rng = np.random.default_rng(7)


def tstat(x):
    x = x[np.isfinite(x)]
    return (x.mean() / x.std() * np.sqrt(len(x))) if len(x) > 10 and x.std() > 0 else np.nan, len(x), (x.mean() if len(x) else np.nan)


def scramble(X):
    """placebo: shift each share's series by a random 200-1500 days (keeps its own behaviour, breaks the calendar link)."""
    Y = np.empty_like(X)
    for j in range(X.shape[1]):
        Y[:, j] = np.roll(X[:, j], int(rng.integers(200, 1500)))
    return Y


def per_share_select(score_fn, n_opts, X, label):
    """score_fn(Xcol, mask, opt) -> array of values of trades for option opt in period mask. Select best opt on H1 by t, test H2/H3."""
    res = []
    for j in range(X.shape[1]):
        x = X[:, j]
        best, bt = None, 0
        for o in range(n_opts):
            t, n, m = tstat(score_fn(x, H1, o, j))
            if np.isfinite(t) and abs(t) > abs(bt) and n >= 30: best, bt = o, t
        if best is None: continue
        t2, n2, m2 = tstat(score_fn(x, H2, best, j)); t3, n3, m3 = tstat(score_fn(x, H3, best, j))
        res.append(dict(share=cols[j], opt=best, t1=bt, t2=t2, m2=m2 * 100 if np.isfinite(m2) else np.nan, n2=n2, t3=t3, m3=m3 * 100 if np.isfinite(m3) else np.nan, n3=n3))
    D = pd.DataFrame(res)
    D['pass'] = (np.sign(D.t1) == np.sign(D.t2)) & (D.t2.abs() >= 2) & (np.sign(D.t3) == np.sign(D.t1)) & (D.m3.abs() >= 0.25)
    return D


def compare(score_fn, n_opts, name, optname):
    X = ex.values
    real = per_share_select(score_fn, n_opts, X, name)
    plac = per_share_select(score_fn, n_opts, scramble(X), name + ' placebo')
    md(f'\n## {name}: {len(real)} shares jaanche')
    md(f'- Asli: {int(real["pass"].sum())} shares pass (2003-14 mein chuna, 2015-26 mein t>=2 same disha, Nov23-ab bhi same disha aur 0.25%+)')
    md(f'- Placebo (tareekhein ulat-pulat): {int(plac["pass"].sum())} shares "pass" — itne kismat se bhi aa jaate hain')
    real['label'] = real.opt.map(optname) + np.where(real.t1 < 0, ' [ULTA: is din share bazaar se peeche]', ' [is din share bazaar se aage]')
    real.to_csv(os.path.join(OUT, f'nl_{part}.csv'), index=False)
    P_ = real[real['pass']].sort_values('t2', key=abs, ascending=False)
    if len(P_):
        md('- Pass wale (sabse mazboot pehle):')
        for x in P_.head(15).itertuples():
            md(f'  - {x.share}: {x.label} | 2015-26 avg {x.m2:+.2f}%/trade (t {x.t2:.1f}, {x.n2} baar), Nov23-ab {x.m3:+.2f}% ({x.n3} baar)')
    verdict = 'KISMAT JAISA (asli ~ placebo)' if real['pass'].sum() <= 1.5 * max(plac['pass'].sum(), 1) else 'placebo se zyada — dekhne layak'
    md(f'- **Faisla: {verdict}**')
    return real, plac


if part == 'trend':
    N = 120
    lp = np.log(A)
    x = np.arange(len(lp), dtype=float)
    Sy = lp.rolling(N).sum(); Sxy = (lp.mul(x, axis=0)).rolling(N).sum()
    xm = pd.Series(x, index=idx).rolling(N).mean()
    Sxx = N * (N * N - 1) / 12.0
    b = (Sxy - Sy.mul(xm, axis=0)) / Sxx  # OLS slope per day
    ym = Sy / N
    fit = ym + b.mul(pd.Series(x, index=idx) - xm, axis=0)
    resid = lp - fit
    vy = lp.rolling(N).var(ddof=0); vres = (vy - b ** 2 * (Sxx / N)).clip(lower=1e-10)
    z = resid / np.sqrt(vres)
    md('# Apni trend line se doori (120 din ki seedhi line, sirf pichhla data)')
    md('z = aaj ka bhaav apni line se kitne sigma upar/neeche. Agle 5/20 din bazaar ke muqable (har 5ve/20ve din, overlap nahi).')
    for h, step in ((5, 5), (20, 20)):
        f = (A.shift(-h) / A - 1).clip(-0.6, 1.5); fx = f.sub(f.mean(axis=1), axis=0)
        sel = np.zeros(len(idx), bool); sel[::step] = True
        for lo, hi, nm in ((-9, -2, 'z <= -2 (line se bahut neeche)'), (-2, -1, '-2..-1'), (-1, 1, 'line ke paas'), (1, 2, '+1..+2'), (2, 9, 'z >= +2 (line se bahut upar)')):
            m = (z >= lo) & (z < hi)
            v = fx.where(m).values[sel]
            def per(mask):
                vv = v[mask[sel]]; mm = np.nanmean(vv, axis=1); return np.nanmean(mm) * 100, tstat(mm)[0]
            a1, t1 = per(H1); a2, t2 = per(H2); a3, t3 = per(H3)
            md(f'- {h} din | {nm:30s}: 2003-14 {a1:+.2f}% (t {t1:.1f}) | 2015-26 {a2:+.2f}% (t {t2:.1f}) | Nov23-ab {a3:+.2f}% (t {t3:.1f})')
    # slope itself: steep own trend (b) top vs bottom
    md('\nApni line ki dhalaan (kitni tezi se chadh raha) — top 10% vs neeche 10%, agle 20 din:')
    f = (A.shift(-20) / A - 1).clip(-0.6, 1.5); fx = f.sub(f.mean(axis=1), axis=0); br = b.rank(axis=1, pct=True)
    sel = np.zeros(len(idx), bool); sel[::20] = True
    for nm, m in (('sabse tez chadhti line (top 10%)', br >= 0.9), ('sabse tez girti line (neeche 10%)', br <= 0.1)):
        v = np.nanmean(fx.where(m).values[sel], axis=1)
        for per_, msk in (('2003-14', H1), ('2015-26', H2), ('Nov23-ab', H3)):
            vv = v[msk[sel]]; md(f'- {nm} {per_}: {np.nanmean(vv) * 100:+.2f}% (t {tstat(vv)[0]:.1f})')
    # per share: best z rule (buy below -2 or sell above +2) chosen 2003-14
    Z = z.values
    f5 = (A.shift(-5) / A - 1).clip(-0.6, 1.5); F5 = f5.sub(f5.mean(axis=1), axis=0).values
    thin = np.zeros(len(idx), bool); thin[::5] = True
    def sc(xcol, mask, o, j):
        zz = Z[:, j]; cond = (zz <= -2) if o == 0 else (zz >= 2)
        return F5[mask & cond & thin, j]
    real = per_share_select(sc, 2, F5, 'trend share')
    plac_X = scramble(F5)
    def sc_p(xcol, mask, o, j):
        zz = Z[:, j]; cond = (zz <= -2) if o == 0 else (zz >= 2)
        return plac_X[mask & cond & thin, j]
    plac = per_share_select(sc_p, 2, plac_X, 'trend placebo')
    md(f'\nHar share ka apna niyam (line se -2 sigma par khareed ya +2 par bech): asli pass {int(real["pass"].sum())}, placebo {int(plac["pass"].sum())}')
    real['label'] = real.opt.map({0: 'line se -2 sigma neeche', 1: 'line se +2 sigma upar'}) + np.where(real.t1 < 0, ' -> aage aur kamzor', ' -> aage bazaar se behtar')
    for x in real[real['pass']].sort_values('t2', key=abs, ascending=False).head(15).itertuples():
        md(f'  - {x.share}: {x.label} | 2015-26 {x.m2:+.2f}%/5 din (t {x.t2:.1f}, {x.n2}), Nov23-ab {x.m3:+.2f}% ({x.n3})')
    real.to_csv(os.path.join(OUT, 'nl_trend_share.csv'), index=False)

elif part == 'lag':
    LAGS = list(range(2, 61))
    def sc(x, mask, o, j):
        k = LAGS[o]; prev = np.roll(x, k); prev[:k] = np.nan
        return np.sign(prev[mask]) * x[mask] if True else None
    md('# Har k din baad dohraav (k = 2..60): kal se k din pehle ka rukh aaj dohrata hai?')
    compare(sc, len(LAGS), 'lag', {i: f'har {k} din baad wahi rukh' for i, k in enumerate(LAGS)})

elif part == 'event':
    mk = r.mean(axis=1); big = (mk.abs() >= 0.02).values; sgn = np.sign(mk.values)
    KS = list(range(1, 31))
    def sc(x, mask, o, j):
        k = KS[o]; ev = np.where(big & mask)[0]; ev = ev[ev + k < len(x)]
        return sgn[ev] * x[ev + k]  # + means share follows the big-day direction on day +k
    md('# Bade bazaar wale din (sab shares ka ausat 2%+ chala) ke baad +k din (1..30): kaun sa share kis din pe dohrata/palatta?')
    compare(sc, len(KS), 'event', {i: f'bade din ke +{k} din (+ = usi disha, - = ulta)' for i, k in enumerate(KS)})

elif part == 'numbers':
    dom = idx.day.values; tdy = pd.Series(1, index=idx).groupby(idx.year).cumsum().values
    OPTS = [('tareekh', n, rr) for n in range(2, 32) for rr in range(n) if not (n > 15 and rr > 31 - n)] + [('saal ka trading din', n, rr) for n in (7, 9, 11, 13, 19, 21, 27) for rr in range(n)]
    def sc(x, mask, o, j):
        kind, n, rr = OPTS[o]; d = dom if kind == 'tareekh' else tdy
        return x[mask & (d % n == rr)]
    md(f'# Numbers: tareekh % n = r (n 2..31, jaise 19) aur saal ka trading-din % n — {len(OPTS)} number-niyam har share par')
    compare(sc, len(OPTS), 'numbers', {i: f'{k} % {n} = {rr}' for i, (k, n, rr) in enumerate(OPTS)})

open(os.path.join(OUT, f'nl_{part}.md'), 'w').write('\n'.join(MD) + '\n')
