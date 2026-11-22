# Gemini (gemini-3-flash-preview)

**TAG: condor-2026-11-22**

### 1) Top 5 Methodological Risks
1.  **Selection Bias (Test A):** The 45 "missing" weeks in the friend’s data are the "smoking gun." A 30% omission rate in a backtest usually hides the largest drawdowns. Including them flipped the result from +2.68L to ~zero.
2.  **Liquidity/Bhavcopy Bias (Test B):** NSE "Close" prices for OTM options are often stale or represent a wide bid-ask spread rather than a tradable mid-price. Using 1% slippage for wings that might have a 20-50% spread in reality (especially 2010-2018) grossly underestimates costs.
3.  **Multiple Testing Bias (P-Hacking):** Claude tested ~8,600 combinations. With a 28% success rate and only 269 "PASS" results (~3% of total), these are likely statistical noise (false discoveries) rather than a robust edge. The out-of-sample failure (5.4% -> -0.77%) confirms this.
4.  **Path-Dependency & SL Execution:** Checking SLs at "Daily Close" or using "High-Low" proxies ignores the intraday sequence. In a "gamma squeeze," an Iron Condor’s loss often peaks and triggers SLs mid-day before Mean Reversion brings it back by the close.
5.  **Fixed-Strike vs. Delta:** Using z-scores (EM) is better than fixed points, but the study doesn't account for "pinned" strikes or the psychological/operational inability to execute 4-leg orders at specific "fair" prices simultaneously.

### 2) Missing Tests (NSE Bhavcopy specific)
*   **Strike Availability Check:** Ensure the "z-score" strikes actually existed and had volume > 100 contracts. OTM liquidity in early years (2010-2016) was abysmal; the strategy might be untradable.
*   **VIX-Regime Partitioning:** Run the d3/z1.25 combo specifically during VIX < 15 vs VIX > 20. Condors often look like "alpha" in low-vol regimes but are "insurance-selling" disasters when VIX spikes.
*   **Slippage Sensitivity Stress-Test:** Re-run with 5% and 10% slippage on the BUY legs (wings). If the "edge" vanishes, it was just a liquidity illusion.
*   **Drawdown Duration:** Calculate the longest "underwater" period in days. A strategy that loses in 2024 and 2026 (as noted) would likely be abandoned by a human trader.

### 3) Is the final conclusion justified?
**Partly.**
The conclusion correctly identifies the friend's "edge" as an artifact of cherry-picking and bad SL logic. However, the "small, lumpy edge" found in Test B is likely over-optimized. The fact that the "best" settings lost money in 2024 and 2026 suggests the strategy is currently failing in the high-vol/high-gamma regime of the modern NSE.

### 4) Better Variant (Specific Rules)
**The "VIX-Adaptive Short Wing"**
*   **Entry:** 3 Days to Expiry (d3) at 10:00 AM (avoid open volatility).
*   **Strikes:** Short legs at 0.15 Delta (proxy: F ± 1.5*EM). Long legs 200 points further (Fixed width to control margin).
*   **Filter:** Only enter if India VIX > 14 and < 22. (Avoids "pennies under steamroller" and "uncontrollable gaps").
*   **SL:** 100% of the *individual* short leg premium (not the whole structure). If one side hits, close the whole condor.

### 5) Suspicious Numbers
*   **2025 Outperformance:** The +Rs49.8k/lot in 2025 is an extreme outlier compared to other years (+1k to +18k). This suggests a few "black swan" weeks where the condor survived a massive premium crush that might not be replicable with real-world slippage.
*   **AlgoTest Entry Prices:** Friend's prices being "inside Low-High" is a weak verification. In low-volume OTMs, the "Low-High" can be a single trade.
*   **1% Slippage:** For a 20-point option, 0.2 points slippage is unrealistic for a retail trader using market orders on Nifty weeklies; 0.5 to 1.0 points is more common.
