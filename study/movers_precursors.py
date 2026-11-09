"""What came BEFORE the top gainers / losers? (user 9 Nov 2026: 'top gainer hamare haath se kaise nikla, pehle kaise pakdein')
Daily: top 20 gainers / losers (A/B, not D) each day; weekly: top 20 by 5-day return. Features measured at the PREVIOUS close
(no look-ahead): RS 3m top 10%, within 2% of 20d high, within 5% of 52w high, volume 5d >= 1.8x of 50d, RSI2 <= 10,
above 200 DMA, 8%+ below 20 DMA, yesterday +5%, yesterday -5%, 3 green days, small price < 100.
Lift = share of movers having the feature / share of all stocks having it. Hit rate = P(becomes top-20 | feature) vs base.
Halves (first/second year) to check it holds. Data: data/daily_all (~2 years)."""
import os, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd = lambda f: pd.read_csv(os.path.join(R, 'data', 'daily_all', f), index_col=0, parse_dates=True)
C, H, V = rd('close.csv.gz'), rd('high.csv.gz'), rd('volume.csv.gz')
liq = pd.read_csv(os.path.join(R, 'study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
AV = set(open(os.path.join(R, 'paper', 'avoid_liquidity_D.txt')).read().split())
AB = [s for s in C.columns if liq.get(s) in ('A', 'B') and s not in AV]
C, H, V = C[AB].ffill(limit=3), H[AB], V[AB]
r1 = C.pct_change() * 100; d = C.diff()
g = d.clip(lower=0).ewm(alpha=0.5).mean(); l = (-d.clip(upper=0)).ewm(alpha=0.5).mean(); rsi2 = 100 - 100 / (1 + g / l)
FE = {
    'RS 3m top 10%': C.pct_change(63).rank(axis=1, pct=True) >= 0.9,
    '20d high ke 2% paas': C >= H.rolling(20).max() * 0.98,
    '52w high ke 5% paas': C >= H.rolling(250, min_periods=200).max() * 0.95,
    'volume 5d >= 1.8x': V.rolling(5).mean() >= 1.8 * V.rolling(50).mean().shift(5),
    'RSI2 <= 10': rsi2 <= 10,
    '200 DMA ke upar': C > C.rolling(200).mean(),
    '20 DMA se 8%+ neeche': C <= C.rolling(20).mean() * 0.92,
    'kal +5% ya zyada': r1 >= 5,
    'kal -5% ya zyada gira': r1 <= -5,
    '3 din lagatar hara': (r1 > 0).rolling(3).sum() == 3,
    'bhaav 100 se kam': C < 100,
}
out = []
for hz, name in ((1, 'DAILY (agla din)'), (5, 'WEEKLY (agle 5 din)')):
    fr = (C.shift(-hz) / C - 1) * 100
    valid = fr.notna() & C.notna() & (V > 0)
    rk_up = fr.where(valid).rank(axis=1, ascending=False); rk_dn = fr.where(valid).rank(axis=1)
    top = rk_up <= 20; bot = rk_dn <= 20
    dates = fr.index[250:-hz] if hz else fr.index[250:]
    half = dates[len(dates) // 2]
    for fname, F in FE.items():
        F = F.reindex_like(fr).fillna(False) & valid
        for side, M in (('UP', top), ('DOWN', bot)):
            for per, ds in (('sab', dates), ('pehla aadha', dates[dates < half]), ('doosra aadha', dates[dates >= half])):
                f, m = F.loc[ds], M.loc[ds]
                base_f = f.values.sum() / valid.loc[ds].values.sum(); in_m = (f & m).values.sum() / max(m.values.sum(), 1)
                hit = (f & m).values.sum() / max(f.values.sum(), 1); base_hit = m.values.sum() / valid.loc[ds].values.sum()
                out.append(dict(horizon=name, side=side, feature=fname, period=per, movers_with=round(in_m * 100, 1), all_with=round(base_f * 100, 1),
                                lift=round(in_m / base_f, 2) if base_f else np.nan, hit_rate=round(hit * 100, 2), base_rate=round(base_hit * 100, 2)))
T = pd.DataFrame(out); T.to_csv(os.path.join(R, 'study', 'results', 'movers_precursors.csv'), index=False)
for hz in T.horizon.unique():
    for side in ('UP', 'DOWN'):
        x = T[(T.horizon == hz) & (T.side == side)].pivot(index='feature', columns='period', values='lift')
        h = T[(T.horizon == hz) & (T.side == side) & (T.period == 'sab')].set_index('feature')[['movers_with', 'all_with', 'hit_rate', 'base_rate']]
        print(f'\n== {hz} {side} ==\n', h.join(x).sort_values('sab', ascending=False).to_string())
