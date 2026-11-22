# EMA Crossover with RSI >= 40 Framework for Swing and Positional Trading
स्रोत: Dhan (YouTube) · https://www.youtube.com/watch?v=LpCo69ZZBRg · Gemini ने पढ़ा 2026-11-22 18:17 UTC

## Point-by-point
- Positional vs Swing Trading: Swing trading holding period ranges from a few days to a few weeks; Positional trading holding period ranges up to 11-12 months.
- Technical Setup Components: Uses a combination of Exponential Moving Averages (25 EMA and 55 EMA, or 20 EMA and 50 EMA) alongside Relative Strength Index (RSI 14).
- EMA Bullish Crossover: Shorter EMA (25 EMA) crossing above longer EMA (55 EMA) from below signifies increasing demand (buy signal).
- RSI Momentum Filter: Modify RSI middle limit setting from default 50 to 40. Trade entries require RSI > 40 to ensure existing momentum (avoid buying stocks in dead/no-momentum zones near 30).
- Trend Quality Filter: Both EMAs must be rising/up-trending with good separation. Avoid taking signals when EMAs are flat or moving sideways.
- Screener Parameters (ScanX): Filter for NSE stocks with Market Cap > 10,000 Crore (ensures high liquidity/volume for active trading), Price >= 20 EMA, Price >= 50 EMA, and RSI(14) >= 40.
- Risk Management & Exit: Stop loss placed at the recent technical price support (swing low) prior to the crossover. Target can be fixed 1:2 Risk-Reward (e.g., 5% risk, 10% target) or trailing stop-loss (moving stop up by 10% for every 10% price move), or holding until a bearish EMA crossover occurs.

## Niyam
- [new/yes] Daily 25/55 EMA Bullish Crossover + RSI >= 40 + Market Cap > 10,000 Cr Filter | entry: Buy when 25 EMA crosses above 55 EMA from below (or 20 EMA crosses above 50 EMA) AND RSI(14) >= 40 AND both EMAs are actively sloping upward (rising). | exit: Exit on Bearish EMA Crossover (25 EMA crosses below 55 EMA) OR when 1:2 Risk-Reward target is met OR trail stop-loss up 10% for every 10% gain. | stop: Set stop-loss at recent price action support level (swing low prior to the bullish crossover).
