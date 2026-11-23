# ROBOT
"""MO-25 (WCS 27, Dec 2022): Consistent vs Volatile sectors -> out-of-sample Dec2022->now (plus in-sample 2004-22, biased).
MO-26 (WCS 27 'Consistent Wealth Creator' price rule): stock beat EW market in each of last 5 calendar years -> next 12m excess."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from ni_common import load, REPO, COST
P = load(); a = P['a']
info = pd.read_csv(f'{REPO}/data/fund/info.csv').set_index('symbol')
PSUB = {'SBIN','BANKBARODA','PNB','CANBK','UNIONBANK','INDIANB','BANKINDIA','CENTRALBK','IOB','UCOBANK','MAHABANK','PSB'}
TYRE = {'MRF','APOLLOTYRE','CEATLTD','JKTYRE','BALKRISIND','TVSSRICHAK','GOODYEAR'}
CONS = {'Auto Parts','Specialty Chemicals','Chemicals','Tobacco','Luxury Goods','Credit Services','Mortgage Finance','Asset Management',
        'Capital Markets','Household & Personal Products','Packaged Foods','Confectioners','Information Technology Services',
        'Software - Application','Software - Infrastructure','Integrated Freight & Logistics','Oil & Gas Refining & Marketing',
        'Oil & Gas Integrated','Utilities - Regulated Gas','Drug Manufacturers - Specialty & Generic','Drug Manufacturers - General',
        'Utilities - Regulated Electric','Utilities - Independent Power Producers','Utilities - Renewable','Building Materials'}
VOL = {'Airlines','Beverages - Wineries & Distilleries','Beverages - Brewers','Auto Manufacturers','Specialty Industrial Machinery',
       'Electrical Equipment & Parts','Farm & Heavy Construction Machinery','Engineering & Construction','Furnishings, Fixtures & Appliances',
       'Consumer Electronics','Medical Care Facilities','Lodging','Restaurants','Entertainment','Broadcasting','Publishing','Steel',
       'Aluminum','Other Industrial Metals & Mining','Copper','Thermal Coal','Coking Coal','Packaging & Containers','Paper & Paper Products',
       'Real Estate - Development','Real Estate - Diversified','Apparel Retail','Department Stores','Specialty Retail','Marine Shipping',
       'Telecom Services','Textile Manufacturing','Apparel Manufacturing','Lumber & Wood Production'}
def grp(s):
    if s in PSUB or s in TYRE: return 'vol'
    if s not in info.index: return None
    ind = info.loc[s, 'industry']
    if ind == 'Banks - Regional': return 'cons'
    return 'cons' if ind in CONS else ('vol' if ind in VOL else 'other')
G = pd.Series({s: grp(s) for s in a.columns}).dropna()
L = []
# MO-25 out-of-sample: buy 30 Dec 2022 close, hold to dates
def period(st, en):
    i0 = a.index[a.index.get_indexer([pd.Timestamp(st)], method='nearest')[0]]
    i1 = a.index[a.index.get_indexer([pd.Timestamp(en)], method='nearest')[0]]
    r = (a.loc[i1] / a.loc[i0] - 1).dropna(); r = r[r.abs() < 20]
    out = {g: r[[s for s in r.index if G.get(s) == g]] for g in ('cons', 'vol', 'other')}
    return i0, i1, r, out
last = a.index[-1]
L.append('MO-25 sector groups (EW, mean / median, n):')
for st, en in [('2022-12-30', last), ('2022-12-30', '2023-12-29'), ('2023-12-29', '2024-12-31'), ('2024-12-31', '2025-12-31'), ('2025-12-31', last),
               (last - pd.DateOffset(months=2), last), (last - pd.DateOffset(months=4), last), (last - pd.DateOffset(months=6), last)]:
    i0, i1, r, o = period(st, en)
    L.append(f"  {i0.date()}->{i1.date()} all {r.mean()*100:+.1f}% | cons {o['cons'].mean()*100:+.1f} (med {o['cons'].median()*100:+.1f}, n{len(o['cons'])}) | vol {o['vol'].mean()*100:+.1f} (med {o['vol'].median()*100:+.1f}, n{len(o['vol'])}) | other {o['other'].mean()*100:+.1f}")
# in-sample yearly 2004-2022 (biased: classification made with this data)
ye = a.resample('YE').last()
yr = ye.pct_change(fill_method=None).where(lambda x: x.abs() < 20)
rows = []
for d in yr.index:
    x = yr.loc[d].dropna()
    if len(x) < 100: continue
    c = x[[s for s in x.index if G.get(s) == 'cons']]; v = x[[s for s in x.index if G.get(s) == 'vol']]
    rows.append((d.year, (c.mean()-v.mean())*100))
Y = pd.DataFrame(rows, columns=['yr', 'cons_minus_vol']).set_index('yr')
L.append('  yearly cons-vol (pp): ' + ' '.join(f"{y}:{v:+.0f}" for y, v in Y.cons_minus_vol.items()))
L.append(f"  2004-22 avg {Y.loc[2004:2022].cons_minus_vol.mean():+.1f}pp, cons beat in {100*(Y.loc[2004:2022].cons_minus_vol>0).mean():.0f}% yrs; 2023-26 avg {Y.loc[2023:].cons_minus_vol.mean():+.1f}pp")
# MO-26: beat EW mkt in each of last K calendar years
mk = yr.mean(axis=1)
beat = yr.gt(mk, axis=0) & yr.notna()
avail = yr.notna()
res = []
for i in range(5, len(yr.index) - 1):
    d = yr.index[i]; nx = yr.index[i + 1]
    if d.year < 2006: continue
    cnt = beat.iloc[i-4:i+1].sum(); ok = avail.iloc[i-4:i+1].all()
    nxt = yr.loc[nx]; m = nxt.dropna().mean()
    for k in (5, 4, 3, 0):
        sel = [s for s in cnt.index if ok[s] and cnt[s] == k and pd.notna(nxt[s])]
        if len(sel) < 5: continue
        ex = (nxt[sel] - m) * 100
        res.append(dict(year=nx.year, k=k, n=len(sel), ex=ex.mean() - COST, med=ex.median(), hit=(ex > 0).mean() * 100))
R = pd.DataFrame(res)
L.append('MO-26 beat market k of last 5 yrs -> next calendar year excess vs EW all (after 0.25% cost):')
for k, x in R.groupby('k'):
    L.append(f"  k={k}: n~{int(x.n.median())} mean {x.ex.mean():+.1f}% median-of-yr-medians {x.med.mean():+.1f}% stock-hit {x.hit.mean():.0f}% yrs+ {100*(x.ex>0).mean():.0f}%")
    for nm, lo, hi in (('2007-12', 2007, 2012), ('2013-20', 2013, 2020), ('2021-26', 2021, 2026)):
        y = x[(x.year >= lo) & (x.year <= hi)]
        if len(y): L.append(f"     {nm}: {y.ex.mean():+.1f}% (yrs {len(y)}, med {y.med.mean():+.1f})")
L.append('  2026 YTD row: ' + R[R.year == R.year.max()].to_string(index=False).replace('\n', ' | '))
txt = '\n'.join(L); print(txt)
open(f'{REPO}/study/research/r060_consistents/result.txt', 'w').write(txt + '\n')
