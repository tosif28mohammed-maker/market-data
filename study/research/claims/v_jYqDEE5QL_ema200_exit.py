"""Video jYqDEE5QL-w claim: small-cap growth portfolio - exit / limit downside when stock falls below 200 EMA.
Rule fixed before results:
 A) EVENT: close crosses below EMA200 after >=20 days above. Forward 20/60/120d excess vs equal-weight market.
    If exit rule works, excess should be clearly negative (selling avoids underperformance).
 B) PORTFOLIO: each day hold only stocks whose previous close > MA (exit/re-enter at close), vs hold all.
    Cost 0.25% per round trip charged on switches. Compare CAGR, max drawdown, by era and by size group.
 MA variants: EMA200 (claim), SMA200, EMA100, EMA50.
"""
import sys, numpy as np, pandas as pd
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
import ni_common as nc

P = nc.load()
a = P['a']; c = P['c']; v = P['v']
turn = (c * v).rolling(60, min_periods=40).median() / 1e7  # Rs cr/day
small = turn.lt(turn.median(axis=1), axis=0)  # below cross-sectional median = small group
F, mkt = nc.fwd(P, hs=(20, 60, 120))

out = []
for name, ma in [('EMA200', a.ewm(span=200, adjust=False, min_periods=200).mean()),
                 ('SMA200', a.rolling(200, min_periods=200).mean()),
                 ('EMA100', a.ewm(span=100, adjust=False, min_periods=100).mean()),
                 ('EMA50', a.ewm(span=50, adjust=False, min_periods=50).mean())]:
    above = a.gt(ma) & ma.notna()
    above20 = above.shift(1).rolling(20).sum().eq(20)
    ev = above20 & ~above
    ev = nc.thin(ev, 20)
    for grp, g in [('all', ev), ('small', ev & small), ('big', ev & ~small)]:
        for r in nc.evaluate(g, F, f'{name}_crossdown_{grp}', hs=(20, 60, 120)):
            if r['era'] in ('ALL', '2003-12', '2013-20', '2021-26', 'Nov23-now', 'ex-crisis'):
                out.append(r)
    # B) portfolio filter
    r1 = a.pct_change(fill_method=None); r1 = r1.where(r1.abs() < 0.5)
    hold = above.shift(1).fillna(False) & r1.notna()
    sw = above.astype(int).diff().abs().shift(1).fillna(0)  # switches
    for grp, gm in [('all', None), ('small', small.shift(1).fillna(False)), ('big', ~small.shift(1).fillna(True))]:
        base = r1.notna() if gm is None else (r1.notna() & gm)
        h = hold & base
        allret = r1.where(base).mean(axis=1)
        cnt = h.sum(axis=1)
        filt = (r1.where(h).sum(axis=1) - (sw.where(h | (base & ~h)).sum(axis=1) * 0.00125)) / base.sum(axis=1)
        # filtered: money in stocks above MA, rest cash (0) -> equal weight over whole base, so exposure varies
        filt_full = r1.where(h).mean(axis=1)  # fully invested only in stocks above MA
        for era, s, e in [('2003-26', '2003-01-01', '2026-12-31'), ('2003-12', '2003-01-01', '2012-12-31'),
                          ('2013-20', '2013-01-01', '2020-12-31'), ('2021-26', '2021-01-01', '2026-12-31')]:
            def stats(x):
                x = x.loc[s:e].fillna(0)
                eq = (1 + x).cumprod()
                yrs = len(x) / 248
                return round((eq.iloc[-1] ** (1 / yrs) - 1) * 100, 1), round((eq / eq.cummax() - 1).min() * 100, 1)
            b, f, ff = stats(allret), stats(filt), stats(filt_full)
            out.append(dict(study=f'{name}_portfolio_{grp}', era=era, hold_all_cagr=b[0], hold_all_maxdd=b[1],
                            exit_below_cagr=f[0], exit_below_maxdd=f[1], only_above_full_cagr=ff[0],
                            only_above_full_maxdd=ff[1], avg_exposure=round((cnt / base.sum(axis=1)).loc[s:e].mean() * 100, 1)))
df = pd.DataFrame(out)
df.to_csv('study/results/v_jYqDEE5QL_ema200_exit.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400)
ev_cols = ['study', 'h', 'era', 'n', 'excess', 'excess_med', 'win_vs_mkt', 't_dates']
print(df[df.study.str.contains('crossdown')][ev_cols].to_string(index=False))
print(df[df.study.str.contains('portfolio')].dropna(axis=1, how='all').to_string(index=False))
