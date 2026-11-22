"""r049 (22 Nov 2026) FII-01: very big FII net-BUY month (Nov 2026 = record +1.12 lakh cr, after 6+ selling months)
-> what did Nifty / stocks do in the next 1, 3, 6 months?
RULES WRITTEN BEFORE RESULTS:
 data: data/fii/fii_monthly_tapetide.csv (cash-market FII net, Rs cr, 2014-01..2026-10 complete; Nov 2026 partial = live case).
 BIG_BUY  = month net >= 80th pct of |all| scaled: we use z = net / std(net over previous 24 months) >= 1.5  (scale-free)
            and also the raw cut net >= +20,000 cr.
 TURN     = BIG_BUY and >= 4 of previous 6 months were net SELL (the Nov 2026 shape).
 BIG_SELL = z <= -1.5.
 outcome: Nifty (data/NIFTY.csv, month-end close) next 1/3/6 month return vs all months; non-overlap check = events
          at least 3 months apart; chance = 10,000 shuffles of the forward returns over the same months.
 scenarios: next-3m Nifty up(>+3%)/flat/down(<-3%) -> circumstances at the signal month end: Nifty prior 3m, Nifty vs
          200DMA, India VIX, USDINR 3m change, Brent 3m change, S&P500 prior 3m, DXY 3m change.
 stock level (wider sample): u1000+u2000 panel (liq D dropped): next-1m/3m return of LARGE (top 100 by 6m median
          traded value) vs REST, and prior-6m LOSERS (bottom 20%) vs WINNERS (top 20%), after BIG_BUY months vs other months.
 costs: delivery 0.25% round trip on stock legs; index numbers gross (buy & hold proxy).
"""
import os, sys, numpy as np, pandas as pd
R = '/home/claude/market-data'
sys.path.insert(0, f'{R}/study')
f = pd.read_csv(f'{R}/data/fii/fii_monthly_tapetide.csv')
f['m'] = pd.PeriodIndex(f.month, freq='M'); f = f.set_index('m').fii_net_cr
live = f.iloc[-1]; f = f.iloc[:-1]
sd = f.rolling(24, min_periods=12).std().shift(1)
z = f / sd
def g(name):
    d = pd.read_csv(f'{R}/data/global/{name}.csv' if not name.startswith('NIFTY') and not name.startswith('INDIA') else f'{R}/data/{name}.csv', parse_dates=['date']).set_index('date')
    c = d['adj'] if 'adj' in d and (d['adj'] > 0).all() else d['close']
    return c.dropna()
nif = g('NIFTY'); vix = g('INDIAVIX')
me = nif.resample('ME').last(); me.index = me.index.to_period('M')
dma = (nif / nif.rolling(200).mean() - 1).resample('ME').last(); dma.index = dma.index.to_period('M')
vixm = vix.resample('ME').last(); vixm.index = vixm.index.to_period('M')
def m3(name):
    s = g(name).resample('ME').last(); s.index = s.index.to_period('M'); return (s / s.shift(3) - 1) * 100
inr, brent, spx, dxy = m3('FX_USDINR'), m3('CMD_BRENT'), m3('US_SP500'), m3('FX_DOLLAR_INDEX')
fw = {h: (me.shift(-h) / me - 1) * 100 for h in (1, 3, 6)}
pr3 = (me / me.shift(3) - 1) * 100
D = pd.DataFrame({'net': f, 'z': z, 'r1': fw[1], 'r3': fw[3], 'r6': fw[6], 'pr3': pr3, 'dma': dma * 100, 'vix': vixm,
                  'inr3': inr, 'brent3': brent, 'spx3': spx, 'dxy3': dxy, 'cur': (me / me.shift(1) - 1) * 100}).loc[f.index]
D['sell6'] = (f.shift(1).rolling(6).apply(lambda x: (x < 0).sum()))
D['BIG'] = (D.z >= 1.5); D['BIGRAW'] = D.net >= 20000; D['TURN'] = D.BIG & (D.sell6 >= 4); D['SELL'] = D.z <= -1.5
rng = np.random.default_rng(49)
def test(mask, lab):
    out = []
    for h in ('r1', 'r3', 'r6'):
        x = D.loc[mask, h].dropna(); allv = D[h].dropna()
        if len(x) == 0: continue
        sims = np.array([rng.choice(allv.values, len(x), replace=False).mean() for _ in range(10000)])
        p = (sims >= x.mean()).mean()
        out.append(f'{h} n{len(x)} mean {x.mean():+.2f} (up {100*(x>0).mean():.0f}%) vs all {allv.mean():+.2f} ({100*(allv>0).mean():.0f}%) p_hi {p:.3f}')
    print(lab, '|', ' ; '.join(out))
print('LIVE Nov 2026 partial', live, 'z vs prev24 std', round(live / f.iloc[-24:].std(), 2))
for k in ['BIG', 'BIGRAW', 'TURN', 'SELL']:
    test(D[k], k)
    for era, a, b in [('2014-19', '2014', '2019'), ('2020-26', '2020', '2026')]:
        m = D[k] & (D.index >= pd.Period(a + '-01', 'M')) & (D.index <= pd.Period(b + '-12', 'M'))
        test(m, f'  {k} {era}')
print('\nconcurrent month Nifty return in BIG months', D.loc[D.BIG, 'cur'].mean().round(2), 'vs all', D.cur.mean().round(2), 'corr(net,cur)', D.net.corr(D.cur).round(2), 'corr(net,r1)', D.net.corr(D.r1).round(2), 'corr(z,r3)', D.z.corr(D.r3).round(2))
print('\nBIG months list:')
cols = ['net', 'z', 'cur', 'r1', 'r3', 'r6', 'pr3', 'dma', 'vix', 'inr3', 'brent3', 'spx3', 'dxy3', 'sell6', 'TURN']
print(D.loc[D.BIG, cols].round(1).to_string())
# non-overlap BIG (>=3 months apart)
idx = []; last = None
for m in D.index[D.BIG]:
    if last is None or (m - last).n >= 3: idx.append(m); last = m
test(D.index.isin(idx), 'BIG non-overlap(3m)')
# scenarios for BIG events by next-3m outcome
B = D.loc[D.BIG].dropna(subset=['r3']).copy()
B['sc'] = np.where(B.r3 > 3, 'UP', np.where(B.r3 < -3, 'DOWN', 'FLAT'))
print('\nscenario means (BIG events):'); print(B.groupby('sc')[['pr3', 'dma', 'vix', 'inr3', 'brent3', 'spx3', 'dxy3', 'sell6', 'r3']].mean().round(1).assign(n=B.groupby('sc').size()))
# circumstance check over ALL months: does the circumstance predict r3 anyway? (so scenario finding is not just general)
for c in ['dma', 'pr3', 'inr3', 'brent3', 'spx3', 'dxy3']:
    a = D[[c, 'r3']].dropna(); b = B[[c, 'r3']].dropna()
    print(f'corr({c}, r3): all {a[c].corr(a.r3):+.2f}  BIG {b[c].corr(b.r3):+.2f} (n{len(b)})')
D.to_csv(f'{R}/study/research/fii_month_big.csv')

# ---------- stock level ----------
from ni_common import load
P = load(); A = P['a']; C = P['c']; V = P['v']
mA = A.resample('ME').last(); mA.index = mA.index.to_period('M')
tv = (C * V).rolling(126, min_periods=60).median().resample('ME').last(); tv.index = tv.index.to_period('M')
mA = mA.loc['2013-06':]; tv = tv.reindex(mA.index)
rk = tv.rank(axis=1, ascending=False)
mom6 = mA / mA.shift(6) - 1
res = []
for h in (1, 3):
    fr = (mA.shift(-h) / mA - 1).where(lambda x: x.abs() < 3) * 100
    for m in D.index:
        if m not in fr.index: continue
        row = fr.loc[m].dropna()
        if len(row) < 200: continue
        lg = row[rk.loc[m].reindex(row.index) <= 100]; rest = row[rk.loc[m].reindex(row.index) > 100]
        mo = mom6.loc[m].reindex(row.index).dropna(); q = mo.quantile([.2, .8])
        los = row.reindex(mo[mo <= q.iloc[0]].index).dropna(); win = row.reindex(mo[mo >= q.iloc[1]].index).dropna()
        res.append(dict(m=m, h=h, BIG=bool(D.loc[m, 'BIG']), large=lg.mean(), rest=rest.mean(), losers=los.mean(), winners=win.mean(), all=row.mean()))
S = pd.DataFrame(res)
S['L_minus_R'] = S.large - S.rest; S['Los_minus_Win'] = S.losers - S.winners
print('\nSTOCK LEVEL (equal-weight, gross; subtract 0.25 cost per leg-trade):')
for h in (1, 3):
    s = S[S.h == h]
    for c in ['all', 'large', 'rest', 'L_minus_R', 'Los_minus_Win']:
        x = s.loc[s.BIG, c]; y = s.loc[~s.BIG, c]
        sims = np.array([rng.choice(s[c].values, len(x), replace=False).mean() for _ in range(5000)])
        print(f'h{h} {c:14s} BIG {x.mean():+.2f} (n{len(x)}, pos {100*(x>0).mean():.0f}%) vs other {y.mean():+.2f}  p_hi {(sims>=x.mean()).mean():.3f} p_lo {(sims<=x.mean()).mean():.3f}')
S.to_csv(f'{R}/study/research/fii_month_big_stocks.csv', index=False)
