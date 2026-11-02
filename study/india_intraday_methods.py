"""Popular Indian intraday methods tested on 15-minute candles (last ~60 days) of every liquid A/B stock (user, 2 Nov 2026 night):
 OL  'Open = Low'  : first 15-min candle's low == the day's open (±0.05%) and candle green -> buy at 9:30, stop = that low, exit 15:15
 OH  'Open = High' : mirror -> short
 ORB 15-min opening range breakout: first close above the 9:15-9:30 high (before 14:00) -> buy, stop = range low, target 2x range, exit 15:15; mirror short
 G9  Gann square of 9: levels (sqrt(open) +/- 0.125*k)^2; first 15-min close above level 1 -> buy, target level 2, stop below open level; mirror short
Cost 0.1% per round trip (intraday). Results per trade, per stock, per method.  python study/india_intraday_methods.py out.pkl dir"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; files = sorted(glob.glob(os.path.join(sys.argv[2], '*.csv.gz')))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = pd.read_csv(os.path.join(ROOT, 'study/results/liq_all.csv')).set_index('symbol').liquidity.str[0]
COST = 0.001; rows = []
def run_trade(z, i0, side, entry, stop, target):
    for j in range(i0, len(z)):
        hi, lo, t = z.high.iat[j], z.low.iat[j], z.hm.iat[j]
        if side == 1 and lo <= stop: return stop / entry - 1, 'SL'
        if side == -1 and hi >= stop: return entry / stop - 1, 'SL'
        if target is not None:
            if side == 1 and hi >= target: return target / entry - 1, 'T'
            if side == -1 and lo <= target: return entry / target - 1, 'T'
        if t >= '15:15': return side * (z.close.iat[j] / entry - 1), 'time'
    return side * (z.close.iat[-1] / entry - 1), 'time'
for f in files:
    s = os.path.basename(f)[:-7]
    if L.get(s) not in ('A', 'B'): continue
    d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['close'])
    d['day'] = d.time.dt.normalize(); d['hm'] = d.time.dt.strftime('%H:%M'); d = d[(d.hm >= '09:15') & (d.hm <= '15:15')]
    for day, z in d.groupby('day'):
        z = z.sort_values('time').reset_index(drop=True)
        if len(z) < 20 or z.hm.iat[0] != '09:15': continue
        o = z.open.iat[0]; f_hi, f_lo, f_c = z.high.iat[0], z.low.iat[0], z.close.iat[0]
        # OL / OH (entry at 9:30 = open of 2nd candle)
        e = z.open.iat[1]
        if abs(f_lo / o - 1) <= 0.0005 and f_c > o and e > f_lo:
            r, why = run_trade(z, 1, 1, e, f_lo, None); rows.append((s, day, 'OL Open=Low खरीद', r - COST, why))
        if abs(f_hi / o - 1) <= 0.0005 and f_c < o and e < f_hi:
            r, why = run_trade(z, 1, -1, e, f_hi, None); rows.append((s, day, 'OH Open=High बेच (short)', r - COST, why))
        # ORB 15-min
        rng = f_hi - f_lo
        if rng > 0:
            for j in range(1, len(z)):
                if z.hm.iat[j] >= '14:00': break
                if z.close.iat[j] > f_hi:
                    r, why = run_trade(z, j + 1, 1, z.close.iat[j], f_lo, z.close.iat[j] + 2 * rng) if j + 1 < len(z) else (0, 'none'); rows.append((s, day, 'ORB 15-मिनट ऊपर (खरीद)', r - COST, why)); break
                if z.close.iat[j] < f_lo:
                    r, why = run_trade(z, j + 1, -1, z.close.iat[j], f_hi, z.close.iat[j] - 2 * rng) if j + 1 < len(z) else (0, 'none'); rows.append((s, day, 'ORB 15-मिनट नीचे (short)', r - COST, why)); break
        # Gann square of 9
        sq = np.sqrt(o); up1, up2 = (sq + 0.125) ** 2, (sq + 0.25) ** 2; dn1, dn2 = (sq - 0.125) ** 2, (sq - 0.25) ** 2
        for j in range(0, len(z)):
            if z.hm.iat[j] >= '14:00': break
            if z.close.iat[j] > up1:
                if j + 1 < len(z): r, why = run_trade(z, j + 1, 1, z.close.iat[j], dn1, up2); rows.append((s, day, 'Gann sq9 ऊपर (खरीद)', r - COST, why))
                break
            if z.close.iat[j] < dn1:
                if j + 1 < len(z): r, why = run_trade(z, j + 1, -1, z.close.iat[j], up1, dn2); rows.append((s, day, 'Gann sq9 नीचे (short)', r - COST, why))
                break
    print(s, flush=True)
pd.DataFrame(rows, columns=['stock', 'day', 'method', 'ret', 'exit']).to_pickle(OUT); print('done', len(rows))
