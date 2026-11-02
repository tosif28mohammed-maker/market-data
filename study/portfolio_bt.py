"""Portfolio backtest: Rs 1 lakh, realistic (user, 2 Nov 2026 night: 'think like you are making the money yourself').
Universe: liquidity A/B stocks (today's list -> survivorship bias, results flattered). Daily data 2005-2026. Costs 0.25% per round trip
(delivery: STT 0.1%+0.1%, stamp, exchange, DP) + 0.1% slippage. Signals at the close, trade at that close (~3:25 PM, per timing study).
Strategies:
 DIP   : stock's 52-week trend >= +30%, close below its own 10th-percentile distance from EMA20 (learned on the trailing 3 years), fresh;
         buy at close; sell at first close >= EMA20 (or +12% stop below, or 20 days). Up to 10 positions, 10% each.
 MOM   : month-end: top 10 by 12-1 month return among stocks above their 200 DMA; hold 1 month; only when Nifty > 200 DMA (else cash).
 BLEND : 50% DIP + 50% MOM.
Benchmarks: Nifty buy & hold.  Reports CAGR, max drawdown, by period (2005-12, 2013-20, 2021-26) and the 1-lakh path.
python study/portfolio_bt.py out.pkl dir1 [dir2]"""
import sys, os, glob, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
L = pd.read_csv(os.path.join(ROOT, 'study/results/liq_all.csv')).set_index('symbol').liquidity.str[0]
C = {}
for f in files:
    s = os.path.basename(f)[:-7]
    if L.get(s) not in ('A', 'B') or s in C: continue
    d = pd.read_csv(f, parse_dates=['date'], usecols=['date', 'close']).dropna().drop_duplicates('date').set_index('date').close.sort_index()
    d = d[d > 0]; j = d.pct_change().abs(); bad = np.flatnonzero((j > 0.3).values)
    if len(bad): d = d.iloc[bad[-1]:]
    if len(d) > 300: C[s] = d
P = pd.DataFrame(C).sort_index(); P = P[P.index >= '2004-01-01']
nifty = pd.read_csv(os.path.join(ROOT, 'data/NIFTY.csv'), parse_dates=['date']).drop_duplicates('date').set_index('date').close.sort_index().reindex(P.index).ffill()
R = P.pct_change(fill_method=None).clip(-0.3, 0.3)
E20 = P.ewm(span=20, adjust=False).mean(); dist = P / E20 - 1
thr = dist.rolling(750, min_periods=250).quantile(0.10).shift(1)
tr52 = P / P.shift(250) - 1; ma200 = P.rolling(200).mean()
COST = 0.0035
def run_dip(start, slots=10):
    eq = 1.0; cash = 1.0; pos = {}; curve = []; trades = []
    days = P.index[P.index >= start]
    for t in days:
        px = P.loc[t]
        # mark & exits
        for s in list(pos):
            p = px.get(s)
            if pd.isna(p): continue
            q = pos[s]; q['days'] += 1
            if p >= E20.at[t, s] or p <= q['entry'] * 0.88 or q['days'] >= 20:
                cash += q['units'] * p * (1 - COST / 2); trades.append((s, q['t0'], t, p / q['entry'] - 1 - COST)); del pos[s]
        val = cash + sum(q['units'] * px.get(s, q['entry']) for s, q in pos.items() if not pd.isna(px.get(s)))
        # entries
        if len(pos) < slots:
            sig = (dist.loc[t] <= thr.loc[t]) & (dist.shift(1).loc[t] > thr.loc[t]) & (tr52.loc[t] >= 0.30)
            cands = sig[sig].index.difference(list(pos))
            if len(cands):
                cands = (dist.loc[t, cands] - thr.loc[t, cands]).sort_values().index
                for s in cands[:slots - len(pos)]:
                    amt = min(val / slots, cash)
                    if amt < val / slots * 0.5: break
                    p = px[s]; pos[s] = dict(units=amt * (1 - COST / 2) / p, entry=p, days=0, t0=t); cash -= amt
        val = cash + sum(q['units'] * px.get(s, q['entry']) for s, q in pos.items() if not pd.isna(px.get(s)))
        curve.append((t, val))
    return pd.Series(dict(curve)), pd.DataFrame(trades, columns=['stock', 'entry', 'exit', 'ret'])
def run_mom(start, n=10):
    me = P.index.to_series().groupby(P.index.to_period('M')).last()
    me = me[me >= start]; curve = []; val = 1.0; hold = []
    nma = nifty.rolling(200).mean()
    idx = P.index[P.index >= start]; mpos = 0
    rebal = set(me.values)
    for i, t in enumerate(idx):
        if i > 0 and hold:
            r = R.loc[t, hold].fillna(0).mean(); val *= 1 + r
        if t in rebal:
            if nifty[t] > nma[t]:
                mom = P.loc[t] / P.shift(250).loc[t] - P.loc[t] / P.shift(21).loc[t] * 0 - 1
                mom = (P.shift(21).loc[t] / P.shift(250).loc[t] - 1)
                ok = (P.loc[t] > ma200.loc[t]) & mom.notna()
                new = mom[ok].sort_values(ascending=False).index[:n].tolist()
            else: new = []
            turnover = len(set(new) ^ set(hold)) / max(2 * n, 1)
            val *= 1 - COST * turnover * 2 / 2 if new or hold else 1
            hold = new
        curve.append((t, val))
    return pd.Series(dict(curve))
res = {}
start = pd.Timestamp('2005-06-30')
dipc, dipt = run_dip(start); momc = run_mom(start)
bl = 0.5 * dipc / dipc.iloc[0] + 0.5 * momc / momc.iloc[0]
nf = nifty[nifty.index >= start]; nf = nf / nf.iloc[0]
curves = pd.DataFrame({'DIP (मज़बूत trend में गिरावट पर खरीद)': dipc / dipc.iloc[0], 'MOM (महीने के top-10 momentum, Nifty 200 DMA filter)': momc / momc.iloc[0], 'BLEND (आधा-आधा)': bl, 'Nifty खरीदकर रखो': nf})
def stats(s):
    yrs = (s.index[-1] - s.index[0]).days / 365.25; cagr = (s.iloc[-1] / s.iloc[0]) ** (1 / yrs) - 1; dd = (s / s.cummax() - 1).min()
    return pd.Series({'सालाना बढ़त (CAGR) %': cagr * 100, 'सबसे बड़ी गिरावट %': dd * 100, '₹1 लाख बना (₹)': 100000 * s.iloc[-1] / s.iloc[0]})
tab = []
for nm, (a, b) in {'पूरा 2005-2026': ('2005-06-30', '2026-12-31'), '2005-12': ('2005-06-30', '2012-12-31'), '2013-20': ('2013-01-01', '2020-12-31'), '2021-26': ('2021-01-01', '2026-12-31'), 'Nov23-अब': ('2023-11-01', '2026-12-31')}.items():
    for col in curves:
        s = curves[col][(curves.index >= a) & (curves.index <= b)].dropna()
        if len(s) > 50: tab.append(dict(दौर=nm, रणनीति=col, **stats(s)))
T = pd.DataFrame(tab)
pd.to_pickle(dict(curves=curves, table=T, dip_trades=dipt), OUT)
pd.set_option('display.width', 250); print(T.round(1).to_string()); print('dip trades', len(dipt), 'win', (dipt.ret > 0).mean(), 'avg', dipt.ret.mean())
