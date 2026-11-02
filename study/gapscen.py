"""Gap-up / gap-down day scenarios per stock (daily OHLC 2003-2026) (user, 2 Nov 2026).
For every day with |gap| >= 0.5%: gap size bucket, and what happened that day and next:
 green = close > open; held = close stays beyond previous close (up: close > prev close; down: close < prev close);
 filled = price touched previous close during the day; extended = moved another 1%+ beyond the open in the gap's direction;
 oc = open->close %, nxt = next day close-to-close %, o3 = open -> close 2 days later.
Also one random control day per gap day (same stock, same period) with the same outcome fields measured as if the gap were the same size.
python study/gapscen.py out.pkl dir1 [dir2 ...]"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
if os.environ.get('CHUNK'): k, n = map(int, os.environ['CHUNK'].split('/')); files = files[k::n]
rows = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['open', 'high', 'low', 'close']).drop_duplicates('date').sort_values('date').reset_index(drop=True)
    d = d[(d.close > 0) & (d.open > 0) & (d.date >= '2003-01-01')].reset_index(drop=True)
    if len(d) < 500: continue
    pc = d.close.shift(); gap = d.open / pc - 1; cc = d.close / pc - 1
    bad = (d.open == pc) | (d.open > d.high * 1.001) | (d.open < d.low * 0.999) | (cc.abs() > 0.2) | (gap.abs() > 0.15) | (d.high == d.low)
    sgn = np.sign(gap)
    oc = d.close / d.open - 1
    held = np.where(sgn > 0, d.close > pc, d.close < pc)
    filled = np.where(sgn > 0, d.low <= pc, d.high >= pc)
    ext = np.where(sgn > 0, d.high >= d.open * 1.01, d.low <= d.open * 0.99)
    nxt = cc.shift(-1); o3 = d.close.shift(-2) / d.open - 1
    T = pd.DataFrame({'stock': s, 'date': d.date, 'gap': gap, 'green': (d.close > d.open).values, 'held': held, 'filled': filled, 'ext': ext,
                      'oc': oc, 'nxt': nxt, 'o3': o3, 'bad': bad.values})
    T = T[~T.bad & T.gap.notna()].drop(columns='bad')
    rows.append(T[T.gap.abs() >= 0.005])
    # control: all ordinary days (for base rates)
    base = T[T.gap.abs() < 0.005]
    rows.append(base.assign(gap=0.0).sample(min(len(base), 400), random_state=1))
    print(s, flush=True)
pd.concat(rows).to_pickle(OUT); print('done')
