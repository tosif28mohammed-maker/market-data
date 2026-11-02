"""Liquidity check for small positions (user's size ~Rs 50-60k). For each stock (gz csv dir(s)):
median daily turnover (6 months), worst-month median turnover, share of days traded (last 250), lower/upper-circuit-lock days
(high == low and move >= 1.9%), and the user's order as % of a normal day's turnover.
Usage: python study/liquidity.py out.csv dir1 [dir2 ...]"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; rows = []
for D in sys.argv[2:]:
    for f in glob.glob(os.path.join(D, '*.csv.gz')):
        s = os.path.basename(f)[:-7]
        d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close']).sort_values('date')
        if len(d) < 60: continue
        last = d[d.date >= d.date.max() - pd.Timedelta(days=365)].copy(); last['to'] = last.close * last.volume
        r6 = last[last.date >= last.date.max() - pd.Timedelta(days=183)]
        mon = last.groupby(last.date.dt.to_period('M')).to.median()
        ret = last.close.pct_change().abs()
        lock = ((last.high == last.low) & (ret >= 0.019)).mean()
        med = r6.to.median()
        rows.append(dict(symbol=s, turnover_cr=med / 1e7, worst_month_cr=mon.min() / 1e7, traded_days=(last.volume > 0).mean(), lock_days=lock,
                         order_pct=60000 / med * 100 if med > 0 else np.nan, price=d.close.iloc[-1]))
L = pd.DataFrame(rows).drop_duplicates('symbol')
def cls(r):
    if r.traded_days < 0.95 or r.lock_days > 0.03 or r.worst_month_cr < 0.1: return 'D: सावधान'
    if r.turnover_cr >= 5: return 'A: बहुत liquid'
    if r.turnover_cr >= 1: return 'B: ठीक'
    if r.turnover_cr >= 0.25: return 'C: छोटी मात्रा ठीक'
    return 'D: सावधान'
L['liquidity'] = L.apply(cls, axis=1); L.to_csv(OUT, index=False); print(L.liquidity.value_counts())
