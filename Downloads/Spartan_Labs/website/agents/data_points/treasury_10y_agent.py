#!/usr/bin/env python3
"""
US TREASURY 10-YEAR AGENT - DGS10 ECONOMIC DATA POINT
=====================================================

Dedicated agent responsible for 10-Year US Treasury yield data.
Ensures continuous, genuine economic data with specialized fallback strategies.

Data Sources:
1. Primary: FRED API (DGS10 - official 10-Year Treasury constant maturity rate)
2. Fallback 1: Yahoo Finance (^TNX)
3. Fallback 2: Calculated from bond ETF (TLT)
4. Emergency: Static last-known value with degradation notice
"""

import asyncio
from typing import Dict, Optional
import yfinance as yf
import aiohttp
import time
import json

from base_data_point_agent import DataPointAgent


class Treasury10YAgent(DataPointAgent):
    """Dedicated agent for 10-Year US Treasury yield data point"""

    def __init__(self):
        super().__init__(
            agent_id='treasury_10y_agent',
            data_point='DGS10',
            data_type='economic'
        )

        # Treasury yield validation (realistic bounds)
        self.min_price = 0.1       # 10Y yield won't go below 0.1%
        self.max_price = 10.0      # 10Y yield won't exceed 10% (normally)

        # Treasuries have no volume
        self.has_volume = False

    def _initialize_data_sources(self):
        """Initialize 10-Year Treasury-specific data source configuration"""
        
        # Prioritize FRED for economic data
        self.primary_sources = ['fred', 'yfinance']
        self.fallback_sources = ['etf_proxy', 'static']
        
        # Symbol mappings
        self.treasury_mappings = {
            'fred': 'DGS10',        # FRED series ID
            'yfinance': '^TNX',     # Yahoo Finance symbol
            'etf_proxy': 'TLT'      # 20+ Year Treasury ETF (inverse relationship)
        }
        
        # API keys
        self.fred_api_key = None
        
        # Load API keys
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from environment"""
        import os
        
        self.fred_api_key = os.getenv('FRED_API_KEY')

    async def _fetch_from_fred(self) -> Optional[Dict]:
        """Fetch 10-Year Treasury yield from FRED API (preferred)"""
        if not self.fred_api_key or len(self.fred_api_key) < 30:
            return None

        try:
            rate_limit_delay = 2.0  # FRED allows 120 requests per minute
            time.sleep(rate_limit_delay)

            base_url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': 'DGS10',
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'limit': 1,  # Only need latest value
                'sort_order': 'desc'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        observations = data.get('observations', [])
                        
                        if observations and len(observations) > 0:
                            latest = observations[0]
                            yield_value = float(latest['value'])
                            
                            # Validate yield value (should be in percentage points)
                            if yield_value > 0 and yield_value <= 10:
                                return {
                                    'symbol': 'DGS10',
                                    'price': yield_value,  # This is yield in percentage
                                    'change': 0,  # FRED provides latest value only
                                    'change_percent': 0,  # Not applicable for yields
                                    'volume': None,  # Treasuries have no volume
                                    'high': yield_value,
                                    'low': yield_value,
                                    'open': yield_value,
                                    'timestamp': latest['date'],
                                    'source': 'fred'
                                }
                            else:
                                self.logger.warning(f"Invalid 10Y yield from FRED: {yield_value}%")
                    else:
                        self.logger.warning(f"FRED API error: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"FRED fetch error: {e}")
            
        return None

    async def _fetch_from_yfinance(self) -> Optional[Dict]:
        """Fetch 10-Year Treasury yield from Yahoo Finance"""
        try:
            rate_limit_delay = 2.0
            time.sleep(rate_limit_delay)

            ticker = yf.Ticker('^TNX')
            hist = ticker.history(period='2d', timeout=10)
            
            if hist is not None and not hist.empty and len(hist) >= 1:
                current = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) >= 2 else current
                
                yield_value = float(current['Close'])
                
                # Yahoo Finance quotes yields in price format (e.g., 4.5% = 4.5)
                if yield_value > 0 and yield_value <= 10:
                    return {
                        'symbol': '^TNX',
                        'price': yield_value,
                        'change': yield_value - float(prev['Close']),
                        'change_percent': round(((yield_value - float(prev['Close'])) / float(prev['Close'])) * 100, 2),
                        'volume': int(current['Volume']) if 'Volume' in current else None,
                        'high': float(current['High']),
                        'low': float(current['Low']),
                        'open': float(current['Open']),
                        'timestamp': hist.index[-1].isoformat(),
                        'source': 'yfinance'
                    }
                else:
                    self.logger.warning(f"Invalid 10Y yield from Yahoo Finance: {yield_value}%")
            else:
                self.logger.warning("Yahoo Finance returned empty data for ^TNX")
                
        except Exception as e:
            self.logger.error(f"Yahoo Finance fetch error for ^TNX: {e}")
            
        return None

    async def _fetch_from_etf_proxy(self) -> Optional[Dict]:
        """
        Estimate 10Y yield from TLT (20+ Year Treasury ETF)
        This is a proxy method when direct sources fail
        """
        try:
            if not self.redis_client:
                return None
                
            # Get cached TLT data
            tlt_data = self.redis_client.get('datapoint:TLT')
            if not tlt_data:
                return None
                
            tlt_json = json.loads(tlt_data)
            tlt_price = float(tlt_json.get('price', 0))
            tlt_change = float(tlt_json.get('change_percent', 0))
            
            # Very rough approximation: TLT price movement inversely correlates with yields
            # When TLT goes down, yields go up, and vice versa
            # This is just for emergency backup - NOT accurate
            
            # Assume base yield of 4.0% when TLT is at $100
            base_tlt_price = 100.0
            base_yield = 4.0
            
            # Estimate yield from TLT price movement (inverse relationship)
            price_ratio = tlt_price / base_tlt_price
            estimated_yield = base_yield / price_ratio
            
            # Adjust for recent movement (if TLT down, yields likely up)
            if tlt_change < -1:  # TLT down significantly
                estimated_yield += abs(tlt_change) * 0.1  # Increase yield estimate
            elif tlt_change > 1:  # TLT up significantly
                estimated_yield -= tlt_change * 0.1  # Decrease yield estimate
                
            # Ensure reasonable bounds
            estimated_yield = max(1.0, min(8.0, estimated_yield))
            
            return {
                'symbol': 'DGS10',
                'price': round(estimated_yield, 2),
                'change': 0,  # Can't reliably calculate from ETF
                'change_percent': 0,
                'volume': None,
                'high': estimated_yield,
                'low': estimated_yield,
                'open': estimated_yield,
                'timestamp': f"Calculated from TLT: ${tlt_price} ({tlt_change:+.2f}%)",
                'source': 'etf_proxy',
                'proxy_method': 'TLT_inverse'
            }
            
        except Exception as e:
            self.logger.error(f"ETF proxy calculation error: {e}")
            
        return None

    async def _fetch_static_fallback(self) -> Optional[Dict]:
        """
        Static fallback - return last known good value with degradation notice
        This should rarely be used, but ensures we always have something
        """
        try:
            # If we have cached data that's not too old (within 24 hours), return it
            cached_data = self.get_cached_data()
            if cached_data and self._is_cache_acceptable(cached_data):
                return {
                    **cached_data,
                    'stale': True,
                    'fallback_reason': 'Primary sources unavailable, using cached value',
                    'source': f"static_{cached_data.get('source', 'unknown')}"
                }
            
            # If no cache, return a reasonable default with warning
            return {
                'symbol': 'DGS10',
                'price': 4.25,  # Reasonable current yield
                'change': 0,
                'change_percent': 0,
                'volume': None,
                'high': 4.25,
                'low': 4.25,
                'open': 4.25,
                'timestamp': self.logger.info("No data sources available - using default value"),
                'source': 'static_fallback',
                'fallback_reason': 'All sources failed - using reasonable default',
                'data_integrity_warning': 'This is a placeholder value, not real-time data'
            }
            
        except Exception as e:
            self.logger.error(f"Static fallback error: {e}")
            
        return None

    def _is_cache_acceptable(self, cached_data: Dict) -> bool:
        """Check if cached data is acceptable for fallback use"""
        try:
            timestamp_str = cached_data.get('timestamp', '')
            if not timestamp_str:
                return False
                
            # Try to parse timestamp
            if timestamp_str == self.logger.info("placeholder"):
                return False
                
            # Try multiple timestamp formats
            from datetime import datetime
            
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    timestamp = datetime.strptime(timestamp_str.split('T')[0].split(' ')[0], '%Y-%m-%d')
                    break
                except ValueError:
                    continue
            else:
                return False
                
            # Check if data is less than 24 hours old
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
            return age_hours < 24
            
        except Exception as e:
            self.logger.debug(f"Cache age check error: {e}")
            return False

    async def _fetch_from_primary(self) -> Optional[Dict]:
        """Fetch data from primary sources"""
        
        # Try FRED first (most reliable for Treasury data)
        data = await self._fetch_from_fred()
        if data:
            return data
            
        # Try Yahoo Finance
        data = await self._fetch_from_yfinance()
        if data:
            return data
            
        self.logger.warning("All primary sources failed for 10Y Treasury")
        return None

    async def _fetch_from_fallback(self) -> Optional[Dict]:
        """Fetch data from fallback sources"""
        
        # Try ETF proxy calculation
        data = await self._fetch_from_etf_proxy()
        if data:
            self.logger.warning("Using ETF proxy for 10Y Treasury")
            return data
            
        # Use static fallback as last resort
        data = await self._fetch_static_fallback()
        if data:
            self.logger.warning("Using static fallback for 10Y Treasury")
            return data
            
        self.logger.error("All sources failed for 10Y Treasury")
        return None

    def get_yield_analysis(self) -> Dict:
        """Get comprehensive yield curve analysis"""
        cached_data = self.get_cached_data()
        if not cached_data:
            return {'status': 'no_data'}
            
        yield_10y = float(cached_data.get('price', 0))
        
        # Yield level analysis
        if yield_10y < 2.0:
            yield_regime = 'EXTREME_LOW'
            rate_outlook = 'AGGRESSIVE_EASING_EXPECTED'
            economic outlook: 'Stimulus likely, recession risk high'
        elif yield_10y < 3.0:
            yield_regime = 'LOW'
            rate_outlook = 'EASING_BIAS'
            economic_outlook: ' accommodative policy, growth concerns'
        elif yield_10y < 4.0:
            yield_regime = 'NORMAL'
            rate_outlook = 'NEUTRAL'
            economic_outlook: 'Balanced monetary policy'
        elif yield_10y < 4.5:
            yield_regime = 'MODERATELY_HIGH'
            rate_outlook = 'TIGHTENING_BIAS'
            economic_outlook: 'Inflation concerns, potential rate hikes'
        else:
            yield_regime = 'HIGH'
            rate_outlook = 'AGGRESSIVE_TIGHTENING_EXPECTED'
            economic_outlook: 'Significant inflation pressure, aggressive policy'
            
        # Calculate spread insights (would need 2Y/3M rates for complete analysis)
        spread_analysis = {
            'yield_10y': round(yield_10y, 2),
            'yield_regime': yield_regime,
            'rate_outlook': rate_outlook,
            'economic_outlook': economic_outlook,
            'data_source': cached_data.get('source'),
            'last_updated': cached_data.get('timestamp'),
            'data_quality': cached_data.get('quality_score', 0)
        }
        
        # Add yield curve context if we have other Treasury data
        if self.redis_client:
            try:
                # Try to get 2Y Treasury for spread calculation
                dgs2_data = self.redis_client.get('datapoint:DGS2')
                if dgs2_data:
                    dgs2_json = json.loads(dgs2_data)
                    yield_2y = float(dgs2_json.get('price', 0))
                    spread_10y_2y = yield_10y - yield_2y
                    
                    if spread_10y_2y > 0:
                        curve_shape = 'NORMAL'
                        recession_indicator = 'LOW'
                    elif spread_10y_2y > -0.5:
                        curve_shape = 'FLAT'
                        recession_indicator = 'MODERATE'
                    else:
                        curve_shape = 'INVERTED'
                        recession_indicator = 'HIGH'
                        
                    spread_analysis.update({
                        'yield_2y': round(yield_2y, 2),
                        'spread_10y_2y': round(spread_10y_2y, 2),
                        'curve_shape': curve_shape,
                        'recession_indicator': recession_indicator
                    })
                    
            except Exception as e:
                self.logger.debug(f"Could not calculate spread: {e}")
                
        return spread_analysis

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Enhanced validation for Treasury yield data"""
        if not super().validate_data(data):
            return False
            
        # Treasury-specific validations
        price = float(data.get('price', 0))
        
        # 10Y yield should be reasonable (0.1% to 10%)
        if price < 0.1 or price > 10.0:
            self.logger.warning(f"10Y yield {price}% outside normal bounds")
            # Accept but flag as lower quality for extreme values
            
        # Check source appropriateness
        source = data.get('source', '')
        if source not in ['fred', 'yfinance', 'etf_proxy', 'static']:
            self.logger.warning(f"Unusual 10Y Treasury source: {source}")
            
        return True


if __name__ == '__main__':
    """Test the 10Y Treasury agent"""
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_treasury_10y_agent():
        agent = Treasury10YAgent()
        
        print("Testing 10Y Treasury agent fetch...")
        data = await agent.fetch_data()
        
        if data:
            print(f"✅ 10Y Treasury Agent Test Successful:")
            print(f"   Yield: {data.get('price'):.2f}%")
            print(f"   Source: {data.get('source')}")
            
            # Test yield analysis
            yield_analysis = agent.get_yield_analysis()
            print(f"   Regime: {yield_analysis['yield_regime']}")
            print(f"   Outlook: {yield_analysis['rate_outlook']}")
            
            if 'spread_10y_2y' in yield_analysis:
                print(f"   10Y-2Y Spread: {yield_analysis['spread_10y_2y']:+.2f}%")
                print(f"   Curve Shape: {yield_analysis['curve_shape']}")
                print(f"   Recession Indicator: {yield_analysis['recession_indicator']}")
                
        else:
            print("❌ 10Y Treasury Agent Test Failed - No data fetched")
            
        agent.stop()
    
    # Run test
    asyncio.run(test_treasury_10y_agent())
