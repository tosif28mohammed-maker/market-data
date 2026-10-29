# Claude paper trading (कोई असली पैसा नहीं)
हर trading दिन शाम 5 बजे (IST) GitHub पर `paper/engine.py` चलता है: पहले से तय नियमों से trade खोलता/बंद करता है।
- `journal.csv` सारे trade (mode: replay = 1 Sep-28 Oct 2026 का पीछे का replay, live = 29 Oct 2026 से)
- `summary_live.csv`, `summary_replay.csv` हर तरीके का हिसाब; `reports/YYYY-MM-DD.md` रोज़ की रिपोर्ट
- `state.json` खुले trade और कल के pending orders
Options की क़ीमत India VIX से Black-Scholes द्वारा अनुमानित है (असली premium अलग होगा). Nifty lot 65.
