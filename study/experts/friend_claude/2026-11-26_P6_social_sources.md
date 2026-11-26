ROLE: You are a financial-news researcher who tracks how market-moving information spreads on social media. Use web search a lot (at least 20-30 searches). Never invent account names or links — only list accounts/channels you actually found and checked; mark anything you could not verify as UNSURE.

PASTED

I'll research the sources (official feeds, newsroom handles, data accounts, SEBI finfluencer actions, past "first and right" events, and robot-access limits), then give you the list in your format, plus a CSV file your robot can load.

I searched about 36 times and built 88 source entries. Every account and link in the list came up in those searches, except the ones marked UNSURE. Those are well-known handles I didn't re-check here, so confirm them before you rely on them.

Gaps:

Group 3 (individual scoop journalists) is thin. I couldn't find documented track records for people who break RBI news or FII/F&O data first, and I didn't want to fill it with names I can't back up. The robot should build its own scorecard over time (see rule 7).
Telegram: only one reputable public channel was confirmed (Moneycontrol). Test other candidates with t.me/s/ before adding them.
1. CSV

The full 88-row CSV is in india_market_sources.csv. Load that file into the robot. Below are the header and sample rows:

csv
name,handle_or_url,platform,group,language,gives,speed,reliability,reliability_reason,bias_or_conflict,robot_access,label
NSE Financial Results RSS,https://nsearchives.nseindia.com/content/RSS/Financial_Results.xml,RSS,1,English,Company result filings,minutes,high,Primary exchange filing,Company text not pre-verified,RSS,CONFIRMED
SEBI RSS,https://www.sebi.gov.in/sebirss.xml,RSS,1,English,Press releases+circulars+orders,minutes-hours,high,Regulator primary,None,RSS,CONFIRMED
RBI Press Releases RSS,https://rbi.org.in/pressreleases_rss.xml,RSS,1,English,Policy/liquidity releases,minutes,high,Central bank primary,None,RSS,CONFIRMED
CNBC-TV18 ticker,@CNBCTV18Live,X,2,English,Breaking flashes,minutes,medium-high,Fast tier-1 desk,Ad-funded,manual only,CONFIRMED
Walter Bloomberg,@DeItaone,X,2,English,Headline relay,seconds,medium-low,False tariff headline Apr 2025,Anonymous,manual only,CONFIRMED
NSDL FPI daily,https://www.fpi.nsdl.co.in/web/Reports/Latest.aspx,web,4,English,FPI flows,day,high,Depository data,None,HTML scrape,CONFIRMED
Moneycontrol Telegram,https://t.me/s/moneycontrolcom,Telegram,5,English,Headlines,minutes,medium-high,Official channel,Ad-funded,web preview,CONFIRMED
Markets by Zerodha,https://www.youtube.com/@marketsbyzerodha,YouTube,6,English,Daily Brief,day,medium-high,No tips,Broker-owned,YouTube RSS,CONFIRMED
ValuePickr,https://forum.valuepickr.com/latest.rss,Forum,7,English,Deep research,day,medium-high,Long-form work,Posters hold stocks,Discourse RSS,REPORTED
Polymarket,https://gamma-api.polymarket.com/events,API,8,English,Event odds,minutes,medium,Real money odds,Thin on India,Free JSON,CONFIRMED
2. "First and right" examples
Event	Who was first	Lead over mainstream	Right?
Adani–Hindenburg, Jan 2023	The publisher itself (@HindenburgRes); Hindenburg shared its report on Twitter at 8:15 am on January 25 (IST)	Hours. Indian TV mostly chose not to discuss it on Jan 25–26	Big market move: $150 billion wiped from the conglomerate's market value in 5 weeks. The allegations were contested: Adani called the report "maliciously mischievous," "bogus". Label: CONFIRMED
Election results, Jun 2024	Official ECI counting trends. Exit polls were wrong	Live, from 8 am	Exit polls had projected around 350-370 seats. Sensex fell 6,234.35 points or 8.9% to hit an intraday low. CONFIRMED
SEBI F&O rules, Oct 2024	SEBI circular (primary). A July 2024 consultation paper had flagged it	Same day	From Dec 1, 2024, weekly contracts are available for one benchmark index per exchange (Nifty 50 for NSE and Sensex for BSE). CONFIRMED
RBI, Jun 6 2025	The RBI governor's live announcement. Analyst polls were wrong	0 min	RBI cut 50 basis points (bps) to 5.5 per cent, surprising markets, which had largely priced in a more modest reduction of 25 bps. CONFIRMED
Fake tariff pause, Apr 7 2025	@DeItaone: first and WRONG	Minutes	The rumour pushed the S&P 500 to soar over 7%, and then give up nearly all those gains. One hour later, though, the White House issued its statement denying the report. CONFIRMED
Real tariff pause, Apr 9 2025	Trump's own Truth Social post	0 min. Wires followed	At 1:18 p.m. ET, Trump posted on his social media platform Truth Social there would be a 90-day pause. CONFIRMED
US 50% tariff on India, Aug 2025	White House order, then a US implementation notice	Days of warning	Markets fell when the Trump administration issued a notification to impose an additional 25 per cent tariff. CONFIRMED
Budget, Jul 23 2024	The finance minister's speech (no leak found)	0 min	Knee-jerk drop, then recovery: Sensex closed down by 73.04 points at 80,429.04 after recovering most of its 1,200-point intra-day loss. CONFIRMED 
media analysis how indian news outlets reacted to the hindenburg adani saga
 +11
3. AVOID list (documented)
Baap of Chart: SEBI passed an interim order barring Mohammad Nasiruddin Ansari and others behind 'Baap of Chart' (BoC) from securities trading and impounded ₹17.2 crore. Order 
barandbench
Avadhut Sathe: directed... to refund ₹546.17 crore collected from participants for providing unregistered investment advisory and research analyst services (final order, Oct 2026). Order 
businesstoday
Asmita Patel: Recommendations for buying/selling specific securities were provided and uploaded on telegram channels owned by APGSOT. (Feb 2025) 
yourstory
Safebulls (Telegram): suspected pump and dump of stocks using Social Media Telegram Channel named Safebulls. Order 
sebi
Superior Finlease channels: SEBI barred 17 entities and individuals from the securities market for five years over misleading tips on Telegram channels. 
business-standard
Intraday Jackpot (Telegram): paid telegram channels linked through the free telegram Channel "Intraday Jackpot" were providing advice. Order 
sebi
Hemant Gupta family / 'Den of Wealth': gave stock recommendations on social media platforms, executed opposite trades contrary to their recommendations and made unlawful gains (May 2026). 
publictv
Sadhna Broadcast YouTube channels: The five channels were found to be operated by Manish Mishra. Actor Arshad Warsi was barred for a year. 
theprint
Use with caution, not banned: @DeItaone and @yourfavorito, because of the false tariff-pause headline in April 2025.
4. Signal-vs-noise rules
Primary first. No market call until the NSE/BSE filing, SEBI/RBI/PIB release or official post exists. A headline with no link counts as a rumour.
Two independent tier-1 sources for anything not primary. Two reposts of one source count as one.
Check what was actually said. The fake April 2025 pause began as a misread interview question: the rumour seems to have been based on a misinterpretation of comments made by Mr Hassett in a Fox News interview. 
rte
Watch for an official denial within about 60 minutes before trusting a big move.
Red flags: unregistered adviser, "courses" plus live tips, guaranteed returns, small/SME stock with no news, a paid Telegram funnel. SEBI's advice is caution with companies which see sudden spikes in prices without any attributable change in fundamentals. 
business-standard
Consensus is not truth. Exit polls (2024) and analyst polls (RBI, June 2025) were both wrong.
Score every source. Log first-post time, the official confirmation time and whether it turned out right. Downgrade a source after two misses.
Disclosures: holds positions, broker-owned, sells courses. Note the bias, then weigh accordingly.
5. Robot access notes (2026)
X: there's no free read access. pay-per-use is the default X API pricing for new developers: $0.01 per post created, $0.005 per post read. X has no RSS feeds either, so treat X as "manual only" or budget a few dollars a month. 
postproxy
Telegram: the web preview works without login. Telegram renders the 20 most recent messages of any public channel. It's paginated, HTML-rendered, and rate-sensitive, and reactions aren't shown. 
dev
apify
Reddit: this breaks. On May 28, 2026, Reddit announced it is deprecating unauthenticated .json endpoints — within days, appending .json to a URL started returning 403. Use .rss instead. RSS still works but is throttled: feeds began returning HTTP 429 Too Many Requests errors starting June 11, 2025. 
dev
lavx
YouTube: RSS works but needs the channel ID, not the @handle. Feeds show roughly the most recent 15 uploads, and the endpoint had a rough patch in late 2025, so retry on a 404. 
wprssaggregator
NSE JSON: fragile. It needs cookies from visiting the homepage first. One developer reports that NSE blocks all server access straight using robots.txt. Expect GitHub Actions IPs to get blocked, so prefer the nsearchives RSS feeds and NSDL pages. 
unofficed
SEC EDGAR: Current max request rate: 10 requests/second. Send a User-Agent header with your name and email. 
sec
Reuters: Reuters stopped updating its public feeds in 2020. Use Google News RSS searches instead. 
feeder
Polymarket: All market data is available through public REST endpoints. No API key, no authentication, no wallet required. Kalshi market data is similar. 
polymarket
Google Trends: the official API is alpha and needs an application: We're now accepting applications for alpha testers. 
google
New data: NSDL has introduced daily reporting of domestic institutional investor (DII) investment activity. 
kotakneo
6. Daily routine

9:15 IST is 6:45 Kuwait time.

Morning (15 min, 6:30–6:45 Kuwait):

Fed and US overnight: Fed RSS, Kalshi Fed odds, Truth Social and White House for tariff news.
RBI press RSS and SEBI RSS: anything after 6 pm IST yesterday.
NSE announcements and results RSS: overnight filings for your watchlist.
FII/DII figures: NSE provisional numbers from last night, then NSDL confirmed data.
Moneycontrol on Telegram plus @CNBCTV18Live: what the market already knows.
Markets by Zerodha Daily Brief: context.
India VIX and the Nifty option chain once data is live: positioning.
Write one line: "Top risk today = ___, source ___, confirmed Y/N."

Evening (10 min, after 7 pm IST):

NSE FII/DII provisional figures and block deals.
NSE insider-trading and board-meeting RSS.
SEBI orders, including new finfluencer bans, so you can update the blocklist.
Aftermarket Report: check whether the day's move matched your morning forecast.
Score yesterday's rumours as right or wrong.
7. Sources
NSE RSS
SEBI RSS
SEBI X notice
Fed feeds
PIB RSS
SEC EDGAR access
SEBI FPI links
X API pricing
Kalshi public data
Polymarket data
Google Trends API
SEBI F&O circular

This is for study only and isn't trading advice.

India market sources
Table
·CSV