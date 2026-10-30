"""Ladder orders + GTT on Angel One (SmartAPI) from a simple plan file. Runs on YOUR computer / server (never share passwords).

Plan file (CSV), one line per stock — Claude can prepare it for you:
    symbol,qty,ladder,sl,t1,t2
    BEL,100,"-1,-5,-10",340,374,395
  ladder = steps below the live price: numbers are rupees ("-1,-5,-10") or percent with % ("0%,-1.5%,-3%").
  qty is split evenly over the steps (100 -> 33,33,34). sl/t1/t2 are used by the "gtt" command after your buys fill.

Commands:
    python ladder.py plan.csv            -> TEST: only prints the orders (nothing is sent)
    python ladder.py plan.csv --live     -> places LIMIT, DELIVERY, DAY buy orders on NSE
    python ladder.py gtt plan.csv        -> TEST print of GTT rules (SL for all qty; half qty at T1, half at T2)
    python ladder.py gtt plan.csv --live -> creates the GTT rules (use only after the buys have filled)

Setup (once): pip install smartapi-python pyotp pandas ; put these in a file named .env next to this script:
    ANGEL_API_KEY=...   ANGEL_CLIENT=...   ANGEL_MPIN=...   ANGEL_TOTP_SECRET=...
From 1 Apr 2026 API orders are accepted only from your registered static IP (SmartAPI dashboard -> app -> Primary Static IP).
Market/IOC orders are not allowed for API (algo) orders; this tool uses LIMIT only. Max 10 orders per second (tool waits 0.3 s)."""
import os, sys, time, math, csv
LIVE = '--live' in sys.argv; args = [a for a in sys.argv[1:] if a != '--live']
MODE = 'gtt' if args and args[0] == 'gtt' else 'buy'; PLAN = args[-1] if args else 'plan.csv'
def env():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(p):
        for line in open(p):
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1); os.environ.setdefault(k.strip(), v.strip())
def tick(x): return round(math.floor(x / 0.05 + 1e-9) * 0.05, 2)   # NSE tick 0.05, round down for buys
def split(q, n): b = q // n; r = q - b * n; return [b + (1 if i >= n - r else 0) for i in range(n)]
def login():
    from SmartApi import SmartConnect; import pyotp
    env(); c = SmartConnect(api_key=os.environ['ANGEL_API_KEY'])
    s = c.generateSession(os.environ['ANGEL_CLIENT'], os.environ['ANGEL_MPIN'], pyotp.TOTP(os.environ['ANGEL_TOTP_SECRET']).now())
    if not s or not s.get('status'): sys.exit(f'login failed: {s}')
    return c
def token(c, sym):
    r = c.searchScrip('NSE', sym)
    for x in (r or {}).get('data', []) or []:
        if x.get('tradingsymbol') == f'{sym}-EQ': return x['tradingsymbol'], x['symboltoken']
    sys.exit(f'{sym}: symbol not found on NSE')
def ltp(c, ts, tok): return float(c.ltpData('NSE', ts, tok)['data']['ltp'])
rows = list(csv.DictReader(open(PLAN)))
c = login() if (LIVE or os.environ.get('ANGEL_API_KEY') or os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))) else None
print('LIVE - orders WILL be sent' if LIVE else 'TEST - nothing will be sent', '\n')
for r in rows:
    sym = r['symbol'].strip().upper(); qty = int(r['qty'])
    ts, tok = token(c, sym) if c else (f'{sym}-EQ', '?')
    if MODE == 'buy':
        price = ltp(c, ts, tok) if c else float(r.get('ref') or 0)
        steps = [s.strip() for s in r['ladder'].split(',') if s.strip()]; qs = split(qty, len(steps))
        print(f'{sym}: live price {price}')
        for s, q in zip(steps, qs):
            px = tick(price * (1 + float(s[:-1]) / 100)) if s.endswith('%') else tick(price + float(s))
            print(f'   BUY {q:>5} @ {px:>9.2f} (LIMIT, DELIVERY, DAY)')
            if LIVE and q > 0:
                o = c.placeOrder({'variety': 'NORMAL', 'tradingsymbol': ts, 'symboltoken': tok, 'transactiontype': 'BUY', 'exchange': 'NSE', 'ordertype': 'LIMIT',
                                  'producttype': 'DELIVERY', 'duration': 'DAY', 'price': str(px), 'quantity': str(q)})
                print('      order id', o); time.sleep(0.3)
    else:
        sl, t1, t2 = float(r['sl']), float(r['t1']), float(r.get('t2') or r['t1']); h1 = qty // 2; h2 = qty - h1
        rules = [('SL', sl, qty, tick(sl * 0.995)), ('T1', t1, h1, tick(t1)), ('T2', t2, h2, tick(t2))]
        for nm, trig, q, px in rules:
            print(f'{sym}: GTT {nm} SELL {q} when price {"<=" if nm == "SL" else ">="} {trig} (limit {px})')
            if LIVE and q > 0:
                g = c.gttCreateRule({'tradingsymbol': ts, 'symboltoken': tok, 'exchange': 'NSE', 'transactiontype': 'SELL', 'producttype': 'DELIVERY',
                                     'price': str(px), 'qty': str(q), 'triggerprice': str(tick(trig)), 'disclosedqty': str(q), 'timeperiod': '365'})
                print('      gtt id', g); time.sleep(0.3)
print('\nDone. Check the Orders / GTT tab in Angel One.')
