#!/usr/bin/env python3
"""
Autonomous Data Agent Base Class
=================================

Template for all micro-agents that fetch and cache individual data points.

Architecture:
- One agent per data source/symbol
- Autonomous operation with health monitoring
- Redis + PostgreSQL dual storage
- Configurable update intervals
- Fault isolation (one agent failure doesn't crash system)
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
import random

import psycopg2
import redis
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class AutonomousDataAgent(ABC):
    """
    Base class for autonomous data agents.

    Each agent:
    1. Fetches data from a specific source
    2. Stores to Redis (fast cache)
    3. Backs up to PostgreSQL (persistent)
    4. Runs on independent schedule
    5. Reports health status
    """

    def __init__(
        self,
        name: str,
        symbol: str,
        source: str,
        update_interval: int = 900,  # 15 minutes default
        redis_key_prefix: str = "market",
        critical: bool = False
    ):
        """
        Initialize autonomous agent.

        Args:
            name: Human-readable agent name (e.g., "SPY Price Agent")
            symbol: Symbol/identifier to fetch (e.g., "SPY", "DGS10")
            source: Data source name (e.g., "yfinance", "fred", "polygon")
            update_interval: Seconds between updates (default 900 = 15 min)
            redis_key_prefix: Redis key prefix (e.g., "market", "fundamental")
            critical: If True, agent failure triggers alerts
        """
        self.name = name
        self.symbol = symbol
        self.source = source
        self.update_interval = update_interval
        self.redis_key_prefix = redis_key_prefix
        self.critical = critical

        # Redis key pattern: {prefix}:{type}:{symbol}
        self.redis_key = f"{redis_key_prefix}:symbol:{symbol}"

        # Agent state
        self.running = False
        self.last_update = None
        self.last_success = None
        self.consecutive_failures = 0
        self.total_fetches = 0
        self.successful_fetches = 0

        # Logger
        self.logger = logging.getLogger(self.name)

        # Database connections
        self.redis_client = None
        self.db_conn = None

    async def initialize(self):
        """Initialize database connections"""
        try:
            # Connect to Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            self.logger.info(f"✅ Connected to Redis")

            # Connect to PostgreSQL
            self.db_conn = psycopg2.connect(
                dbname="spartan_research_db",
                user="spartan",
                password="spartan",
                host="localhost",
                port=5432
            )
            self.logger.info(f"✅ Connected to PostgreSQL")

            return True

        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            return False

    @abstractmethod
    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data from source (MUST BE IMPLEMENTED BY SUBCLASS).

        Returns:
            Dict with data or None on failure

        Example return format:
        {
            'symbol': 'SPY',
            'price': 659.03,
            'change': 2.45,
            'changePercent': 0.37,
            'volume': 45123456,
            'timestamp': '2025-11-25T10:30:00'
        }
        """
        pass

    async def store_data(self, data: Dict[str, Any]):
        """
        Store data to Redis and PostgreSQL.

        Args:
            data: Data dictionary to store
        """
        if not data:
            return

        try:
            # Add metadata
            data['agent_name'] = self.name
            data['source'] = self.source
            data['fetched_at'] = datetime.utcnow().isoformat()

            # Store to Redis (15-minute TTL)
            if self.redis_client:
                self.redis_client.setex(
                    self.redis_key,
                    900,  # 15 minutes
                    json.dumps(data)
                )
                self.logger.debug(f"✅ Stored to Redis: {self.redis_key}")

            # Backup to PostgreSQL
            if self.db_conn:
                cursor = self.db_conn.cursor()

                # Extract data fields matching schema
                price = data.get('price') or data.get('value')
                change_percent = data.get('changePercent', 0)
                volume = data.get('volume')

                # Determine data_type
                if 'price' in data:
                    data_type = 'price'
                elif 'value' in data:
                    data_type = 'economic'
                elif 'narrative' in data:
                    data_type = 'narrative'
                else:
                    data_type = 'market_data'

                cursor.execute("""
                    INSERT INTO preloaded_market_data
                        (symbol, data_type, price, change_percent, volume, metadata, source, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (symbol, data_type, timestamp)
                    DO UPDATE SET
                        price = EXCLUDED.price,
                        change_percent = EXCLUDED.change_percent,
                        volume = EXCLUDED.volume,
                        metadata = EXCLUDED.metadata,
                        source = EXCLUDED.source
                """, (
                    self.symbol,
                    data_type,
                    price,
                    change_percent,
                    volume,
                    json.dumps(data),
                    self.source
                ))
                self.db_conn.commit()
                cursor.close()
                self.logger.debug(f"✅ Backed up to PostgreSQL")

        except Exception as e:
            self.logger.error(f"❌ Storage failed: {e}")

    async def fetch_with_retry(self, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Fetch data with exponential backoff retry logic.

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            Data dict or None on failure
        """
        for attempt in range(max_retries):
            try:
                # Add random jitter to avoid thundering herd
                if attempt > 0:
                    jitter = random.uniform(0, 2 ** attempt)
                    await asyncio.sleep(jitter)
                    self.logger.info(f"Retry attempt {attempt + 1}/{max_retries}")

                # Fetch data
                data = await self.fetch_data()

                if data:
                    return data

                # If fetch returned None, wait before retry
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except Exception as e:
                self.logger.error(f"Fetch attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return None

    async def update_cycle(self):
        """Single update cycle: fetch and store"""
        self.total_fetches += 1
        self.last_update = datetime.utcnow()

        try:
            # Fetch data with retry logic
            data = await self.fetch_with_retry(max_retries=3)

            if data:
                # Store data
                await self.store_data(data)

                # Update success metrics
                self.successful_fetches += 1
                self.consecutive_failures = 0
                self.last_success = datetime.utcnow()

                self.logger.info(
                    f"✅ Updated {self.symbol} | "
                    f"Success rate: {self.success_rate:.1%} | "
                    f"Next update in {self.update_interval}s"
                )
            else:
                # Track failure
                self.consecutive_failures += 1
                self.logger.warning(
                    f"⚠️  Failed to fetch {self.symbol} | "
                    f"Consecutive failures: {self.consecutive_failures}"
                )

                # Alert if critical agent failing
                if self.critical and self.consecutive_failures >= 3:
                    self.logger.error(
                        f"🚨 CRITICAL AGENT FAILURE: {self.name} | "
                        f"{self.consecutive_failures} consecutive failures"
                    )

        except Exception as e:
            self.consecutive_failures += 1
            self.logger.error(f"❌ Update cycle failed: {e}")

    async def run(self):
        """
        Main agent loop.

        Runs continuously:
        1. Fetch data from source
        2. Store to Redis + PostgreSQL
        3. Wait for update_interval
        4. Repeat
        """
        # Initialize connections
        if not await self.initialize():
            self.logger.error(f"❌ Failed to initialize {self.name}")
            return

        self.running = True
        self.logger.info(
            f"🚀 {self.name} started | "
            f"Symbol: {self.symbol} | "
            f"Source: {self.source} | "
            f"Interval: {self.update_interval}s | "
            f"Critical: {self.critical}"
        )

        while self.running:
            try:
                # Execute update cycle
                await self.update_cycle()

                # Wait for next update
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                self.logger.error(f"❌ Agent loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    def stop(self):
        """Stop the agent"""
        self.running = False
        self.logger.info(f"🛑 {self.name} stopped")

        # Close database connections
        if self.redis_client:
            self.redis_client.close()
        if self.db_conn:
            self.db_conn.close()

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_fetches == 0:
            return 0.0
        return self.successful_fetches / self.total_fetches

    @property
    def health_status(self) -> Dict[str, Any]:
        """Get agent health status"""
        return {
            'name': self.name,
            'symbol': self.symbol,
            'source': self.source,
            'running': self.running,
            'critical': self.critical,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'consecutive_failures': self.consecutive_failures,
            'total_fetches': self.total_fetches,
            'successful_fetches': self.successful_fetches,
            'success_rate': self.success_rate,
            'update_interval': self.update_interval
        }


# Example subclass implementation
class YahooFinanceAgent(AutonomousDataAgent):
    """Agent that fetches from Yahoo Finance (yfinance)"""

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch from Yahoo Finance"""
        try:
            import yfinance as yf

            ticker = yf.Ticker(self.symbol)
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            # Calculate metrics
            current_price = float(hist['Close'][-1])
            prev_close = float(hist['Close'][-2]) if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            # 5-day change
            if len(hist) >= 5:
                price_5d_ago = float(hist['Close'][-5])
                change_5d_pct = ((current_price - price_5d_ago) / price_5d_ago * 100)
            else:
                change_5d_pct = 0

            return {
                'symbol': self.symbol,
                'price': current_price,
                'change': change,
                'changePercent': change_pct,
                'changePercent5d': change_5d_pct,
                'volume': int(hist['Volume'][-1]),
                'timestamp': hist.index[-1].isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Yahoo Finance fetch failed: {e}")
            return None


class FREDAgent(AutonomousDataAgent):
    """Agent that fetches from FRED (Federal Reserve Economic Data)"""

    def __init__(self, name: str, symbol: str, fred_series: str, **kwargs):
        """
        Initialize FRED agent.

        Args:
            name: Agent name
            symbol: Symbol to use for storage
            fred_series: FRED series ID (e.g., "DGS10", "UNRATE")
            **kwargs: Other base class arguments
        """
        super().__init__(name, symbol, "fred", **kwargs)
        self.fred_series = fred_series
        self.fred_api_key = None  # Set from environment or config

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch from FRED API"""
        try:
            # TODO: Implement FRED API fetch
            # For now, return placeholder
            self.logger.warning(f"⚠️  FRED API not yet implemented for {self.fred_series}")
            return None

        except Exception as e:
            self.logger.error(f"❌ FRED fetch failed: {e}")
            return None
