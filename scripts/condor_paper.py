"""CONDOR_FRIEND paper robot (user 19 Nov 2026): dost ka Nifty weekly iron condor, ASLI NSE bhavcopy bhaav par, bina paise.
Rules = tools/hedged_strangle_v2.pine / study/condor_friend.py:
  expiry ke agle trading din OPEN par entry (VIX pichhla close 10-22), SELL CE/PE = Nifty open +- 1 SD (VIX, calendar din),
  BUY hedge 300 pt door; target 60% premium, SL nuksaan 150%; warna expiry par Nifty close par settle.
Do kitaabein: A = SL/target sirf din ke close par; B = SL din ke andar chhua (sold leg HIGH, hedge LOW) to SL level par.
Rs = lot 65, Rs 300/lot kharcha, 0.5 pt/leg/side slippage.
Har run pichhle din se aaj tak ke saare din pakadta hai (bhavcopy na mile: purana din = chhutti, aaj = baad mein dobara).
Files: paper/condor_state.json, paper/condor_journal.csv (band trades), paper/condor_daily.csv (roz ka hisaab), paper/condor_today.md
"""
import os, io, json, math, time, zipfile, datetime as dt
import pandas as pd, numpy as np, requests
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = os.path.join(R, 'paper')
ST, JR, DY, MDF = (os.path.join(P, f) for f in ('condor_state.json', 'condor_journal.csv', 'condor_daily.csv', 'condor_today.md'))
START = os.environ.get('CONDOR_START', '2026-11-10')  # pehla din (9 Nov expiry ke agle din se live)
PREV_EXP = os.environ.get('CONDOR_PREV_EXP', '2026-11-09')  # START se pehle wali expiry
LOT, COST, SLIP, STEP, HEDGE, K, TGT, SL, VMIN, VMAX = 65, 300.0, 0.5, 50, 300, 1.0, 60, 150, 10, 22

S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
                  'Accept': '*/*', 'Referer': 'https://www.nseindia.com/'})


def get(url):
    for u in (url.replace('nsearchives.nseindia.com', 'archives.nseindia.com'), url):
        for _ in range(2):
            try:
                r = S.get(u, timeout=20)
                if r.status_code == 200 and len(r.content) > 200: return r.content
                if r.status_code in (403, 404): break
            except Exception:
                time.sleep(2)
    return None


LOCAL = os.environ.get('CONDOR_LOCAL')  # test: pickle of nse_opt NIFTY rows
_LC = {}


def bhav(d):
    """NIFTY options of date d -> DataFrame(exp, type, K, open, high, low, px) or None."""
    if LOCAL:
        if not _LC:
            o = pd.read_pickle(LOCAL); o['date'] = pd.to_datetime(o.date).dt.date; _LC.update({k: g for k, g in o.groupby('date')})
        x = _LC.get(d)
        if x is None: return None
        tr = pd.to_numeric(x.contracts, errors='coerce').fillna(0) > 0
        return pd.DataFrame({'exp': pd.to_datetime(x.exp).dt.date, 'type': x.type.astype(str).str[0], 'K': x.K,
                             'open': np.where(tr & (x.open > 0), x.open, np.nan), 'px': np.where(tr, x.close, x.settle),
                             'high': np.where(tr, x.high, np.where(tr, x.close, x.settle)), 'low': np.where(tr, x.low, np.where(tr, x.close, x.settle))})
    new = d >= dt.date(2024, 7, 8); mon = d.strftime('%b').upper()
    url = (f'https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{d:%Y%m%d}_F_0000.csv.zip' if new else
           f'https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{d.year}/{mon}/fo{d:%d}{mon}{d.year}bhav.csv.zip')
    b = get(url)
    if not b: return None
    z = zipfile.ZipFile(io.BytesIO(b)); x = pd.read_csv(z.open(z.namelist()[0]))
    if new:
        x = x.rename(columns={'FinInstrmTp': 'INSTRUMENT', 'TckrSymb': 'SYMBOL', 'XpryDt': 'EXPIRY_DT', 'OptnTp': 'OPTION_TYP', 'ClsPric': 'CLOSE',
                              'StrkPric': 'STRIKE_PR', 'OpnPric': 'OPEN', 'HghPric': 'HIGH', 'LwPric': 'LOW', 'SttlmPric': 'SETTLE_PR', 'TtlTradgVol': 'CONTRACTS'})
        x['INSTRUMENT'] = x.INSTRUMENT.map({'STF': 'FUTSTK', 'IDF': 'FUTIDX', 'STO': 'OPTSTK', 'IDO': 'OPTIDX'})
    x.columns = [c.strip() for c in x.columns]
    x = x[(x.INSTRUMENT == 'OPTIDX') & (x.SYMBOL.astype(str).str.strip() == 'NIFTY')].copy()
    if not len(x): return None
    for c in ('OPEN', 'HIGH', 'LOW', 'CLOSE', 'SETTLE_PR', 'CONTRACTS', 'STRIKE_PR'): x[c] = pd.to_numeric(x[c], errors='coerce').fillna(0)
    tr = x.CONTRACTS > 0
    return pd.DataFrame({'exp': pd.to_datetime(x.EXPIRY_DT, errors='coerce', dayfirst=not new).dt.date, 'type': x.OPTION_TYP.astype(str).str[0],
                         'K': x.STRIKE_PR, 'open': np.where(tr & (x.OPEN > 0), x.OPEN, np.nan), 'px': np.where(tr, x.CLOSE, x.SETTLE_PR),
                         'high': np.where(tr, x.HIGH, np.where(tr, x.CLOSE, x.SETTLE_PR)), 'low': np.where(tr, x.LOW, np.where(tr, x.CLOSE, x.SETTLE_PR))})


def ix(n):
    d = pd.read_csv(os.path.join(R, 'data', f'{n}.csv'), parse_dates=['date']).set_index('date').sort_index()
    return d[~d.index.duplicated()].dropna(subset=['close'])


def leg(b, e, t, k):
    y = b[(b.exp == e) & (b.type == t) & (b.K == k)]
    return None if not len(y) else y.iloc[0]


state = json.load(open(ST)) if os.path.exists(ST) else {'last_done': (pd.Timestamp(START) - pd.Timedelta(days=1)).strftime('%Y-%m-%d'),
                                                         'next_exp': PREV_EXP, 'books': {'A': None, 'B': None}, 'notes': []}
J = pd.read_csv(JR).to_dict('records') if os.path.exists(JR) else []
DAYS = pd.read_csv(DY).to_dict('records') if os.path.exists(DY) else []
N = ix('NIFTY'); V = ix('INDIAVIX').close
today = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)).date()
d = pd.Timestamp(state['last_done']).date() + dt.timedelta(days=1)
while d <= today:
    if d.weekday() >= 5: d += dt.timedelta(days=1); continue
    b = bhav(d)
    if b is None:
        if pd.Timestamp(d) not in N.index and d < today:  # NIFTY.csv mein bhi nahi = chhutti
            state['last_done'] = str(d); d += dt.timedelta(days=1); continue
        if d < today - dt.timedelta(days=10):
            state['notes'].append(f'{d}: bhavcopy nahi mila (10+ din) — din chhoda'); state['last_done'] = str(d); d += dt.timedelta(days=1); continue
        print('bhavcopy abhi nahi', d, '— agle run mein dobara'); break
    ts = pd.Timestamp(d)
    if ts not in N.index: print('NIFTY.csv mein', d, 'abhi nahi — baad mein'); break
    exps = sorted(e for e in b.exp.dropna().unique() if e >= d)
    near = exps[0] if exps else None
    if state['next_exp'] is None: state['next_exp'] = str(near)  # pehla din: is cycle ki expiry ka intezaar
    ne = pd.Timestamp(state['next_exp']).date()
    entry_day = d > ne
    nrow = N.loc[ts]
    # ---- manage open books ----
    for bk in ('A', 'B'):
        pos = state['books'][bk]
        if not pos: continue
        e = pd.Timestamp(pos['exp']).date()
        legs = [leg(b, e, t, k) for t, k in (('C', pos['sCE']), ('P', pos['sPE']), ('C', pos['bCE']), ('P', pos['bPE']))]
        cr = pos['credit']; out = None
        if d >= e:
            St = float(nrow.close)
            v = max(St - pos['sCE'], 0) - max(St - pos['bCE'], 0) + max(pos['sPE'] - St, 0) - max(pos['bPE'] - St, 0)
            out = (v, 'expiry')
        elif all(l is not None for l in legs):
            val = legs[0].px + legs[1].px - legs[2].px - legs[3].px
            if bk == 'B':
                up = float(nrow.high) - pos['S'] >= pos['S'] - float(nrow.low)
                worst = (legs[0].high - legs[2].low + legs[1].px - legs[3].px) if up else (legs[1].high - legs[3].low + legs[0].px - legs[2].px)
                if min(worst, HEDGE) - cr >= cr * SL / 100: out = (cr * (1 + SL / 100) + 4 * SLIP, 'SL (din ke andar)')
            if out is None and cr - val >= cr * TGT / 100: out = (val + 4 * SLIP, 'target')
            if out is None and val - cr >= cr * SL / 100: out = (val + 4 * SLIP, 'SL')
            pos['last_val'] = round(val, 2); pos['last_date'] = str(d)
        if out:
            pts = cr - out[0]
            J.append(dict(book=bk, entry=pos['entry'], exp=pos['exp'], exit_date=str(d), how=out[1], vix=pos['vix'], S=pos['S'], sCE=pos['sCE'], sPE=pos['sPE'],
                          bCE=pos['bCE'], bPE=pos['bPE'], credit=cr, exit_val=round(out[0], 2), pts=round(pts, 2), rs=round(pts * LOT - COST, 0)))
            state['books'][bk] = None
        else:
            DAYS.append(dict(date=str(d), book=bk, exp=pos['exp'], credit=cr, value=pos.get('last_val'), open_pts=round(cr - (pos.get('last_val') or cr), 2),
                             open_rs=round((cr - (pos.get('last_val') or cr)) * LOT, 0)))
    # ---- entry ----
    if entry_day:
        state['next_exp'] = str(near)
        vv = V[V.index < ts]
        vix = float(vv.iloc[-1]) if len(vv) else np.nan
        Sx = float(nrow.open); cal = (pd.Timestamp(near) - ts).days
        if not (VMIN <= vix <= VMAX):
            state['notes'].append(f'{d}: VIX {vix:.2f} — hafta chhoda')
        else:
            em = Sx * vix / 100 * math.sqrt(cal / 365)
            sc = math.ceil((Sx + K * em) / STEP) * STEP; sp = math.floor((Sx - K * em) / STEP) * STEP
            bc, bp = sc + HEDGE, sp - HEDGE
            legs = [leg(b, near, t, k) for t, k in (('C', sc), ('P', sp), ('C', bc), ('P', bp))]
            if any(l is None for l in legs):
                state['notes'].append(f'{d}: strike data nahi — hafta chhoda')
            else:
                p = [l.open if np.isfinite(l.open) else l.px for l in legs]
                cr = round(p[0] + p[1] - p[2] - p[3] - 4 * SLIP, 2)
                if cr > 0:
                    for bk in ('A', 'B'):
                        state['books'][bk] = dict(entry=str(d), exp=str(near), vix=round(vix, 2), S=round(Sx, 1), sCE=sc, sPE=sp, bCE=bc, bPE=bp,
                                                  credit=cr, legs_open=[round(x, 2) for x in p])
                    # same-day close check (Pine bhi entry candle ka close dekhta hai) -> next loop iteration handles from tomorrow; do today's here
                    val = legs[0].px + legs[1].px - legs[2].px - legs[3].px
                    for bk in ('A', 'B'):
                        pos = state['books'][bk]; out = None
                        if bk == 'B':
                            up = float(nrow.high) - Sx >= Sx - float(nrow.low)
                            worst = (legs[0].high - legs[2].low + legs[1].px - legs[3].px) if up else (legs[1].high - legs[3].low + legs[0].px - legs[2].px)
                            if min(worst, HEDGE) - cr >= cr * SL / 100: out = (cr * (1 + SL / 100) + 4 * SLIP, 'SL (din ke andar)')
                        if out is None and cr - val >= cr * TGT / 100: out = (val + 4 * SLIP, 'target')
                        if out is None and val - cr >= cr * SL / 100: out = (val + 4 * SLIP, 'SL')
                        pos['last_val'] = round(val, 2); pos['last_date'] = str(d)
                        if out:
                            pts = cr - out[0]
                            J.append(dict(book=bk, entry=pos['entry'], exp=pos['exp'], exit_date=str(d), how=out[1], vix=pos['vix'], S=pos['S'], sCE=sc, sPE=sp,
                                          bCE=bc, bPE=bp, credit=cr, exit_val=round(out[0], 2), pts=round(pts, 2), rs=round(pts * LOT - COST, 0)))
                            state['books'][bk] = None
                        else:
                            DAYS.append(dict(date=str(d), book=bk, exp=pos['exp'], credit=cr, value=round(val, 2), open_pts=round(cr - val, 2), open_rs=round((cr - val) * LOT, 0)))
    state['last_done'] = str(d)
    d += dt.timedelta(days=1); time.sleep(0.4)

state['notes'] = state['notes'][-30:]
json.dump(state, open(ST, 'w'), indent=1, default=str)
pd.DataFrame(J).to_csv(JR, index=False); pd.DataFrame(DAYS).to_csv(DY, index=False)
L = ['# CONDOR_FRIEND paper (dost ka Nifty iron condor, ASLI NSE bhaav) — ' + state['last_done'],
     'Paper hai, asli paisa nahi. Backtest 2019-26 (study/results/cf_condor_friend.md): dost ki settings NUKSAAN mein. Ye robot dekhta hai ki aage bhi waisa hi hai ya nahi.', '']
for bk, nm in (('A', 'A (close par check)'), ('B', 'B (SL din ke andar)')):
    pos = state['books'][bk]
    jj = [r for r in J if r['book'] == bk]
    tot = sum(r['rs'] for r in jj); w = sum(1 for r in jj if r['rs'] > 0)
    L.append(f'## Kitaab {nm}: band trades {len(jj)}, jeet {w}, kul Rs {tot:,.0f}')
    if pos:
        op = pos['credit'] - (pos.get('last_val') or pos['credit'])
        L.append(f'- KHULA: {pos["entry"]} se, expiry {pos["exp"]} | SELL {pos["sCE"]:.0f} CE / {pos["sPE"]:.0f} PE, BUY {pos["bCE"]:.0f} CE / {pos["bPE"]:.0f} PE | '
                 f'credit {pos["credit"]} pt | {pos.get("last_date")} close par value {pos.get("last_val")} -> {op:+.1f} pt (Rs {op * LOT:+,.0f})')
        L.append(f'- Target jab value <= {pos["credit"] * 0.4:.1f} pt; SL jab value >= {pos["credit"] * 2.5:.1f} pt')
    else:
        L.append(f'- Koi khula trade nahi. Agli entry: expiry {state["next_exp"]} ke agle trading din, open par.')
    for r in jj[-5:]:
        L.append(f'  - {r["entry"]} -> {r["exit_date"]} {r["how"]}: credit {r["credit"]}, {r["pts"]:+.1f} pt, Rs {r["rs"]:+,.0f}')
if state['notes']: L += ['', 'Notes: ' + ' | '.join(state['notes'][-5:])]
open(MDF, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
