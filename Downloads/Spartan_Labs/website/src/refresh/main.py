#!/usr/bin/env python3
"""
Spartan Research Station - Background Refresh Service
==============================================================================
Refreshes all market data in the background every 1 hour.
Updates PostgreSQL database silently with ZERO user impact.
==============================================================================
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from concurrent.futures import ThreadPoolExecutor, as_completed
import structlog

# Add parent directory to path to import preloader modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.preloader.main import (
    DataSource,
    Config,
    DatabaseManager,
    CacheManager,
    YahooFinanceFetcher,
    FREDFetcher,
    AlphaVantageFetcher,
    TwelveDataFetcher,
    FinnhubFetcher,
    PolygonFetcher,
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()


class RefreshConfig:
    """Configuration for background refresh service"""

    # Refresh interval in seconds (default 1 hour)
    REFRESH_INTERVAL = int(os.getenv('REFRESH_INTERVAL', '3600'))

    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://spartan_user:spartan_pass_2025@postgres:5432/spartan_research')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

    # Parallel processing
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '10'))

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    # Success threshold
    SUCCESS_THRESHOLD = int(os.getenv('SUCCESS_THRESHOLD', '90'))  # Minimum success rate

    # Alert configuration
    ALERT_ON_FAILURE = os.getenv('ALERT_ON_FAILURE', 'true').lower() == 'true'
    ALERT_EMAIL = os.getenv('ALERT_EMAIL', '')

    # Data sources (same as preloader)
    DATA_SOURCES = Config.DATA_SOURCES


class RefreshStats:
    """Track refresh statistics"""

    def __init__(self):
        self.total_sources = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.total_rows_updated = 0
        self.start_time = None
        self.end_time = None
        self.errors: List[Dict] = []

    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_sources == 0:
            return 0.0
        return (self.successful / self.total_sources) * 100

    def duration_seconds(self) -> float:
        """Calculate refresh duration"""
        if not self.start_time or not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict:
        """Convert stats to dictionary"""
        return {
            'total_sources': self.total_sources,
            'successful': self.successful,
            'failed': self.failed,
            'skipped': self.skipped,
            'total_rows_updated': self.total_rows_updated,
            'success_rate': self.success_rate(),
            'duration_seconds': self.duration_seconds(),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'errors': self.errors,
        }


class BackgroundRefreshService:
    """Background service that refreshes market data every hour"""

    def __init__(self):
        self.config = RefreshConfig()
        self.db_manager = DatabaseManager()
        self.cache_manager = CacheManager()
        self.stats = RefreshStats()
        self.last_refresh_time = None
        self.refresh_count = 0

        logger.info("background_refresh_service_initialized",
                   refresh_interval=self.config.REFRESH_INTERVAL,
                   max_workers=self.config.MAX_WORKERS,
                   success_threshold=self.config.SUCCESS_THRESHOLD)

    def wait_for_dependencies(self):
        """Wait for PostgreSQL and Redis to be ready"""
        logger.info("waiting_for_dependencies")

        # Wait for PostgreSQL
        max_retries = 30
        for i in range(max_retries):
            try:
                conn = psycopg2.connect(self.config.DATABASE_URL)
                conn.close()
                logger.info("postgresql_ready")
                break
            except psycopg2.OperationalError:
                if i == max_retries - 1:
                    logger.error("postgresql_not_ready_after_retries", retries=max_retries)
                    raise
                time.sleep(2)

        # Wait for Redis
        for i in range(max_retries):
            try:
                r = redis.from_url(self.config.REDIS_URL)
                r.ping()
                logger.info("redis_ready")
                break
            except redis.ConnectionError:
                if i == max_retries - 1:
                    logger.error("redis_not_ready_after_retries", retries=max_retries)
                    raise
                time.sleep(1)

    def fetch_source(self, source: DataSource) -> Dict:
        """Fetch data from a single source"""
        if not source.enabled:
            logger.info("source_skipped_disabled", source_id=source.id)
            return {
                'source_id': source.id,
                'success': False,
                'skipped': True,
                'rows_updated': 0,
                'error': 'Source disabled'
            }

        logger.info("fetching_source", source_id=source.id, source_name=source.name)
        start_time = datetime.now()

        try:
            # Select appropriate fetcher based on source
            fetcher = None
            data = None

            if 'yahoo' in source.id.lower():
                fetcher = YahooFinanceFetcher()
                if source.category == 'stocks':
                    data = fetcher.fetch_quotes(source.symbols or [])
                elif source.category == 'forex':
                    data = fetcher.fetch_forex(source.symbols or [])
                elif source.category == 'crypto':
                    data = fetcher.fetch_crypto(source.symbols or [])
                elif source.category == 'commodities':
                    data = fetcher.fetch_commodities(source.symbols or [])

            elif 'fred' in source.id.lower():
                fetcher = FREDFetcher()
                data = fetcher.fetch_series(source.symbols or [])

            elif 'polygon' in source.id.lower():
                fetcher = PolygonFetcher()
                data = fetcher.fetch_quotes(source.symbols or [])

            elif 'alpha_vantage' in source.id.lower():
                fetcher = AlphaVantageFetcher()
                data = fetcher.fetch_quotes(source.symbols or [])

            elif 'twelve_data' in source.id.lower():
                fetcher = TwelveDataFetcher()
                data = fetcher.fetch_quotes(source.symbols or [])

            elif 'finnhub' in source.id.lower():
                fetcher = FinnhubFetcher()
                data = fetcher.fetch_quotes(source.symbols or [])

            else:
                logger.warning("no_fetcher_for_source", source_id=source.id)
                return {
                    'source_id': source.id,
                    'success': False,
                    'skipped': True,
                    'rows_updated': 0,
                    'error': 'No fetcher available'
                }

            # Insert data into database
            if data and len(data) > 0:
                rows_inserted = self.db_manager.insert_market_data(source.category, data)

                # Update health status
                response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                self.db_manager.update_health_status(
                    source.id,
                    success=True,
                    response_time_ms=response_time_ms,
                    error=None
                )

                logger.info("source_fetched_successfully",
                           source_id=source.id,
                           rows_updated=rows_inserted,
                           response_time_ms=response_time_ms)

                return {
                    'source_id': source.id,
                    'success': True,
                    'skipped': False,
                    'rows_updated': rows_inserted,
                    'response_time_ms': response_time_ms,
                }
            else:
                logger.warning("source_returned_no_data", source_id=source.id)
                self.db_manager.update_health_status(
                    source.id,
                    success=False,
                    response_time_ms=0,
                    error='No data returned'
                )
                return {
                    'source_id': source.id,
                    'success': False,
                    'skipped': False,
                    'rows_updated': 0,
                    'error': 'No data returned'
                }

        except Exception as e:
            logger.error("source_fetch_failed",
                        source_id=source.id,
                        error=str(e),
                        exc_info=True)

            # Update health status with error
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.db_manager.update_health_status(
                source.id,
                success=False,
                response_time_ms=response_time_ms,
                error=str(e)
            )

            return {
                'source_id': source.id,
                'success': False,
                'skipped': False,
                'rows_updated': 0,
                'error': str(e)
            }

    def refresh_all_data(self):
        """Refresh all data sources in parallel"""
        logger.info("starting_refresh_cycle",
                   refresh_count=self.refresh_count,
                   total_sources=len(self.config.DATA_SOURCES))

        # Reset stats
        self.stats = RefreshStats()
        self.stats.start_time = datetime.now()
        self.stats.total_sources = len(self.config.DATA_SOURCES)

        # Update Redis with refresh status
        r = redis.from_url(self.config.REDIS_URL)
        r.hset('refresh:status', mapping={
            'in_progress': 'true',
            'started_at': self.stats.start_time.isoformat(),
            'total_sources': self.stats.total_sources,
        })

        # Fetch all sources in parallel
        with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
            future_to_source = {
                executor.submit(self.fetch_source, source): source
                for source in self.config.DATA_SOURCES
            }

            for future in as_completed(future_to_source):
                result = future.result()

                if result.get('skipped'):
                    self.stats.skipped += 1
                elif result.get('success'):
                    self.stats.successful += 1
                    self.stats.total_rows_updated += result.get('rows_updated', 0)
                else:
                    self.stats.failed += 1
                    self.stats.errors.append({
                        'source_id': result['source_id'],
                        'error': result.get('error', 'Unknown error')
                    })

                # Update progress in Redis
                r.hset('refresh:status', mapping={
                    'completed_sources': self.stats.successful + self.stats.failed + self.stats.skipped,
                    'successful_sources': self.stats.successful,
                    'failed_sources': self.stats.failed,
                })

        self.stats.end_time = datetime.now()

        # Update Redis with final status
        r.hset('refresh:status', mapping={
            'in_progress': 'false',
            'completed_at': self.stats.end_time.isoformat(),
            'success_rate': f"{self.stats.success_rate():.2f}",
            'duration_seconds': f"{self.stats.duration_seconds():.2f}",
            'total_rows_updated': self.stats.total_rows_updated,
        })

        # Store stats in Redis (for monitoring)
        r.set(
            f"refresh:history:{self.stats.end_time.isoformat()}",
            str(self.stats.to_dict()),
            ex=86400 * 7  # Keep for 7 days
        )

        logger.info("refresh_cycle_completed",
                   **self.stats.to_dict())

        # Check if we met success threshold
        if self.stats.success_rate() < self.config.SUCCESS_THRESHOLD:
            logger.warning("refresh_below_success_threshold",
                          success_rate=self.stats.success_rate(),
                          threshold=self.config.SUCCESS_THRESHOLD,
                          failed_sources=len(self.stats.errors))

            if self.config.ALERT_ON_FAILURE:
                self.send_alert()

        self.last_refresh_time = self.stats.end_time
        self.refresh_count += 1

    def send_alert(self):
        """Send alert on refresh failure"""
        # TODO: Implement email/Twilio alerts
        logger.error("refresh_failed_alert",
                    success_rate=self.stats.success_rate(),
                    errors=self.stats.errors)

    def run(self):
        """Main run loop - refreshes every hour"""
        logger.info("background_refresh_service_starting")

        # Wait for dependencies
        self.wait_for_dependencies()

        logger.info("background_refresh_service_ready",
                   refresh_interval_minutes=self.config.REFRESH_INTERVAL / 60)

        # Main loop
        while True:
            try:
                # Perform refresh
                self.refresh_all_data()

                # Calculate next refresh time
                next_refresh = datetime.now() + timedelta(seconds=self.config.REFRESH_INTERVAL)
                logger.info("refresh_scheduled",
                           next_refresh=next_refresh.isoformat(),
                           wait_seconds=self.config.REFRESH_INTERVAL)

                # Sleep until next refresh
                time.sleep(self.config.REFRESH_INTERVAL)

            except KeyboardInterrupt:
                logger.info("background_refresh_service_interrupted")
                break

            except Exception as e:
                logger.error("refresh_cycle_error",
                           error=str(e),
                           exc_info=True)

                # Wait before retrying
                logger.info("waiting_before_retry", wait_seconds=60)
                time.sleep(60)


def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           SPARTAN RESEARCH STATION                           ║
║           Background Refresh Service                          ║
║                                                               ║
║  Refresh Interval: 1 hour                                    ║
║  Silent Updates: Zero user impact                            ║
║  Database-First: PostgreSQL + Redis cache                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    service = BackgroundRefreshService()
    service.run()


if __name__ == '__main__':
    main()
