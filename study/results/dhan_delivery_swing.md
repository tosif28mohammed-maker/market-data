# DHAN-315 delivery swing test (21 Nov 2026)
Source: https://youtu.be/LbtF1cD5ckM . Script: study/dhan_delivery_swing.py; table: dhan_delivery_swing.csv; trades: dhan_delivery_swing_trades.csv.gz
- Full system (delivery top-10% daily AND weekly, 5d up, >EMA20/50, Supertrend green, buy-stop above day high, stop day low, 1:2): 4282 trades 2008-26, target hit 31.9%, net -0.07%/trade. FAILS bar.
- Delivery filter vs same setup without it: +0.3%/trade, every era. KEEP as extra filter (analysis).
- Supertrend flat/just-green preference: no difference. USELESS.
- Fixed 3% stop worse than day-low stop.
- Scenario: strong breadth (>60% above 50DMA) 2016-26: 35.6% hit, +0.36%/trade (n=741). Borderline, watch.
