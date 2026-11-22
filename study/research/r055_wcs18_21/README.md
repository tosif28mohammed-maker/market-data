# r055 — Motilal WCS 18-21 claims + arXiv efficiency claim (23 Nov 2026, 02:11 Kuwait)
Data: u1000+u2000 daily (liquidity D हटाए), sectors = data/fund/info.csv (आज का sector), NIFTY.csv 2007-26. Costs 0.25%.
Survivorship: panel = आज ज़िंदा शेयर (सब buckets पर एक जैसा असर; bottom bucket पर सबसे ज़्यादा).

## MO-14 मंदी/ख़राब बाज़ार में IT, Pharma, Consumer आगे (WCS 2008-13) → बेकार
Nifty 200DMA से नीचे (65 महीने) या 12m return <0 (54 महीने) के महीने-अंत पर अगले 12 महीने sector basket − market (mean / median):
- Consumer Defensive: below200 -3.6 (median +3.9); neg12m -5.0. सिर्फ़ 2003-12 में अच्छा (+4.5), 2013-20 -8.5, 2021-26 -8.1.
- Healthcare: below200 -3.3 (median -2.4); neg12m -4.2.
- Technology: below200 +9.6 पर median -1.2, 48% महीने ही आगे (2020 के एक उछाल का असर).
- उल्टा: Basic Materials ख़राब दौर के बाद +7.9 / +12.0 (cyclical rebound).
नतीजा: "मंदी में defensive ख़रीदो" India में 2013 के बाद काम नहीं किया. Script: claims/mo14_defensive_slowdown.py, result mo14_result.csv.

## MO-15 तेज़ wealth creators टिकते हैं (Eicher/Page/Ajanta कई studies में) → बेकार
हर मार्च, पिछले 5 साल के top-10 return वाले शेयर: अगले 1 साल market से -4.8% (median -8.5%, 37% साल आगे), अगले 3 साल -23.8% (median -32.5%).
3 साल lookback top-10: 3y आगे -28.5%. Bottom decile आगे ज़्यादा (+45% 3y) पर survivorship से फूला हुआ — भरोसा नहीं.
नतीजा: पिछली लिस्ट के "fastest creators" को आगे ख़रीदना घाटे का. Script: claims/mo15_longwinner_persist.py.

## ARX-01 Indian index random walk नहीं (arXiv 1510.03704, 2012.01160) → अभी analysis में
Nifty daily 2007-26: lag-1 autocorr 0.04 (2013 के बाद ~0). पर up-day के बाद अगला दिन ऊपर 55.7% (avg +0.095%) vs down-day के बाद 49.8% (-0.011%).
दौर: 2013-20 56.9 vs 50.1, 2021-26 57.6 vs 48.1, पिछले 6 महीने 50.8 vs 49.2 (कमज़ोर). फ़र्क ~0.1%/दिन — delivery cost (0.25%) से छोटा; सिर्फ़ futures/ETF पर, regime filter की तरह सोचना.
Script: claims/arx01_autocorr.py.

## WCS 18-21 पढ़ा (Findings Summary): ज़्यादातर winners की सूची (survivorship). नया: WCS18 #9 "payback <1x सबसे भरोसेमंद" (MO-02 जैसा),
WCS21 theme Focused investing 15-20 शेयर + Kelly (MO-16, portfolio आकार — कम priority).

## MO-17 (= AI-9B587E, WCS12/18 #7) young companies (<10 yrs) ज़्यादा wealth बनाते हैं → बेकार
उम्र = panel में पहला trading दिन (2004 के बाद listed). हर मार्च, अगले 12 महीने market से (mean / median), 2008-26, 19 साल:
- listing के 1-3 साल: -2.6 / -3.3, सिर्फ़ 37% साल आगे, तीनों दौर में नीचे (survivorship इनके पक्ष में होते हुए भी).
- 3-10 साल: +1.2 / -0.4. पुराने (≥10): -0.3 / +1.6.
नतीजा: नई listed कंपनी को उम्र के आधार पर चुनना फ़ायदेमंद नहीं; 1-3 साल पुराने IPO शेयर औसतन पीछे. Script: claims/mo_young_age.py.
