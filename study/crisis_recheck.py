"""Re-check headline findings with and without the crisis windows (2008 GFC 1 Jan 2008-30 Jun 2009, COVID 15 Feb-30 Jun 2020)."""
import sys, os, glob, numpy as np, pandas as pd
S = sys.argv[1]; dirs = sys.argv[2:]
CR = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
def crisis(d):
    d = pd.to_datetime(d); m = np.zeros(len(d), bool)
    for a, b in CR: m |= ((d >= a) & (d <= b)).values if hasattr(d, 'values') else ((d >= a) & (d <= b))
    return m
def era(d): d = pd.to_datetime(d); return np.select([d < '2013-01-01', d < '2021-01-01'], ['2003-12', '2013-20'], '2021-26')
out = []
def add(finding, e, allv, exv, nall, nex, unit): out.append(dict(नतीजा=finding, दौर=e, **{'संकट समेत': allv, 'संकट हटाकर': exv, 'बार (समेत)': nall, 'बार (हटाकर)': nex, 'इकाई': unit}))
# 1 dip-buy below MA, by trend bucket
E = pd.read_pickle('/home/claude/work/y20/dip_by_trend.pkl')['E']; E['cr'] = crisis(E.date)
for e, g in E.groupby('era'):
    for nm, z in (('MA से नीचे खरीद: जीत %', g), ('MA से नीचे खरीद (52-हफ्ते trend 30%+): जीत %', g[g.trail_trend_pct >= 30])):
        add(nm, e, z.win.mean() * 100, z[~z.cr].win.mean() * 100, len(z), int((~z.cr).sum()), '%')
    add('MA से नीचे खरीद: औसत फायदा %', e, g.ret.mean() * 100, g[~g.cr].ret.mean() * 100, len(g), int((~g.cr).sum()), '%')
# 2 gap scenarios
G = pd.read_pickle(f'{S}/gs_all.pkl'); G['cr'] = crisis(G.date)
for e, g in G.groupby('era'):
    for nm, z, col, inv in (('Gap up 1-2% → दिन में नीचे बंद %', g[(g.dir == 'Gap UP') & (g['size'] == '1-2%')], 'green', True),
                            ('Gap down 2-4% → दिन में ऊपर बंद %', g[(g.dir == 'Gap DOWN') & (g['size'] == '2-4%')], 'green', False),
                            ('Gap down 2-4% → कल के close से नीचे बंद (gap टिका) %', g[(g.dir == 'Gap DOWN') & (g['size'] == '2-4%')], 'held', False)):
        f = lambda x: (1 - x[col].mean()) * 100 if inv else x[col].mean() * 100
        add(nm, e, f(z), f(z[~z.cr]), len(z), int((~z.cr).sum()), '%')
# 3 chart patterns: ascending triangle target-before-stop real vs shuffled
P = pd.read_pickle(f'{S}/pat_all.pkl'); P['cr'] = crisis(P.date)
for e, g in P.groupby('era'):
    for d_ in ('real', 'shuffled'):
        z = g[(g.kind == 'Ascending Triangle') & (g.data == d_) & (g.res != 'none')]
        add(f'Ascending Triangle target पहले % ({"असली" if d_ == "real" else "किस्मत"})', e, (z.res == 'target').mean() * 100, (z[~z.cr].res == 'target').mean() * 100, len(z), int((~z.cr).sum()), '%')
# 4 overnight vs day, day after expiry, first 3 days, dates 11-24 (basket of all stocks per date)
files = []
for D in dirs: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
on, oc, cc = [], [], []
for f in files:
    d = pd.read_csv(f, parse_dates=['date'], usecols=['date', 'open', 'close']).dropna().drop_duplicates('date').set_index('date').sort_index()
    d = d[(d.open > 0) & (d.close > 0) & (d.index >= '2003-01-01')]
    pc = d.close.shift(); a = d.open / pc - 1; b = d.close / d.open - 1; c = d.close / pc - 1
    bad = (d.open == pc) | (c.abs() > 0.2) | (a.abs() > 0.15)
    on.append(a[~bad].rename(f)); oc.append(b[~bad].rename(f)); cc.append(c[c.abs() <= 0.2].rename(f))
ON = pd.concat(on, axis=1).mean(1); OC = pd.concat(oc, axis=1).mean(1); CC = pd.concat(cc, axis=1); UP = (CC > 0).sum(1) / CC.notna().sum(1); CCm = CC.mean(1)
B = pd.DataFrame({'on': ON, 'oc': OC, 'up': UP, 'cc': CCm}).dropna(); B = B[CC.notna().sum(1).reindex(B.index) >= 30]
B['cr'] = crisis(B.index.to_series()); B['era'] = era(B.index.to_series())
cal = pd.Series(B.index); m_ = cal.dt.to_period('M')
def expd(s):
    o = set()
    for (y, m), g in s.groupby([s.dt.year, s.dt.month]):
        last = pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0); tgt = 1 if pd.Timestamp(y, m, 1) >= pd.Timestamp(2025, 9, 1) else 3
        while last.dayofweek != tgt: last -= pd.Timedelta(days=1)
        c_ = g[g <= last]
        if len(c_): o.add(c_.iloc[-1])
    return o
Ex = expd(cal); L = list(cal); B['after_exp'] = B.index.isin([L[i + 1] for i in range(len(L) - 1) if L[i] in Ex]); B['first3'] = B.index.isin(cal[cal.groupby(m_).cumcount() < 3]); B['mid'] = B.index.day.isin(range(11, 25))
for e, g in B.groupby('era'):
    add('रात भर (close→open) औसत % रोज़', e, g.on.mean() * 100, g[~g.cr].on.mean() * 100, len(g), int((~g.cr).sum()), '%')
    add('दिन में (open→close) औसत % रोज़', e, g.oc.mean() * 100, g[~g.cr].oc.mean() * 100, len(g), int((~g.cr).sum()), '%')
    for nm, col in (('Expiry के अगले दिन: ऊपर वाले शेयर % (आम दिन से फर्क)', 'after_exp'), ('महीने के पहले 3 दिन: ऊपर वाले शेयर % (आम दिन से फर्क)', 'first3'), ('तारीख 11-24: ऊपर वाले शेयर % (आम दिन से फर्क)', 'mid')):
        f = lambda x: (x[x[col]].up.mean() - x[~x[col]].up.mean()) * 100
        add(nm, e, f(g), f(g[~g.cr]), int(g[col].sum()), int((g[col] & ~g.cr).sum()), 'अंक')
R = pd.DataFrame(out); R['फर्क'] = R['संकट हटाकर'] - R['संकट समेत']; R.to_pickle(f'{S}/crisis_recheck.pkl')
pd.set_option('display.width', 250); print(R.round(2).to_string())
