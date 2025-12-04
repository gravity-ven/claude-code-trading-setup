#!/usr/bin/env python3
"""
DATA POINT AGENT BASE CLASS
==========================

Base class for all individual data point agents.
Each agent is responsible for ONE specific data point and ensures
its availability 24/7 with specialized recovery mechanisms.

Key Principles:
- Single Responsibility: Each agent owns ONE data point
- Continuous Monitoring: 24/7 health checks and data validation
- Specialized Recovery: Source-specific fallback strategies
- Data Integrity Guarantee: Never returns null/fake data
- Independent Lifecycle: Failures don't affect other agents
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from abc import ABC, abstractmethod
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import data fetching utilities
from data_fetcher_fallback import fetch_stock_price, fetch_crypto_price, fetch_forex_rate


class DataPointAgent(ABC):
    """
    Base class for individual data point agents
    
    Each agent is responsible for:
    1. Continuously fetching ONE specific data point
    2. Validating data integrity
    3. Implementing source-specific fallback strategies
    4. Maintaining cached data with freshness guarantees
    5. Providing health status and metrics
    """

    def __init__(self, agent_id: str, data_point: str, data_type: str = 'stock'):
        """
        Initialize data point agent
        
        Args:
            agent_id: Unique agent identifier (e.g., 'spy_agent', 'btc_usd_agent')
            data_point: The specific data point this agent owns (e.g., 'SPY', 'BTC-USD')
            data_type: Type of data ('stock', 'crypto', 'forex', 'economic', 'index')
        """
        self.agent_id = agent_id
        self.data_point = data_point.upper()
        self.data_type = data_type
        self.agent_tier = "DATA_POINT_AGENT"
        
        # Setup logging with agent context
        self.logger = logging.getLogger(f"Agent-{self.agent_id}")
        self.logger.setLevel(logging.INFO)
        
        # Create console handler if it doesn't exist
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Data source configuration
        self.primary_sources = []
        self.fallback_sources = []
        self.current_source = None
        
        # Cache configuration
        self.cache_ttl = 300  # 5 minutes
        self.max_age_before_stale = 600  # 10 minutes before considered stale
        self.max_retries = 3
        self.retry_delay = 30  # seconds
        
        # Data quality thresholds
        self.min_price = 0.001  # Minimum valid price
        self.max_price = 100000000  # Maximum valid price
        self.max_change_pct = 50  # Maximum reasonable daily change percentage
        
        # Monitoring metrics
        self.metrics = {
            'last_fetch': None,
            'last_successful_fetch': None,
            'consecutive_failures': 0,
            'total_fetches': 0,
            'successful_fetches': 0,
            'cache_hits': 0,
            'source_switches': 0,
            'data_quality_score': 0,
            'uptime_percentage': 0,
            'agent_start_time': datetime.now()
        }
        
        # Health status
        self.health_status = 'STARTING'
        self.last_health_check = datetime.now()
        
        # Database connections
        self.redis_client = None
        self.db_conn = None
        
        # Initialize connections and data sources
        self._initialize_connections()
        self._initialize_data_sources()
        
        self.logger.info(f"Initialized {self.agent_id} for {self.data_point} ({self.data_type})")

    def _initialize_connections(self):
        """Initialize Redis and PostgreSQL connections"""
        try:
            # Redis connection
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.redis_client.ping()
            self.logger.info("✅ Connected to Redis")
        except Exception as e:
            self.logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None

        try:
            # PostgreSQL connection
            db_url = os.getenv(
                'DATABASE_URL',
                'postgresql://spartan:spartan@localhost:5432/spartan_research_db'
            )
            self.db_conn = psycopg2.connect(db_url)
            self.db_conn.autocommit = True
            self.logger.info("✅ Connected to PostgreSQL")
        except Exception as e:
            self.logger.error(f"❌ PostgreSQL connection failed: {e}")
            self.db_conn = None

    @abstractmethod
    def _initialize_data_sources(self):
        """
        Initialize the primary and fallback data sources for this specific data point
        
        Each agent must implement this method to define:
        - Primary data sources (most reliable)
        - Fallback sources (backup options)
        - Source-specific fetch parameters
        """
        pass

    @abstractmethod
    async def _fetch_from_primary(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data from primary source(s)
        
        Returns:
            Dict with fetched data or None if failed
        """
        pass

    @abstractmethod
    async def _fetch_from_fallback(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data from fallback source(s)
        
        Returns:
            Dict with fetched data or None if failed
        """
        pass

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate fetched data for quality and sanity
        
        Args:
            data: Fetched data dictionary
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check required fields
            if not data or 'price' not in data:
                self.logger.warning("Missing price field in data")
                return False

            price = float(data['price'])
            
            # Price sanity checks
            if price <= self.min_price or price > self.max_price:
                self.logger.warning(f"Price {price} out of reasonable bounds")
                return False

            # Change percentage validation
            if 'change_percent' in data:
                change_pct = float(data['change_percent'])
                if abs(change_pct) > self.max_change_pct:
                    self.logger.warning(f"Change percentage {change_pct}% seems unreasonable")
                    # Don't reject outright, but log warning

            # Timestamp validation
            timestamp_str = data.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    # Check if data is too old (more than 1 hour)
                    if datetime.now(timestamp.tzinfo) - timestamp > timedelta(hours=1):
                        self.logger.warning(f"Data timestamp is too old: {timestamp}")
                        return False
                except ValueError as e:
                    self.logger.warning(f"Invalid timestamp format: {e}")
                    return False

            return True

        except (ValueError, TypeError) as e:
            self.logger.error(f"Data validation error: {e}")
            return False

    def calculate_data_quality_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate data quality score (0-100)
        
        Factors:
        - Data completeness
        - Freshness
        - Source reliability
        - Consistency with previous values
        
        Args:
            data: Data dictionary
            
        Returns:
            Quality score between 0 and 100
        """
        score = 0
        
        # Completeness scoring (40 points)
        completeness_fields = ['price', 'change', 'change_percent', 'volume', 'timestamp']
        complete_fields = sum(1 for field in completeness_fields if field in data and data[field] is not None)
        score += (complete_fields / len(completeness_fields)) * 40

        # Freshness scoring (30 points)
        if 'timestamp' in data:
            try:
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                age_minutes = (datetime.now(timestamp.tzinfo) - timestamp).total_seconds() / 60
                freshness_score = max(0, 30 - (age_minutes / 10))  # Lose 3 points per 10 minutes
                score += max(0, freshness_score)
            except:
                pass

        # Source reliability (30 points)
        source = data.get('source', 'unknown')
        if source in ['polygon', 'yfinance', 'coingecko']:
            score += 25
        elif source in ['alpha_vantage', 'twelve_data', 'finnhub']:
            score += 20
        elif source in ['exchangerate_api']:
            score += 15
        else:
            score += 10

        return min(100, max(0, score))

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch data with intelligent source selection and fallback
        
        Returns:
            Validated data dictionary or None if all sources fail
        """
        self.metrics['total_fetches'] += 1
        start_time = time.time()

        try:
            # Try primary sources first
            data = await self._fetch_from_primary()
            if data and self.validate_data(data):
                self.metrics['successful_fetches'] += 1
                self.metrics['last_successful_fetch'] = datetime.now()
                self.metrics['consecutive_failures'] = 0
                self.current_source = data.get('source', 'primary')
                
                fetch_time = time.time() - start_time
                self.logger.info(f"✅ {self.data_point}: ${data.get('price')} from {self.current_source} ({fetch_time:.2f}s)")
                return data
            else:
                self.logger.warning(f"Primary source failed for {self.data_point}")

        except Exception as e:
            self.logger.error(f"Primary source error for {self.data_point}: {e}")

        # Try fallback sources
        try:
            data = await self._fetch_from_fallback()
            if data and self.validate_data(data):
                self.metrics['successful_fetches'] += 1
                self.metrics['last_successful_fetch'] = datetime.now()
                self.metrics['consecutive_failures'] = 0
                self.current_source = data.get('source', 'fallback')
                self.metrics['source_switches'] += 1
                
                fetch_time = time.time() - start_time
                self.logger.info(f"⚡ {self.data_point}: ${data.get('price')} from fallback {self.current_source} ({fetch_time:.2f}s)")
                return data
            else:
                self.logger.warning(f"Fallback source failed for {self.data_point}")

        except Exception as e:
            self.logger.error(f"Fallback source error for {self.data_point}: {e}")

        # All sources failed
        self.metrics['consecutive_failures'] += 1
        self.logger.error(f"❌ All sources failed for {self.data_point} (consecutive failures: {self.metrics['consecutive_failures']})")
        return None

    def cache_data(self, data: Dict[str, Any]) -> bool:
        """
        Store data in Redis cache and PostgreSQL backup
        
        Args:
            data: Validated data to cache
            
        Returns:
            True if caching successful, False otherwise
        """
        success = True
        
        # Calculate quality score
        quality_score = self.calculate_data_quality_score(data)
        data['quality_score'] = quality_score
        self.metrics['data_quality_score'] = quality_score

        # Store in Redis (primary cache)
        if self.redis_client:
            try:
                cache_key = f"datapoint:{self.data_point}"
                cache_data = {
                    **data,
                    'agent_id': self.agent_id,
                    'cached_at': datetime.now().isoformat(),
                    'cache_ttl': self.cache_ttl
                }
                
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(cache_data)
                )
                
                # Also store in agent-specific key for monitoring
                agent_key = f"agent:{self.agent_id}:latest"
                self.redis_client.setex(
                    agent_key,
                    self.cache_ttl * 2,  # Longer TTL for agent monitoring
                    json.dumps({
                        'data_point': self.data_point,
                        'data': data,
                        'timestamp': datetime.now().isoformat(),
                        'source': self.current_source,
                        'quality_score': quality_score
                    })
                )
                
            except Exception as e:
                self.logger.error(f"Redis caching failed: {e}")
                success = False

        # Store in PostgreSQL (backup)
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                
                cursor.execute("""
                    INSERT INTO data_point_cache (
                        agent_id, data_point, data_type, price, change_percent,
                        volume, metadata, source, quality_score, timestamp
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (agent_id, data_point)
                    DO UPDATE SET
                        price = EXCLUDED.price,
                        change_percent = EXCLUDED.change_percent,
                        volume = EXCLUDED.volume,
                        metadata = EXCLUDED.metadata,
                        source = EXCLUDED.source,
                        quality_score = EXCLUDED.quality_score,
                        timestamp = EXCLUDED.timestamp,
                        updated_at = NOW()
                """, (
                    self.agent_id,
                    self.data_point,
                    self.data_type,
                    data.get('price'),
                    data.get('change_percent'),
                    data.get('volume'),
                    json.dumps(data),
                    self.current_source,
                    quality_score,
                    datetime.now()
                ))
                
            except Exception as e:
                self.logger.error(f"PostgreSQL backup failed: {e}")
                success = False

        return success

    def get_cached_data(self) -> Optional[Dict[str, Any]]:
        """
        Get cached data from Redis (preferred) or PostgreSQL (fallback)
        
        Returns:
            Cached data or None if not available
        """
        # Try Redis first
        if self.redis_client:
            try:
                cache_key = f"datapoint:{self.data_point}"
                cached_data = self.redis_client.get(cache_key)
                
                if cached_data:
                    data = json.loads(cached_data)
                    
                    # Check if data is still fresh
                    cached_at = datetime.fromisoformat(data.get('cached_at', '1970-01-01'))
                    age_seconds = (datetime.now() - cached_at).total_seconds()
                    
                    if age_seconds < self.max_age_before_stale:
                        self.metrics['cache_hits'] += 1
                        self.logger.debug(f"Redis cache hit for {self.data_point} (age: {age_seconds:.0f}s)")
                        return data
                    else:
                        self.logger.debug(f"Redis cache stale for {self.data_point} (age: {age_seconds:.0f}s)")
                        
            except Exception as e:
                self.logger.error(f"Redis cache read error: {e}")

        # Try PostgreSQL fallback
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute("""
                    SELECT * FROM data_point_cache
                    WHERE data_point = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (self.data_point,))
                
                row = cursor.fetchone()
                if row:
                    data = dict(row)
                    
                    # Parse JSON metadata
                    if isinstance(data.get('metadata'), str):
                        try:
                            data['metadata'] = json.loads(data['metadata'])
                        except:
                            pass
                    
                    # Check freshness
                    age_seconds = (datetime.now() - data['timestamp']).total_seconds()
                    if age_seconds < self.max_age_before_stale:
                        self.logger.debug(f"PostgreSQL cache hit for {self.data_point} (age: {age_seconds:.0f}s)")
                        return data
                    else:
                        self.logger.debug(f"PostgreSQL cache stale for {self.data_point} (age: {age_seconds:.0f}s)")
                        
            except Exception as e:
                self.logger.error(f"PostgreSQL cache read error: {e}")

        return None

    def update_health_status(self):
        """Update agent health status based on metrics"""
        now = datetime.now()
        
        # Check if we had a recent successful fetch
        if self.metrics['last_successful_fetch']:
            time_since_success = (now - self.metrics['last_successful_fetch']).total_seconds()
            
            if time_since_success < 300:  # 5 minutes
                self.health_status = 'HEALTHY'
            elif time_since_success < 900:  # 15 minutes
                self.health_status = 'WARNING'
            else:
                self.health_status = 'CRITICAL'
        else:
            self.health_status = 'FAILED'

        # Update uptime percentage
        uptime = (now - self.metrics['agent_start_time']).total_seconds()
        if uptime > 0:
            success_rate = (self.metrics['successful_fetches'] / max(1, self.metrics['total_fetches'])) * 100
            self.metrics['uptime_percentage'] = success_rate

        self.last_health_check = now

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status for monitoring
        
        Returns:
            Health status dictionary with metrics
        """
        self.update_health_status()
        
        return {
            'agent_id': self.agent_id,
            'data_point': self.data_point,
            'data_type': self.data_type,
            'health_status': self.health_status,
            'current_source': self.current_source,
            'last_fetch': self.metrics['last_fetch'].isoformat() if self.metrics['last_fetch'] else None,
            'last_successful_fetch': self.metrics['last_successful_fetch'].isoformat() if self.metrics['last_successful_fetch'] else None,
            'consecutive_failures': self.metrics['consecutive_failures'],
            'total_fetches': self.metrics['total_fetches'],
            'successful_fetches': self.metrics['successful_fetches'],
            'cache_hits': self.metrics['cache_hits'],
            'source_switches': self.metrics['source_switches'],
            'data_quality_score': self.metrics['data_quality_score'],
            'uptime_percentage': self.metrics['uptime_percentage'],
            'agent_start_time': self.metrics['agent_start_time'].isoformat(),
            'last_health_check': self.last_health_check.isoformat()
        }

    async def run_continuous(self) -> None:
        """
        Main continuous execution loop
        
        Continuously fetches, validates, and caches data for this data point.
        Implements smart retry logic with exponential backoff.
        """
        self.logger.info(f"🚀 Starting continuous monitoring for {self.data_point}")
        
        while True:
            try:
                # Record fetch attempt
                self.metrics['last_fetch'] = datetime.now()
                
                # Try to get fresh data
                data = await self.fetch_data()
                
                if data:
                    # Cache the valid data
                    if self.cache_data(data):
                        self.logger.debug(f"✅ Successfully cached {self.data_point}")
                    else:
                        self.logger.warning(f"⚠️ Failed to cache {self.data_point}")
                    
                    # Short sleep after successful fetch
                    await asyncio.sleep(self.cache_ttl - 60)  # Update 1 minute before TTL expires
                    
                else:
                    # Failed to fetch data - try using stale cached data
                    cached_data = self.get_cached_data()
                    if cached_data:
                        self.logger.warning(f"🔄 Fetch failed, using stale cache for {self.data_point}")
                        # Still serve stale data but mark it
                        cached_data['stale'] = True
                        cached_data['fetch_failed'] = True
                        self.cache_data(cached_data)
                    else:
                        self.logger.error(f"❌ No cached data available for {self.data_point}")
                    
                    # Exponential backoff on failures
                    backoff_time = min(300, 30 * (2 ** min(self.metrics['consecutive_failures'], 4)))
                    self.logger.info(f"🔄 Retrying in {backoff_time}s (consecutive failures: {self.metrics['consecutive_failures']})")
                    await asyncio.sleep(backoff_time)

            except Exception as e:
                self.logger.error(f"❌ Unexpected error in main loop: {e}")
                self.metrics['consecutive_failures'] += 1
                await asyncio.sleep(60)  # Wait 1 minute on unexpected errors

    async def start(self) -> None:
        """Start the agent's continuous monitoring loop"""
        await self.run_continuous()

    def stop(self) -> None:
        """Stop the agent and clean up resources"""
        self.logger.info(f"🛑 Stopping {self.agent_id}")
        
        if self.redis_client:
            self.redis_client.close()
        
        if self.db_conn:
            self.db_conn.close()
        
        self.logger.info(f"✅ {self.agent_id} stopped successfully")
