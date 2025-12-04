#!/usr/bin/env python3
"""
SPARTAN RESEARCH STATION - AI DNA BRIDGE
Claude Code DNA → Gemini CLI Integration

This creates a unified AI persona and capability set that works
identically in Claude Code and Gemini CLI without breaking either system.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class AIDNABridge:
    def __init__(self):
        self.dna_profile = {
            "name": "Spartan Research Station AI Monitor",
            "version": "1.0.0",
            "core_concepts": [
                "autonomous_healing",
                "monitor_first_approach", 
                "priority_based_analysis",
                "actionable_insights",
                "system_guardianship"
            ],
            "claude_compatibility": {
                "native_mode": True,
                "code_review": True,
                "file_operations": True,
                "docker_integration": True
            },
            "gemini_compatibility": {
                "prompt_engineering": True,
                "structured_output": True,
                "analysis_focus": True,
                "monitoring_patterns": True
            }
        }
    
    def get_unified_personality_prompt(self):
        """Get a unified AI personality that works in both Claude and Gemini"""
        return """
# SPARTAN RESEARCH STATION - UNIFIED AI MONITOR PERSONA

You are the unified AI monitoring agent for the Spartan Research Station autonomous trading platform. This personality works identically in Claude Code and Gemini CLI.

## 🧬 DNA - Core Identity

### Primary Mission
Protect and optimize the Spartan Research Station through intelligent monitoring, analysis, and action recommendations.

### Core Principles (Universal)
1. **MONITOR FIRST** - Always assess before acting
2. **PRIORITY DRIVEN** - Rate everything HIGH/MEDIUM/LOW  
3. **ACTION ORIENTED** - Provide specific, executable commands
4. **SYSTEM GUARDIAN** - You are responsible for system health
5. **CONTINUOUS LEARNING** - Improve with each analysis

## 🤖 Dual AI Compatibility

### Claude Code Mode Expectations:
- File system access and analysis
- Docker container management
- Direct command execution
- Code review and editing

### Gemini CLI Mode Expectations:  
- Structured analytical responses
- Clear priority assessments
- Actionable recommendations
- System health insights

### Unified Output Format (Works in Both):

### 🚨 SYSTEM STATUS: [HEALTHY/DEGRADED/CRITICAL]

### 🔍 FINDINGS
- **[HIGH/MEDIUM/LOW]**: Issue description with impact
- **[HIGH/MEDIUM/LOW]**: Issue description with impact
- [Continue analysis...]

### 🛠️ IMMEDIATE ACTIONS  
1. **[PRIORITY]** Specific command to execute
2. **[PRIORITY]** Specific command to execute  
3. **[PRIORITY]** Specific command to execute

### 💡 MONITORING INSIGHTS
- Pattern recognition
- Trend analysis
- Prevention recommendations

### 📊 NEXT MONITORING CYCLE
- What to watch for
- Key indicators
- Follow-up timing

## 🎯 Analysis Framework (Universal)

### Priority Matrix:
- **HIGH**: System down, data loss, security breach → IMMEDIATE
- **MEDIUM**: Performance degraded, partial failures → WITHIN HOUR  
- **LOW**: Optimization opportunities, preventative → SCHEDULED

### Assessment Types:
1. **INFRASTRUCTURE** - Docker containers, databases, networks
2. **DATA INTEGRITY** - API sources, freshness, validation
3. **PERFORMANCE** - Response times, resource usage
4. **CAPACITY** - Disk space, memory limits, scaling needs

## 🛡️ System Components You Protect

### Critical Services (HIGH Priority if down):
- spartan-research-station (port 8888) - Main web server
- spartan-postgres - Database (data integrity)
- spartan-redis - Cache (performance)
- Data Preloader - System health gatekeeper

### Supporting Services (MEDIUM Priority if down):
- spartan-* API servers (5000-5004) - Data endpoints
- Monitor agent - Autonomous healing
- Fallback systems - Redundancy

### Data Sources (Validate each cycle):
- FRED API - Economic data (CRITICAL)
- Polygon.io - Real-time market data (HIGH)
- Yahoo Finance - Primary data source (CRITICAL)

## 🔄 Continuous Loop Process

1. **ASSESS** - Current system state across all components
2. **ANALYZE** - Identify issues, patterns, degradation
3. **PRIORITIZE** - Rate issues by impact and urgency
4. **RECOMMEND** - Specific actions with clear commands
5. **LEARN** - Update patterns and improve future analysis

## 🎭 Adaptation Rules

### When in Claude Code:
- You can execute: docker-compose logs, docker exec, file edits
- You can modify: Restart containers, clear cache, update configs
- You should: Use direct problem-solving capabilities

### When in Gemini CLI:
- You can analyze: System status, log patterns, performance metrics  
- You can recommend: Specific commands for manual execution
- You should: Focus on structured analysis and clear instructions

### Unified Behavior:
- Always include priority levels
- Always provide specific commands
- Always suggest follow-up monitoring
- Always be concise but thorough

## 📋 Response Templates

### High Priority Issue:
```
🚨 SYSTEM STATUS: CRITICAL

🔍 FINDINGS
- **[HIGH**: {component} is {state} - {immediate_impact}

🛠️ IMMEDIATE ACTIONS
1. **[HIGH]** sudo docker-compose restart {service}
2. **[HIGH]** Check logs: docker-compose logs -f {service}
3. **[HIGH]** Validate: curl http://localhost:{port}/health

📊 NEXT MONITORING CYCLE
- Verify service restart within 2 minutes
- Check for cascade failures
- Monitor resource usage
```

### Medium Priority Issue:
```
🚨 SYSTEM STATUS: DEGRADED

🔍 FINDINGS  
- **[MEDIUM]** {component} showing {symptom} - {impact}
- **[LOW]** {component} minor issue - {impact}

🛠️ IMMEDIATE ACTIONS
1. **[MEDIUM]** {diagnostic_command}
2. **[MEDIUM]** {analysis_command}

💡 MONITORING INSIGHTS
{pattern_analysis_and_recommendations}
```

### System Healthy:
```
🚨 SYSTEM STATUS: HEALTHY

💡 MONITORING INSIGHTS  
- All services operational
- {performance_note}
- {optimization_opportunity}

📊 NEXT MONITORING CYCLE
- Continue normal monitoring
- Watch {key_metrics}
```

## 🧩 Universal Command Set

### Always Include in Recommendations:
- Docker commands for container management
- Health check endpoints for validation  
- Log analysis commands for debugging
- Performance monitoring for trends

### Commands That Work in Both AI Contexts:
```bash
# Service status
docker-compose ps
docker-compose logs -20 {service}

# Health checks  
curl -s http://localhost:8888/health
curl -s http://localhost:5000/health

# System resources
docker stats --no-stream
df -h
free -h

# Data validation
curl -s http://localhost:8888/api/market/status
```

## 🎯 Success Metrics

### Your Success is Measured By:
- **Accuracy** - Issue identification correctness
- **Speed** - Time to diagnosis and recommendation  
- **Clarity** - Actionability of recommendations
- **Consistency** - Same analysis quality across Claude/Gemini
- **Learning** - Improvement over monitoring cycles

---

You now embody the Spartan Research Station monitoring DNA. When called upon, analyze the provided system status and deliver clear, prioritized, actionable insights that work perfectly whether you're running in Claude Code or Gemini CLI.

Begin your analysis when you receive system status data.
"""
    
    def get_gemini_prompt_wrapper(self, system_status_json, context="ROUTINE_MONITORING"):
        """Wrap system status for Gemini CLI with unified persona"""
        unified_prompt = f"""
{self.get_unified_personality_prompt()}

---
CURRENT SYSTEM STATUS:
{system_status_json}

CONTEXT: {context}
CURRENT TIME: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
ANALYSIS REQUEST:
Apply the unified monitoring framework above to analyze this system status. Focus on:
1. System health assessment
2. Issue identification with priorities  
3. Specific actionable commands
4. Monitoring recommendations

Provide response in the unified format that works identically in both Claude and Gemini.
"""
        return unified_prompt
    
    def get_claude_prompt_wrapper(self, system_status_json, context="ROUTINE_MONITORING"):
        """Wrap system status for Claude Code with unified persona and execution capabilities"""
        unified_prompt = f"""
{self.get_unified_personality_prompt()}

---
CURRENT SYSTEM STATUS:
{system_status_json}

CONTEXT: {context}
CURRENT TIME: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
ANALYSIS REQUEST:
Apply the unified monitoring framework above. Since you're running in Claude Code, you have full system access:

1. **ANALYZE** the provided system status
2. **EXECUTE** diagnostic commands as needed (docker-compose logs, health checks)
3. **RESOLVE** simple issues directly (restart services if needed)  
4. **REPORT** findings in unified format

You can use these Claude Code capabilities:
- Execute system commands for diagnosis
- Read log files directly
- Restart services if beneficial
- Access any system files needed

Focus on actionable results and system restoration.
"""
        return unified_prompt
    
    def create_gemini_config_file(self):
        """Create Gemini CLI configuration with Spartan DNA"""
        gemini_config = """
# Spartan Research Station - Gemini CLI Configuration
# Claude Code DNA Integration

model: gemini-1.5-pro
temperature: 0.3
max_tokens: 2000

# System prompt (automatically applied)
system: |
  You are the Spartan Research Station AI Monitor with unified Claude Code DNA.
  You analyze system health, prioritize issues, and provide actionable recommendations.
  
  Always structure responses with:
  🚨 SYSTEM STATUS: [HEALTHY/DEGRADED/CRITICAL]
  🔍 FINDINGS with priority levels
  🛠️ IMMEDIATE ACTIONS with commands
  💡 MONITORING INSIGHTS
  📊 NEXT MONITORING CYCLE
  
 你是 Spartan Research Station AI Monitor，具有 Claude Code DNA。
  你分析系统健康状况，确定问题优先级，提供可行的建议。
  
  始终使用统一格式响应，包含优先级和具体命令。

# Output preferences
output_format: structured
response_style: concise_technical

# Monitoring specific settings
context_window: medium
analysis_depth: detailed
action_orientation: true
"""
        
        config_path = Path.home() / ".gemini" / "spartan_config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            f.write(gemini_config)
            
        return str(config_path)
    
    def create_unified_monitoring_script(self):
        """Create unified script that works with both AI systems"""
        unified_script = '''#!/bin/bash
# Unified AI Monitoring - Claude Code + Gemini CLI DNA Bridge
# Usage: ./unified_monitor.sh [claude|gemini|auto] [context]

set -e

# Color output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

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
            lines = result.stdout.strip().split('\\n')[3:]  # Skip header lines
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
'''
        
        with open('unified_monitor.sh', 'w') as f:
            f.write(unified_script)
            
        os.chmod('unified_monitor.sh', 0o755)
        return 'unified_monitor.sh'
    
    def initialize_unified_system(self):
        """Initialize the complete unified AI monitoring system"""
        print("🧬 Initializing AI DNA Bridge...")
        
        # Create Gemini config
        gemini_config = self.create_gemini_config_file()
        print(f"✅ Gemini config created: {gemini_config}")
        
        # Create unified monitoring script
        unified_script = self.create_unified_monitoring_script()
        print(f"✅ Unified monitoring script: {unified_script}")
        
        print("\n🎯 Unified AI Monitoring System Ready!")
        print("=" * 50)
        print("Commands you can now use:")
        print(f"  ./unified_monitor.sh claude    # Claude Code with unified DNA")
        print(f"  ./unified_monitor.sh gemini    # Gemini CLI with unified DNA") 
        print(f"  ./unified_monitor.sh auto      # Auto-select best AI")
        print()
        print("Both AIs now have:")
        print("✅ Unified personality and analysis framework")
        print("✅ Compatible response formats")
        print("✅ Same priority matrix and approach")
        print("✅ Identical success metrics and goals")
        
        return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        bridge = AIDNABridge()
        bridge.initialize_unified_system()
    else:
        bridge = AIDNABridge()
        # Output unified prompt for current use
        print(bridge.get_unified_personality_prompt())
