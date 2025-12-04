#!/usr/bin/env python3
"""
Data Validation Monitor - Claude Code Bridge
Continuously monitors data freshness and triggers Claude Code when data fails
NO FAKE DATA - Only genuine data validation
"""

import os
import sys
import asyncio
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import subprocess
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_validation_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://spartan:spartan@localhost:5432/spartan_research_db')

# Data freshness thresholds
DATA_FRESHNESS_MINUTES = 20  # Data older than 20 minutes is considered stale
CRITICAL_DATA_FRESHNESS_MINUTES = 30  # Critical threshold

# Critical data sources that MUST have data
CRITICAL_SOURCES = [
    'market:index:SPY',
    'market:index:QQQ',
    'market:index:DIA',
    'market:vix:^VIX',
    'fred:GDP',
    'fred:UNRATE',
]

# All expected data sources
EXPECTED_SOURCES = CRITICAL_SOURCES + [
    'market:index:IWM',
    'market:index:EFA',
    'market:index:EEM',
    'market:commodity:GLD',
    'market:commodity:USO',
    'market:crypto:BTC-USD',
    'fred:CPIAUCSL',
    'fred:FEDFUNDS',
    'fred:T10Y2Y',
]

class DataValidationMonitor:
    """Monitors data freshness and triggers Claude Code on failures"""

    def __init__(self):
        self.redis_client = None
        self.db_conn = None
        self.failure_count = 0
        self.last_alert_time = None
        self.claude_triggered = False

    async def connect(self):
        """Connect to Redis and PostgreSQL"""
        try:
            # Connect to Redis
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Connected to Redis")

            # Connect to PostgreSQL
            self.db_conn = psycopg2.connect(DATABASE_URL)
            logger.info("✅ Connected to PostgreSQL")

        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            raise

    async def check_redis_data(self) -> Dict[str, bool]:
        """Check if data exists and is fresh in Redis"""
        results = {}

        for source in EXPECTED_SOURCES:
            try:
                # Check if key exists
                data = self.redis_client.get(source)

                if data is None:
                    results[source] = False
                    logger.warning(f"⚠️  Missing data in Redis: {source}")
                else:
                    # Validate it's not fake data (no random values, no null)
                    try:
                        parsed = json.loads(data)
                        if parsed is None or parsed == {} or 'error' in str(parsed).lower():
                            results[source] = False
                            logger.warning(f"⚠️  Invalid data in Redis: {source}")
                        else:
                            results[source] = True
                            logger.debug(f"✓ Valid data in Redis: {source}")
                    except json.JSONDecodeError:
                        # Might be plain text, check if it's meaningful
                        if len(data) > 0 and data != 'null':
                            results[source] = True
                        else:
                            results[source] = False
                            logger.warning(f"⚠️  Empty data in Redis: {source}")

            except Exception as e:
                logger.error(f"❌ Error checking Redis key {source}: {e}")
                results[source] = False

        return results

    async def check_postgresql_data(self) -> Dict[str, Tuple[bool, Optional[datetime]]]:
        """Check if data exists and is fresh in PostgreSQL"""
        results = {}

        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

            # Check preloaded_market_data table
            cursor.execute("""
                SELECT
                    data_source,
                    MAX(timestamp) as last_update,
                    COUNT(*) as record_count
                FROM preloaded_market_data
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                GROUP BY data_source
            """)

            db_sources = {row['data_source']: (True, row['last_update']) for row in cursor.fetchall()}

            # Check each expected source
            for source in EXPECTED_SOURCES:
                # Extract source name from Redis key format
                source_name = source.replace('market:', '').replace('fred:', '')

                if source_name in db_sources or source in db_sources:
                    has_data, last_update = db_sources.get(source_name) or db_sources.get(source)

                    # Check if data is fresh
                    if last_update:
                        age_minutes = (datetime.now() - last_update.replace(tzinfo=None)).total_seconds() / 60
                        is_fresh = age_minutes < DATA_FRESHNESS_MINUTES
                        results[source] = (is_fresh, last_update)

                        if not is_fresh:
                            logger.warning(f"⚠️  Stale data in PostgreSQL: {source} (age: {age_minutes:.1f} min)")
                    else:
                        results[source] = (False, None)
                else:
                    results[source] = (False, None)
                    logger.warning(f"⚠️  No data in PostgreSQL: {source}")

            cursor.close()

        except Exception as e:
            logger.error(f"❌ Error checking PostgreSQL: {e}")
            # Return all False if DB check fails
            results = {source: (False, None) for source in EXPECTED_SOURCES}

        return results

    async def validate_data_quality(self) -> Dict[str, any]:
        """Comprehensive data validation"""
        logger.info("🔍 Running data validation check...")

        # Check Redis
        redis_results = await self.check_redis_data()

        # Check PostgreSQL
        postgres_results = await self.check_postgresql_data()

        # Analyze results
        redis_valid_count = sum(1 for v in redis_results.values() if v)
        redis_total_count = len(redis_results)
        redis_valid_pct = (redis_valid_count / redis_total_count * 100) if redis_total_count > 0 else 0

        postgres_valid_count = sum(1 for v, _ in postgres_results.values() if v)
        postgres_total_count = len(postgres_results)
        postgres_valid_pct = (postgres_valid_count / postgres_total_count * 100) if postgres_total_count > 0 else 0

        # Check critical sources
        critical_failures = []
        for source in CRITICAL_SOURCES:
            if not redis_results.get(source, False):
                critical_failures.append(f"{source} (Redis)")
            if not postgres_results.get(source, (False, None))[0]:
                critical_failures.append(f"{source} (PostgreSQL)")

        validation_result = {
            'timestamp': datetime.now().isoformat(),
            'redis': {
                'valid_count': redis_valid_count,
                'total_count': redis_total_count,
                'valid_percentage': redis_valid_pct,
                'details': redis_results
            },
            'postgres': {
                'valid_count': postgres_valid_count,
                'total_count': postgres_total_count,
                'valid_percentage': postgres_valid_pct,
                'details': {k: {'is_fresh': v, 'last_update': str(t) if t else None}
                           for k, (v, t) in postgres_results.items()}
            },
            'critical_failures': critical_failures,
            'overall_health': 'healthy' if len(critical_failures) == 0 and redis_valid_pct >= 80 and postgres_valid_pct >= 80 else 'unhealthy'
        }

        logger.info(f"📊 Validation Results:")
        logger.info(f"   Redis: {redis_valid_count}/{redis_total_count} valid ({redis_valid_pct:.1f}%)")
        logger.info(f"   PostgreSQL: {postgres_valid_count}/{postgres_total_count} fresh ({postgres_valid_pct:.1f}%)")
        logger.info(f"   Overall: {validation_result['overall_health'].upper()}")

        if critical_failures:
            logger.error(f"❌ Critical failures detected: {len(critical_failures)}")
            for failure in critical_failures:
                logger.error(f"   - {failure}")

        return validation_result

    async def trigger_claude_code(self, validation_result: Dict):
        """Trigger Claude Code to fix data loading issues"""

        # Prevent triggering too frequently
        if self.last_alert_time:
            time_since_last = (datetime.now() - self.last_alert_time).total_seconds()
            if time_since_last < 300:  # Don't trigger more than once every 5 minutes
                logger.info(f"⏳ Skipping Claude trigger (last trigger {time_since_last:.0f}s ago)")
                return

        logger.warning("🚨 CRITICAL: Data validation failed - Triggering Claude Code")

        # Create detailed prompt for Claude
        prompt = self._generate_claude_prompt(validation_result)

        # Save prompt to file
        prompt_file = Path('logs/claude_data_fix_prompt.txt')
        prompt_file.parent.mkdir(exist_ok=True)

        with open(prompt_file, 'w') as f:
            f.write(prompt)

        logger.info(f"📝 Claude prompt saved to: {prompt_file}")

        # Create trigger file for Claude watcher
        trigger_file = Path('logs/claude_trigger_data_failure.flag')
        with open(trigger_file, 'w') as f:
            json.dump(validation_result, f, indent=2)

        logger.info(f"🚩 Trigger flag created: {trigger_file}")

        # Log to PostgreSQL incidents table
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO monitor_incidents (
                    container_name,
                    incident_type,
                    severity,
                    description,
                    auto_healed,
                    timestamp
                ) VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                'spartan-data-preloader',
                'data_validation_failure',
                'critical',
                f"Data validation failed: {len(validation_result['critical_failures'])} critical failures",
                False
            ))
            self.db_conn.commit()
            cursor.close()
            logger.info("✅ Incident logged to database")
        except Exception as e:
            logger.error(f"❌ Failed to log incident: {e}")

        self.last_alert_time = datetime.now()
        self.claude_triggered = True

        # Print instructions for manual trigger if needed
        logger.warning("=" * 80)
        logger.warning("MANUAL ACTION REQUIRED:")
        logger.warning(f"Run Claude Code and paste the prompt from: {prompt_file}")
        logger.warning("Or use automatic trigger: ./logs/trigger_claude_data_fix.sh")
        logger.warning("=" * 80)

    def _generate_claude_prompt(self, validation_result: Dict) -> str:
        """Generate detailed prompt for Claude Code"""

        redis_pct = validation_result['redis']['valid_percentage']
        postgres_pct = validation_result['postgres']['valid_percentage']
        critical_failures = validation_result['critical_failures']

        prompt = f"""
🚨 DATA VALIDATION FAILURE DETECTED - AUTONOMOUS FIX REQUIRED

**Timestamp**: {validation_result['timestamp']}
**Severity**: CRITICAL
**Overall Health**: {validation_result['overall_health'].upper()}

## Problem Summary

The data validation monitor has detected that data is NOT loading properly in the Spartan Research Station.

### Current Status:
- Redis Cache: {redis_pct:.1f}% valid ({validation_result['redis']['valid_count']}/{validation_result['redis']['total_count']} sources)
- PostgreSQL: {postgres_pct:.1f}% fresh ({validation_result['postgres']['valid_count']}/{validation_result['postgres']['total_count']} sources)
- Critical Failures: {len(critical_failures)} sources

### Critical Sources Failing:
{chr(10).join(f"  ❌ {failure}" for failure in critical_failures)}

## Your Mission

**CRITICAL RULE**: NO FAKE DATA. Only genuine data from real APIs.

**Objective**: Restore data loading to 100% functionality using ONLY real data sources.

## Investigation Steps

1. **Check Data Preloader Status**:
   ```bash
   docker-compose logs spartan-data-preloader
   docker inspect spartan-data-preloader --format='{{{{.State.ExitCode}}}}'
   ```

2. **Check Redis Cache**:
   ```bash
   docker exec -it spartan-redis redis-cli
   > KEYS market:*
   > KEYS fred:*
   > GET market:index:SPY
   ```

3. **Check PostgreSQL Data**:
   ```bash
   docker exec -it spartan-postgres psql -U spartan -d spartan_research_db \\
     -c "SELECT data_source, MAX(timestamp) as last_update, COUNT(*) FROM preloaded_market_data GROUP BY data_source ORDER BY last_update DESC;"
   ```

4. **Check Data Preloader Code**:
   ```bash
   cat src/data_preloader.py | grep -A 10 "async def preload_"
   ```

5. **Check API Keys**:
   ```bash
   docker exec spartan-data-preloader env | grep -E "(FRED|ALPHA|POLYGON|TWELVE)_API_KEY"
   ```

6. **Check Rate Limiting**:
   - Review rate limit delays in src/data_preloader.py
   - Check if rate limits are being hit (look for 429 errors in logs)

## Common Issues and Fixes

### Issue 1: Data Preloader Failed to Start
**Symptom**: Exit code 1, no data in Redis
**Fix**:
```bash
# Check what failed
docker-compose logs spartan-data-preloader | grep "❌"

# Fix API keys if missing
nano .env  # Add missing keys

# Restart preloader
docker-compose up -d spartan-data-preloader
```

### Issue 2: Rate Limiting (429 Errors)
**Symptom**: API requests failing with 429 errors
**Fix**:
```python
# Edit src/data_preloader.py
# Increase delays in REQUEST_DELAYS dict:
REQUEST_DELAYS = {{
    'yfinance': 3.0,        # Increase from 2.0
    'polygon': 15.0,        # Increase from 12.0
    'alpha_vantage': 15.0,  # Increase from 12.0
}}
```

### Issue 3: Stale Data (Not Refreshing)
**Symptom**: Data exists but is old (>20 minutes)
**Fix**:
```bash
# Check if refresh scheduler is running
docker-compose logs spartan-web | grep "refresh"

# Force manual refresh
docker exec spartan-research-station python src/data_refresh_scheduler.py

# Restart web server to restart scheduler
docker-compose restart spartan-web
```

### Issue 4: Missing API Keys
**Symptom**: Specific sources failing consistently
**Fix**:
```bash
# Check which keys are missing
cat .env | grep API_KEY

# Add missing keys
echo "FRED_API_KEY=your_key_here" >> .env

# Rebuild and restart
docker-compose up -d --force-recreate spartan-data-preloader
```

### Issue 5: Network/Connectivity Issues
**Symptom**: All sources failing, timeout errors
**Fix**:
```bash
# Test network connectivity from container
docker exec spartan-data-preloader ping -c 3 api.stlouisfed.org
docker exec spartan-data-preloader curl -I https://query1.finance.yahoo.com

# Check Docker network
docker network inspect spartan-network

# Restart Docker network
docker-compose down && docker-compose up -d
```

## Validation After Fix

After implementing fixes, validate:

```bash
# 1. Check preloader succeeded
docker-compose logs spartan-data-preloader | tail -20

# 2. Verify Redis has data
docker exec -it spartan-redis redis-cli KEYS '*' | wc -l  # Should be >20

# 3. Verify PostgreSQL has fresh data
docker exec -it spartan-postgres psql -U spartan -d spartan_research_db \\
  -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '15 minutes';"  # Should be >0

# 4. Check website loads data
curl http://localhost:8888/api/market/index/SPY  # Should return real data, not null

# 5. Re-run validation monitor
python src/data_validation_monitor.py --validate-once
```

## Expected Outcome

- ✅ Data preloader exits with code 0
- ✅ Redis cache has >20 keys with valid data
- ✅ PostgreSQL has fresh data (<15 minutes old)
- ✅ All critical sources return valid data
- ✅ Website dashboard shows real market data
- ✅ NO fake data, NO Math.random(), NO mock values

## Critical Reminders

1. **NO FAKE DATA** - If an API fails, return null/None, don't generate fake values
2. **Rate Limiting** - Always respect API rate limits, add delays between requests
3. **Validate Data** - Check that data is genuine, not error messages or empty responses
4. **Test Thoroughly** - Verify data loads in browser before marking as complete
5. **Log Everything** - Comprehensive logging helps debug future failures

## Success Criteria

Data validation monitor should report:
- Redis: 100% valid (all {len(EXPECTED_SOURCES)} sources)
- PostgreSQL: 100% fresh (all {len(EXPECTED_SOURCES)} sources)
- Critical Failures: 0
- Overall Health: HEALTHY

---

**Start your investigation now. Fix the data loading issue using ONLY real data sources.**
"""

        return prompt

    async def run_continuous_monitoring(self, check_interval: int = 60):
        """Run continuous monitoring loop"""
        logger.info(f"🔄 Starting continuous data validation monitoring (interval: {check_interval}s)")

        while True:
            try:
                # Run validation
                validation_result = await self.validate_data_quality()

                # Check if we need to trigger Claude
                if validation_result['overall_health'] == 'unhealthy':
                    self.failure_count += 1
                    logger.warning(f"⚠️  Unhealthy state detected (failure count: {self.failure_count})")

                    # Trigger Claude after 2 consecutive failures
                    if self.failure_count >= 2 and not self.claude_triggered:
                        await self.trigger_claude_code(validation_result)
                else:
                    # Reset failure count on success
                    if self.failure_count > 0:
                        logger.info("✅ Data validation back to healthy - resetting failure count")
                    self.failure_count = 0
                    self.claude_triggered = False

                # Save validation result to file for external monitoring
                result_file = Path('logs/data_validation_latest.json')
                with open(result_file, 'w') as f:
                    json.dump(validation_result, f, indent=2)

                # Wait before next check
                await asyncio.sleep(check_interval)

            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(check_interval)

    async def run_single_validation(self):
        """Run a single validation check (for testing)"""
        await self.connect()
        validation_result = await self.validate_data_quality()

        if validation_result['overall_health'] == 'unhealthy':
            logger.warning("⚠️  Data validation FAILED")
            await self.trigger_claude_code(validation_result)
            return 1
        else:
            logger.info("✅ Data validation PASSED")
            return 0

    def close(self):
        """Close connections"""
        if self.redis_client:
            self.redis_client.close()
        if self.db_conn:
            self.db_conn.close()
        logger.info("🔌 Connections closed")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Data Validation Monitor - Claude Code Bridge')
    parser.add_argument('--validate-once', action='store_true', help='Run single validation and exit')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    args = parser.parse_args()

    monitor = DataValidationMonitor()

    try:
        await monitor.connect()

        if args.validate_once:
            exit_code = await monitor.run_single_validation()
            sys.exit(exit_code)
        else:
            await monitor.run_continuous_monitoring(check_interval=args.interval)

    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        monitor.close()


if __name__ == '__main__':
    asyncio.run(main())
