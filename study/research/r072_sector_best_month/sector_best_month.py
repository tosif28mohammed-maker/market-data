# ROBOT  (needs universe500 data via U500)
"""FMCG-01 (CNBC-TV18 26 Nov: 'Nifty FMCG best month in 17 years'): जब कोई sector (equal-weight, info.csv sector)
अपना कई साल का सबसे अच्छा 21-दिन (महीना) देता है, तो अगले 60/120/250 दिन sector vs बाज़ार (सब शेयर EW) कैसा?
Event: sector का 21d return पिछले 5 साल (1250 दिन) के हर 21d return से ज़्यादा; एक sector में 120 दिन तक दोबारा event नहीं।
Placebo: वही sector, random दिन। Control: sector 21d return top-5% (पर record नहीं)। Cost 0.25% (basket)।"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, COST
REPO = os.path.join(os.path.dirname(__file__), '..', '..', '..')
I = pd.read_csv(f'{REPO}/data/fund/info.csv').set_index('symbol')
P = load(); a = P['a']
r1 = a.pct_change(fill_method=None); r1 = r1.where(r1.abs() < 0.5)
mkt = r1.mean(axis=1)
sec = I.sector.reindex(a.columns)
S = {}
for s in sec.dropna().unique():
    cols = sec[sec == s].index
    n = r1[cols].notna().sum(axis=1)
    S[s] = r1[cols].mean(axis=1).where(n >= 8)
S = pd.DataFrame(S)
lS = np.log1p(S.fillna(0)).cumsum(); lM = np.log1p(mkt.fillna(0)).cumsum()
ex = lS.sub(lM, axis=0)  # log relative
r21 = np.expm1(lS - lS.shift(21)) * 100
recmax = r21.shift(1).rolling(1250, min_periods=1000).max()
q95 = r21.shift(1).rolling(1250, min_periods=1000).quantile(0.95)
rng = np.random.default_rng(7)
rows = []
for s in S.columns:
    last = -10**9
    for i in range(len(S)):
        x = r21[s].iloc[i]; m = recmax[s].iloc[i]
        if not (np.isfinite(x) and np.isfinite(m)): continue
        kind = None
        if x > m and i - last >= 120: kind = 'record'; last = i
        elif x > q95[s].iloc[i] and x <= m and rng.random() < 0.05: kind = 'top5'
        elif rng.random() < 0.01: kind = 'placebo'
        if kind is None: continue
        row = dict(sector=s, date=S.index[i], kind=kind, r21=x)
        for h in (20, 60, 120, 250):
            if i + h < len(S):
                row[f'x{h}'] = (np.expm1(ex[s].iloc[i + h] - ex[s].iloc[i])) * 100
                row[f'r{h}'] = (np.expm1(lS[s].iloc[i + h] - lS[s].iloc[i])) * 100
        rows.append(row)
R = pd.DataFrame(rows)
pd.set_option('display.width', 200)
def summ(q, lab):
    o = dict(set=lab, n=len(q))
    for h in (20, 60, 120, 250):
        x = q[f'x{h}'].dropna(); o[f'ex{h}'] = round(x.mean(), 2); o[f"hit{h}"] = round((x > 0).mean() * 100) if len(x) else None
    o['raw120_net'] = round(q.r120.dropna().mean() - COST, 2)
    return o
out = [summ(R[R.kind == k], k) for k in ('record', 'top5', 'placebo')]
E = R[R.kind == 'record'].copy()
for lab, lo, hi in (('2003-12', '2003', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026')):
    out.append(summ(E[(E.date >= lo) & (E.date <= hi + '-12-31')], 'record ' + lab))
print(pd.DataFrame(out).to_string(index=False))
print('\nrecord events:'); print(E[['sector', 'date', 'r21', 'x60', 'x120', 'x250']].round(1).to_string(index=False))
d = S.index[-1]; print('\ntoday', d.date(), 'sector 21d vs 5y record:')
print(pd.DataFrame({'r21': r21.iloc[-1], 'rec5y': recmax.iloc[-1]}).round(1).sort_values('r21', ascending=False).to_string())
R.to_csv(os.path.join(os.path.dirname(__file__), 'sector_best_month_events.csv'), index=False)
