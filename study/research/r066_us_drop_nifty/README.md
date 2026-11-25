# r066 — US/Kospi गिरावट के बाद Nifty (NW-02) + PSU vs private momentum switch (r065 आगे)
Date: 2026-11-25 06:11 Kuwait (silent run). Scripts: study/research/claims/us_drop_nifty.py (+.out.txt), psu_switch.py (+.out.txt)

## NW-02 (25 Nov news: Kospi -5%, Nasdaq tech sell-off)
- Data: data/NIFTY.csv 2007-26, data/global/US_NASDAQ, KR_KOSPI. Nifty दिन से पहले की आख़िरी US close.
- Nasdaq<=-2% (n308): Nifty gap -0.52% (आम +0.09), open->close -0.30, gap उसी दिन नहीं भरता (median fill -0.01). Open खरीद 5d -0.04 (cost बाद -0.29) → बेकार।
- सिर्फ़ Nasdaq<=-2% और Nifty gap-down<=-0.5% (n124): open->5d +0.44% vs आम +0.17, तीनों दौर +0.42/+0.41/+0.48, win 55%; 0.25% cost बाद +0.19. Placebo Nasdaq>=+2% o5 +0.23. Last 6m n3 +3.2 (छोटा).
- Kospi<=-3% उसी दिन (n111): Nifty oc -0.93% पर 2021-26 में +0.03 (अब असर नहीं).
- Verdict: अभी analysis में — edge छोटा (+0.27pp/5d), futures cost (~0.03%) पर दोबारा; forward: 25 Nov 2026.

## AI-C62277b / AI-248E4Cb: 12m relative momentum switch (हर महीने, 1 महीना hold)
- 4 sectors PSU vs private: switch CAGR +21.1 vs private +18.0, PSU +14.8, 50/50 +16.7, उल्टा +11.4; तीनों दौर में 50/50 से आगे; सिर्फ़ 16 switch. 120d lookback +18.1. Last 6m +8.4 vs private +14.5. आज का चुनाव: private.
- Banks: switch +15.7 < हमेशा private +17.7 → बेकार.
- Survivorship: PSU सूची आज की, universe आज की liquid list.
- Verdict: 4-sector switch अभी analysis में (कम फ़ैसले), banks बेकार.
