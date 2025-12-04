#!/bin/bash
# Unified AI Monitoring - Claude Code + Gemini CLI DNA Bridge
# Usage: ./unified_monitor.sh [claude|gemini|auto] [context]

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
AI_CHOICE="${1:-auto}"
CONTEXT="${2:-ROUTINE_MONITORING}"

echo -e "${BLUE}🤖 Spartan Research Station - Unified AI Monitoring${NC}"
echo "=================================================="
echo -e "${YELLOW}🎯 AI: $AI_CHOICE | Context: $CONTEXT${NC}"

# Source the DNA bridge
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get system status
echo "🔍 Collecting system status..."
python3 -c "
import json, subprocess, os, sys
from datetime import datetime

def get_system_status():
    status = {
        'timestamp': datetime.now().isoformat(),
        'containers': [],
        'endpoints': [],
        'disk_memory': {},
        'recent_errors': []
    }
    
    try:
        # Container status
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[3:]  # Skip header lines
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        status['containers'].append({
                            'name': parts[0] if parts[0] != '-' else 'unknown',
                            'state': parts[1] if len(parts) > 1 else 'unknown'
                        })
        
        # Health endpoints
        endpoints = [
            ('Web Server', 'http://localhost:8888/health'),
            ('Daily Planet', 'http://localhost:5000/health'),
            ('GARP API', 'http://localhost:5003/health'),
            ('Swing API', 'http://localhost:5002/health'),
            ('Correlation API', 'http://localhost:5004/health')
        ]
        
        for name, url in endpoints:
            try:
                result = subprocess.run(['curl', '-s', '--max-time', '3', url], 
                                       capture_output=True, text=True, timeout=10)
                status['endpoints'].append({
                    'name': name,
                    'status': 'healthy' if result.returncode == 0 else 'error',
                    'response_time': 'fast' if '200' in (result.stdout + result.stderr) else 'slow'
                })
            except:
                status['endpoints'].append({'name': name, 'status': 'error', 'response_time': 'timeout'})
        
        # Disk and memory
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
            status['disk_memory']['disk'] = result.stdout
        except: status['disk_memory']['disk'] = 'unavailable'
        
        try:
            result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
            status['disk_memory']['memory'] = result.stdout  
        except: status['disk_memory']['memory'] = 'unavailable'
            
    except Exception as e:
        status['error'] = f'Status collection failed: {str(e)[:100]}'
    
    print(json.dumps(status, indent=2, default=str))
" > /tmp/spartan_status.json

# Call the appropriate AI monitoring system
if command -v claude &> /dev/null && [[ "$AI_CHOICE" =~ ^(claude|auto)$ ]]; then
    echo -e "${GREEN}🧠 Using Claude Code with unified DNA...${NC}"
    python3 ai_dna_bridge.py | claude
elif command -v gemini &> /dev/null && [[ "$AI_CHOICE" =~ ^(gemini|auto)$ ]]; then
    echo -e "${GREEN}💎 Using Gemini CLI with unified DNA...${NC}"
    python3 ai_dna_bridge.py | gemini
else
    echo -e "${RED}❌ No AI system available. Install Claude Code or Gemini CLI.${NC}"
    echo -e "${YELLOW}Claude: curl -fsSL https://claude.ai/install.sh | sh${NC}"
    echo -e "${YELLOW}Gemini: gem install google-generative-ai${NC}"
    exit 1
fi

# Clean up
rm -f /tmp/spartan_status.json
