"""Angel One SmartAPI - DATA ONLY (no orders). Reads credentials from environment (GitHub Secrets):
ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PIN, ANGEL_TOTP_SECRET. Never prints them.
Writes data/angel/option_chain_<UNDERLYING>.csv (strike, CE/PE LTP, OI, OI change, volume) for the nearest expiry and data/angel/STATUS.txt.
python scripts/angel_data.py [NIFTY BANKNIFTY RELIANCE ...]"""
import os, sys, json, time, datetime as dt, requests, pandas as pd, pyotp
from SmartApi import SmartConnect
OUT = 'data/angel'; os.makedirs(OUT, exist_ok=True)
E = os.environ; need = ['ANGEL_API_KEY', 'ANGEL_CLIENT_ID', 'ANGEL_PIN', 'ANGEL_TOTP_SECRET']
miss = [k for k in need if not E.get(k)]
if miss: open(f'{OUT}/STATUS.txt', 'w').write(f'missing secrets: {miss}\n'); print('missing', miss); sys.exit(0)
api = SmartConnect(api_key=E['ANGEL_API_KEY'])
s = api.generateSession(E['ANGEL_CLIENT_ID'], E['ANGEL_PIN'], pyotp.TOTP(E['ANGEL_TOTP_SECRET'].replace(' ', '')).now())
ok = bool(s and s.get('status'))
status = [f"{dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC login {'OK' if ok else 'FAILED: ' + str(s.get('message') if s else s)}"]
if not ok: open(f'{OUT}/STATUS.txt', 'w').write('\n'.join(status) + '\n'); sys.exit(0)
M = pd.DataFrame(requests.get('https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json', timeout=60).json())
M = M[M.exch_seg == 'NFO']; M['expiry_d'] = pd.to_datetime(M.expiry, format='%d%b%Y', errors='coerce'); M['strike_r'] = pd.to_numeric(M.strike, errors='coerce') / 100
unds = sys.argv[1:] or ['NIFTY', 'BANKNIFTY']
today = pd.Timestamp.now().normalize()
for u in unds:
    try:
        opt = M[(M.name == u) & M.instrumenttype.isin(['OPTIDX', 'OPTSTK'])]
        exp = opt[opt.expiry_d >= today].expiry_d.min(); opt = opt[opt.expiry_d == exp]
        fut = M[(M.name == u) & M.instrumenttype.isin(['FUTIDX', 'FUTSTK'])].sort_values('expiry_d')
        ftok = fut[fut.expiry_d >= today].token.iloc[0]
        fq = api.getMarketData('LTP', {'NFO': [str(ftok)]})
        if isinstance(fq, (str, bytes)):
            try: fq = json.loads(fq)
            except Exception: raise RuntimeError('LTP reply: ' + str(fq)[:200])
        if not fq.get('status'): raise RuntimeError('LTP reply: ' + str(fq)[:200])
        spot = fq['data']['fetched'][0]['ltp']
        strikes = sorted(opt.strike_r.unique()); near = sorted(strikes, key=lambda k: abs(k - spot))[:30]
        sel = opt[opt.strike_r.isin(near)]; rows = []
        toks = sel.token.tolist()
        for i in range(0, len(toks), 50):
            r = api.getMarketData('FULL', {'NFO': [str(t) for t in toks[i:i + 50]]})
            if isinstance(r, (str, bytes)):
                try: r = json.loads(r)
                except Exception: raise RuntimeError('FULL reply: ' + str(r)[:200])
            for q in (r.get('data') or {}).get('fetched', []): rows.append(q)
            time.sleep(1)
        Q = pd.DataFrame(rows).merge(sel[['token', 'strike_r', 'symbol']], left_on='symbolToken', right_on='token')
        Q['type'] = Q.symbol.str[-2:]
        keep = ['strike_r', 'type', 'ltp', 'opnInterest', 'netChange', 'tradeVolume']
        Q = Q[[c for c in keep if c in Q.columns]].pivot_table(index='strike_r', columns='type', aggfunc='first')
        Q.columns = [f'{b}_{a}' for a, b in Q.columns]; Q = Q.reset_index().rename(columns={'strike_r': 'strike'})
        Q.insert(0, 'expiry', exp.date()); Q.insert(0, 'future_ltp', spot); Q.insert(0, 'time_utc', f'{dt.datetime.utcnow():%Y-%m-%d %H:%M}')
        Q.to_csv(f'{OUT}/option_chain_{u}.csv', index=False)
        status.append(f'{u}: future {spot}, expiry {exp.date()}, strikes {len(Q)}')
    except Exception as e: status.append(f'{u}: error {type(e).__name__}: {str(e)[:150]}')
open(f'{OUT}/STATUS.txt', 'w').write('\n'.join(status) + '\n'); print('\n'.join(status))
try: api.terminateSession(E['ANGEL_CLIENT_ID'])
except Exception: pass
