# Source study — todo (कुछ भी भूलना नहीं)
Updated: 2026-11-22 21:30 Kuwait

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
- [ ] WCS 18-29 पढ़ना (हर run 3-4 studies: सिर्फ़ Key Finding/valuation tables; MO-11 bucket tables तुलना) — WCS 30 का theme हिस्सा (lines 120-2800) भी

- [ ] Blog pages (allocatesmartly, alphaarchitect) web-fetch permission timeout — अगली बार दोबारा कोशिश (AS-03 नियम पढ़ना)

## Claude — भारी (हिस्सों में)
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
