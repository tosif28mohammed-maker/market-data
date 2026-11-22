# ROBOT
"""Claim tests 22 Nov 2026 (06:11 run).
GOLD-01 (Angel One 'Gold Down 33%, Silver Down 60%' / PR Sundar 'Time to BUY GOLD?'): after a deep fall from peak gold/silver is a buy.
  Test: data/global CMD_GOLD/CMD_SILVER (USD, 2000+) and INR version (x FX_USDINR, 2003-12+). Event = first day drawdown from
  running peak crosses -20/-30/-40% (silver -40/-60%) after a fresh peak; forward 60/120/250 trading days vs all days.
ET-02 (ET Markets 'Sharp rupee appreciation may cut IT firms FY27 earnings by up to 13%'): rupee strengthening -> IT stocks lag.
  Test: month-end; USDINR 1-month change <= -1.5% (rupee strong) / >= +1.5% (weak); IT basket (TCS INFY WIPRO HCLTECH TECHM LTIM
  MPHASIS PERSISTENT COFORGE LTTS) equal-weight excess vs all-stock market next 1 and 3 months; also same month.
"""
import sys, os, numpy as np, pandas as pd
B = os.path.dirname(__file__); sys.path.insert(0, os.path.join(B, '..', '..'))
G = os.path.join(B, '..', '..', '..', 'data', 'global')
def rd(n):
    d = pd.read_csv(os.path.join(G, n), parse_dates=['date']).set_index('date')['close'].dropna()
    return d[d > 0]
gold, silv, fx = rd('CMD_GOLD.csv'), rd('CMD_SILVER.csv'), rd('FX_USDINR.csv')
out = ['# GOLD-01 drawdown buy / ET-02 rupee vs IT\n']
def dd_test(s, name, levels):
    pk = s.cummax(); dd = (s / pk - 1) * 100
    for lv in levels:
        ev = []; armed = True
        for i in range(len(s)):
            if dd.iloc[i] == 0: armed = True
            if armed and dd.iloc[i] <= -lv:
                ev.append(i); armed = False
        line = f'{name} dd<=-{lv}%: n={len(ev)} dates={[str(s.index[i].date()) for i in ev]}'
        for h in (60, 120, 250):
            f = (s.shift(-h) / s - 1) * 100
            v = [f.iloc[i] for i in ev if not np.isnan(f.iloc[i])]
            line += f' | {h}d ev={np.round(v,1).tolist()} avg={np.mean(v) if v else np.nan:.1f} all={f.mean():.1f}'
            # worst further drop after event within h
        mins = []
        for i in ev:
            w = s.iloc[i:i + 250]; mins.append(round((w.min() / s.iloc[i] - 1) * 100, 1))
        out.append(line + f' | further worst drop in 250d={mins}')
dd_test(gold, 'GOLD_USD', (20, 30, 40)); dd_test(silv, 'SILVER_USD', (40, 60))
gi = (gold * fx.reindex(gold.index).ffill()).dropna(); si = (silv * fx.reindex(silv.index).ffill()).dropna()
dd_test(gi, 'GOLD_INR', (20, 30)); dd_test(si, 'SILVER_INR', (40, 60))
for nm, s in [('GOLD_USD', gold), ('SILVER_USD', silv), ('GOLD_INR', gi), ('SILVER_INR', si)]:
    out.append(f'{nm} now: {s.iloc[-1]:.1f} on {s.index[-1].date()}, dd from peak {(s.iloc[-1]/s.cummax().iloc[-1]-1)*100:.1f}%')
# ET-02
from ni_common import load
P = load(); a = P['a']
r = a.pct_change(fill_method=None); r = r.where(r.abs() < 0.5)
mk = r.mean(axis=1)
IT = [x for x in ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM', 'MPHASIS', 'PERSISTENT', 'COFORGE', 'LTTS'] if x in a.columns]
itr = r[IT].mean(axis=1)
ex = (np.log1p(itr.fillna(0)) - np.log1p(mk.fillna(0)))
exm = np.expm1(ex.resample('ME').sum()) * 100
fxm = fx.resample('ME').last().pct_change() * 100
D = pd.DataFrame({'fx': fxm, 'it0': exm}).dropna()
D['it1'] = exm.shift(-1); D['it3'] = np.expm1(ex.resample('ME').sum().rolling(3).sum().shift(-3)) * 100
out.append(f'\n## ET-02 IT basket {IT}, months {len(D)} ({D.index[0].date()}..)')
for lab, m in [('rupee strong fx<=-1.5', D.fx <= -1.5), ('rupee weak fx>=+1.5', D.fx >= 1.5), ('middle', (D.fx > -1.5) & (D.fx < 1.5))]:
    s = D[m]
    out.append(f'{lab}: n={len(s)} same-month IT excess={s.it0.mean():.2f} next1m={s.it1.mean():.2f} (IT ahead {(s.it1>0).mean()*100:.0f}%) next3m={s.it3.mean():.2f}')
    for era, a0, a1 in [('2003-12', '2003', '2012'), ('2013-26', '2013', '2026')]:
        t = s.loc[a0:a1]
        out.append(f'   {era}: n={len(t)} same={t.it0.mean():.2f} next1m={t.it1.mean():.2f} next3m={t.it3.mean():.2f}')
out.append(f'corr(fx 1m, IT excess same month)={D.fx.corr(D.it0):.2f}, next month={D.fx.corr(D.it1):.2f}')
out.append(f'last 6 months fx: {fxm.tail(6).round(2).tolist()} IT excess: {exm.tail(6).round(2).tolist()}')
txt = '\n'.join(out); open(os.path.join(B, 'gold_dd_inr_it.out.txt'), 'w').write(txt); print(txt)
