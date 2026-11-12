"""'Sasta + achha + trend' list (user 12 Nov 2026: undervalued, sound fundamentals, revenue & profit growing; downtrend names stay on the
list but are IGNORED until an uptrend starts). Own free data only (data/fund/summary.csv from Yahoo + data/daily_all).
Rules: PE 0-25 and below its sector's median PE; ROE >= 15% (ROCE >= 15% for non-financials); debt/equity <= 0.6 (non-financials);
revenue 1y >= 8% and 3y CAGR >= 10%; profit 1y >= 10%; no loss year; quality >= 6/9; liquidity A/B; market cap >= Rs 2,000 cr.
Trend: UPTREND = close above 200 DMA; 'NAYA' = crossed above 200 DMA in the last 15 sessions.
Entry now = uptrend + not stretched (<= 8% above 20 DMA) + no results in 10 days. Writes data/value.md + data/value.csv.
NOTE: a screen, not a back-tested edge (no historical fundamentals). Momentum part is tested (f72/f77); value part is not."""
import os, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = pd.read_csv(os.path.join(R, 'data', 'fund', 'summary.csv')).set_index('symbol')
C = pd.read_csv(os.path.join(R, 'data', 'daily_all', 'close.csv.gz'), index_col=0, parse_dates=True).ffill(limit=5)
liq = pd.read_csv(os.path.join(R, 'study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
pe = F.trailingPE.where(F.trailingPE > 0); spe = pe.groupby(F.sector).transform('median')
fin = F.sector.astype(str).str.contains('Financial', case=False)
ok = (pe <= 25) & (pe < spe) & (F.roe >= 0.15) & ((F.roce >= 0.15) | fin) & ((F.debt_equity <= 0.6) | fin) & (F.rev_g1 >= 0.08) & (F.rev_cagr3 >= 0.10) \
     & (F.np_g1 >= 0.10) & (F.loss_years.fillna(0) == 0) & (F.quality_score >= 6) & (F.marketCap >= 2000e7)
X = F[ok & F.index.isin(C.columns)].copy(); X = X[[liq.get(s, 'D') in ('A', 'B') for s in X.index]]
c = C[X.index]; p = c.iloc[-1]; m200 = c.rolling(200, min_periods=150).mean(); m50 = c.rolling(50).mean(); m20 = c.rolling(20).mean()
X['close'] = p; X['vs200'] = (p / m200.iloc[-1] - 1) * 100; X['vs20'] = (p / m20.iloc[-1] - 1) * 100; X['r6m'] = (p / c.iloc[-127] - 1) * 100
above = c > m200; X['up'] = above.iloc[-1]
X['naya'] = X.up & (~above.iloc[-16:-1]).any()
X['near'] = (~X.up) & (X.vs200 >= -5) & (c.iloc[-1] > m50.iloc[-1])  # below 200 DMA but within 5% and above 50 DMA   # downtrend but close to turning
try:
    bm = pd.read_csv(os.path.join(R, 'data', 'corp', 'board_meetings.csv')); bm['d'] = pd.to_datetime(bm.date, errors='coerce', dayfirst=True)
    soon = bm[(bm.d >= C.index[-1]) & (bm.d <= C.index[-1] + pd.Timedelta(days=10))].groupby('symbol').d.min()
except Exception:
    soon = pd.Series(dtype='datetime64[ns]')
X['results'] = [soon[s].strftime('%d %b') if s in soon.index else '' for s in X.index]
X['entry_ok'] = X.up & (X.vs20 <= 8) & (X.vs20 >= -10) & (X.results == '')
X['secPE'] = spe[X.index]
cols = ['industry', 'close', 'trailingPE', 'secPE', 'roe', 'rev_g1', 'np_g1', 'q_np_yoy', 'quality_score', 'vs200', 'vs20', 'r6m', 'up', 'naya', 'near', 'results', 'entry_ok']
X[cols].round(3).to_csv(os.path.join(R, 'data', 'value.csv'))
def line(s, r):
    return (f"- **{s}** ({str(r.industry)[:28]}) ₹{r.close:,.0f} | PE {r.trailingPE:.0f} (sector {r.secPE:.0f}) | ROE {r.roe * 100:.0f}% | bikri {r.rev_g1 * 100:+.0f}%, munafa {r.np_g1 * 100:+.0f}%"
            f"{'' if pd.isna(r.q_np_yoy) else f', timahi {r.q_np_yoy * 100:+.0f}%'} | quality {r.quality_score:.0f}/9 | 200 DMA {r.vs200:+.0f}%, 20 DMA {r.vs20:+.0f}%"
            + (' | 🆕 naya uptrend' if r.naya else '') + (f' | nateeje {r.results}' if r.results else ''))
L = [f'# Sasta + achha + trend — {C.index[-1]:%d %b %Y}', '',
     f'{len(X)} shares chhaanti mein pass (PE sector se kam, ROE 15%+, bikri/munafa badh raha, karz kam, quality 6+/9). Ye chhaanti hai, back-test kiya hua niyam nahi.', '',
     '## 🟢 Abhi khareed layak (uptrend + khincha hua nahi + nateeje door)']
a = X[X.entry_ok].sort_values('quality_score', ascending=False); L += [line(s, r) for s, r in a.iterrows()] or ['- aaj koi nahi']
b = X[X.up & ~X.entry_ok]; L += ['', '## 🟡 Uptrend mein, par aaj nahi (20 DMA se 8%+ upar khincha, 10%+ neeche tez gir raha, ya nateeje paas)'] + ([line(s, r) for s, r in b.iterrows()] or ['- koi nahi'])
d = X[X.near]; L += ['', '## 👀 Downtrend, par mudne ke kareeb (200 DMA se 5% ke andar, 50 DMA ke upar) — abhi nahi, nazar'] + ([line(s, r) for s, r in d.iterrows()] or ['- koi nahi'])
e = X[~X.up & ~X.near]; L += ['', f'## ⏸ Downtrend — ignore (naam list mein rahenge, uptrend shuru hone par upar aayenge): ' + ', '.join(f'{s} ({r.vs200:+.0f}%)' for s, r in e.sort_values('vs200', ascending=False).iterrows())]
open(os.path.join(R, 'data', 'value.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
