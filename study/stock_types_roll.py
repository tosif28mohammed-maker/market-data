"""Rolling version: for every stock and calendar year Y, behaviour over the 2 previous years (Y-2, Y-1) -> group;
outcome in year Y: return, max drawdown, volatility, range-ness; plus a range 'buy low / sell high' backtest inside year Y
for every stock (buy when close in bottom 15% of its 120-day range, sell at top 80% or after 60 days, stop -10%, cost 0.25%).
python study/stock_types_roll.py out.pkl dir1 [dir2]  (env CHUNK=k/N)"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
if os.environ.get('CHUNK'): k_, n_ = map(int, os.environ['CHUNK'].split('/')); files = files[k_::n_]
CRISIS = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
def incrisis(t): return any(pd.Timestamp(a) <= t <= pd.Timestamp(b) for a, b in CRISIS)
def stats(c):
    r = np.log(c).diff().dropna()
    if len(r) < 300: return None
    yrs = len(r) / 248; cagr = np.exp(r.sum() / yrs) - 1; vol = r.std() * np.sqrt(248)
    lp = r.cumsum(); mdd = np.exp((lp - lp.cummax()).min()) - 1; t = np.arange(len(lp)); cc = np.corrcoef(t, lp.values)[0, 1]
    r2 = cc * abs(cc); vr = np.log(c).diff(20).dropna().var() / (20 * r.var())
    w = c.resample('W-FRI').last().dropna(); y = (w / w.shift(26) - 1).dropna(); pos26 = (y > 0).mean()
    return dict(cagr=cagr, vol=vol, mdd=mdd, r2=r2, vr=vr, pos26=pos26)
rows = []; trades = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['date'], usecols=['date', 'close']).dropna().drop_duplicates('date').set_index('date').close.sort_index()
    d = d[d > 0]; jr = d.pct_change().abs(); bad = np.flatnonzero((jr > 0.35).values)
    if len(bad): d = d.iloc[bad[-1]:]
    if len(d) < 800: continue
    hi = d.rolling(120).max(); lo = d.rolling(120).min(); pos = (d - lo) / (hi - lo)
    # range backtest over the whole history (trades tagged by year)
    i = 0; idx = d.index; vals = d.values; pv = pos.values; n = len(d)
    while i < n - 1:
        if not np.isnan(pv[i]) and pv[i] <= 0.15 and (hi.values[i] / lo.values[i] - 1) >= 0.12:
            e = vals[i]; j = i + 1; why = 'time'
            while j < n and j - i <= 60:
                if vals[j] <= e * 0.9: why = 'stop'; break
                if not np.isnan(pv[j]) and pv[j] >= 0.8: why = 'top'; break
                j += 1
            j = min(j, n - 1)
            trades.append((s, idx[i], idx[j], vals[j] / e - 1 - 0.0025, why, incrisis(idx[i]) or incrisis(idx[j])))
            i = j + 1
        else: i += 1
    for Y in range(2007, 2027):
        past = d[(d.index >= f'{Y-2}-01-01') & (d.index <= f'{Y-1}-12-31')]; nxt = d[(d.index >= f'{Y}-01-01') & (d.index <= f'{Y}-12-31')]
        if len(past) < 400 or len(nxt) < 100 or past.index[0] > pd.Timestamp(f'{Y-2}-02-15'): continue
        a = stats(past)
        if not a: continue
        r = np.log(nxt).diff().dropna(); lp = r.cumsum()
        rows.append(dict(stock=s, year=Y, **{f'p_{k}': v for k, v in a.items()},
                         y_ret=nxt.iloc[-1] / past.iloc[-1] - 1, y_mdd=np.exp((lp - lp.cummax()).min()) - 1, y_vol=r.std() * np.sqrt(248),
                         y_hilo=nxt.max() / nxt.min() - 1))
    print(s, flush=True)
pd.to_pickle((pd.DataFrame(rows), pd.DataFrame(trades, columns=['stock', 'entry', 'exit', 'ret', 'why', 'crisis'])), OUT); print('done')
