#!/bin/bash
# Quick check if COT data is available

OUTPUT_FILE="output/latest_trade_sheet.txt"

if [ -f "$OUTPUT_FILE" ]; then
    SHEET_DATE=$(head -5 "$OUTPUT_FILE" | grep -oP '\d{4}-\d{2}-\d{2}' | head -1)
    echo "✅ Trade sheet available: $SHEET_DATE"
    echo ""
    echo "View with:"
    echo "  cat output/latest_trade_sheet.txt"
    echo ""
    echo "Recent opportunities:"
    grep -A 5 "TOP LONG" "$OUTPUT_FILE" 2>/dev/null || echo "  (Waiting for CFTC data)"
else
    echo "⏳ No trade sheet yet - waiting for CFTC data"
    echo ""
    echo "Check logs:"
    echo "  tail -20 logs/cot_weekend.log"
fi
