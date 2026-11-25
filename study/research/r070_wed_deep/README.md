# r070 — Wednesday deep study (25-26 Nov 2026)

## भाग A: r065 आगे — div yield>3% blue chips + bear regime (AI-48006Eb)
- नियम: top-100 traded value, trailing 12m dividend yield >3% (adj factor से), महीने की पहली तारीख़ खरीद; regime = Nifty बनाम 200DMA (2008-07 से).
- 250d hold, hi-yield minus बाकी blue chips: bear महीने (N52) +9.95pp, 73% महीने आगे, तीनों दौर + (+7.6/+12.4/+9.9); bull महीने (N154) +1.5pp, 2013-20 -5.5.
- 60d: bear में फ़र्क़ नहीं (-0.08).
- Stop/target -10/+20 (250d तक): bear hi-yield target 45.8%, win +19.6 / loss -10.2, exp +3.43 (cost बाद) बनाम बाकी blue chips bear 40.3%, exp +1.74. bull hi-yield 44.8%, exp +3.12.
- सीमा: bear महीने लगातार आते हैं → असली स्वतंत्र दौर ~10 (2008, 2011, 2013, 2015-16, 2018-19, 2020, 2022, 2025); survivorship (आज की सूची); 2019 bear trades -11.9.
- फ़ैसला: अभी analysis में. आज (2 Nov data) Nifty<200DMA, hi-yield blue chips 18 (PSU/IT/ITC...).
Files: divyield_regime.py/.out.txt/.csv, ctrl_st.py/.out.txt

## भाग B: NW-02 आगे — futures cost 0.03% + 200DMA/VIX filter (NW-02b)
- Signal Nasdaq<=-2% + Nifty gap-down<=-0.5%, open खरीद, 5d: N122 +0.41 (सब दिन +0.19), futures cost बाद +0.38; stop/target -1.5/+1.5: target 44% पर exp 0.00; -2/+3: target 21%.
- Filter: Nifty>200DMA N56 +0.58; <200DMA +0.27 (2013-20 -0.11); VIX>=20 N55 +0.86 (दौर +0.66/+0.78/+1.18), VIX<20 +0.04.
- **Control: बिना US crash वाला gap-down<=-0.5% (Nasdaq>-1%) N160 +0.57, -1.5/+1.5 target 52% exp +0.23** — US crash वाला signal इससे कमज़ोर. यानी US गिरावट में कुछ ख़ास नहीं; जो है वह आम gap-down वापसी है.
- फ़ैसला: NW-02 (US-specific) बेकार. (आम gap-down open खरीद पहले के gap studies में है.)
Files: nw02_filters.py/.out.txt
