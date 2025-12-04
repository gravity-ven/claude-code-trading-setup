#!/usr/bin/env python3
"""
Claude Code Autonomous Monitoring Bridge
Provides real-time status monitoring that Claude Code can query and act upon
Automatically detects issues and provides fix recommendations
"""

import os
import sys
import asyncio
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Optional
from pathlib import Path
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/spartan_research_db')
if 'spartan-postgres' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('spartan-postgres', 'localhost')

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))


class ClaudeCodeBridge:
    """Autonomous monitoring bridge between Spartan system and Claude Code"""

    def __init__(self):
        self.db_conn = None
        self.redis_client = None
        self.status_file = Path('logs/claude_bridge_status.json')
        self.status_file.parent.mkdir(exist_ok=True)

    def connect_infrastructure(self) -> Dict[str, bool]:
        """Connect to PostgreSQL and Redis"""
        status = {
            'postgres': False,
            'redis': False
        }

        # Connect to PostgreSQL
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            status['postgres'] = True
            logger.info("✅ PostgreSQL connected")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")

        # Connect to Redis
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
            self.redis_client.ping()
            status['redis'] = True
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")

        return status

    async def check_service_health(self, port: int, path: str = '/health') -> Dict:
        """Check if a service is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://localhost:{port}{path}', timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'healthy': True,
                            'status_code': 200,
                            'response': data
                        }
                    else:
                        return {
                            'healthy': False,
                            'status_code': response.status,
                            'error': f'HTTP {response.status}'
                        }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }

    async def check_all_services(self) -> Dict[str, Dict]:
        """Check health of all microservices"""
        services = {
            'main_server': {'port': 8888, 'path': '/health'},
            'correlation_api': {'port': 5004, 'path': '/health'},
            'daily_planet_api': {'port': 5000, 'path': '/health'},
            'swing_api': {'port': 5002, 'path': '/api/swing-dashboard/health'},
            'garp_api': {'port': 5003, 'path': '/api/health'},
        }

        results = {}
        for service_name, config in services.items():
            results[service_name] = await self.check_service_health(
                config['port'],
                config['path']
            )

        return results

    def check_data_freshness(self) -> Dict:
        """Check if data is fresh (< 20 minutes old)"""
        try:
            if not self.db_conn:
                return {'status': 'error', 'message': 'Database not connected'}

            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

            # Check last data update
            cursor.execute("""
                SELECT
                    COUNT(*) as total_entries,
                    MAX(timestamp) as last_update,
                    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX(timestamp))) / 60 as minutes_ago
                FROM preloaded_market_data
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """)

            result = cursor.fetchone()

            if result and result['total_entries'] > 0:
                minutes_ago = result['minutes_ago']
                is_fresh = minutes_ago < 20

                return {
                    'status': 'fresh' if is_fresh else 'stale',
                    'total_entries': result['total_entries'],
                    'last_update': str(result['last_update']),
                    'minutes_ago': round(minutes_ago, 1),
                    'threshold_minutes': 20,
                    'recommendation': 'Data is current' if is_fresh else 'Run data refresh'
                }
            else:
                return {
                    'status': 'empty',
                    'message': 'No recent data found',
                    'recommendation': 'Run data preloader: python src/data_preloader.py'
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def check_redis_cache(self) -> Dict:
        """Check Redis cache status"""
        try:
            if not self.redis_client:
                return {'status': 'error', 'message': 'Redis not connected'}

            # Get cache statistics
            info = self.redis_client.info('stats')
            keyspace = self.redis_client.info('keyspace')

            total_keys = 0
            if 'db0' in keyspace:
                total_keys = keyspace['db0']['keys']

            # Sample some market keys
            sample_keys = self.redis_client.keys('market:*')[:5]
            sample_data = []

            for key in sample_keys:
                ttl = self.redis_client.ttl(key)
                sample_data.append({
                    'key': key,
                    'ttl_seconds': ttl,
                    'ttl_minutes': round(ttl / 60, 1) if ttl > 0 else 0
                })

            return {
                'status': 'healthy',
                'total_keys': total_keys,
                'total_commands': info.get('total_commands_processed', 0),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': round(info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100, 2),
                'sample_keys': sample_data
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def check_disk_space(self) -> Dict:
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')

            free_gb = free // (2**30)
            total_gb = total // (2**30)
            used_percent = (used / total) * 100

            status = 'healthy'
            if free_gb < 1:
                status = 'critical'
            elif free_gb < 5:
                status = 'warning'

            return {
                'status': status,
                'free_gb': free_gb,
                'total_gb': total_gb,
                'used_percent': round(used_percent, 1),
                'recommendation': 'Free up disk space' if status != 'healthy' else 'Disk space OK'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_running_processes(self) -> List[Dict]:
        """Get list of running Spartan processes"""
        processes = []

        try:
            # Read PID files
            pids_dir = Path('.pids')
            if pids_dir.exists():
                for pid_file in pids_dir.glob('*.pid'):
                    with open(pid_file) as f:
                        pid = int(f.read().strip())

                    # Check if process is actually running
                    try:
                        subprocess.run(['ps', '-p', str(pid)], check=True, capture_output=True)
                        is_running = True
                    except subprocess.CalledProcessError:
                        is_running = False

                    processes.append({
                        'name': pid_file.stem,
                        'pid': pid,
                        'running': is_running
                    })

        except Exception as e:
            logger.error(f"Error checking processes: {e}")

        return processes

    def check_log_errors(self) -> Dict:
        """Check recent log files for errors"""
        try:
            logs_dir = Path('logs')
            if not logs_dir.exists():
                return {'status': 'no_logs', 'message': 'Logs directory not found'}

            errors = []
            warnings = []

            for log_file in logs_dir.glob('*.log'):
                try:
                    with open(log_file) as f:
                        lines = f.readlines()[-100:]  # Last 100 lines

                    for line in lines:
                        if 'ERROR' in line or 'CRITICAL' in line:
                            errors.append({
                                'file': log_file.name,
                                'line': line.strip()
                            })
                        elif 'WARNING' in line:
                            warnings.append({
                                'file': log_file.name,
                                'line': line.strip()
                            })

                except Exception as e:
                    logger.error(f"Error reading {log_file}: {e}")

            return {
                'status': 'errors_found' if errors else 'clean',
                'error_count': len(errors),
                'warning_count': len(warnings),
                'recent_errors': errors[-5:],  # Last 5 errors
                'recent_warnings': warnings[-5:]  # Last 5 warnings
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    async def generate_full_report(self) -> Dict:
        """Generate comprehensive system status report"""
        logger.info("🔍 Generating system status report...")

        report = {
            'timestamp': datetime.now().isoformat(),
            'infrastructure': self.connect_infrastructure(),
            'services': await self.check_all_services(),
            'data_freshness': self.check_data_freshness(),
            'redis_cache': self.check_redis_cache(),
            'disk_space': self.check_disk_space(),
            'processes': self.get_running_processes(),
            'logs': self.check_log_errors()
        }

        # Calculate overall health score
        health_score = 100

        # Deduct points for issues
        if not report['infrastructure']['postgres']:
            health_score -= 30
        if not report['infrastructure']['redis']:
            health_score -= 20

        unhealthy_services = sum(1 for s in report['services'].values() if not s.get('healthy', False))
        health_score -= unhealthy_services * 10

        if report['data_freshness']['status'] == 'stale':
            health_score -= 15
        elif report['data_freshness']['status'] == 'empty':
            health_score -= 30

        if report['disk_space']['status'] == 'warning':
            health_score -= 10
        elif report['disk_space']['status'] == 'critical':
            health_score -= 25

        health_score = max(0, health_score)

        report['overall_health'] = {
            'score': health_score,
            'status': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 50 else 'critical',
            'summary': self.generate_summary(report)
        }

        # Save report to file for Claude Code to read
        with open(self.status_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"✅ Report saved to {self.status_file}")

        return report

    def generate_summary(self, report: Dict) -> str:
        """Generate human-readable summary"""
        lines = []

        # Infrastructure
        if not report['infrastructure']['postgres']:
            lines.append("❌ PostgreSQL is down - restart with: sudo service postgresql start")
        if not report['infrastructure']['redis']:
            lines.append("❌ Redis is down - restart with: sudo service redis-server start")

        # Services
        for service, status in report['services'].items():
            if not status.get('healthy', False):
                lines.append(f"❌ {service} is not responding - check logs/{{service}}.log")

        # Data
        if report['data_freshness']['status'] == 'empty':
            lines.append("❌ No market data - run: python src/data_preloader.py")
        elif report['data_freshness']['status'] == 'stale':
            lines.append(f"⚠️  Data is {report['data_freshness']['minutes_ago']} minutes old - run refresh")

        # Disk
        if report['disk_space']['status'] in ['warning', 'critical']:
            lines.append(f"⚠️  Low disk space: {report['disk_space']['free_gb']} GB free")

        if not lines:
            lines.append("✅ All systems operational")

        return '\n'.join(lines)

    def print_report(self, report: Dict):
        """Print formatted report to console"""
        print("\n" + "=" * 70)
        print(" SPARTAN RESEARCH STATION - AUTONOMOUS STATUS REPORT")
        print("=" * 70)
        print(f"\nTimestamp: {report['timestamp']}")
        print(f"Overall Health: {report['overall_health']['score']}/100 ({report['overall_health']['status'].upper()})")
        print("\n" + "-" * 70)
        print("SUMMARY:")
        print("-" * 70)
        print(report['overall_health']['summary'])
        print("\n" + "=" * 70)


async def main():
    """Main entry point"""
    bridge = ClaudeCodeBridge()
    report = await bridge.generate_full_report()
    bridge.print_report(report)

    # Close connections
    if bridge.db_conn:
        bridge.db_conn.close()
    if bridge.redis_client:
        bridge.redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())
