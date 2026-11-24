# Zerodha + Claude AI Integration & Portfolio Analysis
स्रोत: Tosif link · https://www.youtube.com/watch?v=jYqDEE5QL-w · Gemini ने पढ़ा 2026-11-24 23:38 UTC

**काम का नहीं:** Video mainly demonstrates Zerodha + Claude AI MCP integration for portfolio analysis (tracking winners/losers, tariff impact, tax loss harvesting). It does not contain specific backtestable trading strategy parameters.

## Point-by-point
- Zerodha has integrated with Claude AI Desktop via Model Context Protocol (MCP), allowing AI to directly access user portfolio holdings, P&L, trades, and sector allocation via Kite APIs.
- Claude AI can be prompted to calculate top 3 winning and losing stocks over the past 6 months without needing to manually export Excel sheets.
- Macro Event Impact Prompting: Claude can evaluate news events (e.g., US Trump tariffs) against a user's portfolio stocks by checking revenue geographic exposure and estimating stock price impact.
- Tax Loss Harvesting Prompting: Claude can scan unrealized losses in portfolio holdings, estimate potential tax savings against Short-Term/Long-Term Capital Gains, and suggest loss booking options.
- Under Indian Tax Laws, short-term and long-term capital losses booked via tax harvesting can be carried forward for up to 8 financial years to set off against future capital gains.
- Growth Investing Portfolio Structure: A high small-cap allocation (>80-90%) yields higher beta and volatility; risk management involves techno-funda filters such as exiting/limiting downside when stocks fall below their 200 EMA.
- Technical Setup of MCP: Requires Node.js and Claude Desktop App, adding Zerodha's MCP remote URL configuration under Claude's Developer settings.
- API Security & Authorization: Every API call fetching data or initiating trade actions requires explicit user authorization prompts to prevent unauthorized trade execution.

## Niyam
