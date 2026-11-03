# Claude paper trading (कोई असली पैसा नहीं)
हर trading दिन शाम 5 बजे (IST) GitHub पर `paper/engine.py` चलता है: पहले से तय नियमों से trade खोलता/बंद करता है।
- `journal.csv` सारे trade (mode: replay = 1 Sep-28 Oct 2026 का पीछे का replay, live = 29 Oct 2026 से)
- `summary_live.csv`, `summary_replay.csv` हर तरीके का हिसाब; `reports/YYYY-MM-DD.md` रोज़ की रिपोर्ट
- `state.json` खुले trade और कल के pending orders
Options की क़ीमत India VIX से Black-Scholes द्वारा अनुमानित है (असली premium अलग होगा). Nifty lot 65.
- `scripts/mom_paper.py` → MOM_MONTHLY (महीने के top-10 momentum): `mom_state.json`, `mom_journal.csv`, `mom_history.csv`
- `scripts/breadth_paper.py` → BREADTH_DIP (3 Nov 2026 से; f57): जिस दिन 20%+ liquid शेयर अपने SMA20 से बहुत नीचे हों, उस दिन 200 DMA के ऊपर वाले fresh dip शेयर (₹10,000 × अधिकतम 10) खरीदो; close ≥ कल का SMA20 या 21 दिन पर बेचो; खर्च 0.35%. Threshold `breadth_thr.csv` (2013-20 से तय). फ़ाइलें `breadth_state.json`, `breadth_journal.csv`, `breadth_history.csv` (रोज़ का breadth भी). 1 Jan 2026 से replay.
