# Tosif ke liye manual-read video list (28 Nov 2026 se). Priority = topic weight + source trust + testability - shorts - fake-AI-voice risk.
# Sources: (1) WebSearch results 26 Nov (hand list below), (2) study/experts/queue.csv YouTube items not yet transcribed/Gemini-read.
import csv, os, re, pandas as pd
E = '/home/claude/market-data/study/experts'
S = [  # (url, title, topic, trust 0-3, note)
('https://www.youtube.com/watch?v=KMY6Lia03Lk','We Backtested 3 NIFTY Option Strategies Across 6.5 Years','options-backtest',2,''),
('https://www.youtube.com/watch?v=6ri3E8edh7c','Proven Option Buying strategy - Fully Backtested','options-buy',1,'claim check'),
('https://www.youtube.com/watch?v=5zn2os2SbPA','Backtesting Smart Straddles','options-backtest',2,''),
('https://www.youtube.com/watch?v=FhH-BBZIV2M','Sensex Weekly & Nifty Monthly Straddle Buying Backtest 2 months','options-buy',1,''),
('https://www.youtube.com/watch?v=0FVJbYBYX-Y','Ultimate Set & Forget Nifty Option Strategy?','options-backtest',1,''),
('https://www.youtube.com/watch?v=FZRFbOrI7ug','Batman Strategy With No Adjustment on Nifty (Hindi)','options-sell',1,''),
('https://www.youtube.com/watch?v=mZDpDwT3ImQ','PR Sundar se khaas baatcheet - options bechne ke khatre (CNBC Awaaz)','options-sell',2,'SEBI ne 2022 me ban kiya tha - sirf risk points'),
('https://www.youtube.com/watch?v=zYqcZaoVhm8','Simple and Low Risk Option Strategy ft PR Sundar','options-sell',1,''),
('https://www.youtube.com/watch?v=cIIBSPkYzQE','How to use FII-DII Data to Make Stock Market Decisions','fii-flows',2,''),
('https://www.youtube.com/watch?v=MwtxJNgAAsw','How to read FII DII PRO data in Indian market context','fii-flows',2,'F&O participant OI'),
('https://www.youtube.com/watch?v=m2V8a1EPS0g','FII/DII data analysis - big players position','fii-flows',1,''),
('https://www.youtube.com/watch?v=It9GfUXfDNU','FII and DII activity on stock futures explained (Hindi)','fii-flows',1,''),
('https://www.youtube.com/watch?v=kfixbsx3Wlo','FII & DII Data Analysis - kaise check karein','fii-flows',1,''),
('https://www.youtube.com/watch?v=qPgqUTPmDjc','Gold vs yields: what changed?','gold-fed',2,''),
('https://www.youtube.com/watch?v=Y27OgzA7rII','Are Real Yields Signaling a Gold Breakout?','gold-fed',2,''),
('https://www.youtube.com/watch?v=CEZlxd8_uj8','Gold Is Sending a Signal the Old Models Can’t Explain','gold-fed',2,'central bank buying vs real yields'),
('https://www.youtube.com/watch?v=kKOckbVvY-I','Market Report: What is Actually Holding Gold Up','gold-fed',2,''),
('https://www.youtube.com/watch?v=aAu4ba4QoKk','Gold Price Hits Fresh 2026 Lows as Fed Rate Hike Bets Climb','gold-fed',2,'2026 live'),
('https://www.youtube.com/watch?v=oEFPVoLrXak','The Fed Is About to Do the One Thing Gold Can’t Survive','gold-fed',0,'clickbait? check channel'),
('https://www.youtube.com/watch?v=hY0-bBBdgZY','Why gold could rise to $4,900 despite recent pullback','gold-fed',1,''),
('https://www.youtube.com/watch?v=saDWvBZlAsg','Aswath Damodaran on Indian Markets, Valuations & Tariffs','value',3,''),
('https://www.youtube.com/watch?v=Y3oxL5Y7WpM','Market Cycles Decoded With Aswath Damodaran','value',3,''),
('https://www.youtube.com/watch?v=jYpduAPfLR0','Pricing vs valuation, with Aswath Damodaran','value',3,''),
('https://www.youtube.com/watch?v=eB1pBo4WGmA','Are Indian Stocks Overpriced? Aswath Damodaran','value',3,''),
('https://www.youtube.com/watch?v=RNyToWaPPOA','Aswath Damodaran, the Dean of Valuation','value',3,''),
('https://www.youtube.com/watch?v=d_brGLdBFTU','Warren Buffett full speech, 2026 Berkshire annual meeting','value',3,''),
('https://www.youtube.com/watch?v=D0kpoZZM1ug','Berkshire 2026 annual meeting - full afternoon session','value',3,''),
('https://www.youtube.com/watch?v=j1vGFpd49wM','Full 2025 Berkshire Hathaway annual meeting','value',3,''),
('https://www.youtube.com/watch?v=Dv97-S9ZL-8','Buffett & Munger full 2023 Berkshire meeting','value',3,''),
('https://www.youtube.com/watch?v=4ICaAKuAudQ','Charlie Munger - Psychology of Human Misjudgment (1995)','emotions',3,'discipline checklist'),
('https://www.youtube.com/watch?v=Gv_BygLxIDg','How The Economic Machine Works (Ray Dalio)','macro',3,''),
('https://www.youtube.com/watch?v=ae7-EEwiFgw','How Debt Cycles Operate (Ray Dalio)','macro',3,''),
('https://www.youtube.com/watch?v=-4NuOAfZjHo','Stan Druckenmiller on Fed policy, bonds, Nvidia','macro',3,'real interview (Bloomberg)'),
('https://www.youtube.com/watch?v=pWZR5Ahjjls','Druckenmiller talks the Fed (Duquesne)','macro',3,''),
('https://www.youtube.com/watch?v=0LBnItvVQfw','Druckenmiller: Fed choice totally matters to market','macro',3,''),
('https://www.youtube.com/watch?v=tunA786XKcE','"Druckenmiller: 2026 Liquidity Trap ... My Exact Playbook"','macro',0,'SHAQ: AI-voice fake channel jaisa - avoid unless real'),
('https://www.youtube.com/watch?v=x_VjC_TbfqI','"Druckenmiller: The 2026 Credit Collapse Has Begun"','macro',0,'SHAQ: AI-voice fake - avoid'),
('https://www.youtube.com/watch?v=SbpKIpvqNfQ','Vijay Kedia - how to pick stocks for investing','value-india',2,''),
('https://www.youtube.com/watch?v=jnMLUHR4CBQ','Vijay Kedia - spotting opportunities before a sector explodes','value-india',2,''),
('https://www.youtube.com/watch?v=eMz7KGKp5B8','Vijay Kedia on stock selection, managing fear','value-india',2,''),
('https://www.youtube.com/watch?v=KnL3ukyb-Hs','Basant Maheshwari - basics of investing, picking stocks','value-india',2,''),
('https://www.youtube.com/watch?v=Q4ej3cbG_zU','Why Patience Creates Wealth in Equities','value-india',1,''),
('https://www.youtube.com/watch?v=7l_a8X0fRwA','Saurabh Mukherjea - Coffee Can playbook 2026','value-india',2,''),
('https://www.youtube.com/watch?v=E4BEWCGQCls','Saurabh Mukherjea - chirpiest about market in years','value-india',2,''),
('https://www.youtube.com/watch?v=sTZvJsR1PnU','Samir Arora - Indian markets aren’t as weak as they look','fii-flows',2,''),
('https://www.youtube.com/watch?v=fV_qTcH7bzo','Samir Arora - foreign investors to return to India?','fii-flows',2,''),
('https://www.youtube.com/watch?v=-K58QbkJk0A','Economy & market outlook - Prashant Jain (3P)','value-india',3,''),
('https://www.youtube.com/watch?v=Bxu2UPLPpwQ','Saurabh Mukherjea on the Jane Street case','options-structure',2,'F&O market structure'),
('https://www.youtube.com/watch?v=jlyid8OhOCs','Mark Minervini SEPA system tutorial part 1','technical',2,'VCP rules testable'),
('https://www.youtube.com/watch?v=I8Usc5lza_Y','Master the Volatility Contraction Pattern (VCP)','technical',2,''),
('https://www.youtube.com/watch?v=lbYBHVx7aJI','Minervini VCP explained (Definedge)','technical',2,''),
('https://www.youtube.com/watch?v=mYw-XrFQv_8','Anchored VWAP strategy for Nifty/BankNifty','intraday',1,''),
('https://www.youtube.com/watch?v=wAxOa0XIUto','Pivot points, VWAP and EMA intraday price action Nifty','intraday',1,'pivots pehle FAIL (r030)'),
('https://www.youtube.com/watch?v=ZsIesKS0XXg','Open High / Open Low intraday strategy (Hindi)','intraday',1,'testable'),
('https://www.youtube.com/watch?v=nsiJmlR5c8E','Open market strategy for intraday in 17 minutes (Elearnmarkets)','intraday',2,''),
('https://www.youtube.com/watch?v=WK_08c17bhE','Strategy for Bank Nifty trading (Face2Face)','intraday',2,''),
('https://www.youtube.com/watch?v=7Wg5vUlMLvI','5-Star RSI set-up - Vishal Malkan','technical',1,'RSI pehle FAIL'),
('https://www.youtube.com/watch?v=_xnj8vyjnUk','Oil price drop: Iran peace talks, Hormuz and rate hikes (Nov 2026)','geopolitics',2,'2026 live'),
('https://www.youtube.com/watch?v=1t4XIJh0Zks','Oil rises after Iran warns Hormuz traffic may not fully recover','geopolitics',2,''),
('https://www.youtube.com/watch?v=Ac6eQXtZhc0','Oil tops $90 after US-Iran tensions disrupt Hormuz shipping','geopolitics',2,''),
('https://www.youtube.com/watch?v=8h54fT_0I3k','How high could the Iran war take oil prices?','geopolitics',2,''),
('https://www.youtube.com/watch?v=nB7bW_gC0M0','Crude falls as US-Iran deal could reopen Hormuz; gold, silver gain','geopolitics',2,''),
('https://www.youtube.com/watch?v=PMszCn78MfU','How the US-Iran deal could affect oil prices','geopolitics',2,''),
('https://www.youtube.com/watch?v=jstOWsWvbAU','Tom Sosnoff - inside the mind of a trading legend (options)','options-sell',2,''),
('https://www.youtube.com/watch?v=PS5MXOlx2IA','Nick Radge - 40 years of systematic trading','technical',3,'rules-based momentum'),
]
W = {'gold-fed': 10, 'options-backtest': 9, 'fii-flows': 9, 'geopolitics': 8, 'macro': 8, 'emotions': 8, 'options-buy': 7, 'value': 7,
     'value-india': 7, 'technical': 6, 'intraday': 6, 'options-sell': 5, 'options-structure': 6, 'news': 3}
rows = [dict(url=u, title=t, topic=tp, source='web search 26 Nov', trust=tr, note=n, score=W[tp] + 2 * tr - (6 if tr == 0 else 0)) for u, t, tp, tr, n in S]
# queue items not yet deep-read
q = pd.read_csv(f'{E}/queue.csv'); y = q[q.type == 'youtube_channel'].copy()
done = set(l.strip() for l in open(f'{E}/gemini/done.txt'))
def deep(r):
    f = str(r.transcript_file) if pd.notna(r.transcript_file) else ''
    return (f and os.path.exists('/home/claude/market-data/' + f) and os.path.getsize('/home/claude/market-data/' + f) > 500) or r.item_id in done or os.path.exists(f'{E}/gemini/{r.item_id}.md')
y = y[~y.apply(deep, axis=1)]
trust = {'Aswath Damodaran': 3, 'Ben Felix': 3, 'The Compound': 2, 'Real Vision': 2, 'Forward Guidance': 2, 'Zerodha (YouTube)': 2, 'CA Rachana Ranade': 2,
         'Elearnmarkets': 2, 'PR Sundar': 1, 'Dhan (YouTube)': 1, 'Groww (YouTube)': 1, 'Angel One (YouTube)': 1, '5paisa (YouTube)': 1, 'Pranjal Kamra': 1,
         'Asset Yogi': 1, 'Trading Chanakya': 1, 'Nitish Kumar Trader': 1, 'NDTV Profit (YouTube)': 1}
kw = [(r'\bgold\b|\bsilver\b|\bfed\b|\byields?\b|rate hike|real rates', 'gold-fed'), ('fii|fpi|foreign', 'fii-flows'), ('option|straddle|strangle|theta|iron condor|expiry', 'options-backtest'),
      ('iran|hormuz|oil|crude|trump|tariff|war', 'geopolitics'), ('valuation|roe|moat|compound|long term|wealth', 'value'), ('intraday|scalp|vwap|breakout|setup|rsi|ema', 'intraday'),
      ('psycholog|emotion|fear|greed|discipline', 'emotions'), ('inflation|recession|economy|liquidity|bond', 'macro')]
for r in y.itertuples():
    t = str(r.title).lower(); tp = next((v for k, v in kw if re.search(k, t)), 'news')
    if re.search(r'tragedy|dead|killed|trapped|accident', t): tp = 'news'
    tr = trust.get(r.source, 1); short = '/shorts/' in str(r.link)
    sc = W[tp] + 2 * tr + min(int(r.score if pd.notna(r.score) else 0), 6) * 0.5 - (4 if short else 0) - (3 if r.source == 'NDTV Profit (YouTube)' and tp == 'news' else 0)
    rows.append(dict(url=r.link, title=r.title, topic=tp, source=r.source + ' (robot queue)', trust=tr, note=('short' if short else ''), score=sc))
D = pd.DataFrame(rows).drop_duplicates('url').sort_values('score', ascending=False)
D = D[D.topic != 'news'].head(200).reset_index(drop=True)
D.insert(0, 'rank', D.index + 1); D['status'] = 'todo'
D.to_csv(f'{E}/manual/video_list.csv', index=False)
L = ['# Tosif के लिए video list (priority क्रम) — बनाई 26 Nov 2026', '',
     'तरीका: link खोलें → description में "...more" → "Show transcript" → पूरा text copy → chat में भेजें (एक बार में 5-10 videos ठीक)।',
     '"SHAQ" वाले = AI-आवाज़ वाले नकली channel जैसे लगते — सबसे नीचे, न पढ़ें तो भी ठीक।', '']
for b in range(0, len(D), 50):
    L.append(f'## Batch {b // 50 + 1} (rank {b + 1}-{min(b + 50, len(D))})'); L.append('')
    for r in D.iloc[b:b + 50].itertuples():
        L.append(f'{r.rank}. [{r.topic}] {r.title} — {r.url}' + (f'  ({r.note})' if r.note else ''))
    L.append('')
open(f'{E}/manual/video_list.md', 'w').write('\n'.join(L))
print(len(D), D.topic.value_counts().to_dict()); print(D.head(12)[['rank', 'topic', 'title']].to_string())
