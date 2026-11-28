28Nov_P16.txt
TXT

I'll pull the SEBI studies, the rule-change data and the research on option-buyer edge, then put together the tables and 10 rules.

Below are the tables, the 10 rules and the links you asked for. Two things to know first. The newest SEBI data is the August 2026 pair of studies covering FY25 and FY26. And there is almost no India-specific, cost-inclusive evidence that buying options as an event play has an edge. Every rule below is a hypothesis to paper-test, not a known edge, and I've marked which parts have data behind them.

(1) SEBI studies: key numbers
Study	Headline	Other key numbers
Jan 2023 (FY22)	89% of individual traders in equity F&O incurred losses, with an average loss of Rs 1.1 lakh during FY22	Only 11% made a profit, with an average profit of Rs 1.5 lakh. 98% traded options and 11% traded futures, versus 89% and 43% in FY19
Sep 2024 (FY22–24)	1.13 crore unique traders lost a combined ₹1.81 lakh crore, including transaction costs	Only 7.2% made a profit over three years, and just 1% made more than ₹1 lakh after costs. More than 75% of loss-makers kept trading
Jul 2024 intraday cash (FY23)	Over 70% of intraday traders lost money, with an average loss of Rs 5,371	Young traders and 'very frequent' traders (more than 500 trades a year) had higher loss rates
Jul 2025 (FY25)	Net losses rose to Rs 105,603 crore from Rs 74,812 crore, and over 91% made losses	Unique traders fell from 61.4 lakh in Q1 to 42.7 lakh in Q4
Aug 2026 (FY25–26)	Loss-makers fell from 90.9% to 87.7%; aggregate net loss fell from ₹1,11,788 cr (revised) to ₹91,685 cr	Before costs only 82.1% lost. Individuals paid about ₹25,000 cr in transaction costs each year. Options were about 92% of losses 
Sebi study suggests 89% retail traders in equity F&O suffered losses
 +8

Profile of the 7–12% who win. SEBI never profiles winners directly. These are the loss rates by group:

Factor	Evidence
Buyer vs seller	97% of traders were mainly options buyers. 'Majorly Options Sellers' had the lowest share of loss-makers (44%) and buyers the highest (90%). However, sellers lost an average of ₹51.7 lakh per trader
Median return on capital (FY26)	Only-buyers −114%, majorly-buyers −15%, majorly-sellers +1%
Age	89% of traders under 30 lost in FY26, against 81% of those over 60
Capital	Peak margin above ₹1 Cr: 36% loss-makers. Below ₹10K: 90%
Frequency	Traders active more than 100 days were 42% of traders but 87% of losses. Average loss was ₹0.22 lakh for ≤100 days and ₹2.76 lakh for >100 days
Persistence	Only 0.5% of the FY22 cohort were profitable in every one of five years; 65.6% lost every year. Of those who earned over ₹10 lakh in FY22–24, about 48% were profitable again in FY25–26
Product	Index options: 87% loss-makers in FY26. Stock options: 76%
Holding period	SEBI has no data on this. The behaviour study gives no holding-period or 0DTE P&L figures. An academic paper finds day-trading profits flat to weakly positive and positions held past the day account for significant losses 
www.sebi.gov.in
 +2
(2) Evidence on when long options make money
Setup	Evidence	Strength
Earnings straddles (US)	ATM straddles bought 3 days before earnings and held to the announcement returned 3.34%. The effect is strongest after a period of low volatility	Strong (JFQA, J. Empirical Finance)
Pre-results IV run-up (India)	An IIM study of 2015–2019 results found IV rose steadily before results and fell sharply after. A Zerodha backtest bought ATM straddles 10 days before results and exited the day before (209 stocks, Oct 2021–Aug 2026): average +4.81%, median −2.19%, win rate 46.24%, 2,643 trades, with no costs or slippage stated	Moderate. The average is driven by a few big winners, and costs could erase it
Selling after results	Selling an ATM straddle after results gave positive average returns at all six exit times	So post-results options still look overpriced. That argues against buying after results
Index VRP / overnight	Nifty option sellers' premium is mainly a reward for overnight risk, and the gap is weaker on days with big jumps in the index	Strong (J. Futures Markets 2024). Buyers bleed overnight, not intraday
Expiry day / 0DTE	75% of FY26 index options turnover was within one day of expiry, and that is where retail losses concentrate. On expiry days, SEBI alleged Jane Street moved Bank Nifty and Nifty 50 closing levels	Strong negative evidence for buyers
VIX regimes / IV rank / skew	No usable India evidence found. A single informal note estimates a half-life of about 60 trading days for India VIX shocks	Weak. Test before relying on it
Trend days	No data found	None 
B0A1714D795BD9799087BCCC2AD A01C4283 54641
 +7
(3) What the rule changes did
Change	Date
One weekly index expiry per exchange; higher tail-risk margin on expiry day	Nov 20, 2024
Bigger contracts (Nifty lot size 75)	Jan 2, 2025
Premium collected upfront from buyers; no calendar-spread margin benefit on expiry day	Feb 10, 2025
NSE expiry moved to Tuesday, BSE to Thursday	Sep 1, 2025
Nifty lot 75 → 65, Bank Nifty 35 → 30	First weekly with the new lot: 6 Jan 2026 
www.sebi.gov.in
 +3

Effects:

The 0DTE share of index options turnover fell from 70% to 59%. 
sebi
Median return on capital for pure buyers improved from −187% to −114%; for sellers it went from −0.4% to +1%. 
sebi
SEBI warns the lower loss rate partly reflects the 20% fall in active traders. 
sebi
One side effect: a shorter week means faster time decay for buyers. With a Tuesday expiry, Monday is only one day before expiry. 
indmoney
(4) Ten option-buy rules to paper-test

The same limits apply to every rule:

Risk at most 0.5% of paper capital per trade and 2% per week.
Count all costs: brokerage, STT, slippage of 1–2 ticks per leg.
Pass mark: at least 100 trades, a positive median after costs, and results that hold up out-of-sample.
#	Catalyst and entry	Strike / expiry	Exit	Base-rate argument
1	F&O stock results. Enter at 3:00 pm, 10 calendar days before results	ATM straddle, first expiry after the results date	3:15 pm, last session before results	India backtest: mean +4.8% but median −2.2% (above). Has data, but no costs
2	Same as #1, but only stocks whose own past median for this trade was positive (rolling, no look-ahead)	Same	Same	134 of 209 stocks had a positive average but only 89 a positive median. Tests whether results differ by stock. Risk of overfitting
3	Same as #1, but only when the current IV is in the bottom third of that stock's past pre-results IVs	Same	Same	The US effect is stronger after low volatility (above). Not tested in India
4	Hold through results only when the straddle's implied move is below the stock's median actual results-day move over the last 8 quarters	ATM straddle, nearest expiry	Next day, 9:45 am	US paper: a high historical move relative to the implied move predicts higher straddle returns. No India test
5	Union Budget. Enter 8 sessions before	Nifty monthly ATM straddle	Close of the last session before the Budget (IV crush comes after)	IV tends to rise before economic events and fall after. Only about 1 event a year, so the sample is too small to prove anything
6	RBI MPC. Enter 5 sessions before the announcement	Nifty monthly ATM straddle	Close the day before	MPC IV spikes are typically smaller than Budget ones. No data; expect a thin edge
7	Intraday only, non-expiry days. Enter after 10:15 am if Nifty breaks the 9:15–10:15 range by 0.3%	ATM, next weekly (not 0DTE)	Hard exit at 3:10 pm; stop at −40% of premium	Sellers earn their premium overnight; intraday long returns are roughly flat before costs (above). Costs will likely decide this
8	VIX regime: India VIX in the bottom 10% of its 1-year range	Nifty ATM straddle, 30–45 DTE	15 sessions, or VIX +25%	Mean-reversion idea from a weak source. VRP research says long volatility loses on average. Unproven
9	Trend day: Nifty gaps more than 1% and the first 30-minute candle closes in the gap's direction	ATM in the gap's direction, next weekly	Same day, 3:10 pm	No data at all. Pure hypothesis
10	Control rule (expected to fail). Tuesday expiry, after 1:30 pm	Nifty OTM, 0DTE	Expiry	This is what most retail does. If it doesn't lose in your test, the backtest has a bug 
We backtested pre-earnings Option buying
 +3

Rejected idea: buying options right after results to ride a post-results drift. Selling after results was profitable on average, so post-results options are still expensive (above). I found no India drift data to argue the other way.

Key links
SEBI FY25–26 profitability study: https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf
SEBI FY25–26 trading-behaviour study (buyers vs sellers): https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233601328.pdf
SEBI Jul 2025 study (FY25): https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1751900271726.pdf
SEBI Sep 2024 press release: https://www.sebi.gov.in/media-and-notifications/press-releases/sep-2024/updated-sebi-study-reveals-93-of-individual-traders-incurred-losses-in-equity-fando-between-fy22-and-fy24-aggregate-losses-exceed-1-8-lakh-crores-over-three-years_86906.html
SEBI Jul 2024 intraday study: https://www.sebi.gov.in/media-and-notifications/press-releases/jul-2024/sebi-study-finds-that-7-out-of-10-individual-intraday-traders-in-equity-cash-segment-make-losses_84948.html
Agarwal, Ghosh, Prabhala, Zhao, "Animal Spirits on Steroids" (India retail options): https://www.cfr-cologne.de/download/workingpaper/cfr-25-09.pdf
Bhat, Pandey, Rao (2024), day vs night returns on Nifty options: https://law-journals-books.vlex.com/vid/the-asymmetry-in-day-1115554990
Zerodha pre-results straddle backtest: https://inthemoneybyzerodha.substack.com/p/we-backtested-pre-earnings-option
Xing & Zhang, earnings straddles (JFQA): https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/anticipating-uncertainty-straddles-around-earnings-announcements/7B34877AD5E06304BA3C55FBA3219FDD

Bottom line: the only India data pointing to an edge for buyers is the IV run-up before stock results (rules 1–3). Even that has a negative median and no costs counted. If you test anything, test those three first.