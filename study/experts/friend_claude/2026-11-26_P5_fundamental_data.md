ROLE: You are a data engineer and quantitative researcher who has built Indian stock-market backtests. Use web search a lot (at least 15-25 searches). Be factual; if something is not found, write "not found". Label each claim CONFIRMED (you opened the page / official docs), REPORTED (one source), UN

PASTED

I'll research each source, checking current pages where I can, then put together the report in your format.

Here is the data plan in your format. In the labels, CONFIRMED means I saw the text on the official page through search extracts. I didn't do full page opens. REPORTED means a single third-party source, and UNSURE means it comes from memory or I couldn't check it. This is not investment advice.

1. Sources (CSV)

csv
source,data_items,history_from_year,point_in_time(yes/no/partly),format_or_api,free_limit,robot_can_download(yes/no/maybe),tos_note,label,link
NSE CM bhavcopy (old cmDDMONYYYYbhav.csv.zip; UDiFF from 2024-07-08),OHLCV incl. later-delisted symbols,1994-ish (UNSURE),yes,ZIP/CSV daily,none,maybe,NSE ToS bans automated collection,CONFIRMED,https://www.nseindia.com/all-reports
NSE PR zip -> MCAPDDMMYYYY.csv,Issue Size (=shares); face value; mcap,2024,yes,CSV inside PRddmmyy.zip,none,maybe,same NSE ToS,CONFIRMED,https://nsearchives.nseindia.com/content/circulars/CMTR60423.pdf
NSE PR zip -> Bmddmmyy.txt / Anddmmyy.txt,board-meeting dates+purpose; announcements,UNSURE (archive depth),yes,TXT daily,none,maybe,same,CONFIRMED (format) / UNSURE (depth),https://www.nseindia.com/static/market-data/description-of-market-activity-reports
NSE market cap of all companies,mcap rank as of Mar/Dec,2013 (top500); 2019+ all,yes,XLS/XLSX,none,maybe,same,CONFIRMED,https://www.nseindia.com/static/regulations/listing-compliance/nse-market-capitalisation-all-companies
AMFI categorisation list,6-mo avg full mcap rank of all listed cos,2017 H2,yes,XLSX half-yearly,none,yes,public page; terms not checked,CONFIRMED,https://www.amfiindia.com/otherdata/categorisation-of-stocks
niftyindices index P/E P/B DivYld,daily index PE/PB/DY,1999 for Nifty50 (UNSURE),yes (method change 2021),web/CSV,none,maybe,NSE Indices terms,CONFIRMED,https://niftyindices.com/reports/historical-data
niftyindices Archives of Daily/Monthly reports,monthly constituents; equity capital; industry; free float,2013-04,yes,CSV/XLS,none,maybe,same,REPORTED,https://www.niftyindices.com/reports
niftyindices press releases ind_prsDDMMYYYY.pdf,adds/drops + effective date,UNSURE (2000s?),yes,PDF,none,yes (static PDF),same,CONFIRMED,https://niftyindices.com/Press_Release/ind_prs23022026.pdf
IndexInclExcl.xls,historical inclusions/exclusions,UNSURE start; ends 2020-07,yes,XLS,none,maybe,same,REPORTED,https://archives.nseindia.com/content/indices/IndexInclExcl.xls
NSE shareholding pattern (+XBRL),promoter %; total shares; FII/DII,XBRL 2018+; older HTML (UNSURE),yes (as-on + submission date),web JSON (cookies) / XBRL,none,no/maybe,ToS; cloud-IP blocks,CONFIRMED,https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern
NSE financial results XBRL / Integrated Filing,quarterly+annual P&L; EPS; BS half-yearly,2018 (XBRL),yes (as filed + broadcast time),XBRL XML,none,maybe,ToS,CONFIRMED,https://www.nseindia.com/companies-listing/corporate-filings-financial-results
BSE XBRL results & SHP,results; SHP; CG,SHP ~2016; results 2017-04,yes,XBRL; unofficial api.bseindia.com (pip bse),none,maybe,BSE ToS not found,CONFIRMED (dates),https://www.bseindia.com/static/about/xbrl_info.aspx
NSE delisted / suspended lists,names; dates,UNSURE,n/a,XLSX,none,maybe,NSE ToS,CONFIRMED,https://www.nseindia.com/static/list/list-of-companies-proposed-to-be-delisted
BSE delisted companies,code; date; reason,UNSURE (690 pages),n/a,HTML,none,maybe,not found,CONFIRMED,https://bseindia.com/corporates/Delist_Comp.aspx
MCA21 AOC-4 XBRL,full statements standalone+consol,FY2011,partly,XBRL docs,paid per company view (UNSURE fee),no (login+payment),govt terms,REPORTED,https://www.mca.gov.in/MinistryV2/view+public+document.html
DPE Public Enterprises Survey,CPSE list = PSU flag (no banks/insurers),1960s; yearly PDF,yes,PDF,none,yes,public,CONFIRMED,https://dpe.gov.in/en/node/94892
yfinance (.NS),annual/quarterly statements; shares,~4 yrs annual / ~5 qtrs,no (restated),Python (unofficial),throttled,yes,Yahoo ToS = personal use,REPORTED,https://github.com/ranaroussi/yfinance
screener.in,10+ yrs P&L/BS/CF; ratios,~10-12 yrs,no (latest restated),Excel per company (login),free acct; screen export premium,no,no API; content copyrighted,REPORTED,https://www.screener.in/guides/terms
Tickertape / Trendlyne / Moneycontrol,financials; SHP history,~10 yrs (UNSURE),no,web only,n/a,no,no public API; Trendlyne scraping clause not found,UNSURE,https://trendlyne.com/terms
EODHD Fundamentals,statements; shares; mcap; EPS,2000 for non-US; small cos 6 yrs,not stated,REST JSON,$59.99/mo; free 20 calls/day,yes (key),personal-use licence,CONFIRMED,https://eodhd.com/pricing
Financial Modeling Prep,statements,India depth not found,not found,REST,paid,yes,check licence,UNSURE,https://site.financialmodelingprep.com/developer/docs
Alpha Vantage,US-centric fundamentals,NSE fundamentals not found,no,REST,small free tier (UNSURE),yes,,UNSURE,https://www.alphavantage.co
Kaggle/GitHub/HF datasets,mostly prices; some Nifty50 constituents,varies,no,CSV,free,yes,check each licence,REPORTED,https://www.kaggle.com/datasets/rohanrao/nifty50-stock-market-data
CMIE Prowess dx,financials; ownership; industry; prices; vintages,1989/1990,partly (vintage snapshots),web bulk export,paid (university library),no,no redistribution,CONFIRMED,https://prowessdx.cmie.com/
Capitaline / ACE Equity,full fundamentals,UNSURE,UNSURE,desktop/web,paid,no,licensed,UNSURE (not checked),not found
RBI DBIE,aggregate corporate finance only (no per-company),n/a,n/a,web,free,yes,,UNSURE,https://dbie.rbi.org.in

2. Best plan (cheapest complete path)

Legal gate first: NSE's terms prohibit any systematic or automated data collection on its website, and an NSE circular states that downloading information with scripts or scraping is not permitted, which is why most pages have a CSV download option. So do the one-time historical pull by hand, or ask NSE under its data-sharing policy for research. Keep the GitHub Actions robot for AMFI, DPE, the niftyindices PDFs and your paid API key. For BSE terms the result is "not found", so treat BSE as maybe. 
Terms of Use
 +2

Universe and delistings. From your 2002+ bhavcopies, list every EQ/BE symbol ever traded, with its first and last trade date. Join this to NSE's delisted .xlsx and the BSE delisted list to get a reason code (merger, voluntary, compulsory). You get universe.csv, which is free of survivorship bias for prices.
Shares outstanding, 2024 onward. NSE added an MCAP report (MCAPDDMMYYYY.csv, with Face Value and Issue Size) to the PR press-file zip. Read Issue Size as shares. You get daily shares.csv. 
nseindia
Shares, 2013–2023. NSE's market-cap page has all companies from Dec 2019, top 1000 for Mar 2019, and top 500 for Mar 2016–2018, plus Mar 2013. For other dates, use the niftyindices monthly constituent files, which carry an Equity Capital column (available from April 2013): shares = equity capital ÷ face value. Fill gaps with total shares from the quarterly SHP filings. 
nseindia
tradingqna
Size-rank cross-check, 2017 onward. AMFI's first half-yearly list came out in January 2018, covering Jun–Dec 2017. It ranks every listed company by six-month average market cap across NSE, BSE and MSEI. 
blogspot
wrightresearch
Fundamentals, FY2017 onward, as filed. BSE started voluntary XBRL for shareholding and results in June 2015 and made XBRL results mandatory from April 1, 2017. NSE introduced XBRL compliance filing in April 2018. Parse revenue, PAT, basic/diluted EPS and net worth (from the half-yearly asset and liability statement), keeping the submission timestamp. Since the Mar-2025 quarter, NSE results are under "Integrated Filing – Financials", so handle both feeds. You get fund_pit.parquet (symbol, period, field, value, known_at). 
About XBRL
 +3
Fundamentals before FY2017. There is no free, machine-readable, point-in-time source. The fair choices are Prowess dx through a university library, or EODHD (non-US from 2000, but minor companies only the last 6 years, and point-in-time "not stated"). Screener exports are restated data: use them only for robustness checks, never as the primary input. 
eodhd
Result dates before XBRL. The PR zip's Bmddmmyy.txt holds board-meeting details and Anddmmyy.txt holds the day's announcements. Take the first "financial results" announcement date at or after the board meeting as known_at. 
nseindia
Index membership. Use the monthly constituent files from 2013. Before 2013, chain backwards through the press releases (adds/drops with effective dates) and IndexInclExcl.xls.
Market PE/PB. Download daily Nifty 50 and Nifty 500 P/E, P/B and dividend yield from niftyindices.
Sector, PSU, promoter %. Take sector from the constituent "Industry" column (the value as of that month). For the PSU flag, use the DPE survey appendices plus PSU Bank/CPSE index members. Take promoter % from SHP.

3. Proxies (and whether they're fair)

Market-cap rank before 2013: shares from the nearest earlier SHP (BSE/NSE pages, UNSURE free depth) × March close. This is fair because shares change rarely, as long as bonus/split ex-dates are applied. If shares are missing, ranking by turnover is not fair: it is biased toward liquid names.
Top-500 universe before 2013: CNX 500 members at each date (from press releases). This is fair and close to the rule, though the index uses free-float criteria rather than full market cap.
No look-ahead without a filing timestamp: use FY(t) data only from the later of the announcement date + 1 day and a fixed lag (quarterly ~45 days, annual ~60 days; SEBI LODR deadlines from memory, UNSURE). The Motilal study ranks in March using FY(t) results. To avoid that look-ahead, use FY(t−1) at March, or move the rebalance to July 1.
PE before 2024: compute it yourself as price ÷ TTM EPS known at that date. The NSE PE file is recent only and was removed from the PR zip from March 24, 2025. 
nseindia
PSU flag: the DPE survey does not cover banking institutions or insurance companies, so add PSU banks and insurers by hand (Nifty PSU Bank, LIC, GIC, New India). 
dpe

4. Traps and fixes

Restated financials: Screener, Yahoo and EODHD show the latest versions. Store the first-filed value plus known_at, and keep restatements in a separate table.
Ind AS switch (FY2016–18) and standalone vs consolidated: pick one basis (consolidated where it exists, standalone otherwise) and flag the switch year. Don't compute growth across a basis change without flagging it.
Nifty PE basis break: a reported drop on 31 Mar 2021 reflects the move to consolidated earnings, not a market move. For R3, compare each stock against the Nifty PE on the same basis, or use the median PE of the top 500. 
tapetide
Bonus/split: apply adjustment factors (from the Bc files or corporate actions) to shares and EPS together. Never mix adjusted prices with unadjusted EPS.
Mergers/demergers: after a demerger, carry the parent's TTM PAT only until the first post-demerger result. For a merger exit, give the holder the acquirer's shares at the swap ratio.
Delisted stocks: for a compulsory or failure delisting, use the last price, or −100% if trading was suspended for more than 6 months. For a voluntary delisting, use the exit price. Don't drop them.
FY changes (some MNCs use December years) and 9- or 15-month years: annualize, or use TTM built from quarters.
Bhavcopy format break on 2024-07-08: the URL moved and column names and date format changed. Map the old SYMBOL/SERIES columns to the UDiFF ones. 
tradingqna
Symbol and ISIN changes: key everything by ISIN. Keep a symbol→ISIN history from each day's bhavcopy, since ISIN is a column there in the old format.
Negative or zero earnings: PEG is "n/a". Don't drop these stocks, because that changes the base rate.
Early years (2002–2012): XBRL didn't exist; the paid replacement is Prowess, the manual one is PDF results. Report results separately for 2003–12 and 2013+ so the reader sees which part of the evidence is weaker.
Small crash sample (R5/R6): only 2–3 episodes (2008–09, 2020, possibly 2011). Present them as case studies, not as statistically significant results.

5. Pseudo-code

python
# helpers: mcap(t)=close(t)*shares_known(t); ttm(x,t)=sum of last 4 quarters with known_at<=t
# fy(x,y,t)=FY y value only if known_at<=t; tr(s,a,b)=total return incl. dividends, delisting rule

# R4 size buckets, 5-yr hold
for t in march_ends(2005, 2021):
    r = rank(mcap(t) over universe_alive(t))              # 1 = biggest
    bucket = cut(r, [1,100,250,1000])                      # 1-100 / 101-250 / 251-1000
    for b in buckets:
        S = stocks in b
        cagr[b,t]  = (mean(1+tr(s,t,t+5y) for s in S))**(1/5)-1   # equal weight
        up[b,t]    = share of S with rank_at(t+5y) <= 100           # delisted = not up
report mean/median by bucket; split 2005-12 vs 2013+

# R2 trailing PEG
for t in march_ends(2007, 2021):
    for s in top500(t):
        pe = close(s,t)/ttm(EPS,t)
        g3 = (fy(PAT,Y-1,t)/fy(PAT,Y-4,t))**(1/3)-1  # Y=FY ending t; needs both PAT>0
        g5 = same with Y-6, power 1/5
        peg = pe/(100*g) if pe>0 and g>0 else NA
        bkt = cut(peg,[0,1,2,3,inf]) or "n/a"
    ret5[bkt] = EW tr(t,t+5y); repeat with g5

# R3 base rate, 10-yr
for t in march_ends(2005, 2016):
    U = top500(t); niftyPE = nifty_pe(t)                 # same earnings basis
    flag = roe_known(s,t)>15 and pe(s,t)<niftyPE
    hit  = (1+tr(s,t,t+10y))**(1/10)-1 >= 0.15          # delisted counted as miss/loss
    tally p(hit|flag), p(hit|~flag), p(hit|all)
pool all t; report lift = p(hit|flag)/p(hit|all) with bootstrap CI by year-cluster

# R1 composite screen
for t in march_ends(2007, 2021):
    U = top500(t) - sector in {Agri,Commodity,IT,Pharma,Utilities}   # sector as of t
    U = [s for s in U if roe_known(s,t)>12 and g3(s,t)>=0.20 and peg(s,t)<2]
    P = concat(top 3 by mcap(t) within each sector of U)
    port = EW tr(P,t,t+5y); bench = EW tr(top500(t),t,t+5y)
    log len(P), port-bench; flag years with len(P)<10

# R5/R6 cheap valuation: normal vs post-crash
dd = nifty/cummax(nifty)-1
crash_dates = first date dd<=-0.30 per episode, plus trough date
entries = month_ends(2004..2021); tag = "post-crash" if within 12m after a crash_date else "normal"
for t in entries:
    for m in [PE, PB, PS]:                    # PS = mcap/ttm(Sales,t); BV from half-yearly BS
        q = quintile(m(s,t) over top500(t))   # exclude m<=0 into own bucket
        fwd[m,q,tag] += EW tr(q-stocks,t,t+3y) and t+5y
compare cheapest-quintile excess return: normal vs post-crash; show per-episode table

6. Sources: the official pages are in the CSV link column. Two others I used: the NSE "no scripts" circular (https://archives.nseindia.com/content/circulars/WEB45032.pdf) and the Motilal Oswal 30th Wealth Creation Study page (https://www.motilaloswal.com/wealth-creation-study). The 30th study came out on 11 Dec 2025 and covers the five years 2020–2025 (March ending). 
motilaloswalgroup