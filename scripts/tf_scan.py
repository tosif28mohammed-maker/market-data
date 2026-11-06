"""TIMEFRAME SCAN (user 6 Nov 2026: 'robot me 4H, 3H, 2H, 1H bhi dalo, short term position ke liye').
Tested rule (f56/f57): price far below its OWN usual distance from the MA (10% lowest distance) -> buy, exit at the MA,
hold up to ~20 trading days. Strongest: 4H SMA20 (+2.6%/month vs placebo -0.7), 4H EMA10, 1H EMA50/SMA50.
Crossing above an MA = fail (not used). 2H/3H: same method, NOT yet tested -> marked 'जाँच बाकी'.
Data: Yahoo 60m, 1 year, liquidity A/B only (never D). Bars per day 7 (9:15..15:15); 2H/3H/4H built per session.
Output: data/tf_scan.csv (every stock x TF), data/tf_zone.csv (in zone now or within 2% of zone = limit-order list).
"""
import os, time, numpy as np, pandas as pd, yfinance as yf
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
liq = pd.read_csv(os.path.join(R, 'study', 'results', 'liq_all.csv'))
av = os.path.join(R, 'paper', 'avoid_liquidity_D.txt')
AV = {l.strip() for l in open(av) if l.strip() and not l.startswith('#')} if os.path.exists(av) else set()
L = liq[liq.liquidity.astype(str).str[0].isin(['A', 'B']) & ~liq.symbol.isin(AV)].set_index('symbol').liquidity.astype(str).str[0]
syms = list(L.index)
RULES = [('1H', 'EMA', 50, 'पक्का'), ('1H', 'SMA', 50, 'पक्का'), ('2H', 'SMA', 20, 'जाँच बाकी'), ('3H', 'SMA', 20, 'जाँच बाकी'),
         ('4H', 'SMA', 20, 'सबसे पक्का'), ('4H', 'EMA', 10, 'पक्का')]


def get(batch):
    for a in range(3):
        try:
            return yf.download([f'{s}.NS' for s in batch], period='1y', interval='60m', group_by='ticker',
                               auto_adjust=False, progress=False, threads=True)
        except Exception as e:
            print('retry', e); time.sleep(5)
    return None


def tf(df, n):
    if n == 1: return df
    d = df.copy(); d['day'] = d.index.date
    d['k'] = d.groupby('day').cumcount() // n
    g = d.groupby(['day', 'k'])
    out = pd.DataFrame({'Open': g.Open.first(), 'High': g.High.max(), 'Low': g.Low.min(), 'Close': g.Close.last(),
                        't': g.apply(lambda x: x.index[-1])}).set_index('t')
    return out


C = pd.read_csv(os.path.join(R, 'data', 'daily_all', 'close.csv.gz'), index_col=0, parse_dates=True)
rows = []
for i in range(0, len(syms), 80):
    part = syms[i:i + 80]; X = get(part)
    if X is None: continue
    for s in part:
        try:
            d = X[f'{s}.NS'][['Open', 'High', 'Low', 'Close']].dropna()
        except Exception:
            continue
        if len(d) < 400: continue
        d.index = d.index.tz_convert('Asia/Kolkata') if d.index.tz is not None else d.index
        for name, kind, n, status in RULES:
            b = tf(d, int(name[0]))
            c = b.Close
            ma = c.rolling(n).mean() if kind == 'SMA' else c.ewm(span=n, adjust=False).mean()
            dist = (c / ma - 1) * 100
            hist = dist.iloc[:-20].dropna()
            if len(hist) < 100: continue
            thr = hist.quantile(0.10)
            last, prev = dist.iloc[-1], dist.iloc[-2]
            zone = ma.iloc[-1] * (1 + thr / 100)
            rows.append(dict(symbol=s, liq=L[s], tf=name, ma=f'{kind}{n}', status=status, close=round(c.iloc[-1], 2),
                             ma_val=round(ma.iloc[-1], 2), dist=round(last, 2), thr=round(thr, 2), zone_price=round(zone, 2),
                             gap_to_zone=round((zone / c.iloc[-1] - 1) * 100, 2), in_zone=last <= thr, fresh=(last <= thr) and (prev > thr),
                             bar=str(c.index[-1])))
    print('done', i + len(part), len(rows))
T = pd.DataFrame(rows)
if T.empty: raise SystemExit('no data')
c = C.reindex(columns=T.symbol.unique())
up200 = (c.iloc[-1] > c.rolling(200, min_periods=180).mean().iloc[-1])
r52 = (c.iloc[-1] / c.iloc[-250] - 1) * 100
T['above200'] = T.symbol.map(up200); T['ret52'] = T.symbol.map(r52).round(0)
T.to_csv(os.path.join(R, 'data', 'tf_scan.csv'), index=False)
Z = T[(T.in_zone | (T.gap_to_zone >= -2)) & (T.above200 == True)].copy()
Z['n_tf'] = Z.groupby('symbol').tf.transform('nunique')
Z['n_tf_inzone'] = Z.symbol.map(T[T.in_zone].groupby('symbol').tf.nunique()).fillna(0).astype(int)
Z = Z.sort_values(['n_tf_inzone', 'ret52'], ascending=False)
Z.to_csv(os.path.join(R, 'data', 'tf_zone.csv'), index=False)
print('in zone (200 DMA up):', Z[Z.in_zone].symbol.nunique(), 'near zone:', Z[~Z.in_zone].symbol.nunique())
