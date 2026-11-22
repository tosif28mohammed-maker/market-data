# Is the Indian Stock Market efficient - A comprehensive study of Bombay Stock Exchange Indices
स्रोत: book: arx_1510_03704v1_is_the_indian_stock_market_efficient_a_compre.txt · arx_1510_03704v1_is_the_indian_stock_market_efficient_a_compre.txt · Gemini ने पढ़ा 2026-11-22 23:30 UTC

**काम का नहीं:** Yeh ek academic research paper hai jo BSE indices ke monthly data par market efficiency aur random walk hypothesis test karta hai (Autocorrelation, Runs Test, ADF Test, Normality Tests ke dwara). Paper me trader ke liye koi concrete execution strategy, clear entry/exit triggers, stop-loss, target, position sizing ya quantitative stock selection rules nahi diye gaye hain.

## Point-by-point
- Study Scope: Paper me September 2005 se June 2015 tak ke 118 monthly observations ka use karke BSE ke 5 major indices (BSE LargeCap, BSE SmallCap, BSE MidCap, BSE MidSmallCap, BSE LargeMidCap) ka statistical analysis kiya gaya hai.
- Lag-1 Autocorrelation in Mid/Small Cap: BSE SmallCap (0.1257), BSE MidCap (0.1320), aur BSE MidSmallCap (0.1343) ke monthly returns me lag-1 autocorrelation standard error (0.019-0.021) ke 2-guna se zyada paaya gaya, jo monthly level par short-term persistence (momentum) darshata hai.
- Longer Lag Negative Autocorrelation: Lags 11 se 14 par negative autocorrelation dekha gaya (maslan Lag 14 par -0.17 se -0.21 tak), jo ~14 mahine ke cycle par mean-reversion ya annual seasonality ka ishara karta hai.
- Non-Normal Distribution of Monthly Returns: Kolmogorov-Smirnov test (test statistic 0.58-0.61, p-value 0.00) aur Jarque-Bera test (p-value < 0.05) se sabit hua ki monthly returns normal distribution follow nahi karte, jisse random walk hypothesis reject hoti hai.
- ADF Unit Root Test: ADF test statistic sabhi 5 indices ke liye -6.74 se -7.48 (p-value 0.001) raha, jisse null hypothesis of unit root reject hui, yaani return series stationary/biased random time series hain.
- Political & Regime Shift Factor: 2014 ke General Elections ke baad industrial-friendly government aane se investor confidence aur FII flows me badhotri hui, jisse market returns par positive shift dekha gaya.
- Market Inefficiency Conclusion: Indian stock market weak-form efficient nahi hai, jisse persistent momentum aur undervalued stocks select karke excess returns kamaye ja sakte hain, lekin paper me koi explicit selection rule nahi diya gaya hai.

## Niyam
- [new/partly] BSE MidCap / SmallCap Monthly Return Persistence (Lag-1 Momentum): Monthly candle close par agar pichle mahine ka return positive raha ho toh index me long position hold karo | entry: Mahine ke ant me (monthly close) agar pichle mahine ka return positive raha ho (lag-1 ACF ~ 0.13) | exit: Mahine ke ant me jab monthly return negative close ho jaaye (number nahi diya) | stop: Number nahi diya
