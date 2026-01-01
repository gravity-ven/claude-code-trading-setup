---
description: Analyze a futures contract (ES, NQ, GC, CL, ZN, etc.)
allowed-tools: Bash(curl:*)
---

Analyze the futures contract "$ARGUMENTS" using the Trading LLM system.

Get COT positioning data:
```bash
curl -s "http://localhost:5001/api/cot/data?symbol=$ARGUMENTS&weeks=12"
```

Get Trading LLM analysis:
```bash
curl -s "http://localhost:9005/api/analyze/futures/$ARGUMENTS"
```

Provide analysis including:
1. COT commercial vs speculator positioning
2. Trading signal with confidence
3. Macro regime context
4. Risk management levels
