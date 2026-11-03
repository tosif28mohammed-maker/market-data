"""Today's zone for the rules that survived the honest check: deep below own 10% distance (learned 2013-20 ex-crisis; hourly: first half) from
1D SMA20, 1D SMA30, 1D SMA50, 1W SMA5, 1M SMA5, plus 4H SMA50 for info. Latest data: daily to 28 Oct + 1-hour candles to 2 Nov."""
import os, glob, numpy as np, pandas as pd
S = '/tmp/claude-0/-home-claude/d80f8346-ebcf-5b0f-b547-7bcd27753fa4/scratchpad'; ROOT = '/home/claude/market-data'; H1 = '/home/claude/intrarepo/intra/h1'
files = {}
for D in ['/home/claude/u500repo/u1000/daily', '/home/claude/u500repo/u2000/daily']:
    for f in sorted(glob.glob(os.path.join(D, '*.csv.gz'))): files.setdefault(os.path.basename(f)[:-7], f)
LQ = pd.read_csv(f'{ROOT}/study/results/liq_all.csv').set_index('symbol')
fo = pd.read_csv(f'{ROOT}/universe/fo_list.csv'); fo.columns = [c.strip() for c in fo.columns]; FO = set(fo.SYMBOL.str.strip())
names = ['NIFTY', 'BANKNIFTY'] + [s for s in files if str(LQ.liquidity.get(s, 'D'))[0] in ('A', 'B')]
CR = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
RULES = [('1D', 20), ('1D', 30), ('1D', 50), ('1W', 5), ('1M', 5), ('4H', 50)]
def load_hourly(s):
    f = os.path.join(H1, f'{s}.csv.gz')
    if not os.path.exists(f): return None
    d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['close']).drop_duplicates('time').set_index('time').sort_index()
    return d[d.index.strftime('%H:%M').isin(['09:15', '10:15', '11:15', '12:15', '13:15', '14:15', '15:15'])][['open', 'high', 'low', 'close']]
def load_daily(s, hh):
    f = f'{ROOT}/data/{s}.csv' if s in ('NIFTY', 'BANKNIFTY') else files[s]
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').set_index('date').sort_index()[['open', 'high', 'low', 'close']]
    d = d[(d.close > 0) & (d.index >= '2003-01-01')]; j = d.close.pct_change().abs(); bad = np.flatnonzero((j > 0.3).values)
    if len(bad): d = d.iloc[bad[-1]:]
    if hh is not None:
        x = hh[hh.index.normalize() > d.index.max()]
        if len(x):
            dx = x.groupby(x.index.normalize()).agg(open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'))
            if abs(dx.close.iloc[0] / d.close.iloc[-1] - 1) < 0.2: d = pd.concat([d, dx])
    return d
rows = []
for s in names:
    try:
        hh = load_hourly(s); dd = load_daily(s, hh)
        sr = {'1D': dd, '1W': dd.resample('W-FRI').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna(),
              '1M': dd.resample('ME').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()}
        if hh is not None and len(hh) > 1500:
            g = np.where(hh.index.strftime('%H:%M') < '13:15', 0, 1); key = hh.index.normalize() + pd.to_timedelta(g * 4, unit='h')
            sr['4H'] = hh.groupby(key).agg(open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'))
        for tf, Ln in RULES:
            d = sr.get(tf)
            if d is None or len(d) < Ln + 60: continue
            ma = d.close.rolling(Ln).mean(); dist = d.close / ma - 1; idx = d.index
            if tf == '4H': A = idx < idx[len(idx) // 2]
            elif tf == '1M': A = (idx >= '2005-01-01') & (idx < '2016-01-01')
            else:
                cr = np.zeros(len(idx), bool)
                for a, b in CR: cr |= (idx >= a) & (idx <= b)
                A = (idx >= '2013-01-01') & (idx < '2021-01-01') & ~cr
            v = dist[A].dropna()
            if len(v) < 25: continue
            thr = float(v.quantile(0.10))
            rows.append(dict(stock=s, tf=tf, L=Ln, last=d.index[-1].date(), close=round(d.close.iloc[-1], 2), ma=round(ma.iloc[-1], 2), dist=round(dist.iloc[-1] * 100, 2),
                             thr=round(thr * 100, 2), zone_price=round(ma.iloc[-1] * (1 + thr), 2), in_zone=dist.iloc[-1] <= thr,
                             fresh=bool(dist.iloc[-1] <= thr and not (dist.iloc[-2] <= thr)), liq=str(LQ.liquidity.get(s, 'A'))[0], fo=s in FO,
                             turn=LQ.turnover_cr.get(s, np.nan), ret52=round((dd.close.iloc[-1] / dd.close.iloc[-250] - 1) * 100, 1) if len(dd) > 250 else np.nan,
                             above200=bool(dd.close.iloc[-1] > dd.close.rolling(200).mean().iloc[-1])))
    except Exception as e: print('ERR', s, e)
Z = pd.DataFrame(rows); Z.to_pickle(f'{S}/zone_now.pkl')
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300)
print(Z[Z.stock.isin(['NIFTY', 'BANKNIFTY'])].to_string(index=False))
iz = Z[Z.in_zone & ~Z.stock.isin(['NIFTY', 'BANKNIFTY'])]
print('in zone counts', iz.groupby('tf').size().to_dict(), 'of', Z.groupby('tf').size().to_dict())
print(iz[iz.tf.isin(['1D', '1W', '1M'])].sort_values('turn', ascending=False).head(60).to_string(index=False))
