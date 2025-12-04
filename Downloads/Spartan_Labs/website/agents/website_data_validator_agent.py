#!/usr/bin/env python3
"""
AUTONOMOUS WEBSITE DATA VALIDATOR AGENT
=======================================

Continuously monitors what data the website needs vs what's in Redis.
Automatically creates aliases and logs missing data.

Purpose: Ensure user never has to manually report missing fields.
"""

import asyncio
import redis
import json
import re
from datetime import datetime
from typing import Dict, List, Set, Optional
from pathlib import Path


class WebsiteDataValidator:
    """
    Autonomous agent that ensures website data requirements are met.

    Actions:
    1. Scans index.html to find required symbols
    2. Checks Redis for available data
    3. Creates aliases for mismatched keys
    4. Logs missing/present data
    5. Sends alerts for critical missing data
    """

    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.html_path = Path(__file__).parent.parent / 'index.html'
        self.log_path = Path(__file__).parent.parent / 'website_data_validation.log'
        self.check_interval = 300  # 5 minutes

        # Known symbol mappings (HTML symbol -> Redis key)
        self.symbol_mappings = {
            '^TNX': 'economic:DGS10',      # 10Y Treasury: HTML wants ^TNX, Redis has DGS10
            '^IRX': 'economic:DTB3',       # 3M Treasury: HTML wants ^IRX, Redis has DTB3
            '^VIX': 'economic:VIXCLS',     # VIX: HTML wants ^VIX, Redis has VIXCLS
        }

    def log(self, message: str):
        """Log with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)

        with open(self.log_path, 'a') as f:
            f.write(log_message + '\n')

    def extract_required_symbols(self) -> Set[str]:
        """
        Parse index.html to find all symbols the website expects.

        Looks for patterns like:
        - 'symbol': '^TNX'
        - .find(d => d.symbol === '^TNX')
        - id="spy-value"
        """
        try:
            with open(self.html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            symbols = set()

            # Pattern 1: 'symbol': 'XXX' or "symbol": "XXX"
            pattern1 = r"['\"]symbol['\"]:\s*['\"]([A-Z0-9\^=\-\.]+)['\"]"
            symbols.update(re.findall(pattern1, html_content))

            # Pattern 2: d.symbol === 'XXX'
            pattern2 = r"d\.symbol\s*===\s*['\"]([A-Z0-9\^=\-\.]+)['\"]"
            symbols.update(re.findall(pattern2, html_content))

            # Pattern 3: asset.symbol === 'XXX'
            pattern3 = r"asset\.symbol\s*===\s*['\"]([A-Z0-9\^=\-\.]+)['\"]"
            symbols.update(re.findall(pattern3, html_content))

            # Known critical symbols (hardcoded as backup)
            critical_symbols = {
                'SPY', 'UUP', 'GLD', 'USO', 'HYG',
                'BTC-USD', 'ETH-USD', 'SOL-USD',
                '^TNX', '^IRX', '^VIX',
                'AUDJPY=X'
            }
            symbols.update(critical_symbols)

            self.log(f"✅ Found {len(symbols)} required symbols in HTML: {sorted(symbols)}")
            return symbols

        except Exception as e:
            self.log(f"❌ Error parsing HTML: {e}")
            return set()

    def check_redis_for_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Check if symbol data exists in Redis.
        Tries multiple key formats.
        """
        key_patterns = [
            f'market:symbol:{symbol}',
            f'economic:{symbol}',
            f'composite:symbol:{symbol}',
            f'market:agent:{symbol}',
        ]

        for key in key_patterns:
            try:
                data = self.redis_client.get(key)
                if data:
                    return {'key': key, 'data': json.loads(data)}
            except:
                continue

        return None

    def create_alias(self, source_key: str, target_symbol: str):
        """
        Create an alias so website can find data under expected symbol.

        Example: Copy economic:DGS10 → market:symbol:^TNX
        """
        try:
            # Get source data
            source_data = self.redis_client.get(source_key)
            if not source_data:
                self.log(f"⚠️  Cannot create alias: {source_key} not found")
                return False

            # Parse and update symbol
            data = json.loads(source_data)
            data['symbol'] = target_symbol
            data['alias_for'] = source_key
            data['alias_created_at'] = datetime.now().isoformat()

            # Store under target key
            target_key = f'market:symbol:{target_symbol}'
            self.redis_client.set(target_key, json.dumps(data))
            self.redis_client.expire(target_key, 900)  # 15 min TTL

            self.log(f"✅ Created alias: {target_key} → {source_key}")
            return True

        except Exception as e:
            self.log(f"❌ Error creating alias {target_symbol}: {e}")
            return False

    async def validate_and_fix(self):
        """
        Main validation loop:
        1. Get required symbols from HTML
        2. Check what's in Redis
        3. Create aliases for mismatches
        4. Log status
        """
        self.log("=" * 80)
        self.log("🔍 WEBSITE DATA VALIDATION")
        self.log("=" * 80)

        # Step 1: Get requirements
        required_symbols = self.extract_required_symbols()

        # Step 2: Check availability
        found = {}
        missing = []
        aliases_created = []

        for symbol in required_symbols:
            # Check if data exists
            result = self.check_redis_for_symbol(symbol)

            if result:
                found[symbol] = result['key']
                self.log(f"✅ {symbol:15} | Found at {result['key']}")
            else:
                # Check if there's a known mapping
                if symbol in self.symbol_mappings:
                    source_key = self.symbol_mappings[symbol]
                    self.log(f"🔄 {symbol:15} | Not found, trying alias from {source_key}")

                    if self.create_alias(source_key, symbol):
                        found[symbol] = f'market:symbol:{symbol} (alias)'
                        aliases_created.append(symbol)
                    else:
                        missing.append(symbol)
                else:
                    missing.append(symbol)
                    self.log(f"❌ {symbol:15} | MISSING - No data found")

        # Step 3: Summary
        total = len(required_symbols)
        found_count = len(found)
        coverage = (found_count / total * 100) if total > 0 else 0

        self.log("")
        self.log("=" * 80)
        self.log(f"📊 VALIDATION SUMMARY")
        self.log("=" * 80)
        self.log(f"Required symbols: {total}")
        self.log(f"Found:            {found_count} ({coverage:.1f}%)")
        self.log(f"Missing:          {len(missing)}")
        self.log(f"Aliases created:  {len(aliases_created)}")

        if aliases_created:
            self.log(f"\n✅ Auto-fixed: {', '.join(aliases_created)}")

        if missing:
            self.log(f"\n❌ Still missing: {', '.join(missing)}")
            self.log(f"\n⚠️  USER ALERT: The following symbols are not available:")
            for symbol in missing:
                self.log(f"   - {symbol}")

        if coverage >= 100:
            self.log("\n🎉 100% DATA COVERAGE ACHIEVED!")
        elif coverage >= 90:
            self.log(f"\n🟢 EXCELLENT ({coverage:.1f}% coverage)")
        elif coverage >= 70:
            self.log(f"\n🟡 GOOD ({coverage:.1f}% coverage)")
        else:
            self.log(f"\n🔴 NEEDS ATTENTION ({coverage:.1f}% coverage)")

        self.log("=" * 80)
        self.log("")

        return coverage, missing

    async def run_forever(self):
        """Run validation loop continuously"""
        self.log("🚀 Website Data Validator Agent started")
        self.log(f"   Check interval: {self.check_interval}s")
        self.log(f"   HTML path: {self.html_path}")
        self.log("")

        while True:
            try:
                await self.validate_and_fix()
                await asyncio.sleep(self.check_interval)
            except KeyboardInterrupt:
                self.log("\n🛑 Validator stopped by user")
                break
            except Exception as e:
                self.log(f"❌ Validation error: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error


async def main():
    """Start the autonomous validator"""
    validator = WebsiteDataValidator()
    await validator.run_forever()


if __name__ == '__main__':
    asyncio.run(main())
