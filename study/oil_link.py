"""Oil -> Indian market (user, 3 Nov 2026: 'oil drop hua to market accha bana - ye signal ho sakta hai').
Brent daily close (US session t) vs India next session (first India date > t): gap, day, and next 5/20 days; plus Brent 5-day / 20-day change
vs India forward 20 days. Nifty, BankNifty and oil-sensitive stocks: oil users (BPCL, HPCL, IOC, ASIANPAINT, INDIGO, PIDILITIND) vs producers (ONGC, OIL).
Periods: 2008-12, 2013-20 (ex-COVID), 2021-26, Nov23-now; GFC/COVID windows removed in all. Chance = all days of the same period."""
import os, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def ld(f): d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').set_index('date').sort_index(); return d[d.close > 0]
B = ld(f'{ROOT}/data/global/CMD_BRENT.csv').close
S = {'NIFTY': ld(f'{ROOT}/data/NIFTY.csv'), 'BANKNIFTY': ld(f'{ROOT}/data/BANKNIFTY.csv')}
for s in ['BPCL', 'HINDPETRO', 'IOC', 'ASIANPAINT', 'INDIGO', 'PIDILITIND', 'ONGC', 'OIL']:
    for D in ['/home/claude/u500repo/u1000/daily', '/home/claude/u500repo/u2000/daily']:
        f = f'{D}/{s}.csv.gz'
        if os.path.exists(f): S[s] = ld(f); break
b1 = B.pct_change(); b5 = B.pct_change(5); b20 = B.pct_change(20)
rows = []
for s, d in S.items():
    c = d.close; o = d.open
    gap = o / c.shift(1) - 1; day = c / o - 1; cc = c.pct_change(); f5 = c.shift(-5) / c.shift(1) - 1; f20 = c.shift(-20) / c.shift(1) - 1   # from previous close (before India opens)
    # map each India date to the latest Brent close strictly before it
    bi = pd.DataFrame({'b1': b1, 'b5': b5, 'b20': b20}); bi.index = bi.index + pd.Timedelta(hours=1)
    m = pd.merge_asof(pd.DataFrame(index=d.index).reset_index(), bi.reset_index().rename(columns={'date': 'bd'}), left_on='date', right_on='bd', allow_exact_matches=False).set_index('date')
    m = m[(d.index.to_series() - m.bd).dt.days <= 4]
    X = pd.DataFrame({'gap': gap, 'day': day, 'cc': cc, 'f5': f5, 'f20': f20}).join(m[['b1', 'b5', 'b20']], how='inner')
    idx = X.index; cr = ((idx >= '2008-01-01') & (idx <= '2009-06-30')) | ((idx >= '2020-02-15') & (idx <= '2020-06-30'))
    PER = {'2008-12': (idx >= '2008-01-01') & (idx < '2013-01-01'), '2013-20': (idx >= '2013-01-01') & (idx < '2021-01-01'), '2021-26': idx >= '2021-01-01', 'Nov23-': idx >= '2023-11-01'}
    for per, pm in PER.items():
        Y = X[pm & ~cr]
        if len(Y) < 200: continue
        q = {'b1': Y.b1.quantile([.1, .9]).values, 'b5': Y.b5.quantile([.1, .9]).values, 'b20': Y.b20.quantile([.1, .9]).values}
        base = Y.mean()
        for sig, lo_hi in q.items():
            for side, sel in (('oil बड़ा गिरा (10%)', Y[sig] <= lo_hi[0]), ('oil बड़ा चढ़ा (10%)', Y[sig] >= lo_hi[1])):
                Z = Y[sel]
                rows.append(dict(stock=s, period=per, signal=sig, side=side, n=len(Z), oil_move=round(Z[sig].mean() * 100, 1),
                                 gap=round((Z.gap.mean() - base.gap) * 100, 2), day=round((Z.day.mean() - base.day) * 100, 2), next_1d=round((Z.cc.mean() - base.cc) * 100, 2),
                                 next_5d=round((Z.f5.mean() - base.f5) * 100, 2), next_20d=round((Z.f20.mean() - base.f20) * 100, 2),
                                 win20=round((Z.f20 > 0).mean(), 2), base_win20=round((Y.f20 > 0).mean(), 2)))
R = pd.DataFrame(rows); R.to_csv(f'{ROOT}/study/results/oil_link.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R[R.stock.isin(['NIFTY', 'BANKNIFTY'])].to_string(index=False))
print(R[(~R.stock.isin(['NIFTY', 'BANKNIFTY'])) & (R.signal == 'b5')].to_string(index=False))
