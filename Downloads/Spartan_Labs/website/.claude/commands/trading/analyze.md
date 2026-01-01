---
description: Analyze a symbol using the Trading LLM AI Agent
allowed-tools: Bash(curl:*), WebFetch
---

Analyze the symbol "$ARGUMENTS" using our Trading LLM AI Agent system.

First, check if the Trading LLM API is running:
```bash
curl -s http://localhost:9005/api/health
```

Then analyze the symbol:
```bash
curl -s -X POST http://localhost:9005/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "$ARGUMENTS", "asset_class": "stocks"}'
```

Provide a comprehensive trading analysis including:
1. Signal direction (buy/sell/hold)
2. Confidence level
3. Entry, stop loss, and take profit levels
4. Key supporting factors and risks
5. Position sizing recommendation
