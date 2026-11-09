"""Industry/theme momentum (user 9 Nov 2026: 'jo industry aage badhegi — solar, AI jaisi — pehle se pakdo').
Test: every month-end rank Yahoo industries (>=4 stocks, not D) by median past return (3/6/12 months, skipping the last month);
hold top-20% industries' stocks (equal weight) for the next 1/3/6 months vs all stocks equal weight. Eras + ex-crisis + halves.
Placebo: random industry labels (shuffled), 200 times. Cost 0.25% per rebalance on the industry basket."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ni_common as nc
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = nc.load(); A = P['a']
I = pd.read_csv(os.path.join(R, 'data', 'fund', 'info.csv')).set_index('symbol').industry.dropna()
cols = [c for c in A.columns if c in I.index]; A = A[cols]; ind = I.reindex(cols)
M = A.resample('ME').last()
out = []; rng = np.random.default_rng(0)
def run(lab, lb, hold):
    res = []
    for i in range(lb + 1, len(M) - hold):
        past = M.iloc[i - 1] / M.iloc[i - 1 - lb] - 1  # skip last month
        fut = M.iloc[i + hold] / M.iloc[i] - 1
        ok = past.notna() & fut.notna()
        g = pd.DataFrame({'p': past[ok], 'f': fut[ok], 'ind': lab.reindex(past[ok].index)}).dropna()
        cnt = g.groupby('ind').size(); good = cnt[cnt >= 4].index
        med = g[g.ind.isin(good)].groupby('ind').p.median()
        if len(med) < 10: continue
        top = med[med >= med.quantile(0.8)].index; bot = med[med <= med.quantile(0.2)].index
        res.append((M.index[i], g[g.ind.isin(top)].f.mean() * 100 - 0.25, g[g.ind.isin(bot)].f.mean() * 100 - 0.25, g.f.mean() * 100))
    return pd.DataFrame(res, columns=['date', 'top', 'bot', 'all']).set_index('date')
L = ['# Industry momentum (top 20% industries vs sab shares), monthly entry, net of 0.25%', '']
for lb in (3, 6, 12):
    for hold in (1, 3, 6):
        d = run(ind, lb, hold)
        row = {'lookback_m': lb, 'hold_m': hold, 'n': len(d)}
        for nm, a, b in nc.ERAS + [('ALL', '2003-01-01', '2026-12-31')]:
            x = d.loc[a:b]; row[f'{nm}_top-all'] = round((x.top - x['all']).mean(), 2); row[f'{nm}_bot-all'] = round((x.bot - x['all']).mean(), 2)
        x = d.copy()
        for a, b in nc.CRISIS: x = x[(x.index < a) | (x.index > b)]
        row['excrisis_top-all'] = round((x.top - x['all']).mean(), 2)
        row['win%'] = round(((d.top - d['all']) > 0).mean() * 100)
        if hold == 3:
            pl = []
            for k in range(100):
                pl.append((run(pd.Series(rng.permutation(ind.values), index=ind.index), lb, hold).pipe(lambda z: (z.top - z['all']).mean())))
            row['placebo_p95'] = round(np.percentile(pl, 95), 2); row['p_value'] = round(np.mean(np.array(pl) >= row['ALL_top-all']), 3)
        out.append(row); print(row, flush=True)
df = pd.DataFrame(out); df.to_csv(os.path.join(R, 'study', 'results', 'industry_mom.csv'), index=False)
L += ['```', df.to_string(index=False), '```']
open(os.path.join(R, 'study', 'results', 'industry_mom.md'), 'w').write('\n'.join(L) + '\n')
