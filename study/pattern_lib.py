"""Pattern / indicator / famous-trader signal library (daily OHLCV). Every function returns {name: (direction, bool array)}.
direction +1 = bullish signal (expect up), -1 = bearish. Signal is known at the CLOSE of day t (trade from the next open).
Catalog (user, 2 Nov 2026 night): candlesticks (Nison), chart patterns (Bulkowski), indicators, famous traders' setups
(Turtle, Darvas, Minervini, Weinstein, O'Neil, Qullamaggie, Connors, Raschke, Crabel, Larry Williams, Wyckoff, Livermore, PTJ),
popular Indian methods (Supertrend 10,3; 44-MA; 20/50 EMA; Camarilla/CPR pivots), and cycles."""
import numpy as np, pandas as pd

# ---------------- helpers ----------------
def sma(x, n): return x.rolling(n).mean()
def ema(x, n): return x.ewm(span=n, adjust=False).mean()
def rsi(c, n=14):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))
def atr(h, l, c, n=14):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()
def cross_up(a, b): return (a > b) & (a.shift() <= b.shift())
def cross_dn(a, b): return (a < b) & (a.shift() >= b.shift())
def B(x): return np.asarray(pd.Series(x).fillna(False).astype(bool).values)

def supertrend(h, l, c, n=10, m=3.0):
    a = atr(h, l, c, n).values; hl2 = ((h + l) / 2).values; cv = c.values; N = len(c)
    ub = hl2 + m * a; lb = hl2 - m * a; fu = ub.copy(); fl = lb.copy(); dirn = np.ones(N)
    for i in range(1, N):
        fu[i] = ub[i] if (ub[i] < fu[i - 1] or cv[i - 1] > fu[i - 1]) else fu[i - 1]
        fl[i] = lb[i] if (lb[i] > fl[i - 1] or cv[i - 1] < fl[i - 1]) else fl[i - 1]
        if dirn[i - 1] == 1: dirn[i] = -1 if cv[i] < fl[i] else 1
        else: dirn[i] = 1 if cv[i] > fu[i] else -1
    return pd.Series(dirn, index=c.index)

def psar(h, l, af0=0.02, afmax=0.2):
    hv, lv = h.values, l.values; N = len(hv); d = np.ones(N); sar = np.zeros(N)
    if N < 3: return pd.Series(d, index=h.index)
    up = True; ep = hv[0]; s = lv[0]; af = af0
    for i in range(1, N):
        s = s + af * (ep - s)
        if up:
            s = min(s, lv[i - 1], lv[i - 2] if i > 1 else lv[i - 1])
            if lv[i] < s: up = False; s = ep; ep = lv[i]; af = af0
            elif hv[i] > ep: ep = hv[i]; af = min(af + af0, afmax)
        else:
            s = max(s, hv[i - 1], hv[i - 2] if i > 1 else hv[i - 1])
            if hv[i] > s: up = True; s = ep; ep = hv[i]; af = af0
            elif lv[i] < ep: ep = lv[i]; af = min(af + af0, afmax)
        d[i] = 1 if up else -1; sar[i] = s
    return pd.Series(d, index=h.index)

def adx(h, l, c, n=14):
    upm = h.diff(); dnm = -l.diff()
    pdm = np.where((upm > dnm) & (upm > 0), upm, 0.0); ndm = np.where((dnm > upm) & (dnm > 0), dnm, 0.0)
    a = atr(h, l, c, n); pdi = 100 * pd.Series(pdm, index=h.index).ewm(alpha=1 / n, adjust=False).mean() / a
    ndi = 100 * pd.Series(ndm, index=h.index).ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean(), pdi, ndi

def zigzag(c, thr):
    piv = []; mode = 0; ei = 0; ep = c[0]
    for i in range(1, len(c)):
        p = c[i]
        if mode == 0:
            if p >= ep * (1 + thr): piv.append((ei, ep, 'L', i)); mode = 1; ei, ep = i, p
            elif p <= ep * (1 - thr): piv.append((ei, ep, 'H', i)); mode = -1; ei, ep = i, p
            continue
        if mode == 1:
            if p > ep: ei, ep = i, p
            elif p <= ep * (1 - thr): piv.append((ei, ep, 'H', i)); mode = -1; ei, ep = i, p
        else:
            if p < ep: ei, ep = i, p
            elif p >= ep * (1 + thr): piv.append((ei, ep, 'L', i)); mode = 1; ei, ep = i, p
    return piv

# ---------------- the catalog ----------------
def signals(d):
    """d: DataFrame with open, high, low, close, volume (date index). Returns dict name -> (dir, bool np.array)."""
    o, h, l, c, v = d.open, d.high, d.low, d.close, d.volume.fillna(0)
    N = len(c); S = {}
    body = (c - o); rng = (h - l).replace(0, np.nan); ab = body.abs(); top = h - np.maximum(o, c); bot = np.minimum(o, c) - l
    a14 = atr(h, l, c, 14); m10 = sma(c, 10); m20 = sma(c, 20); m50 = sma(c, 50); m150 = sma(c, 150); m200 = sma(c, 200)
    downtrend = c < m10; uptrend = c > m10
    longb = ab > 0.6 * rng; smallb = ab < 0.3 * rng
    avgb = ab.rolling(10).mean()
    # ===== A. Candlesticks (Steve Nison) =====
    doji = ab <= 0.1 * rng
    S['C01 Doji (नीचे के trend में)'] = (1, B(doji & downtrend))
    S['C02 Doji (ऊपर के trend में)'] = (-1, B(doji & uptrend))
    S['C03 Dragonfly doji'] = (1, B(doji & (top <= 0.1 * rng) & (bot >= 0.6 * rng) & downtrend))
    S['C04 Gravestone doji'] = (-1, B(doji & (bot <= 0.1 * rng) & (top >= 0.6 * rng) & uptrend))
    S['C05 Long-legged doji'] = (1, B(doji & (top >= 0.35 * rng) & (bot >= 0.35 * rng) & downtrend))
    hammer = (bot >= 2 * ab) & (top <= 0.25 * ab.clip(lower=1e-9) + 0.1 * rng) & (ab > 0)
    S['C06 Hammer'] = (1, B(hammer & downtrend))
    S['C07 Hanging man'] = (-1, B(hammer & uptrend))
    inv = (top >= 2 * ab) & (bot <= 0.1 * rng) & (ab > 0)
    S['C08 Inverted hammer'] = (1, B(inv & downtrend))
    S['C09 Shooting star'] = (-1, B(inv & uptrend))
    S['C10 Bullish marubozu'] = (1, B((body > 0) & (ab >= 0.95 * rng) & (ab > 1.5 * avgb)))
    S['C11 Bearish marubozu'] = (-1, B((body < 0) & (ab >= 0.95 * rng) & (ab > 1.5 * avgb)))
    S['C12 Spinning top (नीचे trend)'] = (1, B(smallb & (top > ab) & (bot > ab) & downtrend))
    pb, po, pc_ = body.shift(), o.shift(), c.shift()
    S['C13 Bullish engulfing'] = (1, B((pb < 0) & (body > 0) & (o <= pc_) & (c >= po) & downtrend.shift()))
    S['C14 Bearish engulfing'] = (-1, B((pb > 0) & (body < 0) & (o >= pc_) & (c <= po) & uptrend.shift()))
    S['C15 Piercing line'] = (1, B((pb < 0) & longb.shift() & (o < l.shift()) & (c > (po + pc_) / 2) & (c < po)))
    S['C16 Dark cloud cover'] = (-1, B((pb > 0) & longb.shift() & (o > h.shift()) & (c < (po + pc_) / 2) & (c > po)))
    harami_in = (np.maximum(o, c) < np.maximum(po, pc_)) & (np.minimum(o, c) > np.minimum(po, pc_))
    S['C17 Bullish harami'] = (1, B((pb < 0) & longb.shift() & harami_in & downtrend.shift()))
    S['C18 Bearish harami'] = (-1, B((pb > 0) & longb.shift() & harami_in & uptrend.shift()))
    S['C19 Bullish harami cross'] = (1, B((pb < 0) & longb.shift() & harami_in & doji & downtrend.shift()))
    S['C20 Tweezer bottom'] = (1, B(((l - l.shift()).abs() <= 0.002 * c) & (pb < 0) & (body > 0) & downtrend.shift()))
    S['C21 Tweezer top'] = (-1, B(((h - h.shift()).abs() <= 0.002 * c) & (pb > 0) & (body < 0) & uptrend.shift()))
    b2, o2, c2 = body.shift(2), o.shift(2), c.shift(2)
    star_small = (ab.shift() <= 0.3 * ab.shift(2))
    S['C22 Morning star'] = (1, B((b2 < 0) & longb.shift(2) & star_small & (np.maximum(o.shift(), c.shift()) < c2) & (body > 0) & (c > (o2 + c2) / 2)))
    S['C23 Evening star'] = (-1, B((b2 > 0) & longb.shift(2) & star_small & (np.minimum(o.shift(), c.shift()) > c2) & (body < 0) & (c < (o2 + c2) / 2)))
    S['C24 Morning doji star'] = (1, B((b2 < 0) & longb.shift(2) & doji.shift() & (h.shift() < c2) & (body > 0) & (c > (o2 + c2) / 2)))
    S['C25 Evening doji star'] = (-1, B((b2 > 0) & longb.shift(2) & doji.shift() & (l.shift() > c2) & (body < 0) & (c < (o2 + c2) / 2)))
    w3 = (body > 0) & (body.shift() > 0) & (body.shift(2) > 0) & (c > c.shift()) & (c.shift() > c.shift(2)) & (o > o.shift()) & (o < c.shift()) & (top < 0.25 * ab) & (top.shift() < 0.25 * ab.shift())
    S['C26 Three white soldiers'] = (1, B(w3))
    b3 = (body < 0) & (body.shift() < 0) & (body.shift(2) < 0) & (c < c.shift()) & (c.shift() < c.shift(2)) & (o < o.shift()) & (o > c.shift()) & (bot < 0.25 * ab)
    S['C27 Three black crows'] = (-1, B(b3))
    S['C28 Three inside up'] = (1, B(pd.Series(S['C17 Bullish harami'][1], index=c.index).shift().fillna(False) & (c > c.shift()) & (c > o.shift(2))))
    S['C29 Three inside down'] = (-1, B(pd.Series(S['C18 Bearish harami'][1], index=c.index).shift().fillna(False) & (c < c.shift()) & (c < o.shift(2))))
    S['C30 Three outside up'] = (1, B(pd.Series(S['C13 Bullish engulfing'][1], index=c.index).shift().fillna(False) & (c > c.shift())))
    S['C31 Three outside down'] = (-1, B(pd.Series(S['C14 Bearish engulfing'][1], index=c.index).shift().fillna(False) & (c < c.shift())))
    r3m = (body.shift(4) > 0) & longb.shift(4)
    for k in (1, 2, 3): r3m &= smallb.shift(k) & (h.shift(k) <= h.shift(4)) & (l.shift(k) >= l.shift(4))
    S['C32 Rising three methods'] = (1, B(r3m & (body > 0) & (c > c.shift(4))))
    f3m = (body.shift(4) < 0) & longb.shift(4)
    for k in (1, 2, 3): f3m &= smallb.shift(k) & (h.shift(k) <= h.shift(4)) & (l.shift(k) >= l.shift(4))
    S['C33 Falling three methods'] = (-1, B(f3m & (body < 0) & (c < c.shift(4))))
    S['C34 Abandoned baby bull'] = (1, B((b2 < 0) & doji.shift() & (h.shift() < l.shift(2)) & (l > h.shift()) & (body > 0)))
    S['C35 Abandoned baby bear'] = (-1, B((b2 > 0) & doji.shift() & (l.shift() > h.shift(2)) & (h < l.shift()) & (body < 0)))
    S['C36 Bullish kicker'] = (1, B((pb < 0) & longb.shift() & (o > po) & (body > 0) & longb))
    S['C37 Bearish kicker'] = (-1, B((pb > 0) & longb.shift() & (o < po) & (body < 0) & longb))
    S['C38 Bullish belt hold'] = (1, B((body > 0) & (o == l) & longb & downtrend))
    S['C39 Bearish belt hold'] = (-1, B((body < 0) & (o == h) & longb & uptrend))
    inside = (h < h.shift()) & (l > l.shift())
    S['C40 Inside bar (ऊपर trend)'] = (1, B(inside & (c > m50)))
    S['C41 Outside bar bullish'] = (1, B((h > h.shift()) & (l < l.shift()) & (c > h.shift())))
    S['C42 Outside bar bearish'] = (-1, B((h > h.shift()) & (l < l.shift()) & (c < l.shift())))
    S['C43 Bullish pin bar'] = (1, B((bot >= 0.66 * rng) & (l < l.rolling(10).min().shift())))
    S['C44 Bearish pin bar'] = (-1, B((top >= 0.66 * rng) & (h > h.rolling(10).max().shift())))
    S['C45 Key reversal up'] = (1, B((l < l.shift()) & (l <= l.rolling(20).min()) & (c > c.shift())))
    S['C46 Key reversal down'] = (-1, B((h > h.shift()) & (h >= h.rolling(20).max()) & (c < c.shift())))
    gup = l > h.shift(); gdn = h < l.shift()
    S['C47 Island reversal bottom'] = (1, B(gup & (gdn.shift(1) | gdn.shift(2) | gdn.shift(3) | gdn.shift(4) | gdn.shift(5))))
    S['C48 Island reversal top'] = (-1, B(gdn & (gup.shift(1) | gup.shift(2) | gup.shift(3) | gup.shift(4) | gup.shift(5))))
    S['C49 Breakaway gap up (20-दिन high के ऊपर)'] = (1, B(gup & (o > h.rolling(20).max().shift())))
    S['C50 Breakaway gap down'] = (-1, B(gdn & (o < l.rolling(20).min().shift())))
    S['C51 Exhaustion gap up (बहुत चढ़ने के बाद) → उल्टा'] = (-1, B(gup & (c.shift() / c.shift(20) - 1 > 0.25) & (c < o)))
    rng_ = h - l
    nr7 = rng_ <= rng_.rolling(7).min(); nr4 = rng_ <= rng_.rolling(4).min()
    S['C52 NR7 (Crabel) ऊपर trend'] = (1, B(nr7 & (c > m50)))
    S['C53 NR4 inside day (Crabel)'] = (1, B(nr4 & inside & (c > m50)))
    S['C54 Raschke 80-20 bull'] = (1, B((pb < 0) & (o.shift() >= h.shift() - 0.2 * rng.shift()) & (c.shift() <= l.shift() + 0.2 * rng.shift()) & (l < l.shift()) & (c > l.shift())))
    # ===== B. Indicators =====
    S['I01 Golden cross 50/200'] = (1, B(cross_up(m50, m200)))
    S['I02 Death cross 50/200'] = (-1, B(cross_dn(m50, m200)))
    S['I03 Close 200 DMA के ऊपर गया'] = (1, B(cross_up(c, m200)))
    S['I04 Close 200 DMA के नीचे गया'] = (-1, B(cross_dn(c, m200)))
    S['I05 20/50 EMA crossover up'] = (1, B(cross_up(ema(c, 20), ema(c, 50))))
    S['I06 9/21 EMA crossover up'] = (1, B(cross_up(ema(c, 9), ema(c, 21))))
    S['I07 9/21 EMA crossover down'] = (-1, B(cross_dn(ema(c, 9), ema(c, 21))))
    macd = ema(c, 12) - ema(c, 26); sig = ema(macd, 9)
    S['I08 MACD signal cross up'] = (1, B(cross_up(macd, sig)))
    S['I09 MACD signal cross down'] = (-1, B(cross_dn(macd, sig)))
    S['I10 MACD zero cross up'] = (1, B(cross_up(macd, pd.Series(0, index=c.index))))
    S['I11 MACD cross up नीचे zone में (<0)'] = (1, B(cross_up(macd, sig) & (macd < 0)))
    r = rsi(c, 14)
    S['I12 RSI 30 के ऊपर लौटा'] = (1, B(cross_up(r, pd.Series(30, index=c.index))))
    S['I13 RSI 70 के नीचे लौटा'] = (-1, B(cross_dn(r, pd.Series(70, index=c.index))))
    S['I14 RSI 50 cross up'] = (1, B(cross_up(r, pd.Series(50, index=c.index))))
    S['I15 RSI > 70 (momentum, ऊपर)'] = (1, B(cross_up(r, pd.Series(70, index=c.index))))
    # RSI divergence (bullish: price lower low over 20d, RSI higher low)
    ll20 = c <= c.rolling(20).min(); prevlow_r = r.rolling(20).min().shift(5)
    S['I16 RSI bullish divergence'] = (1, B(ll20 & (r > prevlow_r + 5) & (r < 40)))
    hh20 = c >= c.rolling(20).max(); prevhigh_r = r.rolling(20).max().shift(5)
    S['I17 RSI bearish divergence'] = (-1, B(hh20 & (r < prevhigh_r - 5) & (r > 60)))
    lo14 = l.rolling(14).min(); hi14 = h.rolling(14).max(); k = 100 * (c - lo14) / (hi14 - lo14).replace(0, np.nan); dk = k.rolling(3).mean()
    S['I18 Stochastic cross up (<20)'] = (1, B(cross_up(k, dk) & (k < 20)))
    S['I19 Stochastic cross down (>80)'] = (-1, B(cross_dn(k, dk) & (k > 80)))
    sd = c.rolling(20).std(); bu = m20 + 2 * sd; bl = m20 - 2 * sd; bw = (bu - bl) / m20
    S['I20 Bollinger निचली band के नीचे close'] = (1, B(c < bl))
    S['I21 Bollinger ऊपरी band के ऊपर close'] = (-1, B(c > bu))
    S['I22 Bollinger ऊपरी band breakout (momentum)'] = (1, B(cross_up(c, bu)))
    S['I23 Bollinger squeeze breakout up'] = (1, B((bw.shift() <= bw.rolling(120).min().shift()) & (c > bu)))
    S['I24 Bollinger squeeze breakout down'] = (-1, B((bw.shift() <= bw.rolling(120).min().shift()) & (c < bl)))
    kc_u = ema(c, 20) + 2 * a14; kc_l = ema(c, 20) - 2 * a14
    S['I25 Keltner breakout up'] = (1, B(cross_up(c, kc_u)))
    S['I26 Keltner breakdown'] = (-1, B(cross_dn(c, kc_l)))
    st = supertrend(h, l, c, 10, 3.0)
    S['I27 Supertrend (10,3) buy'] = (1, B((st == 1) & (st.shift() == -1)))
    S['I28 Supertrend (10,3) sell'] = (-1, B((st == -1) & (st.shift() == 1)))
    st7 = supertrend(h, l, c, 7, 2.0)
    S['I29 Supertrend (7,2) buy'] = (1, B((st7 == 1) & (st7.shift() == -1)))
    ps = psar(h, l)
    S['I30 Parabolic SAR buy'] = (1, B((ps == 1) & (ps.shift() == -1)))
    S['I31 Parabolic SAR sell'] = (-1, B((ps == -1) & (ps.shift() == 1)))
    ax, pdi, ndi = adx(h, l, c)
    S['I32 ADX>25 और +DI cross up'] = (1, B(cross_up(pdi, ndi) & (ax > 25)))
    S['I33 ADX>25 और -DI cross up'] = (-1, B(cross_up(ndi, pdi) & (ax > 25)))
    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2; kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
    spa = ((tenkan + kijun) / 2).shift(26); spb = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26); ctop = np.maximum(spa, spb); cbot = np.minimum(spa, spb)
    S['I34 Ichimoku TK cross बादल के ऊपर'] = (1, B(cross_up(tenkan, kijun) & (c > ctop)))
    S['I35 Ichimoku बादल के ऊपर निकला'] = (1, B(cross_up(c, ctop)))
    S['I36 Ichimoku बादल के नीचे गया'] = (-1, B(cross_dn(c, cbot)))
    hac = (o + h + l + c) / 4; hao = hac.copy()
    hv = hao.to_numpy(dtype=float, copy=True); hcv = hac.to_numpy(dtype=float); ov = o.to_numpy(dtype=float); cv = c.to_numpy(dtype=float)
    hv[0] = (ov[0] + cv[0]) / 2
    for i in range(1, N): hv[i] = (hv[i - 1] + hcv[i - 1]) / 2
    ha_green = pd.Series(hcv > hv, index=c.index)
    S['I37 Heikin-Ashi लाल→3 हरी'] = (1, B(ha_green & ha_green.shift() & ha_green.shift(2) & ~ha_green.shift(3).fillna(True).astype(bool)))
    S['I38 Heikin-Ashi हरी→3 लाल'] = (-1, B(~ha_green & ~ha_green.shift().fillna(True).astype(bool) & ~ha_green.shift(2).fillna(True).astype(bool) & ha_green.shift(3).fillna(False).astype(bool)))
    wr = -100 * (hi14 - c) / (hi14 - lo14).replace(0, np.nan)
    S['I39 Williams %R -80 के ऊपर लौटा'] = (1, B(cross_up(wr, pd.Series(-80, index=c.index))))
    tp = (h + l + c) / 3; cci = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True))
    S['I40 CCI -100 के ऊपर लौटा'] = (1, B(cross_up(cci, pd.Series(-100, index=c.index))))
    S['I41 CCI +100 के ऊपर गया (momentum)'] = (1, B(cross_up(cci, pd.Series(100, index=c.index))))
    au = 100 * h.rolling(26).apply(np.argmax, raw=True) / 25; ad = 100 * l.rolling(26).apply(np.argmin, raw=True) / 25
    S['I42 Aroon up cross'] = (1, B(cross_up(au, ad)))
    obv = (np.sign(c.diff()).fillna(0) * v).cumsum()
    S['I43 OBV 50-दिन high (भाव नहीं)'] = (1, B((obv >= obv.rolling(50).max()) & (c < c.rolling(50).max() * 0.97)))
    vr = v / v.rolling(50).mean()
    S['I44 Volume 2x + close दिन के top पर'] = (1, B((vr > 2) & (c > l + 0.8 * (h - l)) & (body > 0)))
    S['I45 Volume 2x + close दिन के bottom पर'] = (-1, B((vr > 2) & (c < l + 0.2 * (h - l)) & (body < 0)))
    S['I46 Elder impulse हरा शुरू'] = (1, B((ema(c, 13) > ema(c, 13).shift()) & ((macd - sig) > (macd - sig).shift()) & ~((ema(c, 13).shift() > ema(c, 13).shift(2)) & ((macd - sig).shift() > (macd - sig).shift(2)))))
    # ===== C. Famous traders =====
    S['T01 Turtle 20-दिन breakout'] = (1, B(c > h.rolling(20).max().shift()))
    S['T02 Turtle 55-दिन breakout'] = (1, B(c > h.rolling(55).max().shift()))
    S['T03 Turtle 20-दिन breakdown'] = (-1, B(c < l.rolling(20).min().shift()))
    S['T04 Turtle soup (20-दिन low तोड़कर वापस)'] = (1, B((l < l.rolling(20).min().shift()) & (c > l.rolling(20).min().shift()) & (l.rolling(20).min().shift().diff(3) == 0)))
    h52 = h.rolling(250).max(); l52 = l.rolling(250).min()
    # Darvas box: 52w high made, then 3 days below it; box top = that high, bottom = lowest low since; buy on close above top
    newhi = h >= h52
    last_hi_idx = pd.Series(np.where(newhi, np.arange(N), np.nan), index=c.index).ffill()
    since = pd.Series(np.arange(N), index=c.index) - last_hi_idx
    boxtop = h52.where(newhi).ffill()
    S['T05 Darvas box breakout'] = (1, B((since.shift() >= 3) & (since.shift() <= 40) & (c > boxtop.shift()) & (c.shift() <= boxtop.shift())))
    tt = (c > m150) & (c > m200) & (m150 > m200) & (m200 > m200.shift(21)) & (m50 > m150) & (c > m50) & (c >= 1.3 * l52) & (c >= 0.75 * h52)
    S['T06 Minervini trend template (पहला दिन)'] = (1, B(tt & ~tt.shift().fillna(False).astype(bool)))
    # VCP: in trend template, last 3 contraction ranges shrinking (40-day, 20-day, 10-day max-min %), breakout above 10-day high on volume
    r40 = h.rolling(40).max().shift(20) / l.rolling(40).min().shift(20) - 1; r20 = h.rolling(20).max().shift(10) / l.rolling(20).min().shift(10) - 1; r10 = h.rolling(10).max() / l.rolling(10).min() - 1
    S['T07 Minervini VCP breakout'] = (1, B(tt & (r40 > r20) & (r20 > r10.shift()) & (r10.shift() < 0.10) & (c > h.rolling(10).max().shift()) & (vr > 1.4)))
    w = c.rolling(150).mean()  # ~30-week MA
    S['T08 Weinstein stage-2 breakout'] = (1, B((c > w) & (w > w.shift(20)) & (c > h.rolling(120).max().shift()) & (vr > 1.5) & (w.shift(20) <= w.shift(60) * 1.03)))
    S['T09 Weinstein stage-4 breakdown'] = (-1, B((c < w) & (w < w.shift(20)) & (c < l.rolling(120).min().shift())))
    base_ok = (h.rolling(35).max().shift() / l.rolling(35).min().shift() - 1) < 0.35
    S["T10 O'Neil base breakout (52w high, volume +40%)"] = (1, B(base_ok & (c > h.rolling(250).max().shift()) & (vr > 1.4) & (c > m50)))
    S['T11 Qullamaggie episodic pivot (gap 10%+, volume 3x)'] = (1, B((o / c.shift() - 1 > 0.10) & (vr > 3) & (c > o)))
    prior = c.shift(15) / c.shift(60) - 1; tight = (h.rolling(15).max().shift() / l.rolling(15).min().shift() - 1) < 0.15
    S['T12 Qullamaggie breakout (30%+ चाल के बाद tight range)'] = (1, B((prior > 0.3) & tight & (c > h.rolling(15).max().shift())))
    S['T13 High tight flag (2 महीने में 90%+, फिर flag)'] = (1, B((c.shift(10) / c.shift(50) - 1 > 0.9) & (l.rolling(10).min() > h.rolling(10).max() * 0.75) & (c > h.rolling(10).max().shift())))
    r2 = rsi(c, 2)
    S['T14 Connors RSI(2)<10, 200 DMA के ऊपर'] = (1, B((r2 < 10) & (c > m200)))
    S['T15 Connors RSI(2)>90, 200 DMA के नीचे'] = (-1, B((r2 > 90) & (c < m200)))
    S['T16 Connors 3 lower highs/lows, 200 के ऊपर'] = (1, B((c > m200) & (h < h.shift()) & (h.shift() < h.shift(2)) & (h.shift(2) < h.shift(3)) & (l < l.shift()) & (l.shift() < l.shift(2)) & (l.shift(2) < l.shift(3))))
    e20 = ema(c, 20)
    S['T17 Raschke Holy Grail (ADX>30, 20 EMA तक pullback)'] = (1, B((ax > 30) & (pdi > ndi) & (l <= e20) & (c > e20)))
    S['T18 Larry Williams OOPS (prev low के नीचे खुला, ऊपर बंद)'] = (1, B((o < l.shift()) & (c > l.shift())))
    S['T19 Larry Williams OOPS sell'] = (-1, B((o > h.shift()) & (c < h.shift())))
    rng20h = h.rolling(30).max().shift(); rng20l = l.rolling(30).min().shift(); flat = (rng20h / rng20l - 1) < 0.15
    S['T20 Wyckoff spring (range low तोड़कर वापस)'] = (1, B(flat & (l < rng20l) & (c > rng20l)))
    S['T21 Wyckoff upthrust (range high तोड़कर वापस)'] = (-1, B(flat & (h > rng20h) & (c < rng20h)))
    dnvol = v.where(c < c.shift()).rolling(10).max().shift()
    S['T22 Pocket pivot (Kacher/Morales)'] = (1, B((c > c.shift()) & (v > dnvol) & (c > m50) & ((c / sma(c, 10) - 1).abs() < 0.04)))
    S['T23 Livermore pivotal point (pullback के बाद नया high, volume)'] = (1, B((c > h.rolling(40).max().shift()) & (l.rolling(10).min().shift() < h.rolling(40).max().shift() * 0.92) & (vr > 1.3)))
    S['T24 PTJ: 200 DMA के ऊपर लौटा'] = (1, B(cross_up(c, m200) & (m200 > m200.shift(20))))
    # ===== D. Popular in India =====
    m44 = sma(c, 44)
    S['N01 44-MA रणनीति (44 MA ऊपर चढ़ता, उसके पास हरी candle)'] = (1, B((m44 > m44.shift(5)) & (l <= m44 * 1.01) & (c > m44) & (body > 0)))
    S['N02 20/50 EMA + 200 के ऊपर (pullback buy)'] = (1, B((e20 > ema(c, 50)) & (c > m200) & cross_up(c, e20)))
    pp = (h.shift() + l.shift() + c.shift()) / 3; rng1 = (h - l).shift()
    H3 = c.shift() + rng1 * 1.1 / 4; L3 = c.shift() - rng1 * 1.1 / 4; H4 = c.shift() + rng1 * 1.1 / 2; L4 = c.shift() - rng1 * 1.1 / 2
    S['N03 Camarilla H4 के ऊपर close (breakout)'] = (1, B(c > H4))
    S['N04 Camarilla L4 के नीचे close (breakdown)'] = (-1, B(c < L4))
    S['N05 Camarilla L3 छूकर ऊपर बंद (reversal)'] = (1, B((l <= L3) & (c > L3) & (c < pp)))
    bc = (h.shift() + l.shift()) / 2; tc = 2 * pp - bc; cprw = (tc - bc).abs() / pp
    S['N06 Narrow CPR दिन, close CPR के ऊपर'] = (1, B((cprw <= cprw.rolling(20).quantile(0.2)) & (c > np.maximum(tc, bc))))
    S['N07 Narrow CPR दिन, close CPR के नीचे'] = (-1, B((cprw <= cprw.rolling(20).quantile(0.2)) & (c < np.minimum(tc, bc))))
    S['N08 Close pivot के ऊपर, 3 दिन लगातार'] = (1, B((c > pp) & (c.shift() > pp.shift()) & (c.shift(2) > pp.shift(2)) & ~(c.shift(3) > pp.shift(3))))
    # ===== E. Chart patterns (zigzag, Bulkowski) =====
    cvv = c.to_numpy(dtype=float, copy=True); thr = float(np.clip(3 * np.nanmedian(((h - l) / c).values), 0.04, 0.15)); piv = zigzag(cvv, thr)
    cp = {k: np.zeros(N, bool) for k in ['P01 Double bottom', 'P02 Double top', 'P03 Triple bottom', 'P04 Triple top', 'P05 Falling wedge (ऊपर टूटा)', 'P06 Rising wedge (नीचे टूटा)',
                                          'P07 Rectangle breakout up', 'P08 Rectangle breakdown', 'P09 Broadening bottom (ऊपर टूटा)', 'P10 V-bottom', 'P11 Rounding bottom (saucer)', 'P12 Bear flag']}
    def fire(name, start, level, above, maxw=40):
        for t in range(max(start, 1), min(start + maxw, N)):
            if (above and cvv[t] > level and cvv[t - 1] <= level) or ((not above) and cvv[t] < level and cvv[t - 1] >= level): cp[name][t] = True; return
    for j in range(2, len(piv)):
        a_, b_, c_ = piv[j - 2], piv[j - 1], piv[j]
        if a_[2] == 'L' and c_[2] == 'L' and abs(a_[1] / c_[1] - 1) <= 0.03 and 10 <= c_[0] - a_[0] <= 120: fire('P01 Double bottom', c_[3], b_[1], True)
        if a_[2] == 'H' and c_[2] == 'H' and abs(a_[1] / c_[1] - 1) <= 0.03 and 10 <= c_[0] - a_[0] <= 120: fire('P02 Double top', c_[3], b_[1], False)
    for j in range(4, len(piv)):
        p1, p2, p3, p4, p5 = piv[j - 4:j + 1]
        if p1[2] == 'L' and p5[2] == 'L' and max(p1[1], p3[1], p5[1]) / min(p1[1], p3[1], p5[1]) - 1 <= 0.04 and p5[0] - p1[0] <= 200: fire('P03 Triple bottom', p5[3], max(p2[1], p4[1]), True)
        if p1[2] == 'H' and p5[2] == 'H' and max(p1[1], p3[1], p5[1]) / min(p1[1], p3[1], p5[1]) - 1 <= 0.04 and p5[0] - p1[0] <= 200: fire('P04 Triple top', p5[3], min(p2[1], p4[1]), False)
        Hs = [p for p in (p1, p2, p3, p4, p5) if p[2] == 'H']; Ls = [p for p in (p1, p2, p3, p4, p5) if p[2] == 'L']
        if len(Hs) >= 2 and len(Ls) >= 2 and p5[0] - p1[0] <= 150:
            hs = Hs[-1][1] - Hs[-2][1]; ls = Ls[-1][1] - Ls[-2][1]
            if hs < 0 and ls < 0 and hs < ls: fire('P05 Falling wedge (ऊपर टूटा)', p5[3], Hs[-1][1], True)        # both falling, highs fall faster (converging down)
            if hs > 0 and ls > 0 and ls > hs: fire('P06 Rising wedge (नीचे टूटा)', p5[3], Ls[-1][1], False)
            if abs(Hs[-1][1] / Hs[-2][1] - 1) <= 0.02 and abs(Ls[-1][1] / Ls[-2][1] - 1) <= 0.02 and max(Hs[-1][1], Hs[-2][1]) / min(Ls[-1][1], Ls[-2][1]) - 1 >= 0.06:
                fire('P07 Rectangle breakout up', p5[3], max(Hs[-1][1], Hs[-2][1]) * 1.005, True); fire('P08 Rectangle breakdown', p5[3], min(Ls[-1][1], Ls[-2][1]) / 1.005, False)
            if hs > 0 and ls < 0: fire('P09 Broadening bottom (ऊपर टूटा)', p5[3], Hs[-1][1], True)
    # V-bottom: 15%+ fall in <=15 days then recovers 2/3 within 10 days
    fall = c / c.rolling(15).max() - 1
    vb = (c.rolling(10).min() / c.shift(10).rolling(15).max() - 1 < -0.15) & (c >= c.rolling(10).min() + 0.66 * (c.shift(10).rolling(15).max() - c.rolling(10).min()))
    cp['P10 V-bottom'] = B(vb & ~vb.shift().fillna(False).astype(bool))
    # saucer: 60-day U shape: middle third lowest, both ends within 5%, breakout over left rim
    lft = c.shift(60); mid = c.shift(20).rolling(20).min()
    cp['P11 Rounding bottom (saucer)'] = B((mid < lft * 0.85) & (c > lft) & (c.shift() <= lft) & ((c.rolling(60).std() / c.rolling(60).mean()) < 0.12))
    pole = c.shift(8) / c.shift(18) - 1
    cp['P12 Bear flag'] = B((pole < -0.15) & (h.rolling(8).max() < c.shift(18)) & (c < l.rolling(8).min().shift()))
    for k_, arr in cp.items(): S[k_] = (1 if k_ in ('P01 Double bottom', 'P03 Triple bottom', 'P05 Falling wedge (ऊपर टूटा)', 'P07 Rectangle breakout up', 'P09 Broadening bottom (ऊपर टूटा)', 'P10 V-bottom', 'P11 Rounding bottom (saucer)') else -1, arr)
    # 52-week
    S['W01 52-हफ्ते high (पहली बार 20 दिन में)'] = (1, B((c >= h52.shift()) & ~(c.shift(1).rolling(20).max() >= h52.shift(2))))
    S['W02 52-हफ्ते low'] = (-1, B((c <= l52.shift()) & ~(c.shift(1).rolling(20).min() <= l52.shift(2))))
    return S
