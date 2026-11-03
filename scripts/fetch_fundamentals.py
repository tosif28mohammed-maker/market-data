"""Fundamentals robot (user, 3 Nov 2026: 'har share ki financial study: P&L, revenue growth, GP, net profit, cash flow, balance sheet, ROE/ROCE...').
Source: Yahoo Finance via yfinance (annual ~4 years + last ~5 quarters). Universe: paper/gap_universe.csv (A/B) + data/news/watch.txt.
Saves raw rows to data/fund/raw.csv.gz (symbol, statement, freq, date, item, value), company info to data/fund/info.csv,
and computed metrics to data/fund/summary.csv. Runs weekly (Saturday) from .github/workflows/fundamentals.yml. env LIMIT=n for a test run."""
import os, time, gzip, csv, datetime as dt, numpy as np, pandas as pd, yfinance as yf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(ROOT, 'data', 'fund'); os.makedirs(D, exist_ok=True)
U = list(pd.read_csv(os.path.join(ROOT, 'paper', 'gap_universe.csv')).symbol)
wf = os.path.join(ROOT, 'data', 'news', 'watch.txt')
if os.path.exists(wf): U += [l.split('|')[0].strip() for l in open(wf, encoding='utf-8') if l.strip() and not l.startswith('#')]
U = list(dict.fromkeys(U))
if os.environ.get('LIMIT'): U = U[:int(os.environ['LIMIT'])]
ITEMS = {'income': ['Total Revenue', 'Gross Profit', 'Operating Income', 'EBIT', 'EBITDA', 'Net Income', 'Net Income Common Stockholders', 'Diluted EPS',
                    'Interest Expense', 'Pretax Income', 'Tax Provision', 'Net Interest Income', 'Operating Revenue'],
         'balance': ['Total Assets', 'Total Debt', 'Stockholders Equity', 'Cash And Cash Equivalents', 'Current Assets', 'Current Liabilities',
                     'Inventory', 'Accounts Receivable', 'Invested Capital', 'Ordinary Shares Number', 'Total Liabilities Net Minority Interest'],
         'cashflow': ['Operating Cash Flow', 'Capital Expenditure', 'Free Cash Flow', 'Cash Dividends Paid']}
INFO = ['marketCap', 'trailingPE', 'forwardPE', 'priceToBook', 'dividendYield', 'heldPercentInsiders', 'heldPercentInstitutions', 'sector', 'industry',
        'returnOnEquity', 'debtToEquity', 'profitMargins', 'revenueGrowth', 'earningsGrowth', 'beta']
raw = []; info = []
def grab(tk, attr):
    for a in range(3):
        try: return getattr(tk, attr)
        except Exception as e: print('retry', attr, e); time.sleep(4 * (a + 1))
    return None
for n, s in enumerate(U):
    tk = yf.Ticker(f'{s}.NS')
    for st, attrs in (('income', ('income_stmt', 'quarterly_income_stmt')), ('balance', ('balance_sheet', 'quarterly_balance_sheet')), ('cashflow', ('cashflow', 'quarterly_cashflow'))):
        for freq, at in zip(('A', 'Q'), attrs):
            df = grab(tk, at)
            if df is None or not hasattr(df, 'index') or df.empty: continue
            for it in ITEMS[st]:
                if it not in df.index: continue
                for c, v in df.loc[it].items():
                    if pd.notna(v): raw.append((s, st, freq, str(pd.Timestamp(c).date()), it, float(v)))
    try:
        inf = tk.info or {}; info.append({'symbol': s, **{k: inf.get(k) for k in INFO}})
    except Exception as e: print('info', s, e)
    if n % 50 == 0: print(n, s, len(raw), flush=True)
    time.sleep(0.4)
R = pd.DataFrame(raw, columns=['symbol', 'statement', 'freq', 'date', 'item', 'value'])
R.to_csv(os.path.join(D, 'raw.csv.gz'), index=False, compression='gzip'); pd.DataFrame(info).to_csv(os.path.join(D, 'info.csv'), index=False)
# ---- metrics
def series(g, st, freq, item):
    x = g[(g.statement == st) & (g.freq == freq) & (g.item == item)].sort_values('date')
    return pd.Series(x.value.values, index=pd.to_datetime(x.date))
out = []
for s, g in R.groupby('symbol'):
    rev = series(g, 'income', 'A', 'Total Revenue'); ni = series(g, 'income', 'A', 'Net Income'); gp = series(g, 'income', 'A', 'Gross Profit')
    ebit = series(g, 'income', 'A', 'EBIT'); intr = series(g, 'income', 'A', 'Interest Expense')
    eq = series(g, 'balance', 'A', 'Stockholders Equity'); ta = series(g, 'balance', 'A', 'Total Assets'); cl = series(g, 'balance', 'A', 'Current Liabilities')
    ca = series(g, 'balance', 'A', 'Current Assets'); debt = series(g, 'balance', 'A', 'Total Debt'); cash = series(g, 'balance', 'A', 'Cash And Cash Equivalents')
    ocf = series(g, 'cashflow', 'A', 'Operating Cash Flow'); fcf = series(g, 'cashflow', 'A', 'Free Cash Flow')
    qrev = series(g, 'income', 'Q', 'Total Revenue'); qni = series(g, 'income', 'Q', 'Net Income')
    def last(x, k=1): return float(x.iloc[-k]) if len(x) >= k else np.nan
    def yoyq(x):   # latest quarter vs same quarter a year ago (if 5 quarters present)
        if len(x) < 5: return np.nan
        a, b = x.iloc[-1], x.iloc[-5]; return float(a / b - 1) if b and b > 0 else np.nan
    m = dict(symbol=s, fy_last=str(rev.index[-1].date()) if len(rev) else None,
             rev_cr=last(rev) / 1e7, rev_g1=last(rev) / last(rev, 2) - 1 if len(rev) > 1 and last(rev, 2) > 0 else np.nan,
             rev_cagr3=(last(rev) / last(rev, 4)) ** (1 / 3) - 1 if len(rev) > 3 and last(rev, 4) > 0 and last(rev) > 0 else np.nan,
             np_cr=last(ni) / 1e7, np_g1=last(ni) / last(ni, 2) - 1 if len(ni) > 1 and last(ni, 2) > 0 else np.nan,
             gp_margin=last(gp) / last(rev) if len(gp) and last(rev) else np.nan, ebit_margin=last(ebit) / last(rev) if len(ebit) and last(rev) else np.nan,
             np_margin=last(ni) / last(rev) if last(rev) else np.nan,
             roe=last(ni) / np.nanmean([last(eq), last(eq, 2)]) if len(eq) > 1 else (last(ni) / last(eq) if len(eq) else np.nan),
             roce=last(ebit) / (last(ta) - last(cl)) if len(ebit) and len(ta) and len(cl) and (last(ta) - last(cl)) > 0 else np.nan,
             debt_equity=last(debt) / last(eq) if len(debt) and len(eq) and last(eq) > 0 else np.nan, net_cash_cr=(last(cash) - last(debt)) / 1e7 if len(cash) and len(debt) else np.nan,
             int_cover=last(ebit) / abs(last(intr)) if len(intr) and last(intr) else np.nan, current_ratio=last(ca) / last(cl) if len(ca) and len(cl) and last(cl) else np.nan,
             ocf_to_np_3y=ocf.iloc[-3:].sum() / ni.iloc[-3:].sum() if len(ocf) >= 3 and len(ni) >= 3 and ni.iloc[-3:].sum() > 0 else np.nan,
             fcf_cr=last(fcf) / 1e7, q_last=str(qrev.index[-1].date()) if len(qrev) else None, q_rev_yoy=yoyq(qrev), q_np_yoy=yoyq(qni),
             loss_years=int((ni < 0).sum()), years=len(rev))
    # simple quality score 0-9 (Piotroski-style, using what Yahoo gives)
    sc = 0
    sc += (m['np_cr'] or 0) > 0; sc += (m['roe'] or 0) > 0.12; sc += (m['roce'] or 0) > 0.12; sc += (m['rev_g1'] or 0) > 0.08
    sc += (m['np_g1'] or 0) > 0.08; sc += (m['ocf_to_np_3y'] or 0) > 0.8; sc += np.isnan(m['debt_equity']) or m['debt_equity'] < 0.5
    sc += (m['int_cover'] or 99) > 4 if not np.isnan(m['int_cover']) else 1; sc += m['loss_years'] == 0
    m['quality_score'] = int(sc); out.append(m)
S = pd.DataFrame(out).merge(pd.DataFrame(info), on='symbol', how='left')
S['updated'] = str(dt.date.today()); S.round(4).to_csv(os.path.join(D, 'summary.csv'), index=False)
print('done', len(R), 'rows', len(S), 'companies')
