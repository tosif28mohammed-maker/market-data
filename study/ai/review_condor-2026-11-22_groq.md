# Groq (openai/gpt-oss-120b)

**1) Top 5 methodological risks (rank‑ordered)**  

| # | Risk | Why it can overturn the “profitable” conclusion |
|---|------|------------------------------------------------|
| 1 | **Selection / survivorship bias** – The friend’s back‑test uses only 107 of the 149 weekly cycles that actually existed. The 45 omitted weeks are precisely the ones that turn the strategy negative (‑0.9 – ‑1.4 L). Ignoring them inflates the mean P/L and creates the illusion of an edge. |
| 2 | **Look‑ahead / strike‑definition bias** – Strikes are chosen from the *same* day’s price (ATM ± 400, forward‑price‑based F, etc.). In reality the entry price is the *best‑available* bid/ask at the moment of order placement; using the day‑high/low to guarantee the price (as done for the AlgoTest) is a classic look‑ahead error that over‑states fill quality. |
| 3 | **Multiple‑testing / data‑snooping** – Test B evaluates > 5 900 parameter combos (z, w, entry‑date, exit rule, SL type). The “PASS” filter is applied *after* the scan, yet no out‑of‑sample penalty for the huge search space is imposed. The handful of “winning” combos are almost certainly statistical flukes. |
| 4 | **Cost & slippage model unrealistic** – Slippage is fixed at 0.5 pt/leg (or max(0.05, 1 % price) for indices). For a 400‑point OTM leg the market depth on a weekly expiry is thin; a realistic fill could be 2‑3 pts or even a full‑tick miss. Under‑estimating costs turns a marginally negative expectancy into a (fictitious) positive one. |
| 5 | **Exit‑price approximation** – The study uses the *intrinsic* value at expiry (or the “settle” column) as the exit price, but the actual cash‑settlement on NSE is based on the *closing* index value **after** the final auction, which can differ by > 10 pts from the theoretical intrinsic. Using the intrinsic value hides the true loss on a bad expiry. |

---

**2) Tests that are missing and can be run with the daily bhavcopy data**

| Test | What to do (one‑liner) |
|------|------------------------|
| a. **True out‑of‑sample walk‑forward** – Split each underlying’s history into rolling 2‑year windows, optimise z/w/entry‑date on the first year, test on the second year, then roll forward. |
| b. **Monte‑Carlo stress test** – Randomly resample weekly cycles (with replacement) 10 000 times to obtain the distribution of the Sharpe/Profit‑Factor; check whether the observed mean lies in the 95 % CI of a zero‑mean process. |
| c. **Cost‑sensitivity sweep** – Re‑run the best‑performing combos (e.g., d3‑z 1.25‑w 1.0) with slippage = 1 pt, 2 pts, 3 pts per leg and STT doubled; report the break‑even slippage. |
| d. **Intraday‑SL validation** – Use the intra‑day high/low from the bhavcopy (if available) or reconstruct from minute‑bars to enforce the “pessimistic” SL rule on the exact price path, not just daily closes. |
| e. **Volatility‑regime split** – Partition weeks into low‑VIX (≤ 15), medium (15‑25) and high (> 25) periods; compute the strategy’s expectancy in each regime to see if the apparent edge is merely a VIX‑bias. |
| f. **Bid‑ask spread capture** – For every leg record the quoted bid‑ask spread at entry (use the “settle” column of the previous day as a proxy) and deduct half‑spread from the credit. Compare the resulting P/L to the original numbers. |
| g. **Liquidity filter test** – Exclude weeks where any leg has < 10 contracts traded on the entry day; re‑evaluate the edge. |
| h. **Alternative strike construction** – Replace the fixed ±400 pts offset with a *percentage* of spot (e.g., ±6 % of NIFTY) and repeat the back‑test. |

All of the above are doable with the publicly available bhavcopy fields (date, underlying close, option strike, open/high/low/close, contract count).

---

**3) Is the final conclusion justified?**  

**Partly.**  
The analysis correctly identifies that the friend’s “very profitable” claim is an artefact of cherry‑picking the 107 weeks and of an optimistic cost model. The broader 149‑week sample is flat to slightly negative, and the out‑of‑sample performance of the best parameter set is essentially zero (‑0.77 %). However, the study stops short of proving *no* edge exists; a modest, regime‑dependent positive expectancy (≈ +0.4 % per trade for d3‑z 1.0‑1.5‑w 1.0) survives a limited walk‑forward test. Therefore the conclusion that “there is a small, lumpy edge but not a large, reliable profit” is accurate, but the claim that the edge is negligible is **over‑stated** without the additional robustness checks listed above.

---

**4) A better variant of the strategy worth testing**  

| Rule | Rationale |
|------|-----------|
| **Delta‑targeted strikes** – Sell a call and a put each at ~‑0.20 Δ (≈ ATM‑1 % for NIFTY), buy protection at ~‑0.05 Δ (≈ ATM‑3 %). This automatically scales the wing width to the prevailing volatility instead of a fixed 400 pts. |
| **Dynamic hedge width** – Set hedge distance w = (EM / spot) × k where k ≈ 1.0 – 1.2, i.e., hedge in terms of *percentage* of expected move rather than a fixed number of strikes. |
| **Entry 2 days before expiry** – Empirically the “d3” entry performed best; moving to “d2” reduces time‑decay risk while still capturing most theta. |
| **Fixed‑fractional stop‑loss** – Exit when the *net credit* erodes by 60 % (instead of a flat Rs 25 k) to keep risk proportional to the original credit. |
| **Cash‑settlement price source** – Use the official NSE “settlement price” column for the underlying on expiry (the final auction price) to compute intrinsic value, not the theoretical put‑call parity. |
| **Position sizing** – Limit exposure to ≤ 1 % of account equity per leg (rather than a flat 325 contracts). This prevents a single ‑25 k loss from wiping out the whole sample. |

Running this variant with the missing‑weeks data and the robustness tests above will give a much cleaner picture of any true expectancy.

---

**5) Numbers that look suspicious**  

| Observation | Why it raises a red flag |
|-------------|--------------------------|
| **Gross profit = +Rs 2.68 L over 107 weeks → ≈ +Rs 2 500 per week** while the *average loss* is quoted as **2.9 × average win**. With a win‑rate that low, a handful of very large wins must be inflating the mean – a classic “lumpy” distribution that is extremely sensitive to a few outliers. |
| **Cost estimate of Rs 900‑1 550 per week**: With a median credit of ~20.9 pts on a 325‑contract lot, the gross credit ≈ Rs 6 800 per trade. A 0.5‑pt slippage per leg (4 legs) already costs ~Rs 650; adding brokerage, STT and exchange fees should push weekly cost well above Rs 1 200, especially when the credit falls to 10 pts in low‑vol weeks. |
| **Forward price F = K* + C – P** is used to define “ATM”. The forward is derived from the *same* day’s option prices; any bid‑ask spread distortion will move F away from the true forward, biasing the strike‑selection in favour of the back‑test. |
| **Median credit 20.9 pts, wing width 300 pts → max risk ≈ 279 pts**. Yet the “worst trade” is quoted as **‑Rs 25 k per lot**, which corresponds to ≈ ‑77 pts, far below the theoretical maximum loss. Either the wing width was narrower in many trades, or the loss figure has been truncated. |
| **Profit factor 1.41 with 88 % win rate** for the “best” combo, but the yearly P/L swings wildly (+49.8 k in 2025, –13.3 k in 2024). Such volatility is inconsistent with a stable edge; it hints at a few outlier weeks driving the PF. |
| **Median absolute error of 4.5 pts** between the derived expiry underlying and the official NIFTY close. That error alone can flip a marginally profitable condor (credit ≈ 20 pts) into a loss, suggesting the exit‑price approximation is too crude. |

--- 

**Bottom line:** The friend’s claim rests on a biased sample and optimistic execution assumptions. When the full weekly universe, realistic costs, and proper out‑of‑sample validation are applied, the strategy’s expectancy collapses to ~‑0.5 % to +0.4 % per trade, far from “very profitable”. A delta‑targeted, dynamically‑hedged condor entered two days before expiry, with proportional stop‑losses and rigorous cost modeling, is a more defensible hypothesis to test next.
