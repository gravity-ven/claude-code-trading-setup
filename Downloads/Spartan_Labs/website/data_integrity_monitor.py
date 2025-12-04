#!/usr/bin/env python3
"""
Autonomous Data Integrity Monitor
Continuously validates all API endpoints and auto-fixes issues
"""

import requests
import time
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/data_integrity_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

BASE_URL = "http://spartan_web:8888"

# All critical API endpoints that must return valid data
CRITICAL_ENDPOINTS = {
    '/api/market/indices': {
        'required_fields': ['data', 'source'],
        'data_checks': lambda r: len(r.get('data', [])) >= 3,
        'description': 'Market Indices (SPY, QQQ, DIA)'
    },
    '/api/market/commodities': {
        'required_fields': ['data'],
        'data_checks': lambda r: len(r.get('data', [])) >= 2,
        'description': 'Commodities (GLD, SLV)'
    },
    '/api/volatility': {
        'required_fields': ['vix'],
        'data_checks': lambda r: r.get('vix', {}).get('value') is not None,
        'description': 'VIX Volatility Index'
    },
    '/api/market/breadth': {
        'required_fields': ['advancing', 'declining'],
        'data_checks': lambda r: r.get('advancing') is not None,
        'description': 'Market Breadth'
    },
    '/api/economic/fear-greed': {
        'required_fields': ['score'],
        'data_checks': lambda r: isinstance(r.get('score'), (int, float)),
        'description': 'Fear & Greed Index'
    }
}

class DataIntegrityMonitor:
    def __init__(self):
        self.consecutive_failures = {}
        self.last_fix_attempt = {}

    def check_endpoint(self, endpoint: str, checks: Dict) -> Tuple[bool, str]:
        """Check if endpoint returns valid data"""
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)

            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"

            data = response.json()

            # Check for error in response
            if 'error' in data:
                return False, f"API Error: {data['error']}"

            # Check required fields
            for field in checks['required_fields']:
                if field not in data:
                    return False, f"Missing field: {field}"

            # Run data validation checks
            if not checks['data_checks'](data):
                return False, "Data validation failed"

            return True, "OK"

        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def auto_fix_web_server(self):
        """Restart web server to fix connection issues"""
        logger.warning("🔧 AUTO-FIX: Restarting web server...")
        try:
            subprocess.run(['docker', 'restart', 'spartan_web'],
                         capture_output=True, timeout=30)
            time.sleep(15)  # Wait for restart
            logger.info("✅ Web server restarted")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to restart web server: {e}")
            return False

    def auto_fix_database_connections(self):
        """Kill stale database connections"""
        logger.warning("🔧 AUTO-FIX: Resetting database connections...")
        try:
            subprocess.run([
                'docker', 'exec', 'spartan_postgres', 'psql',
                '-U', 'spartan_user', '-d', 'spartan_research',
                '-c', "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'spartan_research' AND pid <> pg_backend_pid();"
            ], capture_output=True, timeout=10)
            logger.info("✅ Database connections reset")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to reset database: {e}")
            return False

    def auto_fix_redis_cache(self):
        """Clear Redis cache to force fresh data"""
        logger.warning("🔧 AUTO-FIX: Clearing Redis cache...")
        try:
            subprocess.run(['docker', 'exec', 'spartan_redis', 'redis-cli', 'FLUSHDB'],
                         capture_output=True, timeout=10)
            logger.info("✅ Redis cache cleared")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear cache: {e}")
            return False

    def run_auto_fix(self, endpoint: str):
        """Run progressive auto-fix attempts"""
        current_time = time.time()

        # Don't retry too quickly
        if endpoint in self.last_fix_attempt:
            if current_time - self.last_fix_attempt[endpoint] < 120:  # 2 minutes
                return

        self.last_fix_attempt[endpoint] = current_time
        failures = self.consecutive_failures.get(endpoint, 0)

        logger.warning(f"🚨 ISSUE DETECTED: {CRITICAL_ENDPOINTS[endpoint]['description']}")
        logger.info(f"Consecutive failures: {failures}")

        if failures >= 1:
            # First attempt: Clear cache
            if self.auto_fix_redis_cache():
                time.sleep(5)

        if failures >= 2:
            # Second attempt: Reset database connections
            if self.auto_fix_database_connections():
                time.sleep(5)

        if failures >= 3:
            # Third attempt: Restart web server
            self.auto_fix_web_server()

    def monitor_loop(self):
        """Continuous monitoring loop"""
        logger.info("=" * 70)
        logger.info("AUTONOMOUS DATA INTEGRITY MONITOR - STARTED")
        logger.info("=" * 70)

        check_count = 0

        while True:
            check_count += 1
            logger.info(f"\n--- Health Check #{check_count} at {datetime.now().strftime('%H:%M:%S')} ---")

            all_healthy = True

            for endpoint, checks in CRITICAL_ENDPOINTS.items():
                is_valid, message = self.check_endpoint(endpoint, checks)

                if is_valid:
                    logger.info(f"✅ {checks['description']}: {message}")
                    self.consecutive_failures[endpoint] = 0
                else:
                    logger.error(f"❌ {checks['description']}: {message}")
                    self.consecutive_failures[endpoint] = self.consecutive_failures.get(endpoint, 0) + 1
                    all_healthy = False

                    # Auto-fix if failures persist
                    if self.consecutive_failures[endpoint] >= 1:
                        self.run_auto_fix(endpoint)

            if all_healthy:
                logger.info("🎉 ALL ENDPOINTS HEALTHY")
            else:
                logger.warning("⚠️  SOME ENDPOINTS HAVE ISSUES - AUTO-FIXING...")

            # Check every 2 minutes
            time.sleep(120)

if __name__ == "__main__":
    monitor = DataIntegrityMonitor()
    monitor.monitor_loop()
