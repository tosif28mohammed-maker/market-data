# r056 — Motilal WCS 22-23 + arXiv monthly momentum (23 Nov 2026, 06:11 Kuwait)

## MO-18: P/E बकेट (WCS 23 "Valuation insights")
Script: study/research/claims/mo18_pe_buckets.py. Data: yfinance annual FY2023-25 (data/fund/raw.csv.gz), P/E = 30-जून का भाव × shares / Net Income; अगले 12 महीने का return, उसी cohort के equal-weight से excess, 0.25% cost. 3,519 stock-years.

| P/E | n | mean excess % | median | बाज़ार से आगे % |
|---|---|---|---|---|
| घाटा | 266 | +22.1 | -4.8 | 46 |
| 0-10 | 246 | +7.7 | -8.3 | 42 |
| 10-20 | 626 | +2.5 | -9.1 | 40 |
| 20-30 | 578 | +1.1 | -10.2 | 40 |
| 30-50 | 808 | -5.4 | -14.0 | 35 |
| 50-75 | 500 | -8.0 | -15.7 | 33 |
| >75 | 494 | -4.9 | -13.0 | 36 |

दिशा Motilal जैसी (महँगा = कमज़ोर), FY23 और FY24 cohorts में साफ़, FY25 cohort में 50-75 +3.0. सिर्फ़ 3 cohorts + survivorship (आज की list) → **अभी analysis में**. Median सब negative = कुछ बड़े winners mean खींचते हैं.

## MO-19: High RoE + High growth
1-साल RoE >15 और 1-साल PAT growth >15: +0.3 vs LoLo +0.4 → छोटे horizon पर कोई edge नहीं. 10-साल वाला दावा data (4 साल) से test नहीं हो सकता → analysis में.

## MO-20: PEG<1, Payback<1
Motilal ने खुद लिखा: "perfect foresight" (असली future PAT) से बना → trade में संभव नहीं → **बेकार** (rule के रूप में).

## ARX-02 / AI-07BCC4: Mid/Small monthly persistence
Script: study/research/claims/ai07bcc4_mid_small_monthly_mom.py. EW proxy (traded-value rank 101-250 = Mid, 251-750 = Small), 2003-26.
- पिछला महीना ऊपर → अगला महीना: Mid +2.6% vs +0.9% (नीचे के बाद), Small +3.4% vs +0.9%; तीनों दौर में.
- पर strategy CAGR buy&hold से कम (बाहर रहने पर cash 0%): Small 25.9 vs 29.1; max DD -42 vs -67.
- पिछले 12 महीने उल्टा (autocorr -0.3). Nifty खुद में कोई persistence नहीं.
- चेतावनी: EW daily-rebalance proxy में bid-ask bounce से persistence बढ़ा दिखता है → असली Midcap/Smallcap index data से दोबारा.
→ **अभी analysis में** (drawdown घटाने का filter बन सकता है, return नहीं).

## MO-21 (WCS 22): Porter Industry Structure Score ≥3.5 वाले उद्योग — test todo में.

## Blocked (test_queue)
Sensex P/E vs G-sec वाले 3 नियम: Nifty PE/G-sec इतिहास नहीं (niftyindices API dead). 10-साल fundamentals वाले 7 नियम: सिर्फ़ 4 साल data. पुराना market-cap वाले 3 नियम: data नहीं.
