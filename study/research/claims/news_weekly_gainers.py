# ROBOT
"""Claim tests 22 Nov 2026 (06:11 run).
ET-01 (ET Markets weekly 'Market winners: 10 stocks that surged up to 14%' lists, queue.csv): buying the week's top Nifty-500 gainers.
  Test: every week's last trading day, top-10 5-day gainers (liq D excluded) -> buy at close; also strict '>=12% week' group;
  contrast = bottom-10 losers. Excess vs equal-weight market, 5/20/60 days, costs 0.25%, eras + last 2/4/6 months.
  Stop/target view: +6% target vs -6% stop within 20 days (stop first if same bar).
BS-01 (Business Standard 'Markets gain 2.6% on FPI inflows'): a strong Nifty week (>=+2.5%) continues next 1/4/12 weeks?
"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, fwd, evaluate, COST
P = load(); a = P['a']
F, mkt = fwd(P, (5, 20, 60))
r5 = a.pct_change(5, fill_method=None) * 100
r5 = r5.where(r5.abs() < 80)
wk = pd.Series(a.index, index=a.index).groupby(a.index.to_period('W')).max().values
isw = a.index.isin(wk)
rank = r5.rank(axis=1, ascending=False)
nst = r5.notna().sum(axis=1)
top = (rank <= 10) & pd.DataFrame(np.repeat(isw[:, None], a.shape[1], 1), index=a.index, columns=a.columns) & (nst.values[:, None] >= 200)
big = top & (r5 >= 12)
rnk2 = r5.rank(axis=1, ascending=True)
bot = (rnk2 <= 10) & top.columns.to_series().pipe(lambda s: True) & pd.DataFrame(np.repeat(isw[:, None], a.shape[1], 1), index=a.index, columns=a.columns) & (nst.values[:, None] >= 200)
rows = []
for nm, ev in [('top10_week_gainers', top), ('top10_and_>=12pct', big), ('bottom10_week_losers', bot)]:
    rows += evaluate(ev, F, nm)
T = pd.DataFrame(rows)
cols = ['study', 'h', 'era', 'n', 'excess', 'win_vs_mkt', 'raw_net', 'raw_win', 't_dates']
out = ['# ET-01 weekly top gainers / BS-01 strong Nifty week\n', T[cols].to_string(index=False)]
# recent windows on 5d and 20d
end = a.index[-1]
for nm, ev in [('top10', top), ('bottom10', bot)]:
    for mths in (2, 4, 6):
        s = end - pd.DateOffset(months=mths)
        for h in (5, 20):
            raw, ex = F[h]
            v = ex.where(ev).loc[s:].stack().dropna(); rv = raw.where(ev).loc[s:].stack().dropna()
            out.append(f'{nm} last {mths}m h={h}: n={len(v)} excess={v.mean():.2f} raw_net={rv.mean()-COST:.2f} win={((rv>COST).mean()*100):.1f}')
# target/stop 6% within 20d
H, L, C = P['h'].values, P['l'].values, a.values
def ts(ev, tg=6, sl=6, md=20):
    res = []
    E = ev.values
    for i, j in zip(*np.nonzero(E)):
        e = C[i, j]
        if not e > 0: continue
        r = None
        for k in range(i + 1, min(i + 1 + md, len(C))):
            if np.isnan(L[k, j]): break
            if L[k, j] <= e * (1 - sl / 100): r = -sl; break
            if H[k, j] >= e * (1 + tg / 100): r = tg; break
        if r is None:
            k = min(i + md, len(C) - 1)
            if np.isnan(C[k, j]): continue
            r = (C[k, j] / e - 1) * 100
        res.append((a.index[i], r))
    d = pd.DataFrame(res, columns=['d', 'r']).set_index('d')
    return d
for nm, ev in [('top10', top), ('bottom10', bot)]:
    d = ts(ev)
    for lab, sub in [('ALL', d), ('2021-26', d.loc['2021':]), ('last6m', d.loc[end - pd.DateOffset(months=6):])]:
        out.append(f'{nm} +6/-6 20d {lab}: n={len(sub)} target_hit={(sub.r>=6).mean()*100:.1f}% stop={(sub.r<=-6).mean()*100:.1f}% avg_net={sub.r.mean()-COST:.2f}%')
# BS-01 Nifty strong week
n = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'NIFTY.csv'))
n.columns = [x.lower() for x in n.columns]
n['date'] = pd.to_datetime(n['date']); n = n.set_index('date')['close'].dropna()
w = n.resample('W-FRI').last().dropna(); wr = w.pct_change() * 100
out.append('\n## BS-01 Nifty weekly (from %s)' % w.index[0].date())
for k in (1, 4, 12):
    f = (w.shift(-k) / w - 1) * 100
    s = f[wr >= 2.5].dropna(); b = f.dropna()
    s2 = f[(wr >= 2.5) & (w.index >= '2015')].dropna(); b2 = f[w.index >= '2015'].dropna()
    out.append(f'next {k}w: after +2.5% week n={len(s)} avg={s.mean():.2f} up={((s>0).mean()*100):.0f}% | all weeks avg={b.mean():.2f} up={((b>0).mean()*100):.0f}% || since2015 strong n={len(s2)} {s2.mean():.2f} vs all {b2.mean():.2f}')
txt = '\n'.join(out)
open(os.path.join(os.path.dirname(__file__), 'news_weekly_gainers.out.txt'), 'w').write(txt)
print(txt)
