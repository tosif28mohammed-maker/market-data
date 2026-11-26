# r075 (loss review 26 Nov: JWL gap-up 5.1% on 25 Nov AND 5.6% on 26 Nov, both SL): gap-fade on a REPEAT gapper
# Rule (pehle likha): event = stock gap-up >=3.5% (open/prev close, adj). Short at open, cover at close (daily proxy of INTRA_GAPFADE),
# cost 0.10% (0.05 charges + 0.05 slippage). Scenarios by yesterday: R = yesterday also gap-up >=3.5%; U = yesterday close-to-close >=+5% (no gap);
# N = normal. Stop proxy: share of days high >= open*1.02 (2% squeeze). Eras + Nov23-now. Liquidity D dropped. Units: stock-days, t over dates.
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/market-data/study'); import ni_common as nc
P = nc.load(); o, h, c, a = P['o'], P['h'], P['a'], P['a']
pc = a.shift(1)
gap = (o / pc - 1) * 100
oc = (a / o - 1) * 100        # long open->close (adj)
hi = (h / o - 1) * 100
ok = gap.abs() < 30
ev = (gap >= 3.5) & ok
prevgap = ev.shift(1, fill_value=False)
prevret = (a.shift(1) / a.shift(2) - 1) * 100
S = pd.DataFrame({'gap': gap[ev].stack(), 'short': -oc[ev].stack() - 0.10, 'sq2': (hi[ev] >= 2).stack(),
                  'pg': prevgap[ev].stack(), 'pr': prevret[ev].stack()}).dropna()
S['sc'] = np.where(S.pg, 'R-repeat gap', np.where(S.pr >= 5, 'U-up yday', 'N-normal'))
dt = S.index.get_level_values(0)
S['era'] = np.select([dt.year <= 2012, dt.year <= 2020], ['2003-12', '2013-20'], '2021-26')
S.loc[dt >= '2023-11-01', 'era2'] = 'Nov23-now'
def summ(g):
    d = g.groupby(level=0).short.mean()
    return pd.Series({'n': len(g), 'days': len(d), 'mean': g.short.mean(), 'win%': (g.short > 0).mean() * 100,
                      'sq2%': g.sq2.mean() * 100, 't_dates': d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 else np.nan})
print(S.groupby('sc').apply(summ).round(2).to_string())
print(S.groupby(['era', 'sc']).apply(summ).round(2)[['n', 'mean', 'win%', 't_dates']].unstack('sc').to_string())
print('Nov23-now\n', S[S.era2 == 'Nov23-now'].groupby('sc').apply(summ).round(2).to_string())
# gap-size inside repeat
S['gb'] = pd.cut(S.gap, [3.5, 5, 8, 30])
print(S.groupby(['gb', 'sc'], observed=True).short.agg(['size', 'mean']).round(2).unstack('sc').to_string())
# day-3: third gap in a row
pg2 = ev.shift(2, fill_value=False)
S['pg2'] = pg2[ev].stack().reindex(S.index)
print('3rd straight gap-up:', S[S.pg & S.pg2].pipe(summ).round(2).to_dict())
# chance: shuffle 'scenario' labels within dates? use difference R - N per date where both exist + bootstrap
diff = S.groupby([S.index.get_level_values(0), 'sc']).short.mean().unstack()
dd = (diff['R-repeat gap'] - diff['N-normal']).dropna()
rng = np.random.default_rng(0); bs = [rng.choice(dd.values, len(dd)).mean() for _ in range(3000)]
print('R-N same-day diff', round(dd.mean(), 3), 'n dates', len(dd), '95% CI', np.percentile(bs, [2.5, 97.5]).round(3))
