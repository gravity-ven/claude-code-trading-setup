# Alert Watcher Agent

## Overview

The Alert Watcher is a background monitoring system that continuously scans logs, metrics, and system state for critical patterns that require immediate attention or escalation to Claude Code.

## Architecture

### Alert Hierarchy

```
Level 1: INFO      → Log only (no action)
Level 2: WARNING   → Log + increment counter
Level 3: CRITICAL  → Log + trigger auto-heal
Level 4: EMERGENCY → Log + escalate to Claude Code
```

### Integration with Monitor

```
Alert Watcher (Pattern Detection)
    ↓
Website Monitor (Execution)
    ↓
Claude Code (Complex Issues)
```

**Alert Watcher** identifies what needs attention
**Website Monitor** executes healing strategies
**Claude Code** handles complex/persistent issues

## Alert Types

### 1. Data Source Alerts

**Pattern**: Consecutive data fetch failures

```python
ALERT_DATA_SOURCE_FAILURE = {
    'pattern': 'Failed to fetch {source}',
    'threshold': 3,  # Consecutive failures
    'severity': 'CRITICAL',
    'action': 'trigger_auto_heal',
    'healing_strategy': 'restart_container',
    'escalate_after': 5  # Escalate to Claude Code after 5 failures
}
```

**Example**:
```
2025-11-20 10:30:01 | WARNING | Failed to fetch yfinance:SPY (attempt 1/3)
2025-11-20 10:30:31 | WARNING | Failed to fetch yfinance:SPY (attempt 2/3)
2025-11-20 10:31:01 | CRITICAL | Failed to fetch yfinance:SPY (attempt 3/3) → Trigger auto-heal
```

### 2. Container Crash Alerts

**Pattern**: Container restart loops

```python
ALERT_CRASH_LOOP = {
    'pattern': 'Container {name} restarted',
    'threshold': 5,  # Restarts per hour
    'severity': 'EMERGENCY',
    'action': 'escalate_to_claude',
    'context': ['container_logs', 'resource_usage', 'recent_changes']
}
```

**Example**:
```
2025-11-20 10:00:00 | INFO | Container spartan-web restarted (1/5)
2025-11-20 10:05:00 | INFO | Container spartan-web restarted (2/5)
2025-11-20 10:10:00 | WARNING | Container spartan-web restarted (3/5)
2025-11-20 10:15:00 | CRITICAL | Container spartan-web restarted (4/5)
2025-11-20 10:20:00 | EMERGENCY | Container spartan-web restarted (5/5) → Escalate to Claude Code
```

### 3. Memory Leak Alerts

**Pattern**: Sustained high memory usage

```python
ALERT_MEMORY_LEAK = {
    'pattern': 'Memory usage > {threshold}%',
    'threshold': 80,
    'duration': 300,  # Sustained for 5 minutes
    'severity': 'WARNING',
    'action': 'log_and_monitor',
    'escalate_after': 600  # Escalate if sustained for 10 minutes
}
```

**Example**:
```
2025-11-20 10:30:00 | INFO | Memory usage: 75% (normal)
2025-11-20 10:35:00 | WARNING | Memory usage: 82% (5 min sustained)
2025-11-20 10:40:00 | CRITICAL | Memory usage: 85% (10 min sustained) → Escalate to Claude Code
```

### 4. Disk Space Alerts

**Pattern**: Low disk space

```python
ALERT_DISK_SPACE = {
    'pattern': 'Disk space < {threshold}%',
    'threshold': 10,
    'severity': 'CRITICAL',
    'action': 'trigger_cleanup',
    'cleanup_targets': ['old_logs', 'temp_files', 'docker_images']
}
```

**Example**:
```
2025-11-20 10:30:00 | WARNING | Disk space: 15% free
2025-11-20 10:35:00 | CRITICAL | Disk space: 8% free → Trigger cleanup
```

### 5. API Rate Limit Alerts

**Pattern**: API rate limit exceeded

```python
ALERT_RATE_LIMIT = {
    'pattern': 'Rate limit exceeded for {api}',
    'severity': 'WARNING',
    'action': 'reduce_request_rate',
    'backoff_strategy': 'exponential',
    'max_backoff': 300  # 5 minutes max delay
}
```

**Example**:
```
2025-11-20 10:30:00 | WARNING | Rate limit exceeded for yfinance → Backoff 10s
2025-11-20 10:30:10 | WARNING | Rate limit exceeded for yfinance → Backoff 20s
2025-11-20 10:30:30 | WARNING | Rate limit exceeded for yfinance → Backoff 40s
```

### 6. Database Connection Alerts

**Pattern**: Database connection errors

```python
ALERT_DB_CONNECTION = {
    'pattern': 'Database connection error',
    'threshold': 3,  # Consecutive errors
    'severity': 'CRITICAL',
    'action': 'reset_connection_pool',
    'escalate_after': 5
}
```

### 7. Data Corruption Alerts

**Pattern**: Fake data or corruption detected

```python
ALERT_DATA_CORRUPTION = {
    'pattern': 'Fake data detected in {source}',
    'severity': 'EMERGENCY',
    'action': 'escalate_to_claude',
    'immediate': True,  # No auto-heal, escalate immediately
    'context': ['data_sample', 'validation_rules', 'recent_changes']
}
```

### 8. Unknown Error Alerts

**Pattern**: Unrecognized error patterns

```python
ALERT_UNKNOWN_ERROR = {
    'pattern': 'Unknown error: {error_message}',
    'severity': 'WARNING',
    'action': 'escalate_to_claude',
    'context': ['full_stack_trace', 'container_logs', 'system_state']
}
```

## Implementation

### Main Class: `AlertWatcher`

**File**: `agents/alert_watcher/alert_watcher.py`

```python
class AlertWatcher:
    """Background alert monitoring with pattern detection."""

    def __init__(self, config_path: str = 'agents/alert_watcher/config.yaml'):
        self.config = self.load_config(config_path)
        self.alert_counters = defaultdict(int)
        self.alert_timers = defaultdict(list)
        self.db_conn = None

    async def start(self):
        """Start continuous monitoring loop."""
        await self.connect_database()

        while True:
            await self.scan_logs()
            await self.check_metrics()
            await self.check_system_state()

            # Process triggered alerts
            await self.process_alerts()

            # Sleep interval
            await asyncio.sleep(self.config['scan_interval'])

    async def scan_logs(self):
        """Scan container logs for alert patterns."""
        containers = ['spartan-web', 'spartan-refresh-scheduler', 'spartan-monitor']

        for container in containers:
            logs = await self.get_container_logs(container, tail=100)

            for line in logs:
                await self.match_alert_patterns(line, container)

    async def match_alert_patterns(self, log_line: str, container: str):
        """Match log line against alert patterns."""
        for alert_type, alert_config in self.config['alerts'].items():
            pattern = alert_config['pattern']

            if re.search(pattern, log_line):
                await self.handle_alert(alert_type, alert_config, log_line, container)

    async def handle_alert(self, alert_type: str, config: dict,
                          log_line: str, container: str):
        """Handle detected alert based on configuration."""
        # Increment counter
        key = f"{container}:{alert_type}"
        self.alert_counters[key] += 1

        # Check threshold
        if self.alert_counters[key] >= config['threshold']:
            severity = config['severity']
            action = config['action']

            # Log to database
            await self.log_alert_to_db(alert_type, severity, container, log_line)

            # Execute action
            if action == 'trigger_auto_heal':
                await self.trigger_auto_heal(container, config.get('healing_strategy'))

            elif action == 'escalate_to_claude':
                await self.escalate_to_claude(alert_type, container,
                                             context=config.get('context', []))

            elif action == 'reduce_request_rate':
                await self.apply_rate_limiting(config['backoff_strategy'])

            elif action == 'trigger_cleanup':
                await self.trigger_cleanup(config['cleanup_targets'])

            # Reset counter after action
            self.alert_counters[key] = 0

    async def escalate_to_claude(self, alert_type: str, container: str,
                                context: list):
        """Escalate complex issue to Claude Code."""
        incident = {
            'timestamp': datetime.now(),
            'alert_type': alert_type,
            'container': container,
            'severity': 'EMERGENCY',
            'context': await self.gather_context(context, container)
        }

        # Log to incident database
        incident_id = await self.create_incident(incident)

        # Trigger Claude Code analysis
        await self.invoke_claude_code(incident_id)

        logger.critical(f"Escalated {alert_type} for {container} to Claude Code (incident #{incident_id})")

    async def gather_context(self, context_types: list, container: str) -> dict:
        """Gather contextual information for Claude Code analysis."""
        context = {}

        for ctx_type in context_types:
            if ctx_type == 'container_logs':
                context['logs'] = await self.get_container_logs(container, tail=500)

            elif ctx_type == 'resource_usage':
                context['resources'] = await self.get_resource_usage(container)

            elif ctx_type == 'recent_changes':
                context['changes'] = await self.get_recent_git_commits()

            elif ctx_type == 'full_stack_trace':
                context['stack_trace'] = await self.extract_stack_trace(container)

            elif ctx_type == 'system_state':
                context['system'] = await self.get_system_state()

        return context
```

### Pattern Matching

Uses regex patterns for flexible log analysis:

```python
ALERT_PATTERNS = {
    'data_source_failure': r'Failed to fetch (\w+):(\w+)',
    'container_restart': r'Container (\S+) restarted',
    'memory_high': r'Memory usage: (\d+)%',
    'disk_low': r'Disk space: (\d+)% free',
    'rate_limit': r'Rate limit exceeded for (\w+)',
    'db_error': r'Database connection error: (.+)',
    'fake_data': r'Fake data detected in (\w+)',
    'unknown_error': r'Unknown error: (.+)'
}
```

## Configuration

**File**: `agents/alert_watcher/config.yaml`

```yaml
alert_watcher:
  enabled: true
  scan_interval: 10  # Seconds between scans
  log_retention_days: 30

alerts:
  data_source_failure:
    pattern: 'Failed to fetch (?P<source>\w+)'
    threshold: 3
    severity: CRITICAL
    action: trigger_auto_heal
    healing_strategy: restart_container
    escalate_after: 5

  container_crash_loop:
    pattern: 'Container (?P<name>\S+) restarted'
    threshold: 5
    severity: EMERGENCY
    action: escalate_to_claude
    context:
      - container_logs
      - resource_usage
      - recent_changes

  memory_leak:
    pattern: 'Memory usage: (?P<percent>\d+)%'
    threshold: 80
    duration_seconds: 300
    severity: WARNING
    action: log_and_monitor
    escalate_after: 600

  disk_space_low:
    pattern: 'Disk space: (?P<percent>\d+)% free'
    threshold: 10
    severity: CRITICAL
    action: trigger_cleanup
    cleanup_targets:
      - old_logs
      - temp_files
      - docker_images

  api_rate_limit:
    pattern: 'Rate limit exceeded for (?P<api>\w+)'
    severity: WARNING
    action: reduce_request_rate
    backoff_strategy: exponential
    max_backoff_seconds: 300

  database_connection:
    pattern: 'Database connection error'
    threshold: 3
    severity: CRITICAL
    action: reset_connection_pool
    escalate_after: 5

  data_corruption:
    pattern: 'Fake data detected in (?P<source>\w+)'
    severity: EMERGENCY
    action: escalate_to_claude
    immediate: true
    context:
      - data_sample
      - validation_rules
      - recent_changes

  unknown_error:
    pattern: 'Unknown error: (?P<message>.+)'
    severity: WARNING
    action: escalate_to_claude
    context:
      - full_stack_trace
      - container_logs
      - system_state

escalation:
  claude_code:
    enabled: true
    incident_db: postgresql://localhost/spartan_research_db
    incident_table: monitor_incidents
    notification_channels:
      - email
      - slack

  notification_settings:
    email:
      enabled: false
      recipients: []
    slack:
      enabled: false
      webhook_url: ""
```

## Database Schema

### Alerts Table

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    container_name VARCHAR(255),
    message TEXT,
    count INTEGER DEFAULT 1,
    action_taken VARCHAR(100),
    escalated BOOLEAN DEFAULT FALSE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_escalated ON alerts(escalated);
```

### Alert History

```sql
CREATE TABLE alert_history (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id),
    timestamp TIMESTAMPTZ NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alert_history_alert_id ON alert_history(alert_id);
```

## Running the Alert Watcher

### Docker (Production)

```bash
# Start as background service
docker-compose up -d spartan-alert-watcher

# View logs
docker-compose logs -f spartan-alert-watcher

# Check status
docker ps | grep alert-watcher
```

### Standalone (Development)

```bash
# Run directly
python3 agents/alert_watcher/alert_watcher.py

# With custom config
python3 agents/alert_watcher/alert_watcher.py --config custom_alerts.yaml

# Dry run (no actions executed)
python3 agents/alert_watcher/alert_watcher.py --dry-run
```

## Monitoring

### Alert Statistics

```sql
-- Alert counts by type (last 24 hours)
SELECT alert_type, severity, COUNT(*) as count
FROM alerts
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY alert_type, severity
ORDER BY count DESC;

-- Escalation rate
SELECT
    DATE(timestamp) as date,
    COUNT(*) as total_alerts,
    SUM(CASE WHEN escalated THEN 1 ELSE 0 END) as escalated,
    ROUND(100.0 * SUM(CASE WHEN escalated THEN 1 ELSE 0 END) / COUNT(*), 2) as escalation_rate
FROM alerts
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Top containers by alerts
SELECT container_name, COUNT(*) as alerts
FROM alerts
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY container_name
ORDER BY alerts DESC;
```

### API Endpoints

```bash
# Recent alerts
curl http://localhost:8888/api/alerts/recent?limit=50

# Alert statistics
curl http://localhost:8888/api/alerts/stats

# Escalated alerts
curl http://localhost:8888/api/alerts/escalated
```

## Integration with NESTED Learning

### Outer Layer: General Alert Patterns

**Slow Updates (Weekly)**:
- Which alert types most commonly escalate
- Optimal thresholds for different containers
- Effective action sequences
- False positive patterns to ignore

### Inner Layer: Container-Specific Patterns

**Fast Updates (Per-Alert)**:
- Container-specific thresholds
- Custom action sequences
- Context requirements per container
- Escalation timing adjustments

**Example**:
```
Outer: "Data source failures usually resolve with container restart"
Inner: "spartan-web data failures often need cache clear first"
Result: Alert watcher learns to suggest cache clear before restart for spartan-web
```

## Troubleshooting

### Alert Watcher Not Detecting Issues

```bash
# Check if watcher is running
docker ps | grep alert-watcher

# Check configuration
cat agents/alert_watcher/config.yaml

# Test pattern matching
python3 -c "import re; print(re.search(r'Failed to fetch (\w+)', 'Failed to fetch SPY'))"

# View watcher logs
tail -f logs/alert_watcher.log
```

### Too Many False Positives

```bash
# Adjust thresholds in config.yaml
# Increase threshold values
# Add minimum duration requirements
# Refine regex patterns

# Example: Increase data source failure threshold from 3 to 5
sed -i 's/threshold: 3/threshold: 5/' agents/alert_watcher/config.yaml
```

### Alerts Not Escalating to Claude Code

```bash
# Check database connection
psql spartan_research_db -c "SELECT COUNT(*) FROM alerts WHERE escalated = true;"

# Check Claude Code configuration
cat .claudeconfig

# Test manual escalation
python3 -c "from agents.alert_watcher.alert_watcher import AlertWatcher; watcher = AlertWatcher(); watcher.escalate_to_claude('test_alert', 'spartan-web', [])"
```

## Related Documentation

- `init/agents/website_monitor.md` - Monitoring and healing system
- `init/agents/data_preloader.md` - Data preloading system
- `ARCHITECTURE.md` - System architecture
- `DEPLOYMENT_GUIDE.md` - Deployment process
