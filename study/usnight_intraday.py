"""After a big US night (S&P 500 top/bottom 10% of 2013-20 days): what happens inside the Indian day, hour by hour (1-hour candles,
Nov 2023-now) and 5-min by 5-min (last 60 days). For NIFTY/BANKNIFTY: fade trade (short after a big US up night, long after a big US
down night) from different entry times to 15:15/close; time of the day's high/low; max favourable/adverse move.
For every liquid stock (long only): buy at different times -> sell at close, on big-down and big-up US nights vs normal days.
python study/usnight_intraday.py out.pkl"""
import sys, os, glob, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); I = '/home/claude/intrarepo/intra'
OUT = sys.argv[1]
us = pd.read_csv(os.path.join(ROOT, 'data/global/US_SP500.csv'), parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').set_index('date').sort_index().close
mv = us.pct_change(); base = mv[(mv.index >= '2013-01-01') & (mv.index <= '2020-12-31') & ~((mv.index >= '2020-02-15') & (mv.index <= '2020-06-30'))].dropna()
LO, HI = base.quantile(0.1), base.quantile(0.9)
def signal(day):
    p = mv[mv.index < day]
    if not len(p) or (day - p.index[-1]).days > 4: return 0, np.nan
    m = p.iloc[-1]; return (1 if m >= HI else (-1 if m <= LO else 0)), m
def day_table(f, slots):
    d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['close']); d['day'] = d.time.dt.normalize(); d['hm'] = d.time.dt.strftime('%H:%M')
    d = d[(d.hm >= '09:15') & (d.hm <= '15:25')]
    return d
out = {'index': [], 'stock': []}
# ---- index: 5-min (60 days) and 1-hour (3 years)
for res, folder, slots in (('5m', 'm5', ['09:15', '09:20', '09:25', '09:30', '09:45', '10:00', '10:15', '10:30', '11:00', '11:30', '12:00', '13:00', '14:00', '15:00']),
                           ('1h', 'h1', ['09:15', '10:15', '11:15', '12:15', '13:15', '14:15'])):
    for idx in ('NIFTY', 'BANKNIFTY'):
        d = day_table(f'{I}/{folder}/{idx}.csv.gz', slots); prev_close = None
        for day, z in d.groupby('day'):
            z = z.sort_values('time').reset_index(drop=True)
            if len(z) < (60 if res == '5m' else 6) or z.hm.iloc[0] != '09:15':
                prev_close = z.close.iloc[-1] if len(z) else prev_close; continue
            sg, m = signal(day); o = z.open.iloc[0]; c = z.close.iloc[-1]
            rec = dict(res=res, idx=idx, day=day, sig=sg, us=m, gap=(o / prev_close - 1) if prev_close else np.nan, oc=c / o - 1)
            hi_i = z.high.idxmax(); lo_i = z.low.idxmin(); rec['high_time'] = z.hm[hi_i]; rec['low_time'] = z.hm[lo_i]
            rec['high_from_open'] = z.high.max() / o - 1; rec['low_from_open'] = z.low.min() / o - 1
            for t in slots:   # entry at that bar's OPEN (09:15 = the day's open)
                q = z[z.hm == t]
                if not len(q): continue
                e = q.open.iloc[0]; after = z[z.time >= q.time.iloc[0]]
                rec[f'ret_{t}'] = c / e - 1; rec[f'mfe_short_{t}'] = 1 - after.low.min() / e; rec[f'mae_short_{t}'] = after.high.max() / e - 1
                rec[f'mfe_long_{t}'] = after.high.max() / e - 1; rec[f'mae_long_{t}'] = 1 - after.low.min() / e
            for t in slots[1:]:   # exit early at that bar's open, from the 9:15 open
                q = z[z.hm == t]
                if len(q): rec[f'open_to_{t}'] = q.open.iloc[0] / o - 1
            out['index'].append(rec); prev_close = c
# ---- stocks (1-hour, long only)
L = pd.read_csv(os.path.join(ROOT, 'study/results/liq_all.csv')).set_index('symbol'); ok = set(L.index[L.liquidity.str[0].isin(['A', 'B'])])
slots = ['09:15', '10:15', '11:15', '12:15', '13:15', '14:15']
for f in sorted(glob.glob(f'{I}/h1/*.csv.gz')):
    s = os.path.basename(f)[:-7]
    if s not in ok: continue
    d = day_table(f, slots); prev_close = None
    for day, z in d.groupby('day'):
        z = z.sort_values('time').reset_index(drop=True)
        if len(z) < 6 or z.hm.iloc[0] != '09:15': prev_close = z.close.iloc[-1] if len(z) else prev_close; continue
        sg, m = signal(day); o = z.open.iloc[0]; c = z.close.iloc[-1]
        rec = dict(stock=s, day=day, sig=sg, gap=(o / prev_close - 1) if prev_close else np.nan, low_slot=z.hm[z.low.idxmin()], high_slot=z.hm[z.high.idxmax()])
        for t in slots:
            q = z[z.hm == t]
            if len(q): rec[f'ret_{t}'] = c / q.open.iloc[0] - 1
        out['stock'].append(rec); prev_close = c
    print(s, flush=True)
pd.to_pickle({k: pd.DataFrame(v) for k, v in out.items()} | {'thr': (LO, HI)}, OUT); print('done')
