"""Multi-lens 'expert' screener (user 5 Nov 2026: Buffett, Jhunjhunwala, Lynch... ke tareeke se shares chuno).
Inputs: data/fund/summary.csv (Yahoo fundamentals, latest), data/daily_all (prices), liquidity list. Lenses (rule-of-thumb versions of each investor's published method):
 BUFFETT   'wonderful company at a fair price': ROE>=15%, ROCE>=15%, debt/equity<0.5, 3y operating cash flow >= 80% of profit, no loss year, P/E<=40
 LYNCH     GARP: profit growth 15-50%, PEG (P/E / growth%) <= 1.2, debt/equity<0.6
 GREENBLATT magic formula: top 15% by (rank ROCE + rank earnings yield 1/PE), non-financial, P/E>0
 QGLP      Raamdeo Agrawal: ROE>=15%, profit growth>=15%, revenue 3y CAGR>=10%, PEG<=1.5
 COFFEECAN Mukherjea (lite, 4y data only): revenue 3y CAGR>=10% and ROCE>=15%, market cap >= Rs 1,000 cr
 CANSLIM   O'Neil: latest quarter profit +25% YoY, annual profit growth>=20%, within 10% of 52w high, 3-month RS in top 20%
 TREND     Minervini template: price>150 & 200 DMA, 150>200, 200 DMA rising (1 month), >=30% above 52w low, within 25% of 52w high, RS top 30%
Caveat: fundamentals are today's snapshot (no point-in-time history) -> cannot be backtested honestly; track forward in paper."""
import numpy as np, pandas as pd
F = pd.read_csv('data/fund/summary.csv').set_index('symbol')
C = pd.read_csv('data/daily_all/close.csv.gz', index_col=0, parse_dates=True).ffill(limit=5)
H = pd.read_csv('data/daily_all/high.csv.gz', index_col=0, parse_dates=True); Lo = pd.read_csv('data/daily_all/low.csv.gz', index_col=0, parse_dates=True)
LQ = pd.read_csv('study/results/liq_all.csv').set_index('symbol')
AV = {l.strip() for l in open('paper/avoid_liquidity_D.txt') if l.strip() and not l.startswith('#')}
syms = [s for s in F.index if s in C.columns and s not in AV]
F = F.loc[syms]; c = C[syms].iloc[-1]
m150 = C[syms].rolling(150).mean().iloc[-1]; m200 = C[syms].rolling(200).mean(); m200n = m200.iloc[-1]; m200p = m200.iloc[-22]
hi = H[syms].iloc[-250:].max(); lo = Lo[syms].iloc[-250:].min(); r63 = c / C[syms].iloc[-64] - 1; rs = r63.rank(pct=True)
pe = F.trailingPE.where(F.trailingPE > 0); g = F.np_g1 * 100; peg = pe / g.where(g > 0)
fin = F.sector.eq('Financial Services')
L = pd.DataFrame(index=syms)
L['BUFFETT'] = (F.roe >= .15) & (F.roce >= .15) & (F.debt_equity.fillna(0) < .5) & (F.ocf_to_np_3y >= .8) & (F.loss_years == 0) & (pe <= 40)
L['LYNCH'] = (g.between(15, 50)) & (peg <= 1.2) & (F.debt_equity.fillna(0) < .6)
ey = 1 / pe; gm = (F.roce.rank(pct=True) + ey.rank(pct=True)).where(~fin & pe.notna() & F.roce.notna())
L['GREENBLATT'] = gm >= gm.quantile(.85)
L['QGLP'] = (F.roe >= .15) & (g >= 15) & (F.rev_cagr3 >= .10) & (peg <= 1.5)
L['COFFEECAN'] = (F.rev_cagr3 >= .10) & (F.roce >= .15) & (F.marketCap >= 1e10)
L['CANSLIM'] = (F.q_np_yoy >= .25) & (g >= 20) & (c / hi >= .90) & (rs >= .80)
L['TREND'] = (c > m150) & (c > m200n) & (m150 > m200n) & (m200n > m200p) & (c / lo >= 1.3) & (c / hi >= .75) & (rs >= .70)
L = L.fillna(False)
L['fund_lenses'] = L[['BUFFETT', 'LYNCH', 'GREENBLATT', 'QGLP', 'COFFEECAN']].sum(1); L['price_lenses'] = L[['CANSLIM', 'TREND']].sum(1)
out = L.join(pd.DataFrame({'close': c.round(2), 'pe': pe.round(1), 'peg': peg.round(2), 'roe%': (F.roe * 100).round(1), 'roce%': (F.roce * 100).round(1), 'de': F.debt_equity.round(2),
                           'np_g%': g.round(0), 'q_np_yoy%': (F.q_np_yoy * 100).round(0), 'rev3y%': (F.rev_cagr3 * 100).round(1), 'from_hi%': ((c / hi - 1) * 100).round(1),
                           'rs3m': (rs * 100).round(0), 'liq': LQ.liquidity.str[0].reindex(syms), 'turn': LQ.turnover_cr.reindex(syms).round(0),
                           'mcap_cr': (F.marketCap / 1e7).round(0), 'sector': F.sector, 'industry': F.industry}))
out.to_csv('study/results/expert_screen.csv')
best = out[(out.fund_lenses >= 2) & (out.price_lenses >= 1) & out.liq.isin(['A', 'B'])].sort_values(['fund_lenses', 'price_lenses', 'turn'], ascending=False)
pd.set_option('display.width', 260); pd.set_option('display.max_rows', 200)
print(L[['BUFFETT', 'LYNCH', 'GREENBLATT', 'QGLP', 'COFFEECAN', 'CANSLIM', 'TREND']].sum().to_dict())
print(len(best)); print(best.drop(columns=['industry']).head(40).to_string())
