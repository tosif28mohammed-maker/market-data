# ROBOT
"""MO-18/MO-19 (Motilal WCS 23, 2018 'Valuation insights'): P/E>50 => poor alpha, P/E<10 small alpha;
High-RoE(>15)+High-growth(>15) beats. Test on our data: yfinance annual fundamentals FY2023-FY2025 (data/fund/raw.csv.gz),
P/E = (close on 30-Jun after FY x Ordinary Shares) / Net Income; forward 12m return (adj) from that date, excess vs
equal-weight of the same cohort, minus 0.25% cost. Survivorship: only currently-listed stocks (bias = winners kept)."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import ni_common as c
P = c.load(); A, C = P['a'], P['c']
r = pd.read_csv(os.path.join(c.REPO, 'data/fund/raw.csv.gz'))
r = r[(r.freq == 'A') & r.item.isin(['Net Income', 'Ordinary Shares Number', 'Stockholders Equity'])]
r['fy'] = r.date.str[:4].astype(int)
w = r.pivot_table(index=['symbol', 'fy'], columns='item', values='value', aggfunc='last').reset_index()
w = w.sort_values(['symbol', 'fy'])
w['ni_prev'] = w.groupby('symbol')['Net Income'].shift(); w['eq_prev'] = w.groupby('symbol')['Stockholders Equity'].shift()
rows = []
for fy in (2023, 2024, 2025):
    d0 = A.index[A.index.searchsorted(pd.Timestamp(f'{fy}-06-30'))]
    i1 = A.index.searchsorted(d0 + pd.DateOffset(months=12))
    if i1 >= len(A.index): continue
    d1 = A.index[i1]
    g = w[w.fy == fy].set_index('symbol')
    g = g[g.index.isin(A.columns)]
    px = C.loc[d0, g.index]; fr = (A.loc[d1, g.index] / A.loc[d0, g.index] - 1) * 100
    g = g.assign(pe=px * g['Ordinary Shares Number'] / g['Net Income'], f12=fr,
                 roe=g['Net Income'] / ((g['Stockholders Equity'] + g['eq_prev']) / 2) * 100,
                 gr=(g['Net Income'] / g['ni_prev'] - 1) * 100 * np.sign(g['ni_prev']))
    g = g.dropna(subset=['f12', 'pe']); g = g[g.f12.abs() < 1000]
    g['ex'] = g.f12 - g.f12.mean() - c.COST; g['cohort'] = fy
    rows.append(g)
D = pd.concat(rows)
bins = [-1e9, 0, 10, 20, 30, 50, 75, 1e9]; lab = ['loss', '0-10', '10-20', '20-30', '30-50', '50-75', '>75']
D['peb'] = pd.cut(D.pe, bins, labels=lab)
out = []
def summ(name, m):
    for (k, s) in m:
        x = D.loc[s]
        out.append(dict(test=name, group=k, n=len(x), mean_ex=round(x.ex.mean(), 2), median_ex=round(x.ex.median(), 2),
                        beat_pct=round((x.ex > 0).mean() * 100, 1),
                        **{f'mean_{y}': round(D.loc[s & (D.cohort == y), 'ex'].mean(), 2) for y in (2023, 2024, 2025)}))
summ('PE bucket', [(b, D.peb == b) for b in lab])
hr, hg = D.roe > 15, D.gr > 15
summ('RoE x growth(1y)', [('HiRoE-HiG', hr & hg), ('LoRoE-HiG', ~hr & hg), ('HiRoE-LoG', hr & ~hg), ('LoRoE-LoG', ~hr & ~hg)])
summ('MO-19 combo', [('PE<20 & RoE>15 & G>15', (D.pe > 0) & (D.pe < 20) & hr & hg), ('PE>50', D.pe > 50), ('all', D.pe == D.pe)])
o = pd.DataFrame(out); print(o.to_string(index=False))
os.makedirs(os.path.join(c.REPO, 'study/research/claims/out'), exist_ok=True)
o.to_csv(os.path.join(c.REPO, 'study/research/claims/out/mo18_pe_buckets.csv'), index=False)
