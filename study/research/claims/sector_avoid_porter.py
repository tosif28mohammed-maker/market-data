# ROBOT
"""AI-184C53 (WCS 19: avoid Utilities/CapGoods/RealEstate/Metals/Telecom) + MO-21 (WCS 22 Porter score>=3.5 industries).
Group EW forward returns vs all-stock EW, start each Jan (and each month for 12m), 2004-2025. Classification = today's yfinance (bias note)."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, REPO
P = load(); a = P['a']
info = pd.read_csv(f'{REPO}/data/fund/info.csv').set_index('symbol')
AV_IND = {'Steel','Aluminum','Other Industrial Metals & Mining','Copper','Thermal Coal','Telecom Services',
          'Specialty Industrial Machinery','Electrical Equipment & Parts','Farm & Heavy Construction Machinery','Engineering & Construction'}
HI_IND = {'Household & Personal Products','Packaged Foods','Confectioners','Tobacco','Beverages - Wineries & Distilleries',
          'Beverages - Brewers','Auto Manufacturers','Utilities - Regulated Gas','Oil & Gas Refining & Marketing'}
PAINT = {'ASIANPAINT','BERGEPAINT','KANSAINER','INDIGOPNTS','AKZOINDIA'}
def grp(s):
    if s not in info.index: return None
    r = info.loc[s]; sec, ind = r.sector, r.industry
    g = []
    if sec in ('Utilities','Real Estate') or ind in AV_IND: g.append('avoid')
    if ind in HI_IND or s in PAINT: g.append('porter_hi')
    return g
G = {s: grp(s) for s in a.columns}
cols = [s for s in a.columns if G[s] is not None]
a = a[cols]
me = a.resample('ME').last()
out = []
for h in (12, 36):
    f = me.shift(-h) / me - 1
    f = f.where(f.abs() < 20)
    for d in me.index:
        if d.year < 2004 or pd.isna(f.loc[d]).all(): continue
        row = f.loc[d].dropna()
        if len(row) < 100: continue
        allm = row.mean()
        for g in ('avoid', 'porter_hi'):
            ins = [s for s in row.index if g in G[s]]
            rest = [s for s in row.index if g not in G[s]]
            out.append(dict(h=h, date=d, grp=g, n=len(ins), ex_all=(row[ins].mean()-allm)*100,
                            ex_rest=(row[ins].mean()-row[rest].mean())*100, hit=(row[ins] > allm).mean()*100))
R = pd.DataFrame(out)
def era(d):
    return '2004-12' if d.year <= 2012 else ('2013-20' if d.year <= 2020 else '2021-26')
R['era'] = R.date.map(era)
lines = []
for (h, g), x in R.groupby(['h', 'grp']):
    lines.append(f"h={h}m {g} n~{int(x.n.median())} all: ex_vs_rest {x.ex_rest.mean():+.1f}% (median {x.ex_rest.median():+.1f}), months group beat rest {100*(x.ex_rest>0).mean():.0f}%, stock hit>{'mkt'} {x.hit.mean():.0f}%")
    for e, y in x.groupby('era'):
        lines.append(f"   {e}: ex_vs_rest {y.ex_rest.mean():+.1f}%  beat {100*(y.ex_rest>0).mean():.0f}%  (starts {len(y)})")
# recent 2/4/6 months: group EW return vs rest
last = a.index[-1]
for m in (2, 4, 6):
    st = a.index[a.index.get_indexer([last - pd.DateOffset(months=m)], method='nearest')[0]]
    r = (a.loc[last] / a.loc[st] - 1).dropna(); r = r[r.abs() < 5]
    for g in ('avoid', 'porter_hi'):
        ins = [s for s in r.index if g in G[s]]; rest = [s for s in r.index if g not in G[s]]
        lines.append(f"last {m}m {g}: {r[ins].mean()*100:+.1f}% vs rest {r[rest].mean()*100:+.1f}% (n {len(ins)})")
txt = '\n'.join(lines); print(txt)
od = f'{REPO}/study/research/r057_sector_avoid_porter'; os.makedirs(od, exist_ok=True)
open(f'{od}/result.txt', 'w').write(txt + '\n')
