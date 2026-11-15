"""Roz ka MILA-JULA ANDAZA (f87; user 15 Nov 2026: 'sab ishaare milakar ek andaza, aur wo kitna sahi baithta hai').
study/combo_model.py ka seekha hua share-model (study/results/combo_share_model.pkl) aaj ke data par:
har A/B share ka 'agle 20 din bazaar se aage rehne ka mauka' (%). Saath mein har din ka andaza log hota hai
(data/andaza_log.csv) aur 20 din baad asli nateeja bhar kar LIVE calibration banta hai: 60% kaha to kitna hua.
Fundamentals (aaj ke) aur AVOID list (f86) sirf saath mein dikhte hain — model mein nahi (unka itihaas nahi).
Output: data/andaza.md, data/andaza_today.csv, data/andaza_log.csv
"""
import os, numpy as np, pandas as pd, joblib, warnings
warnings.filterwarnings('ignore')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(R, *a)
rd = lambda f: pd.read_csv(P('data', 'daily_all', f), index_col=0, parse_dates=True)
a, v = rd('close.csv.gz'), rd('volume.csv.gz')
liqcls = pd.read_csv(P('study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
M = joblib.load(P('study', 'results', 'combo_share_model.pkl')); X = M['X']; mdl = M['gb']
r1 = a.pct_change(fill_method=None); r1 = r1.where(r1.abs() < 0.5)
tv = (a * v).rolling(20, min_periods=15).median(); liq = (tv >= 1e7) & a.columns.isin([s for s in a.columns if liqcls.get(s) in ('A', 'B')])
ind = pd.read_csv(P('data', 'fund', 'summary.csv')).set_index('symbol').industry.reindex(a.columns)
ret = lambda n: a / a.shift(n) - 1
d_ = a.diff(); g_ = d_.clip(lower=0).ewm(alpha=0.5).mean(); l_ = (-d_.clip(upper=0)).ewm(alpha=0.5).mean()
vr1 = v / v.rolling(50, min_periods=40).mean().shift(1)
up200 = a > a.rolling(200, min_periods=180).mean()
last = lambda x: x.iloc[-1]
FE = {
    'r5': last(ret(5)), 'r21': last(ret(21)), 'r63': last(ret(63)), 'r126': last(ret(126)), 'mom12_1': last(a.shift(21) / a.shift(252) - 1),
    'd20': last(a / a.rolling(20).mean() - 1), 'd50': last(a / a.rolling(50).mean() - 1), 'd200': last(a / a.rolling(200, min_periods=180).mean() - 1),
    'dd252': last(a / a.rolling(252, min_periods=200).max() - 1), 'vol5_50': last(v.rolling(5).mean() / v.rolling(50, min_periods=40).mean()),
    'volat20': last(r1.rolling(20).std()), 'rsi2': last(100 - 100 / (1 + g_ / l_)), 'logtv': last(np.log10(tv.clip(lower=1))),
    'shock_dn60': last(((r1 <= -0.10) & (vr1 >= 3)).astype(float).rolling(60, min_periods=1).max()),
    'shock_upweak60': last(((r1 >= 0.10) & (vr1 >= 3) & up200.shift(1).eq(False)).astype(float).rolling(60, min_periods=1).max()),
}
r63 = last(ret(63)); m = last(liq) & r63.notna()
indm = r63[m].groupby(ind[m]).transform('median')
FE['ind_r63'] = indm.reindex(a.columns); FE['r63_vs_ind'] = r63 - FE['ind_r63']
D = pd.DataFrame(FE)[m].replace([np.inf, -np.inf], np.nan)
for k in X: D[k] = D[k].rank(pct=True)
D[X] = D[X].fillna(0.5)
today = a.index[-1]
D['p'] = mdl.predict_proba(D[X].values)[:, 1] * 100
D['dec'] = pd.qcut(D.p.rank(method='first'), 10, labels=False) + 1
D['liq'] = [liqcls.get(s) for s in D.index]; D['industry'] = ind.reindex(D.index)
try:
    F = pd.read_csv(P('data', 'fund', 'summary.csv')).set_index('symbol')
    D['quality'] = F.quality_score.reindex(D.index); D['pe'] = F.trailingPE.reindex(D.index)
except Exception: pass
try: AV = set(pd.read_csv(P('data', 'shock_avoid.csv')).symbol)
except Exception: AV = set()
D['avoid'] = D.index.isin(AV)
D.round(3).to_csv(P('data', 'andaza_today.csv'))
# ---- log + live calibration ----
LF = P('data', 'andaza_log.csv')
L = pd.read_csv(LF) if os.path.exists(LF) else pd.DataFrame(columns=['date', 'symbol', 'p', 'dec', 'exc20'])
L = L[L.date != str(today.date())]
L = pd.concat([L, pd.DataFrame({'date': str(today.date()), 'symbol': D.index, 'p': D.p.round(1), 'dec': D.dec, 'exc20': np.nan})], ignore_index=True)
mk = r1[list(D.index)].mean(axis=1).fillna(0).add(1).cumprod()   # bazaar = aaj ke A/B shares ka barabar-wazan ausat
for dt_, g in L[L.exc20.isna()].groupby('date'):
    i = a.index.get_loc(pd.Timestamp(dt_)) if pd.Timestamp(dt_) in a.index else None
    if i is None or i + 20 >= len(a.index): continue
    sr = a.iloc[i + 20] / a.iloc[i] - 1; mr = mk.iloc[i + 20] / mk.iloc[i] - 1
    L.loc[g.index, 'exc20'] = ((sr.reindex(g.symbol).values - mr) * 100).round(2)
L.to_csv(LF, index=False)
done = L.dropna(subset=['exc20'])
o = [f'# Mila-jula andaza — {today:%d %b %Y} (f87)', '',
     'Har A/B share ka mauka (%) ki wo agle 20 din bazaar se AAGE rahe. 20+ ishaare milakar (chaal, momentum, DMA, 52w, volume, jhatke, industry).',
     'Itihaas (2008-26, walk-forward): dekho study/results/combo_model.md. Ye ANDAZA hai, pakka nahi; fundamentals/khabar alag se jaancho.', '']
top = D[(~D.avoid)].sort_values('p', ascending=False).head(20)
o += ['## Sabse achha andaza (top 20, AVOID hata kar)'] + [f'- {s} ({r.liq}) {r.p:.0f}% | {r.industry} | quality {r.quality if pd.notna(r.get("quality")) else "-"}' for s, r in top.iterrows()] + ['']
bot = D.sort_values('p').head(10)
o += ['## Sabse kamzor andaza (bottom 10)'] + [', '.join(f'{s} {r.p:.0f}%' for s, r in bot.iterrows())] + ['']
try:
    Hd = pd.read_csv(P('paper', 'my_holdings.csv')).symbol.astype(str)
    o += ['## Hamari holdings ka andaza'] + [f'- {s}: {D.p[s]:.0f}% (10 mein se hissa {int(D.dec[s])})' + (' ⚠️ kamzor' if D.dec[s] <= 2 else '') for s in Hd if s in D.index] + ['']
except Exception: pass
if len(done):
    cal = done.groupby('dec').exc20.agg(['count', 'mean']).round(2)
    o += ['## LIVE jaanch: andaze ka hissa (1=sabse kamzor, 10=sabse achha) -> asli 20 din excess %', '```', cal.to_string(), '```']
else:
    o += ['## LIVE jaanch: 20 kaarobaari din baad se shuru (log: data/andaza_log.csv)']
open(P('data', 'andaza.md'), 'w').write('\n'.join(o) + '\n'); print('\n'.join(o))
