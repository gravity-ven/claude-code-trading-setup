#!/bin/bash
"""
Spartan Research Station - Agent Swarm Launcher
================================================

Launches all autonomous data agents via the orchestrator.
"""

echo "="
echo "🤖 SPARTAN RESEARCH STATION - AUTONOMOUS AGENT SWARM"
echo "="
echo ""
echo "Launching Tier 1 Critical Agents (14 agents)..."
echo ""

# Navigate to website directory
cd "$(dirname "$0")"

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running"
    echo "   Start PostgreSQL first:"
    echo "   - macOS: brew services start postgresql@15"
    echo "   - Linux: sudo systemctl start postgresql"
    echo "   - WSL2: sudo service postgresql start"
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running"
    echo "   Start Redis first:"
    echo "   - macOS: brew services start redis"
    echo "   - Linux: sudo systemctl start redis"
    echo "   - WSL2: sudo service redis-server start"
    exit 1
fi

echo "✅ PostgreSQL running"
echo "✅ Redis running"
echo ""

# Launch orchestrator
echo "🚀 Launching agent orchestrator..."
python3 agent_orchestrator.py 2>&1 | tee agent_orchestrator.log
