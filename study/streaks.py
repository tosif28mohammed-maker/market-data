"""STREAK STUDY (user 6 Nov 2026): लगातार कितनी candle green/red, उसके बाद क्या हुआ — हर शेयर, हर timeframe.
Green = close > open (candle color); close == open breaks the streak.
For every stock and timeframe:
  (A) run-length distribution (1,2,3..15+) vs chance (same stock, candle colors shuffled)
  (B) after k greens / k reds: P(next candle same color), next-1 and next-3 candle return (close->close),
      drift-adjusted (minus that stock's average), vs shuffled chance; daily/weekly also by era + ex-crisis
  (C) 'record = ceiling' test: learn each stock's max green/red streak in the 1st half, check 2nd half:
      how many stocks broke their record, and at k == own record does the streak stop more often than
      other stocks at the same k that still have room (k < their record)?
  (D) per stock: max streaks, current streak, own P(continue) at k>=3 -> data for the daily robot.
Usage: python study/streaks.py <group> ; groups: daily (1W,1D) | hourly (4H,3H,2H,1H) | m15 (45m,30m,15m) | m5 | m1
Liquidity D never (paper/avoid_liquidity_D.txt + liq_all.csv). Outputs study/results/streak_<group>_*.csv + .md
"""
import os, sys, glob, gzip, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'study', 'results'); os.makedirs(OUT, exist_ok=True)
G = sys.argv[1]
K = 10           # k = 1..9, 10 means 10+
ERAS = [('ALL', '1900', '2100'), ('2003-12', '2003-01-01', '2012-12-31'), ('2013-20', '2013-01-01', '2020-12-31'),
        ('2021-26', '2021-01-01', '2026-12-31'), ('Nov23-now', '2023-11-01', '2026-12-31'), ('ex-crisis', None, None)]
CRISIS = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
liq = pd.read_csv(os.path.join(R, 'study', 'results', 'liq_all.csv'))
BAD = set(liq.loc[liq.liquidity.astype(str).str[0] == 'D', 'symbol'])
av = os.path.join(R, 'paper', 'avoid_liquidity_D.txt')
if os.path.exists(av): BAD |= {l.strip() for l in open(av) if l.strip() and not l.startswith('#')}
LIQ = liq.set_index('symbol').liquidity.astype(str).str[0].to_dict()
rng = np.random.default_rng(7)


# ---------------- loaders -> dict tf -> list of (symbol, DataFrame[time, open, close]) ----------------
def per_day_group(d, n):
    """combine n consecutive intraday bars inside each session (last group may be shorter)."""
    d = d.copy(); d['day'] = d.time.dt.date; d['k'] = d.groupby('day').cumcount() // n
    g = d.groupby(['day', 'k'], sort=True)
    return pd.DataFrame({'time': g.time.last(), 'open': g.open.first(), 'close': g.close.last()}).reset_index(drop=True)


def load_daily():
    U = os.environ.get('U500', os.path.join(R, '..', 'u500'))
    files = glob.glob(f'{U}/u1000/daily/*.csv.gz') + glob.glob(f'{U}/u2000/daily/*.csv.gz')
    seen = set()
    for f in files:
        s = os.path.basename(f)[:-7]
        if s in BAD or s in seen: continue
        seen.add(s)
        d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['open', 'close']).drop_duplicates('date').sort_values('date')
        d = d[(d.open > 0) & (d.close > 0)]
        if len(d) < 300: continue
        r = (d.adj / d.close).values
        D = pd.DataFrame({'time': d.date.values, 'open': d.open.values * r, 'close': d.adj.values})
        W = D.set_index('time').resample('W-FRI').agg({'open': 'first', 'close': 'last'}).dropna().reset_index()
        yield s, {'1D': D, '1W': W}


def load_intra(sub, tfs):
    I = os.environ.get('INTRA', os.path.join(R, '..', 'ih'))
    for f in sorted(glob.glob(f'{I}/intra/{sub}/*.csv.gz')):
        s = os.path.basename(f)[:-7]
        if s in BAD or s.startswith('^'): continue
        d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['open', 'close']).drop_duplicates('time').sort_values('time')
        d = d[(d.open > 0) & (d.close > 0)].reset_index(drop=True)
        if len(d) < 200: continue
        yield s, {name: (d[['time', 'open', 'close']] if n == 1 else per_day_group(d, n)) for name, n in tfs}


def load_m1():
    import yfinance as yf, datetime as dt
    tc = [c for c in liq.columns if 'turn' in c.lower()]
    top = liq[liq.liquidity.astype(str).str[0] == 'A']
    top = top.sort_values(tc[0], ascending=False) if tc else top
    syms = [s for s in top.symbol if s not in BAD][:250]
    end = dt.date.today()
    for i in range(0, len(syms), 50):
        part = syms[i:i + 50]; frames = {s: [] for s in part}
        for w in range(4):
            e = end - dt.timedelta(days=7 * w); b = e - dt.timedelta(days=7)
            try:
                X = yf.download([f'{s}.NS' for s in part], start=b, end=e + dt.timedelta(days=1), interval='1m', group_by='ticker',
                                auto_adjust=False, progress=False, threads=True)
            except Exception as ex:
                print('m1 fail', ex); continue
            for s in part:
                try:
                    x = X[f'{s}.NS'][['Open', 'Close']].dropna()
                    frames[s].append(x)
                except Exception:
                    pass
        for s, fr in frames.items():
            if not fr: continue
            x = pd.concat(fr).sort_index(); x = x[~x.index.duplicated()]
            if len(x) < 500: continue
            yield s, {'1m': pd.DataFrame({'time': x.index.tz_localize(None) if x.index.tz is None else x.index.tz_convert('Asia/Kolkata').tz_localize(None),
                                          'open': x.Open.values, 'close': x.Close.values})}


# ---------------- core ----------------
def streak_arrays(o, c):
    sg = np.sign(c - o).astype(int)
    st = np.zeros(len(sg), int)
    for i in range(len(sg)):
        if sg[i] == 0: st[i] = 0
        elif i > 0 and sg[i] == sg[i - 1]: st[i] = st[i - 1] + sg[i]
        else: st[i] = sg[i]
    return sg, st


def runs(sg):
    out = {1: [], -1: []}; cur, n = 0, 0
    for v in sg:
        if v == cur and v != 0: n += 1
        else:
            if cur != 0: out[cur].append(n)
            cur, n = v, (1 if v != 0 else 0)
    return out  # last (open) run excluded


class Acc:
    def __init__(self, eras):
        self.e = eras
        z = lambda: np.zeros((len(eras), 2, K + 1))
        self.n, self.same, self.r1, self.r3, self.n3, self.shs, self.shn = z(), z(), z(), z(), z(), z(), z()
        self.rl = {1: np.zeros(17), -1: np.zeros(17)}; self.rls = {1: np.zeros(17), -1: np.zeros(17)}
        # record test
        self.rec = dict(stocks=0, broke_g=0, broke_r=0, at_g=0, at_g_same=0, room_g=0, room_g_same=0,
                        at_r=0, at_r_same=0, room_r=0, room_r_same=0, at_r_ret=0.0, room_r_ret=0.0, at_g_ret=0.0, room_g_ret=0.0)

    def add(self, D, tf):
        o, c, t = D.open.values, D.close.values, pd.to_datetime(D.time.values)
        if len(c) < 60: return None
        sg, st = streak_arrays(o, c)
        r1 = np.r_[c[1:] / c[:-1] - 1, np.nan] * 100
        r3 = np.r_[c[3:] / c[:-3] - 1, [np.nan] * 3] * 100
        r1 = np.where(np.abs(r1) > 40, np.nan, r1)
        mu1, mu3 = np.nanmean(r1), np.nanmean(r3)
        nxt = np.r_[sg[1:], 0]
        valid = np.r_[np.ones(len(sg) - 1, bool), False] & (st != 0) & ~np.isnan(r1)
        kk = np.minimum(np.abs(st), K); side = (st < 0).astype(int)   # 0 = green, 1 = red
        same = (nxt == np.sign(st)) & (nxt != 0)
        # shuffled control
        sgs = rng.permutation(sg); _, sts = streak_arrays(o * 0 + 1, 1 + sgs * 1.0)
        nxs = np.r_[sgs[1:], 0]; vs = np.r_[np.ones(len(sgs) - 1, bool), False] & (sts != 0)
        ks = np.minimum(np.abs(sts), K); sds = (sts < 0).astype(int); sms = (nxs == np.sign(sts)) & (nxs != 0)
        for ei, (en, a, b) in enumerate(self.e):
            if en == 'ex-crisis':
                m = np.ones(len(t), bool)
                for x, y in CRISIS: m &= ~((t >= np.datetime64(x)) & (t <= np.datetime64(y)))
            else:
                m = (t >= np.datetime64(a)) & (t <= np.datetime64(b))
            v = valid & m
            np.add.at(self.n[ei], (side[v], kk[v]), 1)
            np.add.at(self.same[ei], (side[v], kk[v]), same[v])
            np.add.at(self.r1[ei], (side[v], kk[v]), r1[v] - mu1)
            v3 = v & ~np.isnan(r3)
            np.add.at(self.r3[ei], (side[v3], kk[v3]), r3[v3] - mu3); np.add.at(self.n3[ei], (side[v3], kk[v3]), 1)
            vv = vs & m
            np.add.at(self.shn[ei], (sds[vv], ks[vv]), 1); np.add.at(self.shs[ei], (sds[vv], ks[vv]), sms[vv])
        for sgn in (1, -1):
            for L in runs(sg)[sgn]: self.rl[sgn][min(L, 16)] += 1
            for L in runs(sgs)[sgn]: self.rls[sgn][min(L, 16)] += 1
        # record test: learn on 1st half, test on 2nd half
        h = len(sg) // 2
        mg, mr = st[:h].max(), -st[:h].min()
        rec = self.rec; rec['stocks'] += 1
        s2, n2, r2 = st[h:-1], nxt[h:-1], r1[h:-1]
        rec['broke_g'] += int(s2.max() > mg); rec['broke_r'] += int(-s2.min() > mr)
        for k in range(2, 13):
            at_g = s2 == k
            if k == mg: rec['at_g'] += at_g.sum(); rec['at_g_same'] += (n2[at_g] == 1).sum(); rec['at_g_ret'] += np.nansum(r2[at_g] - mu1)
            elif k < mg: rec['room_g'] += at_g.sum(); rec['room_g_same'] += (n2[at_g] == 1).sum(); rec['room_g_ret'] += np.nansum(r2[at_g] - mu1)
            at_r = s2 == -k
            if k == mr: rec['at_r'] += at_r.sum(); rec['at_r_same'] += (n2[at_r] == -1).sum(); rec['at_r_ret'] += np.nansum(r2[at_r] - mu1)
            elif k < mr: rec['room_r'] += at_r.sum(); rec['room_r_same'] += (n2[at_r] == -1).sum(); rec['room_r_ret'] += np.nansum(r2[at_r] - mu1)
        # per stock line (D)
        g3 = (st >= 3) & valid; r3m = (st <= -3) & valid
        return dict(tf=tf, bars=len(sg), first=str(t[0])[:16], last=str(t[-1])[:16], max_green=int(st.max()), max_red=int(-st.min()),
                    max_green_date=str(t[st.argmax()])[:16], max_red_date=str(t[st.argmin()])[:16], now=int(st[-1]),
                    green_pct=round((sg == 1).mean() * 100, 1),
                    p_cont_g3=round(same[g3].mean() * 100, 1) if g3.sum() >= 10 else np.nan, n_g3=int(g3.sum()),
                    p_cont_r3=round(same[r3m].mean() * 100, 1) if r3m.sum() >= 10 else np.nan, n_r3=int(r3m.sum()),
                    ret_after_r3=round(np.nanmean(r1[r3m] - mu1), 3) if r3m.sum() >= 10 else np.nan,
                    ret_after_g3=round(np.nanmean(r1[g3] - mu1), 3) if g3.sum() >= 10 else np.nan)

    def tables(self, tf):
        rows = []
        for ei, (en, _, _) in enumerate(self.e):
            for sd, nm in ((0, 'green'), (1, 'red')):
                for k in range(1, K + 1):
                    n = self.n[ei, sd, k]
                    if n < 30: continue
                    rows.append(dict(tf=tf, era=en, after=f"{k if k < K else str(K) + '+'} {nm}", k=k, side=nm, n=int(n),
                                     p_next_same=round(self.same[ei, sd, k] / n * 100, 1),
                                     chance_p_same=round(self.shs[ei, sd, k] / max(self.shn[ei, sd, k], 1) * 100, 1),
                                     next1_ret_adj=round(self.r1[ei, sd, k] / n, 3),
                                     next3_ret_adj=round(self.r3[ei, sd, k] / max(self.n3[ei, sd, k], 1), 3)))
        T = pd.DataFrame(rows)
        if len(T): T['vs_chance'] = (T.p_next_same - T.chance_p_same).round(1)
        RL = pd.DataFrame({'len': [*range(1, 16), '16+'],
                           'green_runs': self.rl[1][1:17], 'green_chance': self.rls[1][1:17],
                           'red_runs': self.rl[-1][1:17], 'red_chance': self.rls[-1][1:17]})
        RL.insert(0, 'tf', tf)
        rc = self.rec; f = lambda a, b: round(a / b * 100, 1) if b else np.nan
        REC = dict(tf=tf, stocks=rc['stocks'], pct_broke_green_record=f(rc['broke_g'], rc['stocks']), pct_broke_red_record=f(rc['broke_r'], rc['stocks']),
                   at_green_record_n=rc['at_g'], p_continue_at_green_record=f(rc['at_g_same'], rc['at_g']),
                   p_continue_green_room_left=f(rc['room_g_same'], rc['room_g']),
                   at_red_record_n=rc['at_r'], p_continue_at_red_record=f(rc['at_r_same'], rc['at_r']),
                   p_continue_red_room_left=f(rc['room_r_same'], rc['room_r']),
                   ret_after_red_record=round(rc['at_r_ret'] / max(rc['at_r'], 1), 3), ret_after_red_room=round(rc['room_r_ret'] / max(rc['room_r'], 1), 3),
                   ret_after_green_record=round(rc['at_g_ret'] / max(rc['at_g'], 1), 3), ret_after_green_room=round(rc['room_g_ret'] / max(rc['room_g'], 1), 3))
        return T, RL, REC


GROUPS = {'daily': (['1W', '1D'], lambda: load_daily(), ERAS),
          'hourly': (['4H', '3H', '2H', '1H'], lambda: load_intra('h1', [('4H', 4), ('3H', 3), ('2H', 2), ('1H', 1)]),
                     [('ALL', '1900', '2100'), ('half1', '2023-11-01', '2025-04-30'), ('half2', '2025-05-01', '2026-12-31')]),
          'm15': (['45m', '30m', '15m'], lambda: load_intra('m15', [('45m', 3), ('30m', 2), ('15m', 1)]), [('ALL', '1900', '2100')]),
          'm5': (['5m'], lambda: load_intra('m5_all', [('5m', 1)]), [('ALL', '1900', '2100')]),
          'm1': (['1m'], lambda: load_m1(), [('ALL', '1900', '2100')])}
tfs, loader, eras = GROUPS[G]
acc = {tf: Acc(eras) for tf in tfs}; per = []
LIM = int(os.environ.get('LIMIT', '0'))
for i, (s, frames) in enumerate(loader()):
    if LIM and i >= LIM: break
    for tf, D in frames.items():
        r = acc[tf].add(D.reset_index(drop=True), tf)
        if r: r.update(symbol=s, liq=LIQ.get(s, '?')); per.append(r)
    if i % 200 == 0: print(G, i, s, flush=True)
TT, RR, EE = [], [], []
for tf in tfs:
    T, RL, REC = acc[tf].tables(tf); TT.append(T); RR.append(RL); EE.append(REC)
pd.concat(TT).to_csv(f'{OUT}/streak_{G}_cond.csv', index=False)
pd.concat(RR).to_csv(f'{OUT}/streak_{G}_runs.csv', index=False)
pd.DataFrame(EE).to_csv(f'{OUT}/streak_{G}_record.csv', index=False)
P = pd.DataFrame(per); P.to_csv(f'{OUT}/streak_{G}_perstock.csv.gz', index=False)

# short markdown
L = [f'# Streak study — {G}', '']
for tf, T, RL, REC in zip(tfs, TT, RR, EE):
    p = P[P.tf == tf]
    L += [f'## {tf}: {REC["stocks"]} शेयर, औसत {p.bars.mean():.0f} candles ({p["first"].min()} से)', '']
    a = T[T.era == 'ALL'][['after', 'n', 'p_next_same', 'chance_p_same', 'vs_chance', 'next1_ret_adj', 'next3_ret_adj']]
    L += ['अगली candle उसी रंग की (%), किस्मत से फ़र्क, अगली 1/3 candle return (% , औसत घटाकर):', '```', a.to_string(index=False), '```']
    L += [f"Max streak (median शेयर): green {p.max_green.median():.0f}, red {p.max_red.median():.0f}; सबसे लंबी green {p.max_green.max()} ({p.loc[p.max_green.idxmax(), 'symbol']}), red {p.max_red.max()} ({p.loc[p.max_red.idxmax(), 'symbol']})",
          f"Record test: 2nd half में {REC['pct_broke_green_record']}% शेयरों ने green record तोड़ा, {REC['pct_broke_red_record']}% ने red; "
          f"record पर पहुँचकर अगली candle उसी रंग: green {REC['p_continue_at_green_record']}% (बाकी जगह {REC['p_continue_green_room_left']}%), "
          f"red {REC['p_continue_at_red_record']}% (बाकी {REC['p_continue_red_room_left']}%); red record के बाद return {REC['ret_after_red_record']} बनाम {REC['ret_after_red_room']}", '']
    if len(eras) > 1:
        e = T[T.k.isin([3, 5, 7])].pivot_table(index='after', columns='era', values='vs_chance')
        L += ['दौर-वार (किस्मत से फ़र्क, % अंक):', '```', e.to_string(), '```', '']
open(f'{OUT}/streak_{G}.md', 'w').write('\n'.join(L))
print('\n'.join(L))
