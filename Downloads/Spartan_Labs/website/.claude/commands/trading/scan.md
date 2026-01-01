---
description: Run full market scan across all asset classes (futures, stocks, forex, bonds)
allowed-tools: Bash(curl:*)
---

Run a comprehensive market scan using the Trading LLM AI Agent.

First, get the current market context:
```bash
curl -s http://localhost:9005/api/context/summary
```

Then run the full market scan:
```bash
curl -s http://localhost:9005/api/scan
```

Also get the top signals:
```bash
curl -s "http://localhost:9005/api/top-signals?limit=10&min_confidence=60"
```

Summarize:
1. Current market regime (Risk-On/Off, growth, inflation)
2. Top trading opportunities across all asset classes
3. Signals sorted by confidence
4. Any warnings or risk factors to consider
