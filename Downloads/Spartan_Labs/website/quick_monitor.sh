#!/bin/bash
# Quick AI Monitoring - One-liner access
# Usage: ./quick_monitor.sh [claude|gemini|auto]

AI_CHOICE="${1:-auto}"
echo "🚀 Quick AI Monitoring ($AI_CHOICE)..."

# Simple one-liner execution
python3 ai_monitor.py "$AI_CHOICE" 2>/dev/null | grep -E "(✅|❌|🔍|🚨|🔍|🛠️|🎯)" | head -10
