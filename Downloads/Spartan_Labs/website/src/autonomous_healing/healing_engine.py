#!/usr/bin/env python3
"""
SPARTAN LABS - AUTONOMOUS HEALING ENGINE
=========================================

Automatically fixes errors BEFORE users notice them.
Implements NESTED learning approach for intelligent self-healing.

Healing Strategies (OUTER LAYER - General):
1. Retry with exponential backoff
2. Switch to fallback data source
3. Use cached data
4. Rotate API keys
5. Reduce request size

Source-Specific Fixes (INNER LAYER):
- FRED: Switch series, use aggregates
- Yahoo Finance: Use ETF proxies, alternate symbols
- Polygon.io: Downgrade to free tier, use daily instead of intraday
- Alpha Vantage: Cache aggressively, batch requests

Author: Spartan Labs
Version: 1.0.0
"""

import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging
import json

from error_monitor import (
    ErrorEvent, ErrorType, DataSource, HealthStatus,
    ErrorDetectionEngine
)

logger = logging.getLogger(__name__)


@dataclass
class HealingStrategy:
    """Represents a healing strategy with success tracking."""
    name: str
    description: str
    apply_func: Callable
    source: Optional[DataSource]
    error_types: List[ErrorType]
    priority: int  # Lower = higher priority
    success_count: int = 0
    failure_count: int = 0
    avg_fix_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate of this strategy."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0


@dataclass
class HealingResult:
    """Result of healing attempt."""
    success: bool
    strategy_used: str
    fix_time: float
    fallback_used: bool
    data_retrieved: Optional[Any]
    error_message: Optional[str]


class AutonomousHealingEngine:
    """
    Core autonomous healing engine with NESTED learning.

    OUTER LAYER: General healing strategies (slow updates)
    - Retry logic
    - Fallback chains
    - Cache utilization

    INNER LAYER: Source-specific fixes (fast updates)
    - API-specific workarounds
    - Dynamic parameter adjustment
    - Learned optimal sequences
    """

    def __init__(self, error_monitor: ErrorDetectionEngine):
        self.error_monitor = error_monitor
        self.cache = {}  # Emergency cache
        self.cache_ttl = timedelta(hours=1)

        # API key rotation pools
        self.api_key_pools = {
            DataSource.FRED_API: [],
            DataSource.ALPHA_VANTAGE: [],
            DataSource.POLYGON_IO: [],
        }

        # OUTER LAYER: General healing strategies
        self.general_strategies = [
            HealingStrategy(
                name="exponential_backoff_retry",
                description="Retry with exponential backoff",
                apply_func=self._retry_with_backoff,
                source=None,  # Applies to all sources
                error_types=[ErrorType.TIMEOUT, ErrorType.NETWORK_ERROR],
                priority=1,
            ),
            HealingStrategy(
                name="use_cached_data",
                description="Return cached data if available",
                apply_func=self._use_cached_data,
                source=None,
                error_types=[ErrorType.RATE_LIMIT, ErrorType.SERVER_ERROR, ErrorType.TIMEOUT],
                priority=2,
            ),
            HealingStrategy(
                name="reduce_request_size",
                description="Reduce request size/complexity",
                apply_func=self._reduce_request_size,
                source=None,
                error_types=[ErrorType.TIMEOUT, ErrorType.SERVER_ERROR],
                priority=3,
            ),
        ]

        # INNER LAYER: Source-specific healing strategies
        self.source_strategies = {
            DataSource.YAHOO_FINANCE: [
                HealingStrategy(
                    name="yahoo_use_etf_proxy",
                    description="Use ETF proxy for failed ticker",
                    apply_func=self._yahoo_use_etf_proxy,
                    source=DataSource.YAHOO_FINANCE,
                    error_types=[ErrorType.INVALID_DATA, ErrorType.MISSING_DATA],
                    priority=1,
                ),
                HealingStrategy(
                    name="yahoo_alternate_endpoint",
                    description="Switch to alternate Yahoo endpoint",
                    apply_func=self._yahoo_alternate_endpoint,
                    source=DataSource.YAHOO_FINANCE,
                    error_types=[ErrorType.TIMEOUT, ErrorType.SERVER_ERROR],
                    priority=2,
                ),
            ],
            DataSource.FRED_API: [
                HealingStrategy(
                    name="fred_rotate_api_key",
                    description="Rotate to backup FRED API key",
                    apply_func=self._fred_rotate_key,
                    source=DataSource.FRED_API,
                    error_types=[ErrorType.RATE_LIMIT, ErrorType.AUTH_ERROR],
                    priority=1,
                ),
                HealingStrategy(
                    name="fred_use_alternate_series",
                    description="Use alternate FRED series",
                    apply_func=self._fred_alternate_series,
                    source=DataSource.FRED_API,
                    error_types=[ErrorType.INVALID_DATA, ErrorType.MISSING_DATA],
                    priority=2,
                ),
                HealingStrategy(
                    name="fred_batch_request",
                    description="Batch multiple FRED requests",
                    apply_func=self._fred_batch_requests,
                    source=DataSource.FRED_API,
                    error_types=[ErrorType.RATE_LIMIT],
                    priority=3,
                ),
            ],
            DataSource.POLYGON_IO: [
                HealingStrategy(
                    name="polygon_fallback_to_yahoo",
                    description="Fallback from Polygon to Yahoo",
                    apply_func=self._polygon_fallback_yahoo,
                    source=DataSource.POLYGON_IO,
                    error_types=[ErrorType.RATE_LIMIT, ErrorType.AUTH_ERROR, ErrorType.QUOTA_EXCEEDED],
                    priority=1,
                ),
                HealingStrategy(
                    name="polygon_use_daily",
                    description="Use daily data instead of intraday",
                    apply_func=self._polygon_use_daily,
                    source=DataSource.POLYGON_IO,
                    error_types=[ErrorType.RATE_LIMIT],
                    priority=2,
                ),
            ],
            DataSource.ALPHA_VANTAGE: [
                HealingStrategy(
                    name="alphavantage_aggressive_cache",
                    description="Use aggressive caching (24h TTL)",
                    apply_func=self._alphavantage_aggressive_cache,
                    source=DataSource.ALPHA_VANTAGE,
                    error_types=[ErrorType.RATE_LIMIT, ErrorType.QUOTA_EXCEEDED],
                    priority=1,
                ),
                HealingStrategy(
                    name="alphavantage_fallback",
                    description="Fallback to Yahoo for Alpha Vantage data",
                    apply_func=self._alphavantage_fallback_yahoo,
                    source=DataSource.ALPHA_VANTAGE,
                    error_types=[ErrorType.RATE_LIMIT, ErrorType.QUOTA_EXCEEDED],
                    priority=2,
                ),
            ],
        }

    async def heal_error(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> HealingResult:
        """
        Attempt to heal an error autonomously.

        Args:
            error: The detected error event
            original_request_func: Original async function that failed
            original_params: Original request parameters

        Returns:
            HealingResult with success status and retrieved data
        """
        start_time = time.time()

        logger.info(f"🔧 Attempting autonomous healing for {error.source.value}/{error.endpoint}")
        logger.info(f"   Error type: {error.error_type.value}")

        # Get applicable strategies
        strategies = self._get_applicable_strategies(error)

        # Sort by priority and success rate (NESTED learning)
        strategies.sort(key=lambda s: (s.priority, -s.success_rate))

        logger.info(f"   Found {len(strategies)} applicable strategies")

        # Try each strategy in order
        for strategy in strategies:
            logger.info(f"   Trying strategy: {strategy.name}")

            try:
                result = await strategy.apply_func(
                    error=error,
                    original_request_func=original_request_func,
                    original_params=original_params
                )

                fix_time = time.time() - start_time

                if result['success']:
                    # Update strategy success metrics (INNER LAYER learning)
                    strategy.success_count += 1
                    n = strategy.success_count + strategy.failure_count
                    strategy.avg_fix_time = (strategy.avg_fix_time * (n - 1) + fix_time) / n

                    # Update error event with fix details
                    error.fixed_automatically = True
                    error.fix_method = strategy.name
                    await self.error_monitor.record_error(error)

                    logger.info(f"✅ Healing successful using {strategy.name} ({fix_time:.2f}s)")

                    return HealingResult(
                        success=True,
                        strategy_used=strategy.name,
                        fix_time=fix_time,
                        fallback_used=result.get('fallback_used', False),
                        data_retrieved=result.get('data'),
                        error_message=None
                    )
                else:
                    strategy.failure_count += 1
                    logger.warning(f"   Strategy {strategy.name} failed")

            except Exception as e:
                strategy.failure_count += 1
                logger.error(f"   Strategy {strategy.name} raised exception: {e}")

        # All strategies failed
        fix_time = time.time() - start_time
        logger.error(f"❌ All healing strategies failed ({fix_time:.2f}s)")

        return HealingResult(
            success=False,
            strategy_used="none",
            fix_time=fix_time,
            fallback_used=False,
            data_retrieved=None,
            error_message="All healing strategies exhausted"
        )

    def _get_applicable_strategies(self, error: ErrorEvent) -> List[HealingStrategy]:
        """Get list of strategies applicable to this error."""
        strategies = []

        # Add general strategies
        for strategy in self.general_strategies:
            if error.error_type in strategy.error_types:
                strategies.append(strategy)

        # Add source-specific strategies
        if error.source in self.source_strategies:
            for strategy in self.source_strategies[error.source]:
                if error.error_type in strategy.error_types:
                    strategies.append(strategy)

        return strategies

    # ==================== GENERAL STRATEGIES (OUTER LAYER) ====================

    async def _retry_with_backoff(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Retry with exponential backoff."""
        max_retries = 3
        base_delay = 1.0

        for retry in range(max_retries):
            delay = base_delay * (2 ** retry)
            logger.info(f"   Retry {retry+1}/{max_retries} after {delay}s")
            await asyncio.sleep(delay)

            try:
                result = await original_request_func(**original_params)
                return {'success': True, 'data': result}
            except Exception as e:
                logger.warning(f"   Retry {retry+1} failed: {e}")

        return {'success': False}

    async def _use_cached_data(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return cached data if available."""
        cache_key = f"{error.source.value}_{error.endpoint}_{json.dumps(original_params, sort_keys=True)}"

        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            age = datetime.now() - timestamp

            if age < self.cache_ttl:
                logger.info(f"   Using cached data (age: {age.total_seconds():.0f}s)")
                return {'success': True, 'data': cached_data, 'fallback_used': True}

        return {'success': False}

    async def _reduce_request_size(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reduce request size/complexity."""
        # Reduce limit parameter if present
        if 'limit' in original_params and original_params['limit'] > 10:
            reduced_params = original_params.copy()
            reduced_params['limit'] = min(10, original_params['limit'] // 2)

            logger.info(f"   Reducing limit from {original_params['limit']} to {reduced_params['limit']}")

            try:
                result = await original_request_func(**reduced_params)
                return {'success': True, 'data': result}
            except Exception as e:
                logger.warning(f"   Reduced request failed: {e}")

        return {'success': False}

    # ==================== YAHOO FINANCE STRATEGIES ====================

    async def _yahoo_use_etf_proxy(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use ETF proxy for failed Yahoo Finance ticker."""
        # Map individual stocks to sector ETFs
        etf_proxies = {
            # Tech stocks → XLK
            'AAPL': 'XLK', 'MSFT': 'XLK', 'GOOGL': 'XLK', 'AMZN': 'XLK', 'NVDA': 'XLK',
            # Financial stocks → XLF
            'JPM': 'XLF', 'BAC': 'XLF', 'WFC': 'XLF', 'GS': 'XLF',
            # Energy stocks → XLE
            'XOM': 'XLE', 'CVX': 'XLE', 'COP': 'XLE',
            # Healthcare stocks → XLV
            'JNJ': 'XLV', 'UNH': 'XLV', 'PFE': 'XLV',
        }

        symbol = original_params.get('symbol') or original_params.get('symbols', [''])[0]

        if symbol in etf_proxies:
            proxy_symbol = etf_proxies[symbol]
            logger.info(f"   Using ETF proxy {proxy_symbol} for {symbol}")

            proxy_params = original_params.copy()
            if 'symbol' in proxy_params:
                proxy_params['symbol'] = proxy_symbol
            if 'symbols' in proxy_params:
                proxy_params['symbols'] = [proxy_symbol]

            try:
                result = await original_request_func(**proxy_params)
                return {'success': True, 'data': result, 'fallback_used': True}
            except Exception as e:
                logger.warning(f"   ETF proxy failed: {e}")

        return {'success': False}

    async def _yahoo_alternate_endpoint(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Switch to alternate Yahoo Finance endpoint."""
        # Yahoo has multiple endpoints: query1, query2
        # This would be implemented with actual endpoint switching logic
        logger.info("   Switching to alternate Yahoo endpoint")
        return {'success': False}  # Placeholder

    # ==================== FRED API STRATEGIES ====================

    async def _fred_rotate_key(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rotate to backup FRED API key."""
        if self.api_key_pools[DataSource.FRED_API]:
            backup_key = self.api_key_pools[DataSource.FRED_API][0]
            logger.info(f"   Rotating to backup FRED API key")

            rotated_params = original_params.copy()
            rotated_params['api_key'] = backup_key

            try:
                result = await original_request_func(**rotated_params)
                return {'success': True, 'data': result}
            except Exception as e:
                logger.warning(f"   Backup key failed: {e}")

        return {'success': False}

    async def _fred_alternate_series(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use alternate FRED series for same data."""
        # Map series to alternates
        alternate_series = {
            'DGS10': 'GS10',      # 10Y Treasury alternate
            'DGS2': 'GS2',        # 2Y Treasury alternate
            'VIXCLS': 'VIXCLS',   # Same (no alternate)
        }

        series_id = original_params.get('series_id')
        if series_id in alternate_series:
            alt_series = alternate_series[series_id]
            logger.info(f"   Using alternate FRED series {alt_series} for {series_id}")

            alt_params = original_params.copy()
            alt_params['series_id'] = alt_series

            try:
                result = await original_request_func(**alt_params)
                return {'success': True, 'data': result, 'fallback_used': True}
            except Exception as e:
                logger.warning(f"   Alternate series failed: {e}")

        return {'success': False}

    async def _fred_batch_requests(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Batch multiple FRED requests to reduce rate limit pressure."""
        # This would implement request queuing/batching
        logger.info("   Batching FRED requests")
        return {'success': False}  # Placeholder

    # ==================== POLYGON.IO STRATEGIES ====================

    async def _polygon_fallback_yahoo(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback from Polygon.io to Yahoo Finance."""
        logger.info("   Falling back from Polygon to Yahoo Finance")

        # Yahoo Finance fetch logic would go here
        # This is a placeholder showing the strategy
        return {'success': False, 'fallback_used': True}

    async def _polygon_use_daily(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use daily data instead of intraday to save API quota."""
        logger.info("   Switching from intraday to daily data")

        daily_params = original_params.copy()
        if 'timespan' in daily_params:
            daily_params['timespan'] = 'day'

        try:
            result = await original_request_func(**daily_params)
            return {'success': True, 'data': result}
        except Exception as e:
            logger.warning(f"   Daily data fallback failed: {e}")

        return {'success': False}

    # ==================== ALPHA VANTAGE STRATEGIES ====================

    async def _alphavantage_aggressive_cache(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use aggressive caching for Alpha Vantage (24h TTL)."""
        cache_key = f"alphavantage_{json.dumps(original_params, sort_keys=True)}"

        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            age = datetime.now() - timestamp

            if age < timedelta(hours=24):
                logger.info(f"   Using aggressive cache (age: {age.total_seconds()/3600:.1f}h)")
                return {'success': True, 'data': cached_data, 'fallback_used': True}

        return {'success': False}

    async def _alphavantage_fallback_yahoo(
        self,
        error: ErrorEvent,
        original_request_func: Callable,
        original_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback from Alpha Vantage to Yahoo Finance."""
        logger.info("   Falling back from Alpha Vantage to Yahoo Finance")
        return {'success': False, 'fallback_used': True}

    # ==================== LEARNING & OPTIMIZATION ====================

    def get_strategy_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all strategies (for NESTED learning)."""
        performance = {}

        for strategy in self.general_strategies:
            performance[strategy.name] = {
                'success_rate': strategy.success_rate,
                'success_count': strategy.success_count,
                'failure_count': strategy.failure_count,
                'avg_fix_time': strategy.avg_fix_time,
            }

        for source, strategies in self.source_strategies.items():
            for strategy in strategies:
                performance[strategy.name] = {
                    'success_rate': strategy.success_rate,
                    'success_count': strategy.success_count,
                    'failure_count': strategy.failure_count,
                    'avg_fix_time': strategy.avg_fix_time,
                }

        return performance

    async def update_cache(self, key: str, data: Any):
        """Update cache with new data."""
        self.cache[key] = (data, datetime.now())
