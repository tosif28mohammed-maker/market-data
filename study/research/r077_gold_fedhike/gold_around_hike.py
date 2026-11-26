# r077 (Tosif 26 Nov discussion): Fed hike almost fully priced -> gold before vs after the decision (5/10 trading days)
# Rule (pehle likha): FOMC hike announcement days (r040 list 2004-2023). Gold (CMD_GOLD close, US day) returns:
# pre10 = close[d-10]->close[d-1], pre5, post5 = close[d-1]->close[d+5] (decision day included), post10. Control: all 10-day windows.
# Scenario: cycle (2004-06 slow 25bp; 2015-18 slow; 2022-23 fast/big); 10y yield move pre10 up vs down; dollar pre10 up/down.
import numpy as np, pandas as pd, re
src = open('/home/claude/market-data/study/research/r2026-11-21-eve/r040_fed.py').read()
hikes = sorted(set(re.findall(r"'(\d{4}-\d{2}-\d{2})'", src.split('hikes=')[1].split('\n')[0] + src.split('hikes=')[1].split('\n')[1] + src.split('hikes=')[1].split('\n')[2])))
def g(n):
    d = pd.read_csv(f'/home/claude/market-data/data/global/{n}.csv', index_col='date', parse_dates=True); return d.close[~d.index.duplicated()].dropna()
gold = g('CMD_GOLD'); y10 = g('US_10Y').reindex(gold.index).ffill(); dx = g('FX_DOLLAR_INDEX').reindex(gold.index).ffill()
ix = gold.index; rows = []
for h in hikes:
    t = ix.searchsorted(pd.Timestamp(h))
    if t < 11 or t + 10 >= len(ix): continue
    r = lambda a, b: (gold.iloc[b] / gold.iloc[a] - 1) * 100
    rows.append(dict(date=h, pre10=r(t - 11, t - 1), pre5=r(t - 6, t - 1), post5=r(t - 1, t + 5), post10=r(t - 1, t + 10),
                     y10pre=(y10.iloc[t - 1] - y10.iloc[t - 11]), dxpre=(dx.iloc[t - 1] / dx.iloc[t - 11] - 1) * 100,
                     cyc='2004-06' if h < '2010' else ('2015-18' if h < '2020' else '2022-23')))
E = pd.DataFrame(rows); print('hikes', len(E), E.date.min(), E.date.max())
base10 = (gold.shift(-10) / gold - 1).dropna() * 100; base5 = (gold.shift(-5) / gold - 1).dropna() * 100
print('control 10d mean %.2f up %.0f%% | 5d mean %.2f up %.0f%%' % (base10.mean(), (base10 > 0).mean() * 100, base5.mean(), (base5 > 0).mean() * 100))
for c in ['pre10', 'pre5', 'post5', 'post10']:
    print(c, 'mean %.2f median %.2f up %.0f%%' % (E[c].mean(), E[c].median(), (E[c] > 0).mean() * 100))
print(E.groupby('cyc')[['pre10', 'post5', 'post10']].agg(['mean', lambda s: (s > 0).mean() * 100]).round(1).to_string())
E['pre_dir'] = np.where(E.pre10 < 0, 'gold fell before', 'gold rose before')
print(E.groupby('pre_dir')[['post5', 'post10']].agg(['size', 'mean', lambda s: (s > 0).mean() * 100]).round(2).to_string())
E['yld'] = np.where(E.y10pre > 0, 'yield up before', 'yield down before')
print(E.groupby('yld')[['post5', 'post10']].agg(['size', 'mean']).round(2).to_string())
rng = np.random.default_rng(0); vals = base10.values
sims = [rng.choice(vals, len(E)).mean() for _ in range(5000)]
print('post10 vs random-window chance p (two-sided) %.3f' % np.mean(np.abs(np.array(sims) - vals.mean()) >= abs(E.post10.mean() - vals.mean())))
E.round(2).to_csv('/home/claude/market-data/study/research/r077_gold_fedhike/events.csv', index=False)
