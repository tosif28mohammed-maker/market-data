"""Track broker/research tips the user shares (Angel One, Moneycontrol Pro, ...) - user 4 Nov 2026: 'screenshots share karta rahunga, aap study karo'.
Input: paper/tips.csv (one row per tip). Each run (daily robot) checks every open tip from its date onward:
  stocks/futures (type EQ/FUT): daily high/low from Yahoo (symbol.NS);
  options (type OPT): daily high/low of that exact contract from the NSE F&O bhavcopy.
Outcome rule (conservative): entry = price_when_seen if it was outside the recommended range, else reco_high; 'TARGET' if high >= target,
'SL' if low <= sl (if both on the same day -> SL first); options still open at expiry -> closed at expiry close; stocks open after 30 trading days -> closed.
Writes paper/tips_status.csv and a per-source scorecard paper/tips_scorecard.csv (+ section in today's report)."""
import os, io, zipfile, datetime as dt, requests, pandas as pd, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = os.path.join(ROOT, 'paper')
T = pd.read_csv(os.path.join(P, 'tips.csv'), dtype=str).fillna('')
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
cache = {}
def bhav(d):
    if d in cache: return cache[d]
    url = f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{d:%Y%m%d}_F_0000.csv.zip"
    try:
        r = requests.get(url, headers=H, timeout=30)
        if r.status_code != 200: cache[d] = None; return None
        z = zipfile.ZipFile(io.BytesIO(r.content)); df = pd.read_csv(z.open(z.namelist()[0])); cache[d] = df; return df
    except Exception as e: print('bhav', d, e); cache[d] = None; return None
def opt_bars(sym, exp, strike, opt, start, end):
    rows = []
    for d in pd.bdate_range(start, end):
        df = bhav(d.date())
        if df is None: continue
        m = df[(df.TckrSymb == sym) & (df.OptnTp == opt) & (df.StrkPric.astype(float) == float(strike)) & (pd.to_datetime(df.XpryDt).dt.date == pd.Timestamp(exp).date())]
        if len(m): x = m.iloc[0]; rows.append((d.normalize(), float(x.HghPric), float(x.LwPric), float(x.ClsPric)))
    return pd.DataFrame(rows, columns=['date', 'high', 'low', 'close']).set_index('date')
def eq_bars(sym, start):
    import yfinance as yf
    x = yf.download(f'{sym}.NS', start=str(pd.Timestamp(start).date()), progress=False, auto_adjust=False)
    if isinstance(x.columns, pd.MultiIndex): x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None).normalize(); return x.rename(columns=str.lower)[['high', 'low', 'close']]
today = pd.Timestamp(dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date())
out = []
for _, t in T.iterrows():
    if t.type not in ('EQ', 'FUT', 'OPT'):
        out.append(dict(id=t.id, source=t.source, instrument=t.instrument, date=t.date_ist, my_verdict=t.my_verdict, result='RECORD_ONLY (multi-leg)')); continue
    d0 = pd.Timestamp(t.date_ist[:10]); lo, hi = float(t.reco_low or 0), float(t.reco_high or 0); seen = float(t.price_when_seen or hi)
    entry = seen if (seen > hi or seen < lo) else hi; tgt, sl = float(t.target), float(t.sl)
    try:
        if t.type == 'OPT': B = opt_bars(t.symbol, t.expiry, t.strike, t.opt, d0, min(today, pd.Timestamp(t.expiry)))
        else: B = eq_bars(t.symbol, d0)
    except Exception as e: print('ERR', t.id, e); B = pd.DataFrame()
    res, exit_px, exit_d = 'OPEN', np.nan, ''
    for i, (d, b) in enumerate(B.iterrows()):
        if b.low <= sl: res, exit_px, exit_d = 'SL', sl, str(d.date()); break
        if b.high >= tgt: res, exit_px, exit_d = 'TARGET', tgt, str(d.date()); break
        if t.type != 'OPT' and i >= 30: res, exit_px, exit_d = 'TIME', b.close, str(d.date()); break
    if res == 'OPEN' and t.type == 'OPT' and len(B) and today >= pd.Timestamp(t.expiry): res, exit_px, exit_d = 'EXPIRY', B.close.iloc[-1], str(B.index[-1].date())
    last = B.close.iloc[-1] if len(B) else np.nan
    out.append(dict(id=t.id, source=t.source, instrument=t.instrument, date=t.date_ist, entry=entry, target=tgt, sl=sl, my_verdict=t.my_verdict, result=res,
                    exit_date=exit_d, exit_price=exit_px, ret_pct=round((exit_px / entry - 1) * 100, 1) if exit_px == exit_px else np.nan,
                    last=last, open_pct=round((last / entry - 1) * 100, 1) if res == 'OPEN' and last == last else np.nan))
S = pd.DataFrame(out); S.to_csv(os.path.join(P, 'tips_status.csv'), index=False)
done = S[S.result != 'OPEN']
sc = done.groupby('source').agg(tips=('id', 'size'), target_hit=('result', lambda x: (x == 'TARGET').mean()), avg_ret=('ret_pct', 'mean')).round(2).reset_index() if len(done) else pd.DataFrame()
mv = done.groupby('my_verdict').agg(tips=('id', 'size'), avg_ret=('ret_pct', 'mean')).round(2).reset_index() if len(done) else pd.DataFrame()
sc.to_csv(os.path.join(P, 'tips_scorecard.csv'), index=False)
rep = ['', '## Broker tips का हिसाब (Angel/Moneycontrol, user के screenshots)'] + [f"- {r.id} {r.source}: {r.instrument} — {r.result}" + (f" ({r.ret_pct:+.1f}%)" if r.ret_pct == r.ret_pct else (f" (अभी {r.open_pct:+.1f}%)" if r.open_pct == r.open_pct else '')) + f" | मेरी राय: {r.my_verdict}" for r in S.itertuples()]
if len(sc): rep += ['- स्कोरकार्ड: ' + '; '.join(f"{r.source}: {r.tips} tips, target {r.target_hit*100:.0f}%, औसत {r.avg_ret:+.1f}%" for r in sc.itertuples())]
if len(mv): rep += ['- मेरी राय के हिसाब से: ' + '; '.join(f"{r.my_verdict}: {r.tips}, औसत {r.avg_ret:+.1f}%" for r in mv.itertuples())]
rf = os.path.join(P, 'reports', f'{today.date()}.md'); os.makedirs(os.path.dirname(rf), exist_ok=True)
with open(rf, 'a') as fh: fh.write('\n'.join(rep) + '\n')
print('\n'.join(rep))
