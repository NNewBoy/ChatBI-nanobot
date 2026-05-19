---
name: stock-query
description: "Write and execute SQL queries to answer user questions about stock history data"
---

# Stock Query Skill

## When to Use
- User asks a question that requires querying stock history data
- User wants to analyze, compare, or aggregate stock prices/volumes
- User wants to view stock trends over a time period

## Workflow

### Step 1: Understand the Question
- Identify which stock (ts_code) and time period the user is asking about
- Determine which columns are needed (close, pct_chg, vol, etc.)
- If unsure about schema, read the `stock-analysis` skill first

### Step 2: Write the Query
- Always use WHERE clause with ts_code for stock-specific queries
- Use BETWEEN for date range filtering on trade_date
- Use ORDER BY trade_date for time-series results
- Use strftime('%Y-%m', trade_date) for monthly aggregation in SQLite
- Use `change` for the 涨跌额 column (not a reserved word in SQLite)

### Step 3: Execute and Verify
- Run with `query_db(sql="YOUR QUERY")`
- If error: analyze the message, fix the query, retry
- If results look wrong: check WHERE clauses and JOINs

### Step 4: Present Results
- Format results as a clear answer in natural language
- Include the actual numbers/data from the query
- The tool will automatically generate charts — include them in your response

## Common Patterns
- Single stock trend: `WHERE ts_code='600519.SH' AND trade_date BETWEEN '...' AND '...'`
- Multi-stock comparison: `WHERE ts_code IN ('600519.SH','000858.SZ') AND trade_date BETWEEN '...' AND '...'`
- Ranking: `ORDER BY pct_chg DESC LIMIT N`
- Monthly aggregation: `GROUP BY strftime('%Y-%m', trade_date)`

## Error Recovery
- "no such column: change_val" -> use `change` instead
- "no such column" -> check table schema, use PRAGMA table_info(stock_history)
- Wrong results -> verify ts_code format (e.g. 600519.SH not 600519)
