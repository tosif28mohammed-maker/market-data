"""r052 (22 Nov 2026, Tosif live ask): gold/silver crash — buy now, wait, or stagger? which signal marks the bottom?
RULES WRITTEN BEFORE RESULTS (data/global CMD_GOLD, CMD_SILVER 2000-08..2026-11-20, USD; INR = x FX_USDINR 2003-12+;
widen sample with CMD_COPPER, CMD_ALUMINIUM, CMD_BRENT, CMD_CRUDE_WTI for the entry-method part):
 T1 weekly crash: week return (Fri-Fri, 5 trading days) <= -6% gold / <= -10% silver (first in 4 weeks) -> next 1/4/13/26/52 weeks;
    chance = all weeks; split: dollar index 20d up vs down; price below/above 200DMA.
 T2 drawdown zone: first close >= X% below running peak (gold 20/25/30, silver 40/50/60) per episode (episode resets at new peak)
    -> entry methods compared on forward 3/6/12 months and on the extra pain (max further fall from entry within 12 months):
    A buy at once; B 4 equal weekly tranches; C wait first close above 50DMA (max 12 months wait, else buy at the end);
    D wait first weekly close >= 8% above the post-signal low.
 T3 Fed hike: FOMC hike dates (study/research/r2026-11-21-eve/r040_hikes.csv, Indian next day -1) -> gold 20/60/120/250 days;
    first hike of cycle separately (2004-06-30, 2015-12-16, 2022-03-16).
 Costs: ignored in % (ETF ~0.1% + expense ~0.5%/yr; physical 3% GST + making) — reported separately in the message.
"""
import numpy as np, pandas as pd
R = '/home/claude/market-data'
def g(f):
    s = pd.read_csv(f'{R}/data/global/{f}.csv', parse_dates=['date']).set_index('date').close
    s = s[~s.index.duplicated()].dropna(); return s[s > 0]
G, S, I, D = g('CMD_GOLD'), g('CMD_SILVER'), g('FX_USDINR'), g('FX_DOLLAR_INDEX')
GI = (G * I.reindex(G.index).ffill()).dropna(); SI = (S * I.reindex(S.index).ffill()).dropna()
d20 = D / D.shift(20) - 1
rng = np.random.default_rng(52)
print('LIVE 20 Nov: gold', G.iloc[-1], 'week', round((G.iloc[-1] / G.iloc[-6] - 1) * 100, 1), 'dd', round((G.iloc[-1] / G.max() - 1) * 100, 1),
      '| silver', S.iloc[-1], 'week', round((S.iloc[-1] / S.iloc[-6] - 1) * 100, 1), 'dd', round((S.iloc[-1] / S.max() - 1) * 100, 1),
      '| DXY 20d', round(d20.iloc[-1] * 100, 1))
# ---------- T1 weekly crash ----------
def t1(s, th, lab):
    w = s.resample('W-FRI').last().dropna(); wr = w.pct_change()
    ev = []; last = None
    for d, r in wr.items():
        if r <= th and (last is None or (d - last).days > 28): ev.append(d); last = d
    rows = []
    for d in ev:
        i = w.index.get_loc(d); row = {'date': d, 'wk': wr[d] * 100}
        for h in (1, 4, 13, 26, 52):
            row[f'w{h}'] = (w.iloc[i + h] / w.iloc[i] - 1) * 100 if i + h < len(w) else np.nan
        dd = s.loc[:d]; row['below200'] = bool(dd.iloc[-1] < dd.rolling(200).mean().iloc[-1])
        row['dxy_up'] = bool(d20.asof(d) > 0); row['ddpk'] = (dd.iloc[-1] / dd.max() - 1) * 100
        # extra fall within next 13 weeks
        fut = w.iloc[i:i + 14]; row['maxfall13'] = (fut.min() / w.iloc[i] - 1) * 100
        rows.append(row)
    E = pd.DataFrame(rows).set_index('date')
    allw = {h: (w.shift(-h) / w - 1) * 100 for h in (1, 4, 13, 26, 52)}
    print(f'\n== T1 {lab}: weekly <= {th*100:.0f}% events n{len(E)}')
    for h in (1, 4, 13, 26, 52):
        x = E[f'w{h}'].dropna(); a = allw[h].dropna()
        sims = np.array([rng.choice(a.values, len(x)).mean() for _ in range(5000)])
        print(f'  w{h:2d}: {x.mean():+.2f}% (up {100*(x>0).mean():.0f}%, median {x.median():+.2f}) vs all {a.mean():+.2f} ({100*(a>0).mean():.0f}%) p_hi {(sims>=x.mean()).mean():.2f}')
    for c in ['below200', 'dxy_up']:
        print('  split', c, E.groupby(c)[['w1', 'w4', 'w13', 'w26', 'maxfall13']].mean().round(2).assign(n=E.groupby(c).size()).to_dict('index'))
    print(E.round(1).to_string())
    return E
E1 = t1(G, -0.06, 'GOLD USD'); E2 = t1(S, -0.10, 'SILVER USD'); t1(GI, -0.06, 'GOLD INR')
# ---------- T2 drawdown zone entry methods ----------
assets = {'GOLD': G, 'SILVER': S, 'GOLD_INR': GI, 'SILVER_INR': SI, 'COPPER': g('CMD_COPPER'), 'ALUM': g('CMD_ALUMINIUM'), 'BRENT': g('CMD_BRENT'), 'WTI': g('CMD_CRUDE_WTI')}
ths = {'GOLD': [20, 25, 30], 'GOLD_INR': [15, 20, 25], 'SILVER': [40, 50, 60], 'SILVER_INR': [35, 45, 55], 'COPPER': [30, 40], 'ALUM': [25, 35], 'BRENT': [40, 50], 'WTI': [40, 50]}
rows = []
for nm, s in assets.items():
    pk = s.cummax(); ddv = s / pk - 1; m50 = s.rolling(50).mean()
    for th in ths[nm]:
        inep = False; lastpk = None
        for i in range(len(s)):
            d = s.index[i]
            if inep and pk.iloc[i] > lastpk: inep = False
            if not inep and ddv.iloc[i] <= -th / 100:
                inep = True; lastpk = pk.iloc[i]
                if i + 260 >= len(s): rows.append(dict(asset=nm, th=th, date=d, live=True)); continue
                p0 = s.iloc[i]; end = lambda j, h: s.iloc[min(j + h, len(s) - 1)]
                rec = dict(asset=nm, th=th, date=d, live=False)
                # A
                rec['A_entry'] = p0
                # B 4 weekly tranches
                rec['B_entry'] = np.mean([s.iloc[i + 5 * k] for k in range(4)])
                # C first close above 50DMA after signal (max 252 days)
                jc = next((j for j in range(i + 1, min(i + 252, len(s))) if s.iloc[j] > m50.iloc[j]), min(i + 252, len(s) - 1))
                rec['C_entry'] = s.iloc[jc]; rec['C_wait'] = jc - i
                # D first weekly close >= 8% above the post-signal low
                lo = p0; jd = None
                for j in range(i + 1, min(i + 252, len(s))):
                    lo = min(lo, s.iloc[j])
                    if s.index[j].weekday() == 4 and s.iloc[j] >= lo * 1.08: jd = j; break
                jd = jd if jd is not None else min(i + 252, len(s) - 1)
                rec['D_entry'] = s.iloc[jd]; rec['D_wait'] = jd - i
                # value at fixed calendar points measured from SIGNAL date (same horizon for all methods)
                for h, lab in [(63, '3m'), (126, '6m'), (252, '12m')]:
                    pv = end(i, h)
                    for k in 'ABCD': rec[f'{k}_{lab}'] = (pv / rec[f'{k}_entry'] - 1) * 100
                rec['A_maxfall'] = (s.iloc[i:i + 253].min() / p0 - 1) * 100
                rec['low_day'] = int(np.argmin(s.iloc[i:i + 253].values))
                rows.append(rec)
T = pd.DataFrame(rows); T.to_csv(f'{R}/study/research/gold_silver_entry_T2.csv', index=False)
H = T[~T.live]
print('\n== T2 drawdown episodes (non-live):', len(H))
print(H[['asset', 'th', 'date', 'A_3m', 'A_12m', 'B_12m', 'C_12m', 'D_12m', 'C_wait', 'D_wait', 'A_maxfall', 'low_day']].round(1).to_string())
for k in 'ABCD':
    print(f'method {k}: 3m {H[k+"_3m"].mean():+.1f} 6m {H[k+"_6m"].mean():+.1f} 12m {H[k+"_12m"].mean():+.1f} (12m up {100*(H[k+"_12m"]>0).mean():.0f}%, median {H[k+"_12m"].median():+.1f})')
print('precious only:'); P = H[H.asset.str.contains('GOLD|SILVER')]
for k in 'ABCD':
    print(f'  {k}: 12m {P[k+"_12m"].mean():+.1f} (up {100*(P[k+"_12m"]>0).mean():.0f}%) median {P[k+"_12m"].median():+.1f}; n{len(P)}')
print('A extra fall after signal (median, worst):', H.A_maxfall.median().round(1), H.A_maxfall.min().round(1), '| days to low median', H.low_day.median())
print('LIVE episodes:', T[T.live][['asset', 'th', 'date']].to_string())
# ---------- T3 Fed hikes ----------
hk = pd.read_csv(f'{R}/study/research/r2026-11-21-eve/r040_hikes.csv', index_col=0, parse_dates=True).index - pd.Timedelta(days=1)
first = pd.to_datetime(['2004-06-30', '2015-12-16', '2022-03-16'])
def fw(s, d, h):
    i = s.index.searchsorted(d); return (s.iloc[i + h] / s.iloc[i] - 1) * 100 if i + h < len(s) else np.nan
allr = {h: (G.shift(-h) / G - 1).dropna() * 100 for h in (20, 60, 120, 250)}
print('\n== T3 gold after Fed hikes')
for lab, ds in [('all hikes', hk), ('first hike', first)]:
    out = []
    for h in (20, 60, 120, 250):
        x = np.array([fw(G, d, h) for d in ds]); x = x[np.isfinite(x)]
        out.append(f'{h}d {x.mean():+.2f} (up {100*(x>0).mean():.0f}%, n{len(x)}) vs all {allr[h].mean():+.2f}')
    print(lab, ' | '.join(out))
for d in first:
    print('  first hike', d.date(), {h: round(fw(G, d, h), 1) for h in (20, 60, 120, 250)}, 'gold 60d before', round(-fw(G, d - pd.Timedelta(days=90), 0) if False else (G.asof(d) / G.asof(d - pd.Timedelta(days=90)) - 1) * 100, 1),
          'low within +-90d at', G.loc[d - pd.Timedelta(days=90):d + pd.Timedelta(days=90)].idxmin().date())
