"""Claim test DHAN-315 (video https://youtu.be/LbtF1cD5ckM, 21 Nov 2026).
Rule WRITTEN BEFORE RESULTS. Signal at day-t close (proxy for the 3:15 PM scan):
  D1  daily delivery %  in top 10% of the universe that day
  D2  weekly delivery % (5-day deliv_qty / qty) in top 10% that day   (video: pick names in BOTH daily and weekly lists)
  P   5-day price change > 0                                            (high delivery + falling price = skip)
  E   close > EMA20 and close > EMA50
  S   Supertrend(10,3) green;  S+ = flat (line unchanged 3 days) OR turned green within last 3 days (video's preferred)
Execution: buy-stop at day-t high, valid for day t+1 only (fill = max(open, high_t)).
  Stop A: day-t low (skip if risk > 8%).  Stop B: fixed 3% below entry.
  Target = entry + 2 x risk. Max hold 20 days, then exit at close. Same-day stop+target = stop (conservative).
  One open trade per stock. Cost 0.25% round trip. Universe: u1000+u2000, liquidity D dropped.
Variants: FULL (D1 D2 P E S), FULL+ (S+), NO_DELIV control (P E S only), DELIV_ONLY (D1 D2 P).
Bar (user 19 Nov): target hit >= ~40% (never < 35%) and real avg win vs avg loss after costs.
Run: U500=/home/claude/u500 NSE=/home/claude/nse_hist python3 study/dhan_delivery_swing.py
"""
import os, sys, glob, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ni_common import load

NSE = os.environ.get('NSE', '/home/claude/nse_hist')
P = load()
C, H, L, O = P['c'], P['h'], P['l'], P['o']
# work on adjusted OHLC so splits do not create fake moves
r = P['a'] / C
C = P['a']; H = H.copy(); L = L.copy(); O = O.copy()
syms = C.columns

D = pd.concat([pd.read_csv(f, usecols=['date', 'symbol', 'qty', 'deliv_qty', 'deliv_pct'], parse_dates=['date'])
               for f in sorted(glob.glob(f'{NSE}/deliv/*.csv.gz'))])
D = D[D.symbol.isin(syms)].drop_duplicates(['date', 'symbol'])
dp = D.pivot_table(index='date', columns='symbol', values='deliv_pct').reindex(index=C.index, columns=syms)
q = D.pivot_table(index='date', columns='symbol', values='qty').reindex(index=C.index, columns=syms)
dq = D.pivot_table(index='date', columns='symbol', values='deliv_qty').reindex(index=C.index, columns=syms)
wk = dq.rolling(5, min_periods=4).sum() / q.rolling(5, min_periods=4).sum() * 100
has = dp.notna()
D1 = dp.rank(axis=1, pct=True) >= 0.90
D2 = wk.where(has).rank(axis=1, pct=True) >= 0.90
Pc = C / C.shift(5) - 1 > 0
E = (C > C.ewm(span=20, adjust=False).mean()) & (C > C.ewm(span=50, adjust=False).mean())

# Supertrend(10,3), vectorised over stocks, loop over days
tr = pd.concat([H - L, (H - C.shift()).abs(), (L - C.shift()).abs()]).groupby(level=0).max().reindex(C.index)
atr = tr.ewm(alpha=1 / 10, adjust=False).mean()
hl2 = (H + L) / 2
ub, lb = (hl2 + 3 * atr).values, (hl2 - 3 * atr).values
c = C.values
n, m = c.shape
fu, fl = ub.copy(), lb.copy()
st = np.full((n, m), np.nan); up = np.zeros((n, m), bool)
for i in range(1, n):
    fu[i] = np.where((ub[i] < fu[i - 1]) | (c[i - 1] > fu[i - 1]), ub[i], fu[i - 1])
    fl[i] = np.where((lb[i] > fl[i - 1]) | (c[i - 1] < fl[i - 1]), lb[i], fl[i - 1])
    prev_up = up[i - 1]
    up[i] = np.where(prev_up, ~(c[i] < fl[i]), c[i] > fu[i])
    st[i] = np.where(up[i], fl[i], fu[i])
S = pd.DataFrame(up, index=C.index, columns=syms)
STl = pd.DataFrame(st, index=C.index, columns=syms)
flat = S & S.shift(1) & S.shift(2) & ((STl - STl.shift(2)).abs() / C < 0.001)
fresh = S & ~(S.shift(1) & S.shift(2) & S.shift(3)).fillna(False).astype(bool)
Splus = flat | fresh

ok = has & C.notna()
V = {'FULL': ok & D1 & D2 & Pc & E & S,
     'FULL+': ok & D1 & D2 & Pc & E & Splus,
     'NO_DELIV': ok & Pc & E & S,
     'NO_DELIV+': ok & Pc & E & Splus,
     'DELIV_ONLY': ok & D1 & D2 & Pc}

Hv, Lv, Ov, Cv = H.values, L.values, O.values, C.values
idx = C.index


def sim(sig, stop_mode):
    rows = []
    sv = sig.values
    for j in range(m):
        ii = np.flatnonzero(sv[:, j]); busy = -1
        for i in ii:
            if i <= busy or i + 2 >= n: continue
            ht, lt = Hv[i, j], Lv[i, j]
            if not (Hv[i + 1, j] > ht) or np.isnan(ht): continue
            e = max(Ov[i + 1, j], ht)
            sl = lt if stop_mode == 'A' else e * 0.97
            risk = e - sl
            if risk <= 0 or risk / e > 0.08: continue
            tg = e + 2 * risk
            out, k = None, i + 1
            for k in range(i + 1, min(i + 21, n)):
                lo, hi = Lv[k, j], Hv[k, j]
                if np.isnan(lo): continue
                if k > i + 1 and Ov[k, j] <= sl: out = ('SL', Ov[k, j]); break
                if lo <= sl: out = ('SL', sl); break
                if k > i + 1 and Ov[k, j] >= tg: out = ('TG', Ov[k, j]); break
                if hi >= tg: out = ('TG', tg); break
            if out is None: out = ('TO', Cv[k, j])
            ret = (out[1] / e - 1) * 100 - 0.25
            rows.append((idx[i], syms[j], out[0], ret, risk / e * 100, k - i))
            busy = k
    return pd.DataFrame(rows, columns=['date', 'sym', 'exit', 'ret', 'risk', 'days'])


ERAS = [('2008-12', '2008', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'), ('Nov23-now', '2023-11', '2026')]
out = []
lines = []
for name, sig in V.items():
    for sm in ('A', 'B'):
        T = sim(sig.fillna(False), sm)
        T['variant'], T['stop'] = name, sm
        out.append(T)
        for era, a, b in [('ALL', '2008', '2026')] + ERAS:
            t = T[T.date >= '2023-11-01'] if era == 'Nov23-now' else T[(T.date >= a) & (T.date <= f'{b}-12-31')]
            if len(t) < 30: continue
            w, l_ = t[t.ret > 0], t[t.ret <= 0]
            lines.append(dict(variant=name, stop=sm, era=era, n=len(t), target_hit=round((t.exit == 'TG').mean() * 100, 1),
                              stop_hit=round((t.exit == 'SL').mean() * 100, 1), timeout=round((t.exit == 'TO').mean() * 100, 1),
                              win_pct=round(len(w) / len(t) * 100, 1), avg_win=round(w.ret.mean(), 2), avg_loss=round(l_.ret.mean(), 2),
                              avg_net=round(t.ret.mean(), 2), median_risk=round(t.risk.median(), 2), avg_days=round(t.days.mean(), 1)))
R = pd.DataFrame(lines)
res = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
R.to_csv(f'{res}/dhan_delivery_swing.csv', index=False)
pd.concat(out).to_csv(f'{res}/dhan_delivery_swing_trades.csv.gz', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 200)
print(R.to_string(index=False))
