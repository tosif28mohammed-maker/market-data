# r062 — Dhan full transcripts (PC se 16 aaye): 11 AM Theta Trap + MTF swing scan (24 Nov 2026 18:11)

## DHAN-08/11 11 AM Theta Trap (premise) — theta_trap_11am.py
Rule (transcript): 15-min ADX nichhe aa raha ho, behtar <20, 10:30–11:00 ke beech → market shaant rahega → option sell.
Data: intraday_hist m15 NIFTY/BANKNIFTY, sirf 6 Aug – 2 Nov 2026 (60 din).
| index | group | n | 11:00→15:15 |move| median | quiet (max excursion < median) |
|---|---|---|---|---|
| Nifty | ADX falling & <20 | 4 | 0.35% | 25% |
| Nifty | baaki | 56 | 0.26–0.28% | 50–54% |
| BankNifty | ADX falling & <20 | 13 | 0.25% | 31% |
| BankNifty | falling & >=20 / rising | 22 / 25 | 0.10 / 0.30% | 59 / 52% |
Natija: premise ulta — low-ADX din shaant nahi. **बेकार** (sirf 60 din; intraday itihaas badhe to dobara).

## DHAN-16 MTF swing scan — dhan16_adx_rsi_vol.py
close>EMA20>EMA50 + ADX14>20 & rising + RSI 55–70 + volume >1.5x 20d; buy close; 10-din non-overlap.
- h20 excess vs EW market +0.09% vs control (sirf uptrend) +0.28%.
- Trade (stop 10d low, target 2R, max 20d, cost 0.25%): target hit 21% (Nov23+ 16%, last 2m 11%); avg +1.68% all, +0.22% Nov23+, −0.51% last 4m, −3.97% last 2m. Control lagbhag same.
Natija: filters kuch nahi jodte; target hit 35% se bahut neeche → **बेकार**.

## test_queue
40 waiting Gemini niyam (Motilal WCS 25-27): 8 price-family (consistency/CAGR/composite) → done (MO-26, AI-9197A2 me pehle hi बेकार); 32 → blocked (fundamentals/mcap/sector itihaas nahi).
