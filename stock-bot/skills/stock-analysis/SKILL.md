---
name: stock-analysis
description: "Detect stock anomalies using Bollinger Bands — overbought and oversold signals"
---

# Stock Analysis Skill

## When to Use
- User asks about overbought or oversold conditions
- User wants to detect price anomalies
- User asks about Bollinger Bands
- User wants technical analysis signals

## Workflow

### Step 1: Identify Parameters
- Get the stock code (ts_code)
- Optionally get start_date and end_date (defaults to past 1 year)

### Step 2: Call the Bollinger Tool
- Use `boll_detection(ts_code="600519.SH")` for default analysis
- Use `boll_detection(ts_code="600519.SH", start_date="2025-01-01", end_date="2025-12-31")` for custom range

### Step 3: Interpret Results
- **Overbought** (超买): closing price broke above upper band — may indicate overvaluation
- **Oversold** (超卖): closing price fell below lower band — may indicate undervaluation
- **Bollinger Band Position**: 0% = at lower band, 100% = at upper band, 50% = at middle band

### Step 4: Present Results
- Include the full report and chart from the tool
- Explain what the signals mean in plain language
- Always add disclaimer: this is technical analysis only, not investment advice

## Bollinger Band Parameters
- Window: 20 trading days
- Standard deviations: ±2σ
- Upper band = MA(20) + 2σ
- Lower band = MA(20) - 2σ
