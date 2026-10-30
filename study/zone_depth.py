"""Zone-depth study for the 'buy far below MA, sell at MA' rule (user, 30 Oct 2026).
For every signal (close crosses below the stock's own zone line) measures: further fall after signal (MAE, % and ATR),
deepest distance from MA, days to bottom and to exit (first close at/above MA, max 60 days), how far price runs ABOVE the MA
in the 10 days after touching (overshoot), limit-order fills 0..3% below the signal close within 3 days (and what the missed
trades did), and technical state at the signal (RSI14, Bollinger %B, MACD turning, volume, 200 SMA).
Rules: Nifty-50 stocks = EMA 20, zone = 10% lowest distance in the period; focus stocks = own rule (paper/focus_rules.csv).
Zone line is computed inside each period (ALL, 2003-12, 2013-20, 2021-26) so periods compare like with like.
Usage: python study/zone_depth.py out.pkl"""
import os, sys, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DATA = os.path.join(ROOT, 'data')
F = pd.read_csv(os.path.join(ROOT, 'paper', 'focus_rules.csv')).set_index('symbol')
EX = {l.split(',')[0] for l in open(os.path.join(ROOT, 'symbols_extra.txt')) if ',' in l and not l.startswith('#')}
SYMS = [f[:-4] for f in os.listdir(DATA) if f.endswith('.csv') and f not in ('latest.csv',)]
UNIV = [s for s in SYMS if s not in ('NIFTY', 'INDIAVIX', 'BANKNIFTY') and (s not in EX or s in F.index)] + ['NIFTY']
ERAS = {'ALL': ('1990-01-01', '2030-01-01'), '2003-12': ('2003-01-01', '2012-12-31'), '2013-20': ('2013-01-01', '2020-12-31'), '2021-26': ('2021-01-01', '2030-01-01')}
LIMITS = [0, -0.5, -1, -1.5, -2, -3]
def wma(p, n):
    w = np.arange(1, n + 1, dtype=float); o = np.full(len(p), np.nan)
    if len(p) >= n: o[n - 1:] = np.convolve(p, w[::-1], 'valid') / w.sum()
    return o
def ma_any(T, p, n):
    if T == 'SMA': return pd.Series(p).rolling(n).mean().to_numpy()
    if T == 'EMA': e = pd.Series(p).ewm(span=n, adjust=False).mean().to_numpy(copy=True); e[:n] = np.nan; return e
    if T == 'WMA': return wma(p, n)
    h = wma(2 * np.nan_to_num(wma(p, max(n // 2, 1)), nan=p[0]) - np.nan_to_num(wma(p, n), nan=p[0]), max(int(round(np.sqrt(n))), 1)); h[:n] = np.nan; return h
def load(s):
    d = pd.read_csv(os.path.join(DATA, f'{s}.csv'), parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').sort_values('date').reset_index(drop=True)
    d = d[d.close > 0]; r = d.close.pct_change()
    bad = r.abs() > 0.2
    if bad.any():   # split/glitch: keep only data after the last such jump
        d = d.iloc[int(np.flatnonzero(bad.values)[-1]):].reset_index(drop=True)
    return d
rows = []; events = []
for s in UNIV:
    d = load(s)
    if len(d) < 400: continue
    T, L = (F.loc[s, 'type'], int(F.loc[s, 'L'])) if s in F.index else ('EMA', 20)
    c = d.close.values; hi = d.high.values; lo = d.low.values; v = d.volume.values if 'volume' in d else np.zeros(len(d))
    m = ma_any(T, c, L); dist = c / m - 1
    tr = np.maximum(hi[1:] - lo[1:], np.maximum(abs(hi[1:] - c[:-1]), abs(lo[1:] - c[:-1]))); atr = np.r_[np.nan, pd.Series(tr).rolling(14).mean().to_numpy()]
    cs = pd.Series(c); dl = cs.diff(); up = dl.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean(); dn = (-dl.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean(); rsi = (100 - 100 / (1 + up / dn.replace(0, np.nan))).to_numpy()
    m20 = cs.rolling(20).mean(); sd = cs.rolling(20).std(); pb = ((cs - (m20 - 2 * sd)) / (4 * sd)).to_numpy()
    macd = cs.ewm(span=12, adjust=False).mean() - cs.ewm(span=26, adjust=False).mean(); h = (macd - macd.ewm(span=9, adjust=False).mean()).to_numpy()
    s200 = cs.rolling(200).mean().to_numpy(); vr = (pd.Series(v) / pd.Series(v).rolling(20).mean().shift(1)).to_numpy()
    dates = d.date.values
    for era, (a, b) in ERAS.items():
        z = (d.date >= a) & (d.date <= b); idx = np.flatnonzero(z.values & np.isfinite(dist))
        if len(idx) < 250: continue
        thr = np.nanpercentile(dist[idx], 10); i0, i1 = idx[0], idx[-1]
        t = i0 + 1; ev = []
        while t <= i1:
            if dist[t] <= thr and dist[t - 1] > thr and np.isfinite(atr[t]):
                e = t + 1
                while e <= min(t + 60, len(c) - 1) and c[e] < m[e]: e += 1
                if e > len(c) - 1: break
                e = min(e, t + 60, len(c) - 1)
                seg = slice(t + 1, e + 1)
                mae = lo[seg].min() / c[t] - 1 if e > t else 0.0
                k = t + 1 + int(np.argmin(lo[seg])) if e > t else t
                after = slice(e, min(e + 11, len(c)))
                over = hi[after].max() / m[e] - 1 if np.isfinite(m[e]) else np.nan
                rec = dict(stock=s, era=era, date=str(pd.Timestamp(dates[t]).date()), ret=c[e] / c[t] - 1, win=c[e] > c[t], touched=c[e] >= m[e], mae=mae, mae_atr=(c[t] - lo[seg].min()) / atr[t] if e > t else 0,
                           depth=np.nanmin(dist[t:e + 1]), sig_dist=dist[t], days_low=k - t, days_exit=e - t, over=over, rsi=rsi[t], pb=pb[t], macd_up=h[t] > h[t - 1], vol=vr[t], above200=c[t] > s200[t] if np.isfinite(s200[t]) else np.nan)
                lw = lo[t + 1:t + 4].min() if t + 1 < len(c) else np.nan
                for Lm in LIMITS:
                    px = c[t] * (1 + Lm / 100); rec[f'fill{Lm}'] = bool(lw <= px); rec[f'ret{Lm}'] = c[e] / px - 1 if lw <= px else np.nan
                ev.append(rec); t = e + 1
            else: t += 1
        events += ev
        if not ev: continue
        E = pd.DataFrame(ev)
        r = dict(stock=s, rule=f'{T} {L}', era=era, zone_pct=thr * 100, n=len(E), win=E.win.mean(), avg_ret=E.ret.mean() * 100, worst=E.ret.min() * 100,
                 mae_med=E.mae.median() * 100, mae_p25=E.mae.quantile(.25) * 100, mae_p10=E.mae.quantile(.1) * 100, mae_atr_med=E.mae_atr.median(), mae_atr_p90=E.mae_atr.quantile(.9),
                 depth_med=E.depth.median() * 100, depth_p90=E.depth.quantile(.1) * 100, days_low_med=E.days_low.median(), days_exit_med=E.days_exit.median(), days_exit_p90=E.days_exit.quantile(.9),
                 over_med=E.over.median() * 100, over_p25=E.over.quantile(.25) * 100)
        for Lm in LIMITS:
            r[f'fill{Lm}'] = E[f'fill{Lm}'].mean(); r[f'avg{Lm}'] = np.nanmean(E[f'ret{Lm}']) * 100 if E[f'fill{Lm}'].any() else np.nan
            r[f'missed_win{Lm}'] = E.loc[~E[f'fill{Lm}'], 'win'].mean() if (~E[f'fill{Lm}']).any() else np.nan
        rows.append(r)
    print(s, flush=True)
R = pd.DataFrame(rows); EV = pd.DataFrame(events)
pd.to_pickle(dict(R=R, EV=EV), sys.argv[1]); print(len(R), len(EV))
