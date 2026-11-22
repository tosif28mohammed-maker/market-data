# A Study on the Efficiency of the Indian Stock Market (Nifty/Sensex AR(2) Autoregression & Weak-Form Inefficiency)
स्रोत: book: arx_2012_01160v1_a_study_on_the_efficiency_of_the_indian_stock.txt · arx_2012_01160v1_a_study_on_the_efficiency_of_the_indian_stock.txt · Gemini ने पढ़ा 2026-11-22 23:30 UTC

## Point-by-point
- Yeh paper BITS Pilani ke researchers dwara Indian stock market (NSE Nifty aur BSE Sensex) ki Weak-Form Market Efficiency par 10 saal ke data (April 2010 se March 2019) ka vishleshana karta hai.
- Runs Test ke zariye pata chala ki Nifty (Z = -2.768) aur Sensex (Z = -2.857) ka Z-statistic 5% significance level (-1.96) se kam hai, jisse Random Walk Hypothesis reject hota hai aur yeh sidh hota hai ki aaj ki keemat purani keemato par nirbhar karti hai.
- Autocorrelation Test (ACF) me pehle 20 lags ke liye correlation coefficient > 0.95 paya gaya, jo dikhata hai ki index ke daily prices me strong serial dependency / autocorrelation hai.
- Autoregression AR(2) model me dono indices (Nifty aur Sensex) ke Lag 1 (+1.077) aur Lag 2 (-0.077) ke coefficients statistically significant (p-value < 0.05) nikle.
- Model se pata chalta hai ki agle din ka index price Lag 1 se positive momentum aur Lag 2 se thoda pull-back/mean-reversion dikhata hai, jise quantitative intraday ya swing trading model me programmatic tarike se test kiya ja sakta hai.

## Niyam
- [new/yes] Nifty aur Sensex ke daily closing data par AR(2) Autoregressive equation (Index_t = Constant + 1.077 * Index_{t-1} - 0.077 * Index_{t-2}) ka upyog karke agle din ki directional position lena | entry: Agla din (t): Agar AR(2) formula se nikala gaya predicted close (Index_t) aaj ke close (Index_{t-1}) se bada hai toh Long position lo, agar predicted close chhota hai toh Short position lo | exit: Agle din market close par position square-off karein ya jab prediction direction change ho jaye | stop: number nahi diya
