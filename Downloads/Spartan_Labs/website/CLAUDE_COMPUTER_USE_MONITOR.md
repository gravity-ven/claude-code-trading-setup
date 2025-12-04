# Claude Computer Use Visual Monitor

## 🤖 Overview

The **Claude Computer Use Visual Monitor** is an autonomous AI system that visually inspects your Spartan Research Station website using Claude's computer use API and Playwright browser automation. It takes screenshots, analyzes them with Claude's vision capabilities, and automatically fixes detected issues.

## 🎯 Key Features

### 1. **Visual AI Inspection**
- Takes full-page screenshots of the dashboard every 5 minutes
- Uses Claude Sonnet 4.5's vision API to analyze screenshots
- Detects visual errors, broken UI components, and data display issues
- Identifies layout problems, missing images, and error messages

### 2. **Intelligent Analysis**
- Combines Claude's visual analysis with Mojo Spartan Agent's multi-agent reasoning
- Pattern recognition for common issues (database, cache, frontend)
- Historical analysis of fix success rates
- Risk assessment and resource impact calculation

### 3. **Autonomous Fixing**
- **Restart Web Server** - Fixes transaction errors, connection issues
- **Clear Redis Cache** - Resolves stale data problems
- **Reset Database Connections** - Clears aborted transactions
- **Auto-verification** - Re-checks after fixing

### 4. **Multi-Agent Decision Engine (Mojo Spartan Agent)**
- **Agent 1**: Pattern Recognition - Identifies issue types
- **Agent 2**: Historical Analysis - Learns from past fixes
- **Agent 3**: Risk Assessment - Calculates fix risk scores
- **Agent 4**: Resource Impact - Estimates downtime and resource usage
- **Meta-Agent**: Combines insights for optimal strategy

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MONITORING FLOW                          │
│                                                             │
│  1. Playwright → Launch Chromium Browser (Headless)        │
│  2. Browser → Navigate to http://spartan_web:8888          │
│  3. Browser → Wait for content, capture full screenshot    │
│  4. Screenshot → Convert to base64                         │
│  5. Claude API → Analyze screenshot + HTML content         │
│  6. Mojo Agent → Multi-agent reasoning on Claude's output  │
│  7. Decision → Execute auto-fix if confidence > 80%        │
│  8. Verify → Re-check website health                       │
│  9. Sleep → Wait 5 minutes (configurable)                  │
│  10. REPEAT                                                │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Configuration

### Environment Variables

**Required:**
```bash
ANTHROPIC_API_KEY=sk-ant-...  # Claude API key for visual analysis
```

**Optional:**
```bash
WEBSITE_URL=http://spartan_web:8888           # URL to monitor
VISUAL_CHECK_INTERVAL=300                     # Check every 5 minutes
LOG_LEVEL=INFO                                # Logging verbosity
```

### Docker Compose Integration

The monitor is integrated as **Phase 4.6** in `docker-compose.spartan.yml`:

```yaml
claude_computer_use:
  build:
    context: .
    dockerfile: Dockerfile.claude-computer-use
  image: spartan_claude_computer_use:latest
  container_name: spartan_claude_computer_use
  depends_on:
    web:
      condition: service_healthy
  environment:
    ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    WEBSITE_URL: http://spartan_web:8888
    CHECK_INTERVAL: 300
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - ./logs:/app/screenshots:rw
  shm_size: '2gb'  # Chromium requirement
```

## 🚀 Quick Start

### 1. Add API Key to .env

```bash
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env
```

### 2. Build and Start

```bash
# Build the Claude Computer Use container
docker-compose -f docker-compose.spartan.yml build claude_computer_use

# Start all services (including Claude monitor)
docker-compose -f docker-compose.spartan.yml up -d

# Or start just the Claude monitor
docker-compose -f docker-compose.spartan.yml up -d claude_computer_use
```

### 3. Monitor Logs

```bash
# Watch Claude's visual analysis in real-time
docker logs -f spartan_claude_computer_use

# View screenshots
ls -lh logs/*.png
```

## 📊 Example Output

```
[2025-11-20 10:00:00] INFO: ======================================================================
[2025-11-20 10:00:00] INFO: CLAUDE COMPUTER USE MONITOR - STARTED
[2025-11-20 10:00:00] INFO: ======================================================================
[2025-11-20 10:00:00] INFO: Monitoring URL: http://spartan_web:8888
[2025-11-20 10:00:00] INFO: Check interval: 300s
[2025-11-20 10:00:00] INFO:
[2025-11-20 10:00:00] INFO: ======================================================================
[2025-11-20 10:00:00] INFO: Visual Check #1 at 10:00:00
[2025-11-20 10:00:00] INFO: ======================================================================
[2025-11-20 10:00:01] INFO: 🌐 Launching browser...
[2025-11-20 10:00:03] INFO: 📡 Loading http://spartan_web:8888...
[2025-11-20 10:00:08] INFO: ⏳ Waiting for content to load...
[2025-11-20 10:00:13] INFO: 📸 Screenshot saved: /app/screenshots/health_check_20251120_100013.png
[2025-11-20 10:00:15] INFO: 🤖 Analyzing with Claude...
[2025-11-20 10:00:18] INFO: Claude analysis complete: 1842 chars
[2025-11-20 10:00:18] INFO: 📊 ANALYSIS RESULTS:
[2025-11-20 10:00:18] INFO: {
  "status": "warning",
  "issues_found": [
    {
      "severity": "critical",
      "component": "VIX Volatility Index",
      "description": "Displaying 'Error' instead of data",
      "suggested_fix": "Check API endpoint /api/volatility"
    },
    {
      "severity": "warning",
      "component": "Market Breadth",
      "description": "Shows 'N/A' instead of advancing/declining data",
      "suggested_fix": "Verify /api/market/breadth endpoint"
    }
  ],
  "overall_assessment": "Dashboard mostly functional but 2 critical data endpoints failing"
}
[2025-11-20 10:00:18] INFO: 🧠 Mojo Agent: Analyzing issue...
[2025-11-20 10:00:18] INFO: ✅ Mojo Agent: Recommended RESTART_SERVICE
[2025-11-20 10:00:18] INFO:    Confidence: 95.00%
[2025-11-20 10:00:18] INFO:    Expected Success: 85.00%
[2025-11-20 10:00:18] WARNING: 🚨 CRITICAL ISSUES DETECTED - Triggering auto-fix...
[2025-11-20 10:00:18] WARNING: 🔧 AUTONOMOUS FIX: restart web server
[2025-11-20 10:00:18] INFO: Executing fix action: restart web server
[2025-11-20 10:00:28] INFO: ✅ Fix executed successfully: restart web server
[2025-11-20 10:00:28] INFO: 💤 Sleeping for 300 seconds...
```

## 🧩 Integration with Data Integrity Monitor

The Claude Computer Use Monitor **complements** the Data Integrity Monitor:

| **Data Integrity Monitor** | **Claude Computer Use Monitor** |
|---------------------------|-------------------------------|
| ✅ Validates API endpoints programmatically | ✅ Validates visual appearance and UX |
| ✅ Checks JSON response structure | ✅ Detects layout/CSS issues |
| ✅ Fast (HTTP requests only) | ✅ Comprehensive (full browser render) |
| ✅ Runs every 2 minutes | ✅ Runs every 5 minutes |
| ✅ Low resource usage | ✅ Higher resource (browser rendering) |

**Together**, they provide **complete** coverage:
1. Data Integrity Monitor catches API/data errors quickly
2. Claude Computer Use catches visual/UX issues that only appear in browser
3. Both auto-fix autonomously
4. Both log to `/tmp` for debugging

## 📁 File Structure

```
website/
├── claude_computer_use_monitor.py      # Main monitor script
├── Dockerfile.claude-computer-use      # Container definition
├── mojo_spartan_agent.py              # Multi-agent decision engine
├── docker-compose.spartan.yml         # Includes claude_computer_use service
└── logs/
    └── health_check_*.png             # Screenshots saved here
```

## 🔍 Troubleshooting

### Issue: Claude API Error

```bash
# Check API key is set
docker exec spartan_claude_computer_use printenv | grep ANTHROPIC_API_KEY

# Verify API key is valid (test externally)
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

### Issue: Browser Crashes

```bash
# Increase shared memory (already set in docker-compose.yml)
# If still crashing, increase shm_size from 2gb to 4gb

# Check logs
docker logs spartan_claude_computer_use | grep -i "error"
```

### Issue: Screenshots Not Saving

```bash
# Check volume mount
docker inspect spartan_claude_computer_use | grep -A 5 "Mounts"

# Verify permissions
ls -la logs/
```

## 🎓 How It Works: Claude Vision API

The monitor uses Claude's vision capabilities to analyze screenshots. Here's what Claude sees:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_base64  # Full-page screenshot
                }
            },
            {
                "type": "text",
                "text": "Analyze this dashboard and identify ALL errors..."
            }
        ]
    }]
)
```

Claude analyzes:
- ✅ Visual errors ("Error" text, broken icons)
- ✅ Layout issues (misaligned elements)
- ✅ Missing data (empty sections)
- ✅ Color problems (wrong styling)
- ✅ Functional issues (broken buttons, forms)

## 🚀 Advanced Usage

### Custom Fix Strategies

Edit `claude_computer_use_monitor.py` to add custom fixes:

```python
def execute_fix(self, fix_description):
    fix_actions = {
        "restart web server": lambda: subprocess.run(['docker', 'restart', 'spartan_web']),
        "clear redis cache": lambda: subprocess.run(['docker', 'exec', 'spartan_redis', 'redis-cli', 'FLUSHDB']),

        # Add your custom fix here
        "rebuild frontend": lambda: subprocess.run(['docker-compose', '-f', 'docker-compose.spartan.yml', 'up', '-d', '--build', 'web']),
    }
```

### Adjust Check Frequency

```bash
# Check every 2 minutes (more frequent)
VISUAL_CHECK_INTERVAL=120

# Check every 10 minutes (less resource intensive)
VISUAL_CHECK_INTERVAL=600
```

### Screenshot Analysis

Screenshots are saved with timestamps for manual review:

```bash
# View all screenshots
ls -lh logs/health_check_*.png

# Open most recent screenshot
open logs/health_check_$(ls -t logs/health_check_*.png | head -1)
```

## 📈 Performance Impact

| Resource | Impact | Notes |
|----------|--------|-------|
| CPU | Low (5-10% spike during check) | Chromium rendering |
| Memory | ~500MB | Playwright + Chromium |
| Network | ~5MB per check | Screenshot + Claude API |
| Storage | ~2MB per screenshot | Auto-cleaned after 30 days |

## 🔒 Security Notes

- Claude API key stored in `.env` (never commit!)
- Screenshots may contain sensitive data - stored in mounted volume
- Docker socket access required for auto-fixes (container restart)
- HTTPS recommended for production API calls

## 📚 Related Documentation

- [Data Integrity Monitor](DOCKER_AUTONOMOUS_ORCHESTRATION.md) - Programmatic API validation
- [Docker Compose Guide](docker-compose.spartan.yml) - Full stack orchestration
- [Claude API Docs](https://docs.anthropic.com/) - Vision API reference
- [Playwright Docs](https://playwright.dev/) - Browser automation

---

**Created**: November 20, 2025
**Status**: ✅ Production Ready
**Autonomous**: Yes - No user intervention required
**AI-Powered**: Claude Sonnet 4.5 + Mojo Multi-Agent System
