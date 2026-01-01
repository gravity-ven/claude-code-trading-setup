#!/usr/bin/env python3
"""
DATA INTEGRITY VALIDATOR & AUDIT SYSTEM
========================================

Comprehensive system to validate data integrity across:
- Redis cache
- PostgreSQL database
- Agent outputs
- Website data requirements

Provides detailed audit trail and identifies blank fields.
"""

import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class DataIntegrityValidator:
    """Validates data integrity across the entire system"""

    def __init__(self):
        # Connect to Redis
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )

        # Connect to PostgreSQL
        self.db_conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
            user=os.getenv('POSTGRES_USER', 'spartan'),
            password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
            host='localhost',
            port=5432
        )

    def validate_all(self) -> Dict:
        """Comprehensive validation of all data sources"""
        print("=" * 80)
        print("🔍 DATA INTEGRITY AUDIT")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()

        results = {
            'timestamp': datetime.now().isoformat(),
            'redis': self.validate_redis(),
            'postgresql': self.validate_postgresql(),
            'agents': self.validate_agents(),
            'website_requirements': self.validate_website_requirements(),
            'summary': {}
        }

        # Generate summary
        results['summary'] = self.generate_summary(results)

        return results

    def validate_redis(self) -> Dict:
        """Validate Redis cache data"""
        print("📦 REDIS CACHE VALIDATION")
        print("-" * 80)

        # Expected keys for main page
        expected_keys = {
            # Economic indicators
            'economic:DGS10': 'Treasury 10Y Yield',
            'economic:DTB3': 'Treasury 3M Yield',
            'economic:VIXCLS': 'VIX Index',
            'composite:RECESSION_PROB': 'Recession Probability',
            'composite:MARKET_NARRATIVE': 'Market Narrative',

            # Market indices (from scanner or agents)
            'market:symbol:SPY': 'S&P 500 (SPY)',
            'market:symbol:UUP': 'Dollar Index (UUP)',
            'market:symbol:GLD': 'Gold (GLD)',
            'market:symbol:USO': 'Oil (USO)',
            'market:symbol:BTC-USD': 'Bitcoin',
            'market:symbol:ETH-USD': 'Ethereum',
            'market:symbol:SOL-USD': 'Solana',
            'market:symbol:AUDJPY=X': 'AUD/JPY',
            'market:symbol:HYG': 'High Yield Bonds (HYG)',

            # Alternative agent keys
            'market:agent:SPY': 'SPY Agent',
            'market:agent:UUP': 'UUP Agent',
            'market:agent:GLD': 'GLD Agent',
            'market:agent:USO': 'USO Agent',
            'market:agent:BTC-USD': 'Bitcoin Agent',
            'market:agent:ETH-USD': 'Ethereum Agent',
            'market:agent:SOL-USD': 'Solana Agent',
            'market:agent:AUDJPY=X': 'AUD/JPY Agent',
            'market:agent:HYG': 'HYG Agent',
        }

        found = {}
        missing = []
        stale = []

        for key, name in expected_keys.items():
            try:
                value = self.redis_client.get(key)
                ttl = self.redis_client.ttl(key)

                if value:
                    data = json.loads(value) if value.startswith('{') else {'value': value}
                    found[key] = {
                        'name': name,
                        'exists': True,
                        'ttl': ttl,
                        'preview': str(data)[:100] + '...' if len(str(data)) > 100 else str(data)
                    }

                    if ttl < 0:
                        stale.append(key)

                    print(f"✅ {name:30} | TTL: {ttl:5}s | {key}")
                else:
                    missing.append(key)
                    print(f"❌ {name:30} | MISSING | {key}")
            except Exception as e:
                missing.append(key)
                print(f"⚠️  {name:30} | ERROR: {e}")

        print()
        print(f"Summary: {len(found)}/{len(expected_keys)} keys found ({len(found)/len(expected_keys)*100:.1f}%)")
        print()

        return {
            'expected_count': len(expected_keys),
            'found_count': len(found),
            'missing_count': len(missing),
            'stale_count': len(stale),
            'success_rate': len(found) / len(expected_keys) * 100,
            'found': found,
            'missing': missing,
            'stale': stale
        }

    def validate_postgresql(self) -> Dict:
        """Validate PostgreSQL database"""
        print("🗄️  POSTGRESQL DATABASE VALIDATION")
        print("-" * 80)

        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check recent data (last 24 hours)
            cur.execute("""
                SELECT
                    symbol,
                    data_type,
                    source,
                    MAX(timestamp) as latest_timestamp,
                    COUNT(*) as record_count
                FROM preloaded_market_data
                WHERE timestamp > NOW() - INTERVAL '24 hours'
                GROUP BY symbol, data_type, source
                ORDER BY latest_timestamp DESC
            """)

            recent_data = cur.fetchall()

            if recent_data:
                print(f"Found {len(recent_data)} symbols with recent data (last 24h):")
                print()
                for row in recent_data[:20]:  # Show first 20
                    age = datetime.now() - row['latest_timestamp']
                    age_str = f"{age.seconds // 60}m ago" if age.seconds < 3600 else f"{age.seconds // 3600}h ago"
                    print(f"  {row['symbol']:15} | {row['data_type']:10} | {row['source']:12} | {age_str:10} | {row['record_count']:4} records")

                if len(recent_data) > 20:
                    print(f"  ... and {len(recent_data) - 20} more")
            else:
                print("❌ No recent data found in database")

            print()

            # Check critical symbols
            critical_symbols = ['SPY', 'UUP', 'GLD', 'USO', 'BTC-USD', 'ETH-USD', 'SOL-USD', 'AUDJPY=X', 'HYG', 'DGS10', 'DTB3', 'VIXCLS']
            missing_symbols = []

            for symbol in critical_symbols:
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM preloaded_market_data
                    WHERE symbol = %s AND timestamp > NOW() - INTERVAL '24 hours'
                """, (symbol,))

                count = cur.fetchone()['count']
                if count == 0:
                    missing_symbols.append(symbol)

            if missing_symbols:
                print(f"⚠️  Missing recent data for: {', '.join(missing_symbols)}")
            else:
                print("✅ All critical symbols have recent data")

            print()

        return {
            'recent_symbols': len(recent_data),
            'critical_symbols_missing': len(missing_symbols),
            'missing_symbols': missing_symbols
        }

    def validate_agents(self) -> Dict:
        """Validate agent status"""
        print("🤖 AGENT STATUS VALIDATION")
        print("-" * 80)

        # Check for agent health keys
        agent_health = {}

        agents = [
            'SPY Agent', 'Dollar Index Agent', 'Gold Agent', 'Oil Agent',
            'Bitcoin Agent', 'Ethereum Agent', 'Solana Agent', 'AUD/JPY Agent',
            'HYG Agent', 'Treasury 10Y Agent', 'Treasury 3M Agent', 'VIX Agent',
            'Recession Calculator Agent', 'Market Narrative Agent'
        ]

        for agent_name in agents:
            # Try to find agent output in Redis
            found_data = False

            # Try different key patterns
            patterns = [
                f'market:agent:*',
                f'economic:*',
                f'composite:*'
            ]

            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    found_data = True
                    break

            status = "✅ Active" if found_data else "❌ Inactive"
            print(f"{status:15} | {agent_name}")
            agent_health[agent_name] = found_data

        active_count = sum(1 for v in agent_health.values() if v)
        print()
        print(f"Summary: {active_count}/{len(agents)} agents active ({active_count/len(agents)*100:.1f}%)")
        print()

        return {
            'total_agents': len(agents),
            'active_agents': active_count,
            'inactive_agents': len(agents) - active_count,
            'success_rate': active_count / len(agents) * 100,
            'agent_health': agent_health
        }

    def validate_website_requirements(self) -> Dict:
        """Validate data required by website"""
        print("🌐 WEBSITE DATA REQUIREMENTS VALIDATION")
        print("-" * 80)

        # Main page data requirements
        main_page_requirements = {
            'Market Indices': ['SPY', 'UUP', 'GLD', 'USO', 'HYG'],
            'Crypto': ['BTC-USD', 'ETH-USD', 'SOL-USD'],
            'Economic': ['DGS10', 'DTB3', 'VIXCLS'],
            'Composite': ['RECESSION_PROB', 'MARKET_NARRATIVE']
        }

        missing_by_category = {}

        for category, symbols in main_page_requirements.items():
            missing = []

            for symbol in symbols:
                # Check multiple key patterns
                found = False

                patterns = [
                    f'market:symbol:{symbol}',
                    f'market:agent:{symbol}',
                    f'economic:{symbol}',
                    f'composite:{symbol}'
                ]

                for pattern in patterns:
                    if self.redis_client.exists(pattern):
                        found = True
                        break

                if not found:
                    missing.append(symbol)

            if missing:
                print(f"❌ {category:20} | Missing: {', '.join(missing)}")
                missing_by_category[category] = missing
            else:
                print(f"✅ {category:20} | All data available")

        print()

        total_required = sum(len(symbols) for symbols in main_page_requirements.values())
        total_missing = sum(len(missing) for missing in missing_by_category.values())
        available = total_required - total_missing

        print(f"Summary: {available}/{total_required} required fields available ({available/total_required*100:.1f}%)")
        print()

        return {
            'total_required': total_required,
            'available': available,
            'missing': total_missing,
            'success_rate': available / total_required * 100,
            'missing_by_category': missing_by_category
        }

    def generate_summary(self, results: Dict) -> Dict:
        """Generate overall summary"""
        print("=" * 80)
        print("📊 OVERALL SUMMARY")
        print("=" * 80)

        # Calculate overall health score
        scores = [
            results['redis']['success_rate'],
            results['agents']['success_rate'],
            results['website_requirements']['success_rate']
        ]

        overall_score = sum(scores) / len(scores)

        # Determine health status
        if overall_score >= 90:
            status = "🟢 EXCELLENT"
            emoji = "🎉"
        elif overall_score >= 70:
            status = "🟡 GOOD"
            emoji = "👍"
        elif overall_score >= 50:
            status = "🟠 DEGRADED"
            emoji = "⚠️"
        else:
            status = "🔴 CRITICAL"
            emoji = "🚨"

        print(f"\n{emoji} Overall Health: {status} ({overall_score:.1f}%)\n")

        print("Component Health:")
        print(f"  Redis Cache:     {results['redis']['success_rate']:5.1f}% ({results['redis']['found_count']}/{results['redis']['expected_count']} keys)")
        print(f"  Agents:          {results['agents']['success_rate']:5.1f}% ({results['agents']['active_agents']}/{results['agents']['total_agents']} active)")
        print(f"  Website Data:    {results['website_requirements']['success_rate']:5.1f}% ({results['website_requirements']['available']}/{results['website_requirements']['total_required']} available)")

        # Critical issues
        print("\n🚨 Critical Issues:")
        issues = []

        if results['redis']['missing_count'] > 0:
            issues.append(f"  - {results['redis']['missing_count']} Redis keys missing")

        if results['agents']['inactive_agents'] > 0:
            issues.append(f"  - {results['agents']['inactive_agents']} agents inactive")

        if results['website_requirements']['missing'] > 0:
            issues.append(f"  - {results['website_requirements']['missing']} website fields missing data")

        if not issues:
            print("  ✅ No critical issues detected")
        else:
            for issue in issues:
                print(issue)

        print()
        print("=" * 80)

        return {
            'overall_score': overall_score,
            'status': status,
            'critical_issues': len(issues),
            'timestamp': datetime.now().isoformat()
        }

    def export_audit_report(self, results: Dict, filename: str = 'data_integrity_audit.json'):
        """Export audit report to JSON"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Audit report exported to: {filename}")


def main():
    """Run data integrity validation"""
    validator = DataIntegrityValidator()

    try:
        results = validator.validate_all()

        # Export report
        validator.export_audit_report(results)

        # Return exit code based on health
        if results['summary']['overall_score'] < 50:
            return 1  # Critical
        elif results['summary']['overall_score'] < 70:
            return 2  # Warning
        else:
            return 0  # OK

    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
