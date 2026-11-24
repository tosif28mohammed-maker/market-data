# ROBOT  (needs universe500 data via U500)
"""AI-C62277 / AI-C7791E: exclude PSUs in Utilities, Basic Materials (metals/mining), Energy, Industrials (cap goods).
Test: top-300 by traded value, same sectors, PSU vs private basket, monthly formation, hold 60/250d.
PSU list hand-made (central + major state PSUs, Nov 2026 status; ownership changes in past ignored)."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, fwd, era_mask, COST
PSU = set('''SBIN BANKBARODA PNB CANBK UNIONBANK INDIANB BANKINDIA CENTRALBK IOB UCOBANK MAHABANK PSB ONGC IOC BPCL HINDPETRO GAIL OIL
COALINDIA NTPC POWERGRID NHPC SJVN NLCINDIA BEL HAL BHEL BEML SAIL NMDC NATIONALUM HINDCOPPER MOIL KIOCL RECLTD PFC IRFC IREDA HUDCO
LICI GICRE NIACL IRCTC CONCOR RVNL IRCON RAILTEL NBCC ENGINERSIN COCHINSHIP MAZDOCK GRSE BDL MIDHANI SCI MMTC ITDC NFL RCF FACT MRPL
CHENNPETRO BALMLAWRIE ITI MTNL RITES MSTCLTD NSLNISP GMDC GSPL GUJGASLTD GIPCL GSFC GNFC HINDOILEXP MANGCHEFL BHARATDYN TNPL
NAVA ANDHRSUGAR IDBI SBICARD SBILIFE GPIL'''.split()) - {'NAVA', 'ANDHRSUGAR', 'SBICARD', 'SBILIFE', 'GPIL', 'HINDOILEXP', 'MANGCHEFL', 'BHARATDYN'}
SECT = {'Utilities', 'Basic Materials', 'Energy', 'Industrials'}
I = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'fund', 'info.csv')).set_index('symbol')
P = load(); a, c, v = P['a'], P['c'], P['v']
sec = I.sector.reindex(a.columns)
insec = sec.isin(SECT)
ispsu = pd.Series(a.columns.isin(list(PSU)), index=a.columns)
print('PSU found in panel:', int((ispsu & insec).sum()), 'of', len(PSU), '| private same sectors:', int((~ispsu & insec).sum()))
rank = (c * v).rolling(250, min_periods=200).median().rank(axis=1, ascending=False)
F, mkt = fwd(P, hs=(60, 250))
dates = [d for d in a.index.to_series().groupby(a.index.to_period('M')).first().values if d >= pd.Timestamp('2004-01-01')]
rows = []; yr = {}
for h in (60, 250):
    raw = F[h][0]; rec = []
    for d in dates:
        top = rank.loc[d] <= 300
        ps = top & insec & ispsu; pr = top & insec & ~ispsu
        if ps.sum() < 3 or pr.sum() < 3: continue
        rr = raw.loc[d]
        rec.append(dict(date=d, n_psu=int(ps.sum()), n_pr=int(pr.sum()), psu=rr[ps].mean(), pri=rr[pr].mean(),
                        psu_win=(rr[ps] > COST).mean() * 100, pri_win=(rr[pr] > COST).mean() * 100))
    R = pd.DataFrame(rec).dropna(subset=['psu', 'pri']).set_index('date')
    if h == 250:
        yr = (R.psu - R.pri).groupby(R.index.year).mean().round(1).to_dict()
    for era, m in list(era_mask(R.index).items()) + [('last6m', R.index >= R.index.max() - pd.Timedelta(days=180))]:
        s = R[m]
        if len(s) < 3: continue
        dd = s.pri - s.psu
        rows.append(dict(h=h, era=era, months=len(s), n_psu=round(s.n_psu.mean(), 1), n_pri=round(s.n_pr.mean(), 1),
                         psu_net=round(s.psu.mean() - COST, 2), pri_net=round(s.pri.mean() - COST, 2),
                         pri_minus_psu=round(dd.mean(), 2), pct_months_pri_better=round((dd > 0).mean() * 100, 1),
                         psu_win=round(s.psu_win.mean(), 1), pri_win=round(s.pri_win.mean(), 1)))
out = pd.DataFrame(rows); pd.set_option('display.width', 200)
print(out.to_string(index=False)); print('\nby year h=250 (PSU minus private):', yr)
out.to_csv(os.path.join(os.path.dirname(__file__), 'psu_results.csv'), index=False)
