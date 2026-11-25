# Source study — todo (कुछ भी भूलना नहीं)
Updated: 2026-11-25 21:30 Kuwait

## Robot (GitHub) — दिया हुआ
- [x] 22 Nov 22:15 Tosif: **पहले किताबें, YouTube बाद में.** gemini_reader अब: Tosif links → books (हर run 8 हिस्से तक) → YouTube queue सिर्फ़ सारी किताबें ख़त्म होने के बाद. World scan reader के बाद.
- [x] book_finder.py (source_collector में, दिन में 4 बार): Gutenberg public-domain classics (Wyckoff, Selden, Dow/Hamilton...), arXiv India/q-fin papers, books/wishlist.csv (SEBI F&O/intraday P&L study, NSE Market Pulse, RBI FSR, Economic Survey, WGC Gold Demand Trends, SPIVA India, UBS Yearbook) → books/order.txt mix order
- [ ] अगले report में जाँचना: finder_status.json (कितनी किताबें आईं), reader_status.json (book_chunks, books_left)
- [x] Motilal WCS 13-30 (18 PDFs) books/ में आ गए (22 Nov 18:11)
- [x] YouTube: अब Gemini खुद video देखता है (ai_manager.yml) — 22 Nov रात sample जाँचा: 3 videos ठीक पढ़े. सीमा: free quota (125 videos बाकी)
- [ ] हर run: study/ai/tasks.md देखकर Gemini/Groq/robot का हाल जाँचना (videos_ok, world_claims, sorted headlines)
- [ ] world_claims.csv (world scan) के नए claims पढ़ना → claims_log
- [x] Forward Guidance + Rayner id ठीक (22 Nov). Rayner/Northman feed YouTube side खाली — robot पर कुछ नहीं हो सकता
- [x] Reddit + Korea JoongAng बंद (type off). Korea के लिए नया feed ढूँढना (Yonhap/Herald RSS 0 items)
- [ ] Index बदलाव इतिहास (IDX-01): NSE/BSE press releases से Nifty/Sensex inclusion/exclusion तारीख़ें → data/index_changes.csv
- [ ] FII/DII रोज़ाना इतिहास (NW-01 के लिए) — robot script: NSE/NSDL archive से data/fii_dii.csv भरना

## Claude — हल्का (अभी/अगला run)
- [x] queue के 282 new पढ़े; WCS 12 पूरा पढ़ा (22 Nov 18:11)
- [x] WCS 13-17 Key Findings पढ़े (22 Nov 21:11; ज़्यादातर MO-01..11 जैसे; नए MO-12, MO-13)
- [x] WCS 18-21 पढ़े (23 Nov 02:11; MO-14..17)
- [x] WCS 22, 23 पढ़े (23 Nov 06:11; MO-18..21)
- [x] WCS 24, 25 पढ़े (23 Nov 18:11; MO-23 pledge/auditor — data नहीं)
- [x] WCS 26 Summary पढ़ा (23 Nov 21:11; MO-24)
- [x] WCS 27, 28 पढ़े (24 Nov 02:11; MO-25..27)
- [x] 24 Nov 18:11: queue 108 पढ़े; Dhan पूरे transcripts (theta trap, MTF scan) → r062 दोनों बेकार; test_queue 40 waiting निपटाए
- [x] 24 Nov 21:11: PC के 16 transcripts में से बाकी 8 पढ़े (कुछ नया testable नहीं)
- [ ] Tosif link jYqDEE5QL-w: Gemini HTTP 404 — अगले run में browser/PC transcript से पढ़ना
- [ ] बाकी PC transcripts (~150) आने पर पढ़ना (Tosif PC script धीमा चलाए — IpBlocked)
- [ ] Gemini: books_left 3 (WCS 28-30) — quota 429, अपने आप अगले robot run
- [x] WCS 29 पढ़ा + WCS 30 highlights (24 Nov 06:11; MO-28, MO-29 बेकार — r061). WCS 30 theme (India multi-trillion) macro, testable नहीं
- [ ] ARX-01 आगे: Nifty futures cost (~0.03%) के साथ "up-day के बाद hold" + regime filter
- [ ] test_queue pending: AI-419DA0/AI-036DAC (fundamentals history चाहिए — robot से yfinance quarterly/annual इतिहास?), AI-320182 (historical mcap)

- [ ] Blog pages (allocatesmartly, alphaarchitect) web-fetch permission timeout — अगली बार दोबारा कोशिश (AS-03 नियम पढ़ना)

- [ ] Nifty PE/PB/DY इतिहास का नया source (niftyindices API dead): tapetide.com/insight/market-valuation/nifty-pe-ratio-history.md, data.mendeley.com/datasets/6pjd2wzzcc/1, freefincal Nifty PE file, nikhilsuthar.github.io/indian-market-data → robot script → data/indices/NIFTY50_PE.csv; फिर AI-D1EDA5/AI-7292D2/AI-CB739F test (10y G-sec भी चाहिए)
- [ ] 10-साल fundamentals का source (blocked 7 नियम) — sirf 4 saal yfinance hai

- [x] AI-48006E + AI-C62277/C7791E (25 Nov 02:11, r065 analysis; dividend adj factor से निकला)
- [ ] test_queue pending 4 mcap-tier: AI-0B9866/AI-EF9B89/AI-867542/AI-6EF0EE mcap-tier (पुराना mcap proxy = price×आज के shares)
- [ ] book_finder: Gutenberg 503/timeouts — mirror (gutenberg.pglaf.org) या बाद में; Gemini WCS 17 हिस्सा HTTP 404 जाँचना

## Data कमी → robot (23 Nov 22:00, Tosif: "कमी हो तो download करो / किसी और को दो, नहीं हो सके तो मुझे बताओ")
- [x] GDP + macro: scripts/macro_history.py → data/macro/ (World Bank 1960-2025: GDP INR/USD, real growth, CPI, mcap/GDP, lending rate; FRED: 10y G-sec 2011-26 monthly, CPI index, USDINR daily, IIP, India quarterly real GDP 2004-26, US 10y). workflow macro_data.yml (रोज़ 6:55 PM IST)
- [x] Nifty PE (2015-26) से AI-D1EDA5/7292D2/CB739F/0811E2 test (25 Nov 18:11, r067). बाकी: AI-5C5C39 (mcap/GDP); Nifty PE 2015 से पहले (robot 2011 404) — दूसरा source; Next50/Midcap PE पर भी r067 दोहराना
- [ ] World Bank mcap/GDP 2018 और 2025 के आँकड़े अजीब (153%, 267%) — mcap/GDP ख़ुद बनाना: BSE total mcap इतिहास चाहिए
- [ ] Tosif से पूछा: 10 साल company fundamentals (RoE/PAT/dividend) और corporate profit/GDP — free source नहीं मिला (Screener/Prowess login/paid)

## Claude — भारी (हिस्सों में)
- [x] r066: PSU vs private 12m switch (4 sectors analysis, banks बेकार)
- [ ] r065 आगे: div-yield>3% को bear regime (Nifty<200DMA) filter के साथ
- [ ] NW-02 आगे: futures cost (0.03%) + VIX/200DMA filter के साथ "Nasdaq<=-2% + gap-down" open खरीद; forward 25 Nov 2026 (Kospi -5%)
- [ ] AI-C62277b forward: हर महीने 4-sector switch का चुनाव (25 Nov: private) देखना
- [x] AI-248E4C switch (r066 बेकार); बाकी: band हुए private banks (LVB) का असर (data नहीं)
- [ ] AI-062853 आगे: Hurst-high momentum पर stop/target (mfe_mae) + 200DMA regime, weekly/monthly hold
- [x] MO-21 Porter test (r057: edge नहीं, analysis) + AI-184C53 बेकार
- [ ] MO-21 + MO-25 आगे: Porter-hi और Consistent-sector group का गिरावट वाले महीनों (Nifty 200DMA के नीचे) में बचाव — defensive filter test (r060 के बाद)
- [x] robot fix (24 Nov): source_collector.yml अब ROBOT claim scripts से पहले universe500 data clone करता है (U500 env). अगले report में .out.txt देखना
- [x] ET-02 stop/target + 200DMA (r063: close entry काम करता, next open पर नहीं)
- [ ] ET-02c: 3:20 PM entry (intraday m5_all) पर Marubozu-जैसा candle — क्या gap edge पकड़ में आता है? + r063 mkt>200 filter bug (EW index) ठीक करना
- [ ] MO-23 promoter pledge data source (NSE pledge disclosures) → robot script
- [ ] ARX-02 असली Nifty Midcap/Smallcap index data (NSE TRI) से दोबारा + cash पर 6% ब्याज जोड़कर
- [ ] MO-18 forward: FY2026 cohort (30 Jun 2026 → 30 Jun 2027) PE बकेट जाँचना
- [ ] DHAN-15 RSI divergence 2-min scalping — intraday_hist (Nifty/Sensex 1-min) पर divergence detector + test
- [ ] MC-01 forward: VIX≥20 के बाद ≥10% 1-दिन गिरावट आए तो 5/20 दिन देखना
- [ ] MO-10 forward: large vs mid/small (1 Dec 2025 से) हर महीने
- [ ] DHAN-10 BankNifty 1-min 200EMA pullback — intraday_hist पर test
- [ ] AS-03 equity-curve on/off filter — हमारे paper/backtest equity पर test
- [x] BF-01b ATH से X% नीचे buckets (r053, analysis में)
- [ ] BF-01b आगे: episode-स्तर गिनती (हर गिरावट एक बार)
- [ ] MO-01/MO-02 (सस्ता P/E, P/B, payback → wealth creator?) सभी शेयरों पर survivorship-free जाँच: 1) data/fund में P/E P/B इतिहास कितना है देखो 2) robot script 3) नतीजा
- [ ] DHAN-06 (R1/S1 + PDH/PDL zones, Nifty 5-min) intraday_hist पर test
- [ ] AS-01 India sector-implied inflation compass test
- [ ] DHAN-12 Harmonic (Gartley/Bat) — zigzag swing + Fibonacci ratios, daily u500 पर robot script (भारी: 2 हिस्से — 1) pattern detector 2) test)
- [ ] GOLD-01 forward: 20 Nov 2026 gold USD 3539 (-33.5%), silver 41.1 (-64%) — 60/120/250 दिन बाद देखना
- [ ] ET-01 + breadth/200DMA regime filter (i28 के साथ)
- PC transcripts 2026-11-22 11:40 Kuwait: PC मिला पर yt_transcripts फ़ोल्डर इस run से जुड़ा नहीं था (connectedFolders खाली) और device_bash tool उपलब्ध नहीं — script नहीं चली; ok 0, fail 0. Tosif: scheduled task की settings में फ़ोल्डर दोबारा जोड़ें / desktop app अपडेट करें।

- [ ] IDX-01 forward: Shriram Finance (Sensex में) और Trent (बाहर) — 22 Nov से 21 Dec और उसके 20 दिन बाद

## AI manager (22 Nov 2026 रात) — Gemini/Groq robot (.github/workflows/ai_manager.yml)
- Gemini अब YouTube video खुद देखता है (transcript block की दिक्कत ख़त्म) + books/*.txt पढ़ता है → study/experts/gemini/<id>.md (point-by-point), rules_ai.csv
- **Claude के study runs: नए testable नियम study/experts/test_queue.csv (status=waiting) से उठाओ** → Python test → status/result भरो (numbers सिर्फ़ code से)
- Tosif के भेजे YouTube links → study/experts/user_links.txt में जोड़ो (push होते ही robot पढ़ लेता है)
- Groq news छँटाई → data/news/sorted.md (बड़ी शक वाली ख़बर Gemini+Google से जाँच). Groq facts में ग़लत हो सकता है (Nifty को BSE बताया) — सिर्फ़ छँटाई
- Hafta scoreboard → data/scoreboard.md (शनिवार). usage/fail → study/ai/usage.csv, gemini/reader_status.json
- PC transcripts 23 Nov 10:24: PC मिला, पर yt_transcripts फ़ोल्डर इस run से जुड़ा नहीं था और PC shell (device_bash) नहीं मिला → script नहीं चला (ok 0, fail 0). Browser fallback छोड़ा (Gemini अब video खुद देखता है, Claude usage बचाने के लिए). Tosif: Cowork में scheduled task के लिए फ़ोल्डर दोबारा जोड़ें.
- PC transcripts 24 Nov 10:24: PC मिला, पर yt_transcripts फ़ोल्डर फिर इस run से जुड़ा नहीं था और device_bash नहीं मिला → script नहीं चला (ok 0, fail 0). लगातार दूसरा दिन — Tosif: Cowork में इस scheduled task के लिए फ़ोल्डर दोबारा जोड़ें.
- PC transcripts 24 Nov 15:24: 16 मिले, फिर YouTube ने PC IP को IpBlocked किया → रोका. Script में धीमा करना/बीच में रुकना चाहिए (अभी 1.5s gap).
- PC transcripts 2026-11-25 10:24: work folder not connected to the scheduled task (connectedFolders empty) and no device_bash — Tosif to re-attach the yt_transcripts folder in the task settings or run `py pc_transcripts.py 30` by hand

- [ ] PC-01: SEBI closing auction नया ढाँचा कब से — लागू होने पर ET-02b close entry बनाम 3:20 entry दोबारा देखना

- [ ] NW-03 forward (r068): 2, 6, 20 Nov 2026 decoupling signals — 20d बाद (दिसंबर मध्य) देखना
