# किसको क्या काम दिया है (Claude = manager) — 22 Nov 2026

हर 21:11 वाली report में Claude इस सूची का हाल (चला / नहीं चला / क्या मिला) देखकर बताएगा. पहले खुद जाँच करेगा, फिर "हो गया" कहेगा.

## Gemini (मुफ़्त key, GitHub Secrets) — पढ़ना, देखना, सच जाँचना
1. YouTube videos खुद देखना (transcript की ज़रूरत नहीं) — scripts/gemini_reader.py
   - पहले Tosif के भेजे links (study/experts/user_links.txt), फिर queue.csv के YouTube items (हर run में 12 तक)
   - सिर्फ़ test होने लायक नियम: setup, समय, entry/exit, stop/target, filters. Life story / कमाई के दावे / आम सलाह नहीं
   - नतीजा: study/experts/gemini/<id>.md, rules_ai.csv, test_queue.csv
2. किताबें/PDF (books/*.txt) — हर run में एक किताब का अगला ~150k अक्षर हिस्सा
3. बड़ी शक वाली खबरों का Google Search से fact-check (दिन में 8 तक)
4. World scan — scripts/world_scan.py (नया, 22 Nov रात): Google Search से 12 विषय बारी-बारी (हर run 6):
   India setups, India policy/FII, India social (Reddit, X), USA quant studies, USA social (Reddit algotrading, StockTwits, TradingView),
   Japan, Korea, China, Europe papers, Gulf (Saudi, Kuwait, UAE), Global macro, नए free research papers
   → study/experts/world_scan/<date>.md, world_claims.csv
5. Claude के test नतीजों की अलग से आलोचना (ai_review.yml, जब Claude भेजे)

## Groq (मुफ़्त key) — तेज़ छँटाई (fact का source नहीं)
1. रोज़ की news headlines छाँटना: काम की? कौन-सा शेयर/sector? ऊपर/नीचे? ताकत 1-5? fact या अफ़वाह/राय? — scripts/groq_news.py → data/news/sorted.md
2. World scan के claims पर tag लगाना: test हो सकता है? नया या पहले जाँचा हुआ?
3. Claude के test नतीजों की दूसरी राय (ai_review)

## Robot (GitHub Actions, Python) — गिनती और बोझ वाला काम
1. source_collector.yml: 62 sources (YouTube RSS, blogs, news, PIB/RBI/SEBI, podcasts) → queue.csv; free PDF → books/*.txt
   (YouTube transcript यहाँ से नहीं आते — YouTube GitHub IP block करता है; इसलिए video अब Gemini देखता है)
2. ai_manager.yml: दिन में 5 बार Gemini/Groq वाले काम चलाता है (2 PM, 7 PM, 12 AM, 4:30 AM IST + 6:30 AM news)
3. study/research/claims/*.py (# ROBOT): backtests; Nifty/stocks data (universe500, intraday_hist, nse_hist)
4. बाकी: news, FII/DII, fundamentals, global, intraday, paper trading workflows

## जाँच 22 Nov रात (Claude ने खुद देखा)
- Gemini video देखना: चलता है ✔ — 3 videos (Dhan, 5paisa) + WCS 12 का एक हिस्सा पढ़ा, 9 नियम निकले (study/experts/gemini/, rules_ai.csv)
- फिर Gemini free quota खत्म (HTTP 429) → world scan के 6 विषय 0 पढ़े. Quota रोज़ ~11:00 AM Kuwait पर भरता है
- सुधार: world scan अब reader से पहले, हर run 3 विषय; quota खत्म हो तो रुककर अगले run वहीं से (विषय छूटता नहीं)
- Groq news: 1061 में से 264 छँटीं (free limit) — pacing सुधरी, अगले run देखना
- असली सीमा: free Gemini से दिन में बस कुछ videos (एक video = बहुत tokens). 125 videos queue में बाकी

## बाकी / कमी (todo.md में भी)
- Index बदलाव इतिहास, FII रोज़ाना इतिहास (robot scripts बनाने हैं)
- कल 21:11 report में: Gemini कितने videos/rules, world scan कितने claims, Groq कितनी headlines — गिनकर बताना
