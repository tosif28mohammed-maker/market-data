# HANDOFF — नए chat के लिए (Tosif का market study)
सारी याद दो जगह है: (1) Notebook artifact https://claude.ai/artifact/NKBKAFTm7WeJ4Ugi7D5fuV (ArtifactData: findings f1–f63, notes n1–n42, daily_strategy d00–d06); (2) यह repo.
पहले पढ़ो: notes/n42 (खुले काम), daily_strategy/d04-master (सारे नियम), d05-bulletin, d06-experts, d06-rule-changes, notes n26–n41, findings f44–f63; फिर study/expert_playbook.md.

## Repo नक्शा
- data/: NIFTY.csv, BANKNIFTY.csv, INDIAVIX.csv, global/ (78+ series), intraday/*_5m.csv, daily_all/ (2y सब A/B शेयर), fund/summary.csv (fundamentals), news/latest.md (+watch.txt), fii_dii.csv, ipo/, gapday/
- paper/: engine.py रणनीतियाँ (EQ_DIP, FUT_*, OPT_*, INTRA_GAPFADE, IDX_USFADE), mom_paper (MOM_MONTHLY), breadth_paper (BREADTH_DIP), tips.csv/tips_status.csv, reports/<date>.md, gap_universe.csv, avoid_liquidity_D.txt (D कभी नहीं)
- study/: सारी studies (*.py) और results/*.csv; expert_playbook.md; expert_screen.py; sector_trend.py; thrust_buy.py; breadth_dip.py; trend_filter_dip.py; asset_trend.py; oil_link.py
- Robots (.github/workflows): daily (5 PM IST: fetch→gapday→fii→engine→mom→breadth→tips), intraday, global (6:15 IST), news (5:50/12:40/16:10 IST), ipo (11:30/17:20), fundamentals (शनि), scan-data (16:15), archive_5m (शुक्र), fo_list, angel_data (manual)
- Branches: universe500 (u1000/u2000 daily), intraday_hist (h1 ~3y, m5, m5_all)
- GraphQL blocked → gh api REST; Yahoo/NSE सिर्फ Actions से।
