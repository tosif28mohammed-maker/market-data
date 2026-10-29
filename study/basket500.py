"""Basket calendar effects by era on the whole Nifty 500 (dates as units). Usage: python study/basket500.py <u500_dir> <master.csv> <out.csv>"""
import sys, os, math, numpy as np, pandas as pd
U, MASTER, OUT = sys.argv[1:4]; master = set(pd.to_datetime(pd.read_csv(MASTER).date))
HJ = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hijri_tbla.csv'), parse_dates=['date']).set_index('date').hijri
ups = []
for f in os.listdir(os.path.join(U, 'daily')):
    d = pd.read_csv(os.path.join(U, 'daily', f), parse_dates=['date'], usecols=['date', 'close']).dropna()
    d = d[d.date.isin(master)].drop_duplicates('date').sort_values('date'); d['pct'] = d.close.pct_change() * 100
    bad = d.pct.abs() > 20; d = d[~(bad | bad.shift(1, fill_value=False))].dropna()
    ups.append(d.set_index('date').pct.rename(f[:-7]))
P = pd.concat(ups, axis=1); B = pd.DataFrame({'up': (P > 0).sum(1) / P.notna().sum(1), 'pct': P.mean(1), 'n': P.notna().sum(1)}); B = B[B.n >= 20]
B['date'] = B.index; h = HJ.reindex(B.index); B['hm'] = h.str[5:7].astype(int).values; B['hd'] = h.str[8:].astype(int).values; B['hwk'] = (B.hd - 1) // 7 + 1
B['wd'] = B.date.dt.dayofweek + 1; B['gd'] = B.date.dt.day; B['gm'] = B.date.dt.month; B['gwk'] = (B.gd - 1) // 7 + 1
cal = pd.Series(sorted(B.index)); m_ = cal.dt.to_period('M'); B['month_last'] = B.index.isin(cal[m_ != m_.shift(-1)]); B['month_first3'] = B.index.isin(cal[cal.groupby(m_).cumcount() < 3])
def expd(s):
    out = set()
    for (y, m), g in s.groupby([s.dt.year, s.dt.month]):
        last = pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0); tgt = 1 if pd.Timestamp(y, m, 1) >= pd.Timestamp(2025, 9, 1) else 3
        while last.dayofweek != tgt: last -= pd.Timedelta(days=1)
        c = g[g <= last]
        if len(c) and c.iloc[-1] >= pd.Timestamp(2001, 11, 1): out.add(c.iloc[-1])
    return out
E_ = expd(cal); L_ = list(cal); B['after_expiry'] = B.index.isin([L_[i + 1] for i in range(len(L_) - 1) if L_[i] in E_]); B['expiry_day'] = B.index.isin(E_)
nb = pd.Series(L_).shift(-1); bd = np.busday_count(cal.values.astype('datetime64[D]'), nb.fillna(cal).values.astype('datetime64[D]')); B['preholiday'] = B.index.isin(cal[(bd > 1) & nb.notna()])
B['ramadan10'] = (B.hm == 9) & (B.hd >= 20); B['midmonth'] = B.gd.between(11, 24)
SEG = {'ALL': ('1990', '2031'), 'E1': ('1990', '2002-12-31'), 'E2': ('2003', '2012-12-31'), 'E3': ('2013', '2020-12-31'), 'E4': ('2021', '2031'), 'R1': ('2021', '2023-10-31'), 'R2': ('2023-11-01', '2031')}
rows = []
for sg, (a, b) in SEG.items():
    x = B[(B.index >= a) & (B.index <= b)].copy()
    if len(x) < 300: continue
    x['ex'] = (x.up - x.up.mean()) * 100
    for k in ['wd', 'gd', 'gm', 'gwk', 'hd', 'hm', 'hwk']:
        for v, g in x.groupby(k):
            if len(g) >= 8: rows.append(dict(era=sg, key=k, val=str(int(v)), n=len(g), excess=g.ex.mean(), t=g.ex.mean() / (g.ex.std() / math.sqrt(len(g))), pct=g.pct.mean()))
    for e in ['after_expiry', 'expiry_day', 'preholiday', 'month_last', 'month_first3', 'ramadan10', 'midmonth']:
        g = x[x[e]]
        if len(g) >= 8: rows.append(dict(era=sg, key='event', val=e, n=len(g), excess=g.ex.mean(), t=g.ex.mean() / (g.ex.std() / math.sqrt(len(g))), pct=g.pct.mean()))
pd.DataFrame(rows).to_csv(OUT, index=False); print('basket days', len(B))
