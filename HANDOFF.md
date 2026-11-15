# HANDOFF — naye chat ke liye (Tosif ki share market study) — 12 Nov 2026

Saari yaad do jagah hai:
1. Notebook artifact https://claude.ai/artifact/NKBKAFTm7WeJ4Ugi7D5fuV (ArtifactData collections: `notes`, `daily_strategy`, `findings`).
   Pehle padho: `notes/n42` (sthiti + khule kaam), `daily_strategy/d04-master` (saare niyam), `d07-checklist`, findings f44-f84.
2. Yeh repo `tosif28mohammed-maker/market-data` (PUBLIC; gh REST use karo, GraphQL band). Branches: main, universe500 (1,500+ shares 2002-26, u1000/u2000),
   intraday_hist (5m/15m/1h history), nse_hist (delivery 2008-26, F&O OI 2010-26).

## Roz ki briefing ("aaj kya hai") — in files se, isi kram mein
| File | Kya |
|---|---|
| data/decision.md | holdings ka faisla + khareed list (score, limit, stop, target, matra) |
| data/why.md | har khareed/holding ka KYUN (200/20 DMA, RS, fundamentals, khabar) + value list |
| data/checklist.md | calendar, mode (tezi/giravat), timeframes, iron condor ka din, dividend/bonus |
| data/value.md | sasta + achha + trend (uptrend = khareed layak; downtrend = ignore) |
| data/news/latest.md, data/themes.md, data/themes/institutions.md | khabar, themes, badi sansthayein, value chain |
| data/movers/latest.md | kal ke top gainers/losers + sabak |
| paper/intra_today.md, paper/intra_report.md, paper/intra_journal.csv | intraday paper robot |
| paper/summary_live.csv, paper/div_state.json | purani paper kitaab, dividend paper |
| paper/my_holdings.csv, paper/my_orders.csv | user ki ASLI holdings/GTT (screenshot se update karo) |
| data/ideas.md, data/ideas_queue.md | Idea Factory ke nateeje, baaki sawaal |
Briefing format (user ne tay kiya): 1) bazaar + business/duniya ki khabar, 2) aaj kya kharidna aur KYUN (entry samay 2:15-3:25 PM IST, limit, stop, target, matra),
3) kya bechna aur kyun, 4) movers se sabak, 5) themes/value list, 6) paper trading + robots theek ya nahi. Chhota, Hindi/Hinglish.

## Robots (.github/workflows) — sab muft, apne aap
- daily.yml (5 PM IST): data, corp_actions (dividend/bonus/board meetings), paper engine, tips_tracker, div_paper, tf_scan, deliv_daily, movers_review,
  daily_checklist, decision, value_list, why_card.
- news.yml (subah): fetch_news + themes.py. intraday (5-min data). intra_paper.yml (9:00 aur 12:20 IST): intraday paper trading.
- ideas.yml (Shanivaar): idea_factory (150 naye jod + ledger) + seasonal_table. global, scan, ipo.
- Manual: world.yml, sideways.yml, mausam.yml, streak.yml, events.yml, tf.yml, corp.yml.
- Robot fail ho to `gh api repos/.../actions/runs` se dekho; data/*.csv mein non-OHLC file engine ko todti thi (theek kiya 9 Nov).

## Pakke nateeje (findings) — ek nazar
PASS / kaam ke: momentum 12-1 (f72, f77 Clenow: share + bazaar 200 DMA upar), tezi mode (f62/f71: Nifty +2% din ya 10 din +5%), giravat mein dip (f41/f56),
dividend se pehle chadhaai (f64, paper DIV_RUNUP), bonus/split run-up (f71), Nifty+sona 50/50 aur 10-mahine SMA (f72), kam delivery par chadhaai = bacho (f72),
kamzor industry = bacho (f73), value chain auto/power (f74), Nifty weekly iron condor/bull put expiry se 1 din pehle VIX 14-22 (f75),
Shishir kamzor / Hemant mazboot (f79), apna-mahina neeche 10% = bacho (f81), mahine ka pehla hafta (f82, mid/small), base breakout 30 din (f83, dekhne layak),
Sensex ROC18 -10..+10 = lambi khareed zone (f84), IPO base breakout (f84, bias ke saath), bade jhatke ke 5 din baad khareed (f80).
FAIL: Benner India, streaks (f70), apni khabar ke peeche bhaagna (f71), OI buildup/PCR, low-vol India, share options/iron condor (f75), scalping (f76),
ORB/Open=Low (f53), number/tareekh/k-din dohraav (f78), mausam data (f80), ritu->ritu jod (f81), shuruaat ka din (f82), VCP, 21 EMA trailing (f84),
Minervini/Darvas/Turtle/52w-high (f77), option khareedna.
Idea Factory: 463 idea jaanche, asli PASS 1.

## User ke niyam
Hindi/Hinglish, chhota. Koi scheduled task apne aap nahi. Jab pooche tabhi poora jawab. Liquidity D kabhi nahi (A >= 5 cr roz, B 1-5, C 0.25-1; study/liquidity.py).
Har study: poora itihaas, daur-war, 2008/COVID hata kar, placebo, look-ahead nahi, kharcha ghata kar. Khareed 2:15-3:25 PM IST. Paper/asli niyam user OK ke bina mat badlo.
Nayi seekh d04-master + findings mein. Password/PIN/TOTP/API key kabhi chat mein nahi; Claude order nahi lagata. Tips par raay do, sirf kaam ke paper/tips.csv mein.
Paid data (Tickertape) repo mein mat daalo (repo public).

## Holdings 15 Nov (user): MINDACORP 10 BIK GAYA ~735 (13 Nov, +~Rs1,025). HERO/KARUR order nahi bhare.
NAVINFLUOR 1 @8730.62 (stop 8414), SHYAMMETL 8 @1252.96 (stop 1161), SANSERA 2 @4277.04 (stop 4156),
WELCORP 13 @2182.62 (stop 1991, 2370 par 7 bech, aur nahi jodna), AJANTPHARM 10 @3321.67 (stop 3200, target 3590), HFCL 40 @205 (naya 13 Nov; stop 189 close, target ~230, 20 din). GTT BUY MCX 10 @3185.
Laga ~Rs 1.03 lakh; steel+pharma ~69%.

## f86 (15 Nov): top gainers/losers ke BAAD (study/movers_after.py, 2003-26)
Kal ke +10% vol-3x gainer ka peechha = FAIL (200 DMA neeche wala 60 din mein bazaar se -4%, har daur); breakaway (52w high, uptrend) = ~0.
-10% vol-3x giravat = 60 din bazaar se -3.4% (uptrend wala -4.1%) -> dip mat kharido, holding ho to bechne par socho. Mahine ke gire 20 aage bhi -2.7%/60d.
Robot scripts/shock_watch.py (daily.yml) -> data/shock_watch.md + data/shock_avoid.csv (60 din AVOID, holdings alert, mahine ke top/bottom, live paper jaanch).
Briefing mein: holdings alert + naye share AVOID list mein to mat suggest karo. decision.py score mein -2 jodna = user OK baaki.

## User 15 Nov: PAPER mein jo sahi lage bina poochhe daalo (asli paisa/asli niyam = OK zaroori)
Lakshya: 1-2 mahine paper se seekh kar intraday/futures mein roz guide karna. Naya paper:
- WEEKLY_IC + WEEKLY_IC_NS (paper/engine.py): expiry se pehle din close, VIX 14-22, +-1 sigma, 2% wings; ek stop 2x credit, ek bina stop. Replay Sep-Nov 6 sauda: -16.7k / -9.2k (tezi bazaar, chhota sample).
- Seekhne wali futures kitaab (scripts/rare_setup.py -> paper/fut_learn_journal.csv): decision/tezi list ke F&O A shares, 1 lot, stop -8%, target +12%, 20 din, max 4 khule, roz 1. Pehla: DIVISLAB 100 @11442 (13 Nov).
- Intraday discipline niyam D1-D5 (scripts/intra_paper.py, report mein tulna). 59 din replay (f85): D2 R:R>=1.5 = same paisa, 35% kam trade (halka pass); D3 breakeven stop = FAIL (-3.4k); D4 Nifty disha = neutral; D1/D5 lage hi nahi; sab ek saath = bura. Base niyam nahi badle.

## Faisla 13 Nov: intraday/futures ROZ nahi
SEBI FY25: 91% F&O traders ghaate mein; futures intraday se zyada khatarnaak (leverage). Roz ka kaam = share khareed (decision.md).
Sirf kabhi-kabhar BADA MAUKA (A+): scripts/rare_setup.py (daily.yml) -> data/rare_setup.md + paper/rare_fut_journal.csv (futures PAPER,
asli NSE lot size data/fo_lots.csv, cash se tulna). Shart: score>=6, 3+ family, A + F&O, koi warning nahi, nateeje door, Nifty 200 DMA upar + tezi/ghabrahat mode,
R:R>=1.5; discipline: 1 khula, mahine 2, 2 haar -> 10 din band. Briefing mein batao; mauka aaye to khabar jaancho. Asli paisa sirf user OK + 2-3 mahine paper ke baad.
Intraday paper robot study ke liye chalta rahega (experts ke discipline niyam + leverage study = agla kaam, user OK).

## Khule kaam (12 Nov)
- User OK baaki: (a) paper mein purana iron condor niyam hata kar weekly (f75) daalna; (b) base-breakout + IPO-base ko paper strategy banana;
  (c) "kam delivery -1" paper mein; (d) Tickertape se sirf haan/na flags repo mein ya nahi; (e) har share mein kitni rakam (robot Rs 15k maanta, user Rs 28-33k lagata).
- 16 Nov (Som) 3:15 PM IST: Nifty iron condor ka din agar VIX 14-22. 21 Nov: purani chat mein API-credit reminder aayega (faisla: abhi paisa nahi).
- 30 Nov: MOM_MONTHLY rebalance list + Nifty ETF 10-mahine niyam. ~4 Dec: tezi basket review.
- Telegram secrets, DDPI, Angel AG8004 email — user ki taraf se baaki. Mutual fund study alag chat mein.
