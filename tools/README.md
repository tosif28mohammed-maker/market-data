# Ladder orders (Angel One) — एक command में कई order
1. Angel One SmartAPI: smartapi.angelone.in पर login -> "Create App" (Trading APIs) -> API key मिलेगी. TOTP चालू करें (QR के नीचे वाला secret code सेव करें).
2. 1 April 2026 से API से order सिर्फ़ आपके **register किए static IP** से जाते हैं (app में "Primary Static IP"). घर के internet का static IP (ISP से) या एक छोटा cloud server (VPS) चाहिए.
3. Computer पर: Python install -> `pip install smartapi-python pyotp pandas`
4. इस folder में `.env` file बनाएँ (कभी किसी को न भेजें, chat में भी नहीं):
   ANGEL_API_KEY=...  ANGEL_CLIENT=...  ANGEL_MPIN=...  ANGEL_TOTP_SECRET=...
5. Claude से plan.csv बनवाएँ, फिर पहले TEST: `python ladder.py plan.csv` -> सही लगे तो `python ladder.py plan.csv --live`
6. Buy भरने के बाद: `python ladder.py gtt plan.csv --live` (Stop-loss सारी मात्रा पर, आधा T1 पर, आधा T2 पर)
ध्यान: Market order API से मना है, ये tool सिर्फ़ LIMIT लगाता है. पहली बार 1-2 शेयर की मात्रा से test करें.
