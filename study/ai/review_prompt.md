TAG: condor-2026-11-22

You are an independent, skeptical quant reviewer. Another AI (Claude) ran the study below. Your job is NOT to agree. Find flaws, biases, bugs-in-method, missing tests and alternative explanations. Be concrete and short. Answer in English with these sections:
1) Top 5 methodological risks (ranked, each with why it could change the conclusion)
2) Tests that are missing and should be run next (specific, doable with daily NSE bhavcopy data: open/high/low/close/settle/contracts per option per day)
3) Is the final conclusion justified? (yes / partly / no + why)
4) Any better variant of the strategy worth testing (specific rules)
5) Anything in the numbers that looks suspicious

## Context
A user's friend claims a Nifty weekly iron condor is very profitable. Two different rule sets were tested on REAL NSE F&O bhavcopy prices (daily OHLC + settle for every option contract, 2010-Nov 2026).

### Test A: friend's AlgoTest backtest (Jan 2024-Nov 2026, 107 weeks listed)
Rules: entry 9:35 AM on the day after weekly expiry (~6 days before next expiry), SELL ATM+400 CE and ATM-400 PE, BUY 200 points further out, hold to expiry (exit 3:14 PM), qty 325 (5 lots of 65). No costs in friend's numbers.
- Verified: all 420 legs' AlgoTest entry prices fall inside that day's NSE low-high; exit prices match expiry intrinsic (median diff 0.1 pt). Data is genuine.
- Friend's 107 weeks: gross +Rs2.68 lakh; robust to shifting strikes +-100 points (+2.1 to +3.0 lakh). Avg loss 2.9x avg win; 16 weeks lost > Rs30k.
- Estimated costs (brokerage Rs20/order+GST, STT 0.1% sell premium, exchange fees, slippage 0.5 pt/leg/side): ~Rs900-1,550/week -> net +1.0 to +1.7 lakh.
- 149 weekly expiries existed in the period; 45 normal weeks are missing from the friend's list (reason unknown; 2 listed dates are special sessions). On those 45 weeks the same rules (Claude's ATM from day's open) lost -0.9 to -1.4 lakh with 9-11 losses > Rs30k. All 149 weeks: -1.75 lakh to +6k depending on ATM rounding.
- Friend's Excel "with Rs25k weekly SL" = +6.2 lakh, but it only capped the EXPIRY P/L at -25k. Path-aware SL (checked at daily close only): 32 weeks hit SL, 15 of them were expiry winners -> -1.03 lakh gross.
- Same rules 2019-2026 (Claude's ATM): net negative every year per lot.

### Test B: big grid (Claude), 4 indices (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY) + 14 large stocks, 2010-2026
- Model-free: forward F = K* + C - P at strike minimising |C-P|; expected move EM = 1.25 x ATM straddle (close).
- Short call = first strike >= F + z*EM, short put = last strike <= F - z*EM; hedge = w*EM further (>= 1 strike). z in {0.5,0.75,1,1.25,1.5,2}, w in {0.5,1.0}.
- Entry at CLOSE on: day after previous expiry ("after"), 3 trading days before expiry ("d3"), 1 day before ("d1"), (monthly: also 10 days before).
- All 4 legs must have actually traded (contracts>0) at entry, else skip the cycle.
- Exits checked at daily close: hold to expiry, target 50%, T50+SL100%, T50+SL200%, SL100% only, T60+SL150% (friend's Pine). Plus pessimistic intraday-SL variants (SL triggered if short-leg HIGH minus hedge LOW on one side + other side close exceeds SL; exit at SL level).
- Expiry settlement = intrinsic using expiry-day underlying from put-call parity of traded closes (validated vs Nifty spot close: median abs error 4.5 pts). (The exchange 'settle' column on expiry day holds the underlying price or 0, so it was NOT used.)
- Costs: slippage max(0.05, 1% of price) per leg per side for indices (2.5% stocks), Rs20/order+GST, STT 0.1% sell premium, exchange 0.0353%.
- Metric: P/L after costs / max risk (wing width - credit).
- Pre-registered PASS: n>=60, mean>0 in all 3 equal time-thirds, profit factor>=1.15, neighbouring z also positive.
Results:
- 5,988 combos (with intraday variants ~8,600). Only 28% of combos positive. ~269 PASS.
- Out-of-sample (best combo chosen on first half of each symbol's history, tested on second half): only 10 of 20 symbol-cycles stayed positive; average +5.4% -> -0.77%.
- Monthly stock options: median combo clearly negative (-1.5% to -4% per trade).
- Weekly entry timing (median across combos): after -0.44%, d3 +0.84%, d1 +0.86%.
- NIFTY weekly "after" entry (friend's timing): essentially every setting zero/negative over 2019-2026.
- NIFTY weekly best region: entry d3, z 1.0-1.5, w 1.0 (wide hedge). E.g. d3 z1.25 w1.0: hold +Rs71.5k/lot over 2019-2026 (290 trades, win 88%), SL100 at close +93k, SL100 intraday-pessimistic +73k (PF 1.41, all thirds positive). Median credit 20.9 pts, width 300, worst trade -Rs25k/lot. By year (hold, Rs/lot): 2019 +1.8k, 2020 +14.5k, 2021 +3.8k, 2022 +11k, 2023 +18.4k, 2024 -13.3k, 2025 +49.8k, 2026 -14.4k.
- Narrow hedge (w0.5) settings that pass at close-check turn negative under intraday-SL check.
- BANKNIFTY weekly (until Nov 2024 when weeklies ended) shows the same d3 / wide-hedge pattern.

### Claude's tentative conclusion
Friend's data is real, but the edge is from the listed weeks; across all weeks the friend's timing is ~zero/negative, and the SL result in his Excel is an artefact. A small, lumpy edge seems to exist for short-dated (3 days to expiry) far-OTM WIDE-hedged Nifty condors (~Rs9-12k per lot per year, max loss ~Rs25k per trade), not large enough to be "very profitable"; paper-trade first.
