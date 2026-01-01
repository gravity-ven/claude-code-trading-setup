---
description: Get current market context from all data sources (barometers, COT, macro regime)
allowed-tools: Bash(curl:*)
---

Fetch comprehensive market context from the Trading LLM system:

```bash
curl -s http://localhost:9005/api/context
```

Present the market context including:
1. Composite Risk Score (0-100) and status (GREEN/YELLOW/RED)
2. Market Mode (Risk-On, Risk-Off, Transition)
3. VIX level and interpretation
4. Growth and Inflation regimes
5. COT positioning signals for key markets
6. Active breakthrough patterns

Provide actionable interpretation of current conditions.
