---
name: stock-forecast
description: "Forecast stock closing prices using ARIMA model"
---

# Stock Forecast Skill

## When to Use
- User asks to predict future stock prices
- User wants to know where a stock might be heading
- User asks about price trends in the coming days

## Workflow

### Step 1: Identify the Stock
- Get the stock code (ts_code) from the user
- Common codes: 贵州茅台=600519.SH, 五粮液=000858.SZ, 广发证券=000776.SZ, 中芯国际=688981.SH

### Step 2: Call the ARIMA Tool
- Use `arima_stock(ts_code="600519.SH")` for default 5-day forecast
- Use `arima_stock(ts_code="600519.SH", n=10)` for custom forecast days
- The tool uses ARIMA(5,1,5) model on the past year of data

### Step 3: Present Results
- The tool returns a forecast table and chart
- Always include both in your response
- Add a disclaimer that this is statistical prediction only, not investment advice

## Important Notes
- ARIMA requires at least 30 trading days of history
- The model uses the past 1 year of closing price data
- Forecast is based purely on historical price patterns
- Always remind users: this does not constitute investment advice
