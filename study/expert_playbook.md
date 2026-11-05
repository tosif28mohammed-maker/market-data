# Expert investors playbook (बड़े निवेशकों के तरीके → हमारे नियम)
User (5 Nov 2026): "Buffett, Jhunjhunwala, दुनिया के experts की किताबें/तरीके पढ़ो, उनसे आइडिया निकालो; long-term भी चलेगा; पैसा बनाना है; रोज़ top experts की राय पढ़ो."
यह फ़ाइल हर सलाह से पहले पढ़नी है। जो नियम हमारे डेटा पर परखे जा सकते हैं वे `study/expert_screen.py` में code हैं; जो नहीं परखे जा सकते (management, moat) वे यहाँ checklist हैं।

## 1. दुनिया के बड़े निवेशक — मुख्य बातें
| निवेशक / किताब | मूल बात | हमारा नियम |
|---|---|---|
| **Benjamin Graham** — *The Intelligent Investor* | Margin of safety; बाज़ार "Mr. Market" है, उसके मूड से नहीं, कीमत बनाम असली मूल्य से फैसला | P/E, P/B देखो; घबराहट (breadth ≥20%) में अच्छे शेयर सस्ते मिलते हैं |
| **Warren Buffett / Charlie Munger** — Berkshire letters, *Poor Charlie's Almanack* | "Wonderful company at a fair price"; moat; ईमानदार management; कम कर्ज़; लंबा रखो; circle of competence; "be fearful when others are greedy" | BUFFETT lens: ROE≥15%, ROCE≥15%, D/E<0.5, OCF≥80% मुनाफ़ा, घाटे का साल नहीं, P/E≤40 |
| **Philip Fisher** — *Common Stocks and Uncommon Profits* | 15 सवाल: बढ़ती बिक्री, R&D, margin, management की ईमानदारी; "scuttlebutt" (ग्राहक/सप्लायर से जानकारी) | Qualitative checklist (नीचे) |
| **Peter Lynch** — *One Up on Wall Street* | जो जानते हो उसे खरीदो; PEG<1; 6 तरह के शेयर (slow, stalwart, fast grower, cyclical, turnaround, asset play) | LYNCH lens: मुनाफ़ा वृद्धि 15-50%, PEG≤1.2, कम कर्ज़ |
| **Joel Greenblatt** — *The Little Book That Beats the Market* | Magic formula: ऊँचा ROCE + ऊँचा earnings yield (सस्ता) | GREENBLATT lens (non-financial top 15%) |
| **William O'Neil** — *How to Make Money in Stocks* (CANSLIM) | Current quarterly EPS +25%, Annual growth, New high/product, Leader (RS), Institutional support, Market uptrend; 7-8% पर stop | CANSLIM lens + stop −8% (हमारे thrust नियम f62 जैसा) |
| **Mark Minervini** — *Trade Like a Stock Market Wizard* | Trend template (150/200 DMA ऊपर, 200 चढ़ता, 52w high के पास), VCP, छोटा stop | TREND lens |
| **Stan Weinstein / Nicolas Darvas** | Stage 2 (200 DMA ऊपर चढ़ता) में ही खरीदो; box breakout | TREND lens; f58 (लंबे downtrend में नहीं) |
| **Stanley Druckenmiller / George Soros** | पहले पैसे बचाओ; सही हो तो बड़ा दाँव; liquidity (Fed/RBI) और trend देखो; reflexivity | Position size: पक्के signal पर बड़ा, बाकी छोटा; FII/liquidity खबरें |
| **Ray Dalio** — *Principles* | Diversification (कम संबंध वाले asset), cycles | Nifty+Gold+Nasdaq मिश्रण (f60) |
| **Howard Marks** — *The Most Important Thing* | Cycles और भीड़ की भावना; risk = स्थायी नुकसान | Breadth/VIX/खबरों में भावना पढ़ो |
| **Jesse Livermore / Turtles** | Trend के साथ चलो, नुकसान छोटा काटो, जीत को चलने दो | stop + trailing; momentum (f55) |

## 2. भारत के बड़े निवेशक
| निवेशक | मूल बात | हमारा नियम |
|---|---|---|
| **Rakesh Jhunjhunwala** | भारत की ग्रोथ पर भरोसा; मज़बूत competitive advantage + ग्रोथ; लंबा रखो (Titan, CRISIL, Lupin); गलती से सीखो; trading और investing अलग खाते; "market is like a woman — always commanding, mysterious" — भावना पर काबू | Core (लंबा) + trading (छोटा) अलग; quality + growth lenses |
| **Radhakishan Damani** (DMart) | सादा, कम कर्ज़, नकदी पैदा करने वाला बिज़नेस, धैर्य; consumption | BUFFETT + COFFEECAN lens |
| **Raamdeo Agrawal** (Motilal) — QGLP, *100x* | Quality, Growth, Longevity, Price; "buy right, sit tight"; earnings upcycle से पहले खरीदो | QGLP lens (ROE≥15%, मुनाफ़ा +15%, revenue 3y CAGR≥10%, PEG≤1.5) |
| **Vijay Kedia** — SMILE | Small in size, Medium experience, Large aspiration, Extra-large market potential; management सबसे ज़रूरी; धैर्य | Small/mid cap + बड़ा बाज़ार; qualitative checklist |
| **Saurabh Mukherjea** (Marcellus) — *Coffee Can Investing* | 10 साल लगातार revenue ≥10% और ROCE ≥15% वाली कंपनियाँ, 10 साल रखो, कम छेड़छाड़ | COFFEECAN lens (हमारे पास 4 साल का डेटा — lite) |
| **Kenneth Andrade** | Capital-light, industry consolidation, cycle के नीचे खरीदो | sector cycle + valuation |
| **Ramesh Damani / Basant Maheshwari** | Earnings growth ही शेयर चलाता है; P/E re-rating; बड़े trend वाले सेक्टर | CANSLIM/QGLP + sector trend |

## 3. Qualitative checklist (code नहीं कर सकते — हर लंबे निवेश से पहले)
1. Management: promoter ईमानदार? pledge? related-party? SEBI/अदालत केस? (news robot: Supreme Court/SEBI order)
2. Moat: brand, लागत में बढ़त, network, switching cost, license
3. बाज़ार कितना बड़ा (Kedia "XL market"), कंपनी का हिस्सा बढ़ रहा?
4. मुनाफ़ा नकदी में बदलता (OCF/NP ≥0.8)? कर्ज़ घट रहा?
5. Dilution (नए शेयर/ESOP बहुत) तो नहीं?
6. कीमत: P/E अपने इतिहास और साथियों के मुकाबले; PEG
7. Promoter/institution holding बढ़ रही?

## 4. कैसे इस्तेमाल करें (हमारे डेटा के साथ)
- **Core / लंबा (6 महीने – कई साल):** fund lenses ≥2 (BUFFETT/LYNCH/GREENBLATT/QGLP/COFFEECAN) + TREND (200 DMA ऊपर) + checklist; 3 किश्तों में (बाज़ार गिरे तो ज़्यादा); stop सिर्फ बिज़नेस बिगड़ने या 200 DMA के नीचे लंबा टिकने पर.
- **Swing / 1-3 महीने:** thrust (f62) या momentum (f15) + CANSLIM/TREND; stop −8% या 50 DMA.
- **हमेशा:** D liquidity नहीं; खबर/नतीजे की तारीख देखो; एक शेयर में ≤15-20%।
- **ईमानदारी:** fundamentals Yahoo का आज का snapshot हैं (पुराने साल-दर-साल नहीं), इसलिए lens का backtest नहीं हो सकता — paper में आगे परखेंगे।

## 5. रोज़ की expert राय
News robot (`scripts/fetch_news.py`, group 'Experts') में: Raamdeo Agrawal, Vijay Kedia, Samir Arora, Saurabh Mukherjea, Nilesh Shah, Prashant Jain, Sunil Singhania, Basant Maheshwari, Shankar Sharma, Warren Buffett/Berkshire, Howard Marks, Stanley Druckenmiller, brokerage top picks. Bulletin में 2-3 पंक्ति: कौन क्या कह रहा, हमारे डेटा से मेल खाता या नहीं।

Sources (5 Nov 2026 पढ़े): Business Today (Raamdeo Agrawal, 2 Nov 2026), Whalesbook (Samir Arora), TradingView/Moody's (Samvat 2083 brokerage picks), Motilal Oswal blog (Jhunjhunwala), किताबें ऊपर।
