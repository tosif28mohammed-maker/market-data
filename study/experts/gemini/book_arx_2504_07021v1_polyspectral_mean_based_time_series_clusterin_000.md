# Polyspectral Mean based Time Series Clustering of Indian Stock Market
स्रोत: book: arx_2504_07021v1_polyspectral_mean_based_time_series_clusterin.txt · arx_2504_07021v1_polyspectral_mean_based_time_series_clusterin.txt · Gemini ने पढ़ा 2026-11-23 09:47 UTC

## Point-by-point
- Yah research paper NIFTY 50 ke 49 shares par 1000 trading days ke daily VWAP (Value-Weighted Average Price) data ka upayog karke non-linear statistical clustering karta hai.
- First-differencing Preprocessing: Time series ko stationary banane ke liye daily VWAP ka pehla difference (DiffEndStart) nikala jata hai.
- Feature Extraction (Polyspectra): ARMA/GARCH aur linear models se aage badhkar non-linear price patterns ko pakadne ke liye 4 Spectral Means aur 4 Bispectral Means (triangular, circular indicator, radial, cosine weights ke saath) calculate kiye jaate hain.
- Cluster Determination: Optimal cluster count k=5 nikalne ke liye Gap Statistic criterion 'Gap(k) >= Gap(k+1) - s_{k+1}' ka istemal kiya gaya hai.
- 5 Non-Sectoral Risk/Behavior Clusters:
-  - Cluster 1 (Conglomerates & Infra Heavy): ADANIPORTS, BAJAJ-AUTO, HINDALCO, JSWSTEEL, SBIN, SHREECEM, TATASTEEL, ULTRACEMCO (Infrastructure spending, commodity cycles aur government policies se judey hain).
-  - Cluster 2 (Policy & Consumer/Energy Sensitive): BPCL, BRITANNIA, COALINDIA, EICHERMOT, GAIL, HDFCBANK, HEROMOTOCO, INDUSINDBK, IOC, ITC, LT, MARUTI, M&M, ZEEL, NTPC, ONGC, TATAMOTORS, UPL, VEDL (Government regulation, interest rates aur fuel price sensitivity).
-  - Cluster 3 (Defensive & Regulated Cashflow): POWERGRID, TCS, WIPRO (Low volatility, long-term service contracts aur regulated power tariffs).
-  - Cluster 4 (Global Revenue Exposure Defensive): HCLTECH, SUNPHARMA (50%+ revenue US/Europe global markets se, global economy aur currency fluctuations se prabhavit).
-  - Cluster 5 (Large-Cap Liquidity Leaders): ASIANPAINT, AXISBANK, BAJAJFINSV, BAJFINANCE, BHARTIARTL, CIPLA, DRREDDY, GRASIM, HDFC, HINDUNILVR, ICICIBANK, INFY, KOTAKBANK, NESTLEIND, RELIANCE, TECHM, TITAN (High institutional ownership, deep liquidity aur balanced risk profile).
- Time Series Metrics (1000-day Daily VWAP):
-  - Hurst Exponent Trend Persistence: JSWSTEEL (0.629), TATASTEEL (0.619), HINDALCO (0.607), VEDL (0.605) sabse majboot trend-following behavior dikhate hain (H > 0.60).
-  - Hurst Exponent Mean-Reversion: EICHERMOT (0.478), NESTLEIND (0.483), HINDUNILVR (0.486) mean-reversion behavior dikhate hain (H < 0.50).
-  - Seasonality: Nifty 50 shares me daily VWAP data par seasonal strength kafi kam (< 0.17) payi gayi, yaani koi fixed weekly/monthly cycle nahi hai.

## Niyam
- [new/partly] Polyspectral K-Means (k=5) Portfolio Diversification Filter | entry: Traditional sector diversification ki jagah portfolio banate samay 5 Polyspectral Clusters me se har cluster se 1-1 stock select karo (Cluster 1: Conglomerates, Cluster 2: Macro/Policy, Cluster 3: Regulated Defensive, Cluster 4: Global Exposure, Cluster 5: Large-Cap Leaders). Buy execution trigger: number nahi diya. | exit: number nahi diya | stop: number nahi diya
- [new/yes] Hurst Exponent Stock Selection Filter (Trend Following vs Mean Reversion) | entry: Trend-following strategies ke liye un shares ko chunen jinka 1000-day Hurst Exponent H > 0.60 ho (jaise JSWSTEEL H=0.629, TATASTEEL H=0.619, HINDALCO H=0.607, VEDL H=0.605). Mean-reversion strategies ke liye H < 0.50 wale shares chunen (jaise EICHERMOT H=0.478, NESTLEIND H=0.483, HINDUNILVR H=0.486). Trading entry trigger: number nahi diya. | exit: number nahi diya | stop: number nahi diya
