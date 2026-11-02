"""Global markets daily history (Yahoo) -> data/global/<NAME>.csv (full history, merged). For the India vs world lead-lag study.
Names: US_ / JP_ / CN_ / HK_ / EU_ / ADR_ / ETF_ / CMD_ / FX_ prefixes so they never clash with Indian symbols."""
import os, time, pandas as pd, yfinance as yf
G = {
 'US_SP500': '^GSPC', 'US_NASDAQ': '^IXIC', 'US_DOW': '^DJI', 'US_RUSSELL2000': '^RUT', 'US_VIX': '^VIX', 'US_SOX': '^SOX', 'US_10Y': '^TNX',
 'JP_NIKKEI': '^N225', 'CN_SHANGHAI': '000001.SS', 'CN_SHENZHEN': '399001.SZ', 'HK_HANGSENG': '^HSI', 'KR_KOSPI': '^KS11', 'TW_TAIEX': '^TWII', 'SG_STI': '^STI',
 'EU_FTSE': '^FTSE', 'EU_DAX': '^GDAXI', 'EU_STOXX50': '^STOXX50E',
 'CMD_CRUDE_WTI': 'CL=F', 'CMD_BRENT': 'BZ=F', 'CMD_GOLD': 'GC=F', 'CMD_SILVER': 'SI=F', 'CMD_COPPER': 'HG=F', 'CMD_NATGAS': 'NG=F', 'CMD_ALUMINIUM': 'ALI=F',
 'FX_USDINR': 'USDINR=X', 'FX_DOLLAR_INDEX': 'DX-Y.NYB', 'FX_USDJPY': 'JPY=X', 'FX_USDCNY': 'CNY=X',
 'ADR_INFY': 'INFY', 'ADR_WIPRO': 'WIT', 'ADR_HDFCBANK': 'HDB', 'ADR_ICICIBANK': 'IBN', 'ADR_DRREDDY': 'RDY', 'ADR_MMYT': 'MMYT',
 'ETF_INDIA_INDA': 'INDA', 'ETF_INDIA_EPI': 'EPI', 'ETF_INDIA_SMALL_SMIN': 'SMIN', 'ETF_CHINA_FXI': 'FXI', 'ETF_CHINA_INTERNET': 'KWEB', 'ETF_JAPAN_EWJ': 'EWJ', 'ETF_EM_EEM': 'EEM',
 'ETF_US_TECH': 'XLK', 'ETF_US_FIN': 'XLF', 'ETF_US_ENERGY': 'XLE', 'ETF_US_HEALTH': 'XLV', 'ETF_US_MATERIALS': 'XLB', 'ETF_US_METALS': 'XME', 'ETF_US_INDUSTRIAL': 'XLI',
 'ETF_US_CONSUMER': 'XLY', 'ETF_US_STAPLES': 'XLP', 'ETF_US_AUTO_EV': 'DRIV', 'ETF_US_PHARMA': 'PPH', 'ETF_US_BIOTECH': 'IBB', 'ETF_US_SEMIS': 'SOXX', 'ETF_US_REALESTATE': 'XLRE',
 'US_AAPL': 'AAPL', 'US_MSFT': 'MSFT', 'US_NVDA': 'NVDA', 'US_AMZN': 'AMZN', 'US_GOOGL': 'GOOGL', 'US_META': 'META', 'US_TSLA': 'TSLA', 'US_JPM': 'JPM', 'US_XOM': 'XOM',
 'US_ACN': 'ACN', 'US_CTSH': 'CTSH', 'US_IBM': 'IBM', 'US_FCX': 'FCX', 'US_NUE': 'NUE', 'US_CAT': 'CAT', 'US_PFE': 'PFE',
 'JP_TOYOTA': '7203.T', 'JP_SONY': '6758.T', 'JP_SOFTBANK': '9984.T', 'JP_NIPPONSTEEL': '5401.T', 'HK_TENCENT': '0700.HK', 'HK_ALIBABA': '9988.HK', 'US_BABA': 'BABA',
}
os.makedirs('data/global', exist_ok=True); ok = 0
for name, tk in G.items():
    path = f'data/global/{name}.csv'; df = None
    for a in range(3):
        try:
            df = yf.download(tk, period='max' if not os.path.exists(path) else '1mo', interval='1d', auto_adjust=False, progress=False, threads=False)
            if df is not None and len(df): break
        except Exception as e: print(name, e)
        time.sleep(3)
    if df is None or not len(df): print('no data', name); continue
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df = df.reset_index().rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Adj Close': 'adj', 'Volume': 'volume'})
    df['date'] = pd.to_datetime(df.date).dt.tz_localize(None).dt.normalize(); df = df[[c for c in ['date', 'open', 'high', 'low', 'close', 'adj', 'volume'] if c in df.columns]]
    if os.path.exists(path): df = pd.concat([pd.read_csv(path, parse_dates=['date']), df])
    df = df.dropna(subset=['close']).drop_duplicates('date', keep='last').sort_values('date'); df.to_csv(path, index=False, float_format='%.4f'); ok += 1; time.sleep(0.5)
open('data/global/STATUS.txt', 'w').write(f'updated {pd.Timestamp.utcnow():%Y-%m-%d %H:%M} UTC, {ok}/{len(G)} series\n'); print(ok, len(G))
