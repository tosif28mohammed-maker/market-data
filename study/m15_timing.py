"""15-minute candles (last ~60 days): day table per stock for pooled timing checks.
on = prev close -> open; f15 = first 15 min (open -> 9:30 close); r930 = 9:30 close -> day close; r945 = 9:45 -> close; r1015 = 10:15 -> close;
last30 = 15:00 open -> close; last15 = 15:15 bar; slot_<HH:MM> = each 15-min bar return (vs previous bar close; first from open).
python study/m15_timing.py out.pkl dir"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; files = sorted(glob.glob(os.path.join(sys.argv[2], '*.csv.gz'))); rows = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['open', 'close']); d = d[(d.open > 0) & (d.close > 0)]
    if len(d) < 300: continue
    d['day'] = d.time.dt.normalize(); d['slot'] = d.time.dt.strftime('%H:%M')
    O = d.pivot_table(index='day', columns='slot', values='open', aggfunc='first'); C = d.pivot_table(index='day', columns='slot', values='close', aggfunc='last')
    slots = [x for x in C.columns if '09:15' <= x <= '15:15']; C = C[slots]; O = O.reindex(columns=slots)
    ok = C.notna().sum(1) >= 24; C = C[ok].ffill(axis=1); O = O[ok]
    if len(C) < 30 or '09:15' not in C or '15:15' not in C: continue
    T = pd.DataFrame(index=C.index); close = C['15:15']; op = O['09:15']
    T['on'] = op / close.shift() - 1; T['f15'] = C['09:15'] / op - 1; T['r930'] = close / C['09:15'] - 1
    T['r945'] = close / C['09:30'] - 1; T['r1015'] = close / C['10:00'] - 1; T['day'] = close / op - 1
    T['last30'] = close / C['14:45'] - 1; T['last15'] = close / C['15:00'] - 1; T['sofar1445'] = C['14:45'] / op - 1
    prev = C['09:15'] / op - 1
    T['slot_09:15'] = prev
    for a, b in zip(slots[:-1], slots[1:]): T[f'slot_{b}'] = C[b] / C[a] - 1
    T['next_on'] = T.on.shift(-1)
    T = T[(T.on.abs() < 0.15) & (T.day.abs() < 0.2)]
    T['stock'] = s; rows.append(T.rename_axis('date').reset_index())
pd.concat(rows).to_pickle(OUT); print('days', sum(len(r) for r in rows), 'stocks', len(rows))
