#!/usr/bin/env python3
"""
SPARTAN LABS - AUTONOMOUS ERROR DETECTION & MONITORING SYSTEM
==============================================================

Continuously monitors all 50+ data source endpoints for errors and anomalies.
Implements NESTED learning approach for intelligent error detection.

Architecture:
- Outer Layer: General error detection patterns (timeouts, rate limits, auth)
- Inner Layer: Source-specific behavior patterns (FRED vs Yahoo vs Polygon)

Author: Spartan Labs
Version: 1.0.0
"""

import asyncio
import aiohttp
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
import statistics

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/logs/error_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Comprehensive error classification system."""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit_429"
    AUTH_ERROR = "auth_error_403"
    SERVER_ERROR = "server_error_5xx"
    INVALID_DATA = "invalid_data"
    NETWORK_ERROR = "network_error"
    PARSING_ERROR = "parsing_error"
    MISSING_DATA = "missing_data"
    STALE_DATA = "stale_data"
    QUOTA_EXCEEDED = "quota_exceeded"


class DataSource(Enum):
    """All supported data sources."""
    YAHOO_FINANCE = "yahoo_finance"
    FRED_API = "fred_api"
    POLYGON_IO = "polygon_io"
    ALPHA_VANTAGE = "alpha_vantage"
    EXCHANGE_RATE_API = "exchange_rate_api"


class HealthStatus(Enum):
    """Data source health status levels."""
    HEALTHY = "healthy"           # 0-5% error rate
    DEGRADED = "degraded"         # 5-20% error rate
    CRITICAL = "critical"         # 20-50% error rate
    FAILED = "failed"             # 50%+ error rate


@dataclass
class ErrorEvent:
    """Structured error event data."""
    timestamp: datetime
    source: DataSource
    endpoint: str
    error_type: ErrorType
    error_message: str
    response_time: float
    http_status_code: Optional[int]
    request_params: Dict[str, Any]
    retry_count: int
    fixed_automatically: bool
    fix_method: Optional[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'source': self.source.value,
            'endpoint': self.endpoint,
            'error_type': self.error_type.value,
            'error_message': self.error_message,
            'response_time': self.response_time,
            'http_status_code': self.http_status_code,
            'request_params': json.dumps(self.request_params),
            'retry_count': self.retry_count,
            'fixed_automatically': self.fixed_automatically,
            'fix_method': self.fix_method
        }


@dataclass
class EndpointHealth:
    """Real-time endpoint health metrics."""
    source: DataSource
    endpoint: str
    status: HealthStatus
    total_requests: int
    failed_requests: int
    error_rate: float
    avg_response_time: float
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    consecutive_failures: int
    uptime_percentage: float

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'source': self.source.value,
            'endpoint': self.endpoint,
            'status': self.status.value,
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'error_rate': round(self.error_rate, 2),
            'avg_response_time': round(self.avg_response_time, 3),
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'last_failure': self.last_failure.isoformat() if self.last_failure else None,
            'consecutive_failures': self.consecutive_failures,
            'uptime_percentage': round(self.uptime_percentage, 2)
        }


class ErrorDetectionEngine:
    """
    Core error detection engine with NESTED learning.

    OUTER LAYER: General error detection patterns
    - HTTP status code classification
    - Response time anomalies
    - Data validation rules

    INNER LAYER: Source-specific patterns
    - FRED API rate limit behavior
    - Yahoo Finance throttling patterns
    - Polygon.io quota tracking
    """

    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.conn = None

        # OUTER LAYER: General thresholds (slow-changing)
        self.outer_params = {
            'timeout_threshold': 10.0,          # 10 seconds
            'response_time_threshold': 5.0,     # 5 seconds = slow
            'error_rate_degraded': 0.05,        # 5% = degraded
            'error_rate_critical': 0.20,        # 20% = critical
            'consecutive_fail_limit': 3,         # 3 consecutive = circuit break
            'data_freshness_threshold': 3600,   # 1 hour = stale
        }

        # INNER LAYER: Source-specific thresholds (fast-changing)
        self.inner_params = {
            DataSource.YAHOO_FINANCE: {
                'expected_response_time': 2.0,
                'rate_limit_window': 60,         # 60 seconds
                'max_requests_per_window': 2000,
                'retry_delay': 1.0,
            },
            DataSource.FRED_API: {
                'expected_response_time': 1.5,
                'rate_limit_window': 60,         # 120 requests/minute
                'max_requests_per_window': 120,
                'retry_delay': 0.5,
            },
            DataSource.POLYGON_IO: {
                'expected_response_time': 0.8,
                'rate_limit_window': 60,         # Depends on plan
                'max_requests_per_window': 100,
                'retry_delay': 2.0,
            },
            DataSource.ALPHA_VANTAGE: {
                'expected_response_time': 2.5,
                'rate_limit_window': 60,         # 5 per minute free tier
                'max_requests_per_window': 5,
                'retry_delay': 12.0,             # Long delay for free tier
            },
        }

        # Learning history storage
        self.error_patterns = {}  # Learned patterns from past errors
        self.fix_success_rates = {}  # Track which fixes work best

    async def connect_db(self):
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("✅ Connected to PostgreSQL database")
            await self._initialize_tables()
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    async def _initialize_tables(self):
        """Create necessary database tables if they don't exist."""
        with self.conn.cursor() as cur:
            # Error events table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS error_events (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    source VARCHAR(50) NOT NULL,
                    endpoint VARCHAR(255) NOT NULL,
                    error_type VARCHAR(50) NOT NULL,
                    error_message TEXT,
                    response_time FLOAT,
                    http_status_code INT,
                    request_params JSONB,
                    retry_count INT DEFAULT 0,
                    fixed_automatically BOOLEAN DEFAULT FALSE,
                    fix_method VARCHAR(100),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_error_events_timestamp
                    ON error_events(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_error_events_source
                    ON error_events(source);
                CREATE INDEX IF NOT EXISTS idx_error_events_error_type
                    ON error_events(error_type);
            """)

            # Endpoint health metrics table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS endpoint_health (
                    id SERIAL PRIMARY KEY,
                    source VARCHAR(50) NOT NULL,
                    endpoint VARCHAR(255) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    total_requests INT DEFAULT 0,
                    failed_requests INT DEFAULT 0,
                    error_rate FLOAT DEFAULT 0,
                    avg_response_time FLOAT DEFAULT 0,
                    last_success TIMESTAMPTZ,
                    last_failure TIMESTAMPTZ,
                    consecutive_failures INT DEFAULT 0,
                    uptime_percentage FLOAT DEFAULT 100,
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(source, endpoint)
                );

                CREATE INDEX IF NOT EXISTS idx_endpoint_health_status
                    ON endpoint_health(status);
            """)

            # Learning patterns table (NESTED learning storage)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id SERIAL PRIMARY KEY,
                    source VARCHAR(50) NOT NULL,
                    error_type VARCHAR(50) NOT NULL,
                    pattern_signature TEXT NOT NULL,
                    occurrence_count INT DEFAULT 1,
                    fix_method VARCHAR(100),
                    fix_success_rate FLOAT DEFAULT 0,
                    avg_fix_time FLOAT DEFAULT 0,
                    last_seen TIMESTAMPTZ DEFAULT NOW(),
                    confidence_score FLOAT DEFAULT 0,
                    UNIQUE(source, error_type, pattern_signature)
                );
            """)

            self.conn.commit()
            logger.info("✅ Database tables initialized")

    async def detect_error(
        self,
        source: DataSource,
        endpoint: str,
        response: Optional[aiohttp.ClientResponse],
        response_data: Optional[Dict],
        response_time: float,
        exception: Optional[Exception] = None
    ) -> Optional[ErrorEvent]:
        """
        OUTER LAYER: Detect and classify errors using general patterns.

        Returns ErrorEvent if error detected, None if request was successful.
        """
        start_time = time.time()

        # Case 1: Exception occurred (network error, timeout, etc.)
        if exception:
            error_type = self._classify_exception(exception)
            return ErrorEvent(
                timestamp=datetime.now(),
                source=source,
                endpoint=endpoint,
                error_type=error_type,
                error_message=str(exception),
                response_time=response_time,
                http_status_code=None,
                request_params={},
                retry_count=0,
                fixed_automatically=False,
                fix_method=None
            )

        # Case 2: HTTP error status code
        if response and response.status >= 400:
            error_type = self._classify_http_status(response.status)
            return ErrorEvent(
                timestamp=datetime.now(),
                source=source,
                endpoint=endpoint,
                error_type=error_type,
                error_message=f"HTTP {response.status}: {response.reason}",
                response_time=response_time,
                http_status_code=response.status,
                request_params={},
                retry_count=0,
                fixed_automatically=False,
                fix_method=None
            )

        # Case 3: Response too slow
        if response_time > self.outer_params['timeout_threshold']:
            return ErrorEvent(
                timestamp=datetime.now(),
                source=source,
                endpoint=endpoint,
                error_type=ErrorType.TIMEOUT,
                error_message=f"Response time {response_time:.2f}s exceeds threshold",
                response_time=response_time,
                http_status_code=response.status if response else None,
                request_params={},
                retry_count=0,
                fixed_automatically=False,
                fix_method=None
            )

        # Case 4: Invalid or missing data
        if response_data:
            data_error = self._validate_response_data(source, response_data)
            if data_error:
                return ErrorEvent(
                    timestamp=datetime.now(),
                    source=source,
                    endpoint=endpoint,
                    error_type=ErrorType.INVALID_DATA,
                    error_message=data_error,
                    response_time=response_time,
                    http_status_code=response.status if response else None,
                    request_params={},
                    retry_count=0,
                    fixed_automatically=False,
                    fix_method=None
                )

        # No error detected
        return None

    def _classify_exception(self, exception: Exception) -> ErrorType:
        """Classify exception into ErrorType."""
        exception_str = str(type(exception).__name__).lower()

        if 'timeout' in exception_str:
            return ErrorType.TIMEOUT
        elif 'connection' in exception_str:
            return ErrorType.NETWORK_ERROR
        else:
            return ErrorType.NETWORK_ERROR

    def _classify_http_status(self, status_code: int) -> ErrorType:
        """Classify HTTP status code into ErrorType."""
        if status_code == 429:
            return ErrorType.RATE_LIMIT
        elif status_code in (401, 403):
            return ErrorType.AUTH_ERROR
        elif 500 <= status_code < 600:
            return ErrorType.SERVER_ERROR
        else:
            return ErrorType.NETWORK_ERROR

    def _validate_response_data(self, source: DataSource, data: Dict) -> Optional[str]:
        """
        INNER LAYER: Source-specific data validation.

        Returns error message if data is invalid, None if valid.
        """
        # FRED API validation
        if source == DataSource.FRED_API:
            if 'error_message' in data:
                return f"FRED API error: {data['error_message']}"
            if 'observations' in data:
                obs = data['observations']
                if not obs or len(obs) == 0:
                    return "FRED API returned no observations"
                if obs[0].get('value') == '.':
                    return "FRED API returned missing value (.)"

        # Yahoo Finance validation
        elif source == DataSource.YAHOO_FINANCE:
            if 'chart' in data:
                if data['chart'].get('error'):
                    return f"Yahoo Finance error: {data['chart']['error']}"
                if not data['chart'].get('result'):
                    return "Yahoo Finance returned no results"

        # Polygon.io validation
        elif source == DataSource.POLYGON_IO:
            if data.get('status') == 'ERROR':
                return f"Polygon.io error: {data.get('error', 'Unknown error')}"
            if not data.get('results'):
                return "Polygon.io returned no results"

        # Alpha Vantage validation
        elif source == DataSource.ALPHA_VANTAGE:
            if 'Error Message' in data:
                return f"Alpha Vantage error: {data['Error Message']}"
            if 'Note' in data and 'premium' in data['Note'].lower():
                return "Alpha Vantage API call limit reached"

        return None

    async def record_error(self, error: ErrorEvent):
        """Record error event to database."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO error_events
                    (timestamp, source, endpoint, error_type, error_message,
                     response_time, http_status_code, request_params,
                     retry_count, fixed_automatically, fix_method)
                    VALUES (%(timestamp)s, %(source)s, %(endpoint)s, %(error_type)s,
                            %(error_message)s, %(response_time)s, %(http_status_code)s,
                            %(request_params)s, %(retry_count)s, %(fixed_automatically)s,
                            %(fix_method)s)
                """, error.to_dict())
                self.conn.commit()

            logger.warning(f"⚠️ Error recorded: {error.source.value}/{error.endpoint} - {error.error_type.value}")
        except Exception as e:
            logger.error(f"Failed to record error: {e}")

    async def update_endpoint_health(self, source: DataSource, endpoint: str,
                                     success: bool, response_time: float):
        """Update real-time endpoint health metrics."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get current metrics
                cur.execute("""
                    SELECT * FROM endpoint_health
                    WHERE source = %s AND endpoint = %s
                """, (source.value, endpoint))

                current = cur.fetchone()

                if current:
                    # Update existing record
                    total_requests = current['total_requests'] + 1
                    failed_requests = current['failed_requests'] + (0 if success else 1)
                    error_rate = failed_requests / total_requests

                    # Update average response time (rolling average)
                    n = current['total_requests']
                    avg_response_time = (current['avg_response_time'] * n + response_time) / (n + 1)

                    # Update consecutive failures
                    consecutive_failures = 0 if success else current['consecutive_failures'] + 1

                    # Calculate uptime percentage
                    uptime_percentage = ((total_requests - failed_requests) / total_requests) * 100

                    # Determine status
                    if error_rate < 0.05:
                        status = HealthStatus.HEALTHY
                    elif error_rate < 0.20:
                        status = HealthStatus.DEGRADED
                    elif error_rate < 0.50:
                        status = HealthStatus.CRITICAL
                    else:
                        status = HealthStatus.FAILED

                    cur.execute("""
                        UPDATE endpoint_health SET
                            status = %s,
                            total_requests = %s,
                            failed_requests = %s,
                            error_rate = %s,
                            avg_response_time = %s,
                            last_success = CASE WHEN %s THEN NOW() ELSE last_success END,
                            last_failure = CASE WHEN %s THEN NOW() ELSE last_failure END,
                            consecutive_failures = %s,
                            uptime_percentage = %s,
                            updated_at = NOW()
                        WHERE source = %s AND endpoint = %s
                    """, (status.value, total_requests, failed_requests, error_rate,
                          avg_response_time, success, not success, consecutive_failures,
                          uptime_percentage, source.value, endpoint))
                else:
                    # Create new record
                    cur.execute("""
                        INSERT INTO endpoint_health
                        (source, endpoint, status, total_requests, failed_requests,
                         error_rate, avg_response_time, last_success, last_failure,
                         consecutive_failures, uptime_percentage)
                        VALUES (%s, %s, %s, 1, %s, %s, %s, %s, %s, %s, %s)
                    """, (source.value, endpoint, HealthStatus.HEALTHY.value,
                          0 if success else 1, 0.0 if success else 1.0,
                          response_time,
                          datetime.now() if success else None,
                          datetime.now() if not success else None,
                          0 if success else 1,
                          100.0 if success else 0.0))

                self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to update endpoint health: {e}")

    async def get_all_endpoint_health(self) -> List[EndpointHealth]:
        """Get health status for all monitored endpoints."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM endpoint_health
                    ORDER BY error_rate DESC, source ASC
                """)

                rows = cur.fetchall()
                return [
                    EndpointHealth(
                        source=DataSource(row['source']),
                        endpoint=row['endpoint'],
                        status=HealthStatus(row['status']),
                        total_requests=row['total_requests'],
                        failed_requests=row['failed_requests'],
                        error_rate=row['error_rate'],
                        avg_response_time=row['avg_response_time'],
                        last_success=row['last_success'],
                        last_failure=row['last_failure'],
                        consecutive_failures=row['consecutive_failures'],
                        uptime_percentage=row['uptime_percentage']
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Failed to get endpoint health: {e}")
            return []

    async def predict_failure(self, source: DataSource, endpoint: str) -> float:
        """
        NESTED LEARNING: Predict probability of failure based on patterns.

        Returns: Probability (0.0 to 1.0) that next request will fail.
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get recent error pattern
                cur.execute("""
                    SELECT consecutive_failures, error_rate,
                           EXTRACT(EPOCH FROM (NOW() - last_success)) as time_since_success
                    FROM endpoint_health
                    WHERE source = %s AND endpoint = %s
                """, (source.value, endpoint))

                row = cur.fetchone()
                if not row:
                    return 0.0  # No history = assume healthy

                # Calculate failure probability using weighted factors
                consecutive_weight = min(row['consecutive_failures'] / 10.0, 1.0)  # 0-1
                error_rate_weight = min(row['error_rate'] * 2, 1.0)  # 0-1

                # Time since success (longer = more likely to fail)
                time_weight = 0.0
                if row['time_since_success']:
                    time_weight = min(row['time_since_success'] / 3600.0, 1.0)  # 0-1 over 1 hour

                # Weighted average
                failure_probability = (
                    consecutive_weight * 0.4 +
                    error_rate_weight * 0.4 +
                    time_weight * 0.2
                )

                return failure_probability
        except Exception as e:
            logger.error(f"Failed to predict failure: {e}")
            return 0.0

    async def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("✅ Database connection closed")


if __name__ == "__main__":
    # Test error detection engine
    async def test():
        db_config = {
            'dbname': 'spartan_research_db',
            'user': 'spartan_user',
            'password': 'secure_password',
            'host': 'localhost',
            'port': 5432
        }

        engine = ErrorDetectionEngine(db_config)
        await engine.connect_db()

        # Simulate error
        error = ErrorEvent(
            timestamp=datetime.now(),
            source=DataSource.YAHOO_FINANCE,
            endpoint='/quote/AAPL',
            error_type=ErrorType.RATE_LIMIT,
            error_message="Rate limit exceeded",
            response_time=2.5,
            http_status_code=429,
            request_params={'symbol': 'AAPL'},
            retry_count=0,
            fixed_automatically=False,
            fix_method=None
        )

        await engine.record_error(error)
        await engine.update_endpoint_health(DataSource.YAHOO_FINANCE, '/quote/AAPL', False, 2.5)

        # Get health status
        health = await engine.get_all_endpoint_health()
        for h in health:
            print(f"{h.source.value}/{h.endpoint}: {h.status.value} ({h.error_rate*100:.1f}% error rate)")

        await engine.close()

    asyncio.run(test())
