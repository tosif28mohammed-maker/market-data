"""Multi-asset trend study for ETF investing (user, 3 Nov 2026: gold ETF, Nifty/Sensex ETF, currency, mutual funds - kab kharidein?).
Assets in rupees (what an Indian ETF holder gets): Nifty 50 (index, no dividends -> ~1.2%/yr understated), Gold & Silver (USD price x USDINR),
Nasdaq (index x USDINR), US dollar (USDINR itself), Copper (x USDINR). Cash = 6%/yr (liquid ETF proxy).
Rules tested monthly (month-end close, trade next month):
  HOLD     buy and hold
  SMA10M   hold only when price > its 10-month average (~200 DMA), else cash
  MOM12    hold only when the 12-month return > 0, else cash
  BOTH     both conditions
Plus portfolios: equal-weight Nifty+Gold+Nasdaq (+cash), with and without trend filter; Nifty/Gold switch.
Periods: full, 2008-12, 2013-20, 2021-26, Nov23-now. Reports CAGR, max drawdown, time invested, and the current signal."""
import os, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def ld(f): d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').set_index('date').sort_index().close; return d[d > 0]
inr = ld(f'{ROOT}/data/global/FX_USDINR.csv')
raw = {'Nifty50': ld(f'{ROOT}/data/NIFTY.csv'), 'Gold': ld(f'{ROOT}/data/global/CMD_GOLD.csv'), 'Silver': ld(f'{ROOT}/data/global/CMD_SILVER.csv'),
       'Nasdaq': ld(f'{ROOT}/data/global/US_NASDAQ.csv'), 'Copper': ld(f'{ROOT}/data/global/CMD_COPPER.csv'), 'USD': inr}
M = {}
for k, s in raw.items():
    m = s.resample('ME').last()
    if k in ('Gold', 'Silver', 'Nasdaq', 'Copper'): m = m * inr.resample('ME').last().reindex(m.index).ffill()
    M[k] = m
M = pd.DataFrame(M).dropna(how='all'); M = M[M.index >= '2004-01-01']
R = M.pct_change(fill_method=None); cash = (1.06) ** (1 / 12) - 1
sma = M.rolling(10).mean(); mom = M / M.shift(12) - 1
sig = {'HOLD': M.notna(), 'SMA10M': M > sma, 'MOM12': mom > 0, 'BOTH': (M > sma) & (mom > 0)}
cost = 0.002   # per switch (ETF brokerage+spread+STT approx)
def run(asset, rule):
    s = sig[rule][asset].shift(1).fillna(False).astype(bool); r = R[asset]
    out = np.where(s, r, cash) - cost * s.astype(int).diff().abs().fillna(0)
    return pd.Series(out, index=R.index)[r.notna() | ~s]
def stats(x, a, b):
    x = x[(x.index >= a) & (x.index <= b)].dropna()
    if len(x) < 24: return None
    eq = (1 + x).cumprod(); yrs = len(x) / 12
    return dict(CAGR=round(((eq.iloc[-1]) ** (1 / yrs) - 1) * 100, 1), MaxDD=round((eq / eq.cummax() - 1).min() * 100, 1), rs_1lakh=int(100000 * eq.iloc[-1]))
PER = {'पूरा (2005-26)': ('2005-01-01', '2026-12-31'), '2008-12': ('2008-01-01', '2012-12-31'), '2013-20': ('2013-01-01', '2020-12-31'), '2021-26': ('2021-01-01', '2026-12-31'), 'Nov23-अब': ('2023-11-01', '2026-12-31')}
rows = []
for a in M.columns:
    for rule in sig:
        x = run(a, rule)
        for p, (s0, s1) in PER.items():
            st = stats(x, s0, s1)
            if st: rows.append(dict(asset=a, rule=rule, period=p, **st, invested=round(sig[rule][a].shift(1)[(R.index >= s0) & (R.index <= s1)].mean() * 100)))
# portfolios
port = {'3-asset बराबर (Nifty+Gold+Nasdaq) HOLD': (run('Nifty50', 'HOLD') + run('Gold', 'HOLD') + run('Nasdaq', 'HOLD')) / 3,
        '3-asset बराबर + SMA10M filter': (run('Nifty50', 'SMA10M') + run('Gold', 'SMA10M') + run('Nasdaq', 'SMA10M')) / 3,
        'Nifty+Gold आधा-आधा HOLD': (run('Nifty50', 'HOLD') + run('Gold', 'HOLD')) / 2,
        'Nifty+Gold आधा-आधा + SMA10M': (run('Nifty50', 'SMA10M') + run('Gold', 'SMA10M')) / 2}
for nm, x in port.items():
    for p, (s0, s1) in PER.items():
        st = stats(x, s0, s1)
        if st: rows.append(dict(asset=nm, rule='portfolio', period=p, **st, invested=np.nan))
T = pd.DataFrame(rows); T.to_csv(f'{ROOT}/study/results/asset_trend.csv', index=False)
# current status (daily)
now = []
for k, s in raw.items():
    p = s if k in ('Nifty50', 'USD') else s * inr.reindex(s.index).ffill()
    p = p.dropna()
    now.append(dict(asset=k, last=str(p.index[-1].date()), price_inr=round(p.iloc[-1], 2), vs_200dma=round((p.iloc[-1] / p.rolling(200).mean().iloc[-1] - 1) * 100, 1),
                    vs_50dma=round((p.iloc[-1] / p.rolling(50).mean().iloc[-1] - 1) * 100, 1), ret_1m=round((p.iloc[-1] / p.iloc[-22] - 1) * 100, 1),
                    ret_12m=round((p.iloc[-1] / p.iloc[-252] - 1) * 100, 1), from_52w_high=round((p.iloc[-1] / p.iloc[-252:].max() - 1) * 100, 1),
                    signal_SMA10M=bool(M[k].iloc[-1] > sma[k].iloc[-1]), signal_MOM12=bool(mom[k].iloc[-1] > 0)))
N = pd.DataFrame(now); N.to_csv(f'{ROOT}/study/results/asset_now.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300)
print(T.to_string(index=False)); print(N.to_string(index=False))
