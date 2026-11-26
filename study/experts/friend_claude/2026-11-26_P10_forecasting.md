ROLE: You are an expert in forecasting science (Philip Tetlock's Good Judgment Project / "Superforecasting", Daniel Kahneman's "Noise" and base-rate thinking, Nate Silver's "The Signal and the Noise", Annie Duke's "Thinking in Bets") and in applying it to financial markets. Use web search to confirm methods, numbers and studies.

GOAL: I run a study of the Indian stock market (Nifty, Bank Nifty, ~1,850 stocks, gold/silver). A free robot collects data every day. I want to write explicit probability forecasts every day ("Nifty up over next 5 days: 58%", "RBI will hold in Dec: 70%", "this rumour is true: 40%"), score them later, and improve — like superforecasters. Design the best system for this.

PART A — METHODS (explain simply, with numbers from studies):
1. What made superforecasters better (training, teams, updating, granularity of probabilities, base rates first then adjust)? Effect sizes from the Good Judgment Project.
2. Outside view vs inside view; reference-class forecasting — how to pick a reference class for market events (e.g. "Nifty after a 2% up day when VIX < 18").
3. How to update a forecast with new evidence (Bayes in plain words; how big a step to move for weak vs strong evidence; avoiding over- and under-reaction).
4. Scoring: Brier score, log score, calibration curves, resolution vs reliability; what a good Brier score is for 50/50-ish market questions; minimum number of forecasts before judging skill.
5. Known evidence on market forecasting skill: how accurate are economists/strategists/analyst targets (studies, numbers); where some skill exists (e.g. volatility, short-horizon reversals, event outcomes, prediction markets like Polymarket/Kalshi accuracy studies).
6. Combining many weak signals: averaging forecasts, "wisdom of crowds", extremizing, model + human combination; how to avoid overfitting when combining 20+ indicators.
7. Emotions and biases that hurt traders' forecasts (overconfidence, recency, confirmation, loss aversion) and concrete de-biasing routines (pre-mortem, "what would change my mind", forecast before seeing price).

PART B — DESIGN FOR MY STUDY:
1. A daily forecast template (5-8 fixed questions + 1-3 event questions), each with: exact question wording, resolution rule (what counts as yes), horizon, base rate source.
2. How to set the base rate for each question from historical data (I have daily data from 2002).
3. How to record reasoning briefly (3 lines) so it can be reviewed.
4. Weekly and monthly review routine: calibration table, Brier by question type, which signals helped, what to change.
5. When is a forecast good enough to act on with real money (link probability + payoff to position size, e.g. Kelly fraction, but conservative)? Give a simple rule with examples.
6. Common mistakes in such self-scoring systems (cherry-picking questions, changing resolution rules, too few forecasts, forecasting only easy questions).

OUTPUT FORMAT (exactly this order):
1. Key methods (Part A) as short numbered points with numbers and sources.
2. Daily template table: question, resolution_rule, horizon, base_rate_method.
3. CSV block for a forecast log, header: date,question_id,question,horizon_days,prob,reasoning_3_lines,base_rate,resolution_date,outcome,brier
4. Review routine (weekly, monthly).
5. Act-with-money rule (with 3 worked examples).
6. Mistakes list.
7. Sources list.
Keep it under 160 lines. English is fine. For study only.

I ran a few searches to check the key study figures before writing this. Everything is below in the order you asked for, under 160 lines. The base rates in the CSV are placeholders, so work out your own from your 2002+ data.

1. Key methods (Part A)

What made superforecasters better. They used three levers: training, teams and tracking the best people into elite groups. Training corrected cognitive biases, encouraged forecasters to use reference classes, and gave them heuristics such as averaging when several estimates were available. The training lasted under an hour, yet it improved Brier scores by 6 to 11% over the control group. On average, teams were 23% more accurate than individuals. Superforecasters were reportedly over 30% more accurate than US intelligence analysts forecasting the same events with access to classified information. Treat that 30% with some caution, because the comparison mixed groups: it was regular forecasters plus a few dozen superforecasters versus the analysts. 
qt4rg4n9vr noSplash 4ff67e56b3dac616e0163b75090705e6
 +4
Exact numbers beat vague words. Rounding numeric probabilities into the bins that words like "likely" imply consistently lost predictive accuracy (Friedman et al., 888,328 forecasts). Write 58%, not "probably up." 
harvard
Update often, in small steps. The most accurate forecasters made frequent, small updates. Low-skill forecasters stuck with their first judgment or made rare, large revisions. 
repec
Noise matters more than bias. The BIN model found noise reduction was the main driver of improvement. Even training designed to reduce bias worked mostly by reducing noise. In practice, fixed questions, fixed rules and checklists help you as much as fighting biases does. 
wu
Outside view first, then inside view. Start from how often this kind of thing happened historically (the reference class). Only then adjust for today's specifics. To pick a reference class for "Nifty after a 2%+ up day with VIX < 18":
Check the size of the class. If n < 100, widen it, for example to 1.5%+ days or VIX < 20.
Compute two or three neighbouring classes and average them.
Shrink toward the unconditional rate: p = (k + m·p0)/(n + m), with m ≈ 30. Here k is the number of "yes" cases in the class, n is the class size and p0 is the all-days base rate.
Your 5-day windows overlap, so count independent cases as roughly n/5.
Bayes in plain words. New odds = old odds × likelihood ratio (LR), where LR = how much more often you'd see this evidence if "yes" than if "no."
Weak evidence (LR 1.2) moves 50% to 54.5%.
Strong evidence (LR 3) moves 50% to 75%.
Most market news is LR 1.05–1.3, so the usual step is 2–6 points.
Superforecasters' average probability change was about 3.5%. 
utep
Over-reaction means jumping more than 15 points on one headline. Under-reaction means "confirming" yesterday's number despite new evidence.
Scoring.
Brier = (p − outcome)²: 0 is perfect, and always saying 50% scores 0.25.
Log score = −ln(p you gave to the actual outcome). It punishes confident misses harshly.
Brier splits into Reliability − Resolution + Uncertainty. Reliability is calibration: do your 60%s happen 60% of the time? Resolution is how far your forecasts move away from the base rate when they should.
Judge yourself against the base rate with the Brier Skill Score: BSS = 1 − BS/BS_base. If 5-day "up" happens 55% of the time, the base-rate Brier is 0.55 × 0.45 = 0.2475. Realistic market skill is a BSS of 0.5–3%, which means a Brier of about 0.240–0.246. Anything far better probably has a leak or a bug.
Sample size: telling a 55% hit rate from 50% needs about 270 independent forecasts (one-sided, 95%), and about 800 for 80% power. Overlapping 5-day forecasts count about 1/5 each, so give it 1–3 years before you judge skill.
A useful check from a multiyear calibration study: it found a small amount of overconfidence (3%), mostly on the most confident forecasts. 
escholarship
Evidence on market forecasting skill.
Gurus: an eight-year study of gurus' market calls found them right 47% of the time on average, slightly worse than chance. In CXO's current tracking, 1,206 calls were 41% right, while always saying "stocks will go higher" on the same dates was right 62% of the time. The base rate beats the experts. 
kiplinger
cxoadvisory
Analyst targets: only 38% of 12-month target prices were met at the end of the horizon, though 64% were met at some point during it. 
sufe
Economists: of 153 recessions in 63 countries from 1992 to 2014, only five were predicted by the private-sector consensus in April of the year before. 
bnnbloomberg
Prediction markets: Kalshi's Brier score falls from about 0.08–0.09 three months out to about 0.02 at close. These are mostly easier questions than Nifty direction. Also, only 0.15% of takers forecast significantly better than the market under strict testing. 
kalshi
kalshi
Where some skill does exist (classic literature, not re-checked here): volatility clustering (tomorrow's volatility tracks today's), short-horizon reversals (Jegadeesh 1990, Lehmann 1990), 3–12-month momentum, post-earnings drift, and outcomes of scheduled events where the consensus is visible.
Combining many weak signals.
Average in log-odds space.
Equal weights usually beat "optimised" weights out of sample (Dawes' improper linear models; the "forecast combination puzzle").
Extremizing: when independent signals agree, push the average outward a little, e.g. odds^1.3. Fit that exponent on past data only.
Model plus you: the model gives the anchor, you may adjust it by up to ±10 points, and you score both separately.
With 20+ indicators, use a regularised logistic model tested walk-forward, keep at most 5 signals per question, and count how many combinations you tried (multiple testing inflates results; see Bailey & López de Prado on the deflated Sharpe ratio).
De-biasing routines.
Write the probability before you look at today's price or news. This fights anchoring and recency.
Write one line on what would move you 10 points. This fights confirmation bias.
Pre-mortem: "It is 5 days later and I was wrong. Why?"
Never forecast a position you hold without flagging it. Loss aversion and wishful thinking bend those numbers.
Cap any probability at 85% unless the base rate already supports it. This fights overconfidence.

2. Daily template

id	Question (exact wording)	Resolution rule (YES =)	Horizon	Base-rate method
Q1	Will Nifty 50 close higher in 5 trading days than today?	Close(t+5) > Close(t), official NSE close	5d	% up 5-day windows since 2002, by VIX bucket × above/below 200DMA, shrunk
Q2	Will Nifty 50 gain more than 2% over the next 20 trading days?	Close(t+20)/Close(t) − 1 > 2.0%	20d	Same, 20-day windows
Q3	Will Bank Nifty beat Nifty over the next 5 trading days?	Bank Nifty 5d return > Nifty 5d return	5d	% of windows since 2002 (≈50%); condition on the 20d relative trend
Q4	Will India VIX close higher in 5 trading days than today?	VIX close(t+5) > VIX close(t)	5d	History from ~2008; condition on VIX vs its 1-year median (mean reversion)
Q5	Will Nifty close ≥3% below today's close on any day in the next 10 trading days?	Min Close(t+1…t+10) ≤ 0.97 × Close(t)	10d	Hit rate since 2002, by realised-volatility bucket
Q6	Will Nifty move more than 2% either way over 5 trading days?	Abs(5d return) > 2%	5d	By VIX/realised-vol bucket; your most learnable question
Q7	Will the share of your ~1,850 stocks above their 50DMA be higher in 5 trading days?	Breadth(t+5) > Breadth(t), same universe and rules	5d	Breadth series since 2002; condition on breadth level (extremes revert)
Q8	Will MCX gold (₹) beat Nifty over the next 20 trading days?	Gold 20d return > Nifty 20d return	20d	20-day windows since 2002
E1–E3	Event questions, e.g. "Will the RBI MPC keep the repo rate unchanged at its December 2026 meeting?" / "Will company X officially confirm the rumoured deal by date D?"	Official RBI statement or exchange filing only; set a deadline	To event	RBI: % hold decisions in similar inflation/growth settings, then compare with economist polls. Rumours: your own log of past rumours confirmed within 30 days

Base-rate steps (§B2): (1) compute the unconditional rate over all overlapping windows from 2002; (2) compute rates in 2–3 conditioning buckets, never more than 2 conditions at once; (3) shrink with m ≈ 30; (4) recompute monthly on an expanding window, never with future data. Store each base rate in the log so you can score "you vs base rate."

3. Forecast log (CSV). Reasoning has 3 lines separated by " | ": (1) the base rate and why that class, (2) the inside-view adjustment and how many points, (3) what would change your mind. The first row is a fictional resolved example; the base rates are illustrative.

date,question_id,question,horizon_days,prob,reasoning_3_lines,base_rate,resolution_date,outcome,brier
2026-11-18,Q1,Nifty close(t+5) > close(t),5,0.58,"BR 55% (VIX 12-15 & >200DMA, n=610, shrunk) | +3: breadth thrust, FII buying 3d | -10 if Nifty closes < 20DMA",0.55,2026-11-25,1,0.1764
2026-11-26,Q1,Nifty close(t+5) > close(t),5,0.56,"BR 55% same bucket | +1: mild positive breadth; no event edge | -8 if VIX > 16",0.55,2026-12-03,,
2026-11-26,Q4,India VIX close(t+5) > close(t),5,0.47,"BR 46% when VIX below 1y median | +1 policy week ahead | +10 if global VIX spikes >20",0.46,2026-12-03,,
2026-11-26,Q6,Abs(Nifty 5d return) > 2%,5,0.24,"BR 22% for VIX 12-14 bucket | +2 RBI meeting inside window | +8 if gap > 1% at open",0.22,2026-12-03,,
2026-11-26,E1,RBI MPC holds repo rate at Dec 2026 meeting,0,0.70,"BR from past MPC decisions in similar CPI regime | -5: soft CPI print; polls split | -15 if RBI official signals cut",0.65,(RBI calendar date),,

Set brier = (prob − outcome)² once the outcome is known. Never edit prob, reasoning or the rule after the entry is saved; to change your view, add a new row.

4. Review routine

Weekly (20 min): resolve all due rows. Compute Brier per question compared with the base-rate Brier. Read every miss where you gave ≥70% and tag the cause: wrong reference class, over-reacting to news, or an unforeseeable shock. Note one lesson.
Monthly (1 hour):
Calibration table with buckets 0–10%, …, 90–100%: count, average forecast and actual frequency. Flag any bucket off by more than 5 points (once it has 30+ forecasts).
Brier, BSS and log score by question type and by regime (VIX bucket).
Resolution check: are you moving away from the base rate at the right times?
Signal audit: for each signal named in your reasoning, compare its hit rate with the base rate. Drop signals with no lift after 100+ uses.
Add or remove at most one question per month, written down before you see any results.
Quarterly: recompute base rates, and fit the model/human mix and the extremizing exponent on past data only.

5. When to act with real money

Four gates must all pass:

(a) That question type has ≥300 resolved forecasts (count overlapping windows at about 1/5 each), a BSS > 0, and calibration within ±5 points in the relevant bucket.
(b) Shrink your probability toward the base rate: p_use = BR + 0.5 × (p − BR).
(c) Expected value after costs is positive against the actual payoff, not a 1:1 assumption.
(d) Kelly fraction f* = p − (1 − p)/b, where b is win size ÷ loss size. Use ¼ of f*, capped at 1% of capital at risk per idea and 5% in total.

Examples:

Q1 at 58% vs a base rate of 55%. p_use = 56.5%. Long Nifty futures with a 1.5% stop and a 1.5% target, so b = 1. f* = 0.565 − 0.435 = 0.13; a quarter is 3.3%, so the cap applies: 1% risk. Most of this edge is the base rate itself, which simply holding the index already gives you. Your own edge is only 1.5 points, so trade only if the gates have passed.
E1, RBI hold at 70%, with economists' consensus at about 80% hold. You lean toward a cut, but there is no clean binary instrument, and option positions mix in volatility and other effects. Log only, no trade. This is the default for event questions.
Rumour true at 40%. The stock is up 8% on the rumour. If it's false, you expect −6%; if true, +4% more. A short wins 6 with p = 0.6 and loses 4, so b = 1.5. Shrinking toward a rumour base rate of, say, 50% gives p_use = 0.55. f* = 0.55 − 0.45/1.5 = 0.25; a quarter is 6%, so cap at 1% risk, but only through stock futures (cash-market shorts in India are intraday only). If your rumour questions don't yet have 300 resolved forecasts, paper trade.

6. Common mistakes in self-scoring

Picking questions after looking at the chart, or skipping "boring" days. Answer the fixed questions every day, no exceptions.
Changing resolution rules or deadlines after the fact, for example "intraday counts." Rules are frozen at creation.
Treating overlapping 5-day forecasts as independent, which inflates your sample size about fivefold.
Judging skill after 50 forecasts. With fewer than 300, assume luck.
Only easy or extreme questions such as "Nifty above 10,000?", which flatter Brier. Always report BSS against the base rate.
Base rates built with future data, or over-conditioned buckets with n < 50.
Hugging 50% to avoid embarrassment (no resolution), or being 80%+ on coin-flip questions (poor calibration).
Hindsight-rewriting the reasoning, or deleting bad rows. Keep the file append-only, ideally versioned with git.
Scoring only your human forecasts. Always log the model or base-rate forecast next to yours, so you know whether your adjustments add value.
Letting P&L judge forecasts: a good forecast can lose money, and the reverse (Annie Duke's "resulting").

7. Sources

Chang, Chen, Mellers & Tetlock (2016), training study — dlab.sauder.ubc.ca/sjdm/journal/16/16511/jdm16511.html
Mellers et al., "Improving the Accuracy of Geopolitical Risk Assessments" (2019)
Friedman et al., "The Value of Precision in Probability Assessment," International Studies Quarterly (2018)
Atanasov et al., "Small steps to accuracy," OBHDP (2020)
Satopää et al., "Bias, Information, Noise: The BIN Model of Forecasting," Management Science (2021)
Moore et al., "Confidence Calibration in a Multiyear Geopolitical Forecasting Competition"
Karvetski, "Superforecasters: A Decade of Stochastic Dominance," Good Judgment (2021)
CXO Advisory, Guru Grades — cxoadvisory.com/gurus/
Bradshaw, Brown & Huang, Review of Accounting Studies (2013)
An, Jalles & Loungani, IMF WP/18/39 (2018)
Kalshi Research, calibration studies (2026)
Not re-checked in this session: Kahneman & Lovallo (1993), Dawes (1979), Jegadeesh (1990), Tetlock & Gardner, Superforecasting (2015).