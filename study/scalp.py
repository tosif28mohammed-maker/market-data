"""Scalping test (user 9 Nov 2026: 'kuch log 5 sec - 1 min mein call/put leke 2000-5000 nikal lete hain; volatile bazaar mein').
Data: Nifty / BankNifty 5-min candles (intraday_hist, ~3 months) — tick/second data not available to us, so 5-min is the finest
tested here (robot adds 1-min for the last 30 days). Signal on a finished candle, entry next candle open, exit at target / stop /
after N candles. Cost as ATM-option equivalent: delta 0.5, Rs 60 brokerage+taxes + 1 pt slippage each side on the option
= ~6 Nifty points / ~14 BankNifty points per round trip. Compared with RANDOM entries (same exits) = luck baseline.
Split by day volatility (user idea: works when bazaar volatile)."""
import sys, numpy as np, pandas as pd
src = sys.argv[1] if len(sys.argv) > 1 else '/tmp'
res = []
for sym, cost in (('NIFTY', 6.0), ('BANKNIFTY', 14.0)):
    d = pd.read_csv(f'{src}/{sym}.csv.gz', parse_dates=['time']); d['day'] = d.time.dt.date
    d['rng'] = d.high - d.low; d['avg12'] = d.groupby('day').rng.transform(lambda x: x.rolling(12, min_periods=4).mean().shift(1))
    d['pos'] = (d.close - d.low) / d.rng.replace(0, np.nan)
    d['vwap'] = d.groupby('day').close.transform(lambda x: x.expanding().mean())
    dayr = d.groupby('day').apply(lambda x: (x.high.max() - x.low.min()) / x.open.iloc[0] * 100)
    vq = pd.qcut(dayr, 3, labels=['shaant din', 'beech', 'volatile din'])
    unit = d.close.median() * 0.0006  # ~0.06% move = 15 Nifty pts
    rng_ = np.random.default_rng(1)
    def sim(i, side, tgt, stp, hold):
        e = d.open.iloc[i]
        for j in range(i, min(i + hold, len(d))):
            if d.day.iloc[j] != d.day.iloc[i]: return d.close.iloc[j - 1] - e if side == 1 else e - d.close.iloc[j - 1]
            h, l = d.high.iloc[j], d.low.iloc[j]
            if side == 1:
                if l <= e - stp: return -stp
                if h >= e + tgt: return tgt
            else:
                if h >= e + stp: return -stp
                if l <= e - tgt: return tgt
        j = min(i + hold, len(d)) - 1
        return (d.close.iloc[j] - e) * side
    sigs = {}
    burst = (d.rng >= 2 * d.avg12) & d.avg12.notna()
    sigs['MOMENTUM burst (badi candle ki disha)'] = [(i + 1, 1 if d.pos.iloc[i] >= 0.8 else -1) for i in np.where(burst & ((d.pos >= 0.8) | (d.pos <= 0.2)))[0]]
    sigs['FADE burst (badi candle ke ulta)'] = [(i, -s) for i, s in sigs['MOMENTUM burst (badi candle ki disha)']]
    t = d.time.dt.strftime('%H:%M')
    orh = d[t <= '09:25'].groupby('day').high.max(); orl = d[t <= '09:25'].groupby('day').low.min()
    o = []
    for day, g in d[(t > '09:25') & (t < '14:30')].groupby('day'):
        for i in g.index:
            if d.close[i] > orh[day]: o.append((i + 1, 1)); break
            if d.close[i] < orl[day]: o.append((i + 1, -1)); break
    sigs['ORB 15 min breakout'] = o
    trendup = d.close > d.vwap
    pb = [(i + 1, 1 if trendup[i] else -1) for i in np.where((abs(d.close - d.vwap) <= 0.25 * d.avg12) & (abs(d.close.shift(6) - d.vwap.shift(6)) >= 2 * d.avg12))[0]]
    sigs['VWAP pullback (trend ki disha)'] = pb
    allidx = [i for i in range(len(d) - 1) if '09:30' <= t.iloc[i] <= '15:00']
    sigs['RANDOM (kismat)'] = [(int(i), int(s)) for i, s in zip(rng_.choice(allidx, 600, replace=False), rng_.choice([-1, 1], 600))]
    for name, lst in sigs.items():
        lst = [(i, s) for i, s in lst if i < len(d) and '09:20' <= t.iloc[i] <= '15:10']
        for tgt_m, stp_m, hold in ((1, 1, 2), (1.5, 1, 3), (2, 1, 6)):
            tg, sp = tgt_m * unit, stp_m * unit
            for i, s in lst:
                g = sim(i, s, tg, sp, hold)
                res.append(dict(sym=sym, strat=name, setup=f'target {tg:.0f}/stop {sp:.0f} pts, max {hold * 5} min', gross=g, net=g - cost, vol=vq.get(d.day.iloc[i]), day=d.day.iloc[i]))
R = pd.DataFrame(res)
f = lambda x: pd.Series(dict(trades=len(x), per_day=round(len(x) / x.day.nunique(), 1), win_pct=round((x.net > 0).mean() * 100), gross_pts=round(x.gross.mean(), 1), net_pts=round(x.net.mean(), 1)))
pd.set_option('display.width', 250)
for sym in ('NIFTY', 'BANKNIFTY'):
    x = R[R.sym == sym]
    print(f'\n===== {sym} ({x.day.nunique()} din) — net = ATM option kharcha ghata kar (index points; Nifty 1 pt ~ Rs 32/lot option) =====')
    print(x.groupby(['strat', 'setup']).apply(f).to_string())
    print('\nVolatility ke hisaab se (sab setups):'); print(x.groupby(['strat', 'vol'], observed=True).apply(f)[['trades', 'win_pct', 'gross_pts', 'net_pts']].to_string())
R.to_csv('/home/claude/market-data/study/results/scalp_trades.csv.gz', index=False)
