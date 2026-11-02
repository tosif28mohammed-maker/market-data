"""Each stock's own trend periods (user, 2 Nov 2026: Reliance changed character in 2017, again mid-2020, again 2024, now up-down).
Weekly log price is cut into straight-line pieces (optimal segmentation, min 26 weeks per piece, penalty against too many cuts).
Each piece: start, end, yearly trend %, volatility %, biggest fall inside, label (तेज़ तेज़ी / तेज़ी / sideways / मंदी / तेज़ मंदी).
Also a real-time version (no hindsight): trailing 52-week trend % and straightness (R^2) for every week.
Usage: python study/regimes.py out.pkl [penalty] dir1 [dir2 ...]   (penalty default 8)"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; PEN = float(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].replace('.', '').isdigit() else 8.0   # 8 matched the user's own reading of the Reliance chart (2017, 2020, 2024)
DIRS = [a for a in sys.argv[2:] if not a.replace('.', '').isdigit()]; MINW = 26
def segment(y):
    n = len(y); t = np.arange(n, dtype=float)
    c1 = np.r_[0, np.cumsum(t)]; c2 = np.r_[0, np.cumsum(t * t)]; cy = np.r_[0, np.cumsum(y)]; cyy = np.r_[0, np.cumsum(y * y)]; cty = np.r_[0, np.cumsum(t * y)]
    var = np.var(np.diff(y)) if n > 2 else 1e-4; beta = PEN * var * np.log(n) * 4   # penalty per extra piece
    F = np.full(n + 1, np.inf); F[0] = -beta; back = np.zeros(n + 1, int)
    for j in range(MINW, n + 1):
        i = np.arange(0, j - MINW + 1); m = j - i
        St = c1[j] - c1[i]; Stt = c2[j] - c2[i]; Sy = cy[j] - cy[i]; Syy = cyy[j] - cyy[i]; Sty = cty[j] - cty[i]
        vt = Stt - St * St / m; cov = Sty - St * Sy / m; vy = Syy - Sy * Sy / m
        sse = vy - np.where(vt > 0, cov * cov / vt, 0)
        cand = F[i] + sse + beta; k = int(np.argmin(cand)); F[j] = cand[k]; back[j] = i[k]
    cuts = []; j = n
    while j > 0: cuts.append(j); j = back[j]
    return sorted(cuts)
def label(g):
    return 'तेज़ तेज़ी' if g >= 30 else 'तेज़ी' if g >= 10 else 'sideways' if g > -10 else 'मंदी' if g > -30 else 'तेज़ मंदी'
files = []
for D in DIRS: files += glob.glob(os.path.join(D, '*.csv.gz'))
SEG = []; RT = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').sort_values('date')
    d = d[d.close > 0]; r = d.close.pct_change(); bad = np.flatnonzero((r.abs() > 0.25).values)
    if len(bad): d = d.iloc[bad[-1]:]
    w = d.set_index('date').close.resample('W-FRI').last().dropna()
    if len(w) < 104: continue
    y = np.log(w.values); cuts = segment(y); a = 0
    for b in cuts:
        seg = y[a:b]; t = np.arange(len(seg)); slope = np.polyfit(t, seg, 1)[0]; g = (np.exp(slope * 52) - 1) * 100
        p = np.exp(seg); dd = (p / np.maximum.accumulate(p) - 1).min() * 100
        SEG.append(dict(stock=s, start=w.index[a].date(), end=w.index[b - 1].date(), weeks=b - a, trend_pct=g, vol_pct=np.std(np.diff(seg)) * np.sqrt(52) * 100 if len(seg) > 2 else np.nan,
                        max_fall=dd, start_px=p[0], end_px=p[-1], label=label(g)))
        a = b
    # real-time trailing 52-week trend and straightness
    ys = pd.Series(y, index=w.index); tt = np.arange(52, dtype=float)
    for k in range(52, len(y)):
        seg = y[k - 52:k]; sl, ic = np.polyfit(tt, seg, 1); fit = sl * tt + ic; r2 = 1 - ((seg - fit) ** 2).sum() / max(((seg - seg.mean()) ** 2).sum(), 1e-12)
        RT.append((s, w.index[k - 1], (np.exp(sl * 52) - 1) * 100, r2))
    print(s, len(cuts), flush=True)
S = pd.DataFrame(SEG); R = pd.DataFrame(RT, columns=['stock', 'week', 'trail_trend_pct', 'trail_r2'])
pd.to_pickle(dict(SEG=S, RT=R), OUT); print('pieces', len(S))
