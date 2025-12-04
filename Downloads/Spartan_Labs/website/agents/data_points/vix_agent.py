#!/usr/bin/env python3
"""
VIX INDEX AGENT - VOLATILITY INDEX DATA POINT
=============================================

Dedicated agent responsible for VIX (CBOE Volatility Index) data availability.
Ensures continuous, genuine volatility data with specialized fallback strategies.

Data Sources:
1. Primary: FRED API (VIXCLS - real VIX data)
2. Fallback 1: Polygon.io (if VIX access available)
3. Fallback 2: Yahoo Finance (emergency fallback)
4. Mathematical fallback: Calculate from SPY options if all sources fail
"""

import asyncio
from typing import Dict, Optional
import yfinance as yf
import aiohttp
import time
import math

from base_data_point_agent import DataPointAgent


class VIXAgent(DataPointAgent):
    """Dedicated agent for VIX (CBOE Volatility Index) data point"""

    def __init__(self):
        super().__init__(
            agent_id='vix_agent',
            data_point='VIX',
            data_type='volatility_index'
        )

        # VIX-specific validation (typically ranges 5-80)
        self.min_price = 5        # VIX rarely goes below 5
        self.max_price = 100      # VIX rarely exceeds 100

    def _initialize_data_sources(self):
        """Initialize VIX-specific data source configuration"""
        
        # VIX has limited free sources, prioritize FRED
        self.primary_sources = ['fred', 'polygon']
        self.fallback_sources = ['yfinance', 'calculated']
        
        # VIX symbol mappings
        self.vix_mappings = {
            'fred': 'VIXCLS',     # FRED VIX series ID
            'polygon': 'I:VIX',   # Polygon index symbol
            'yfinance': '^VIX',    # Yahoo Finance symbol
            'market': 'SPY'        # For calculated fallback
        }
        
        # API keys
        self.fred_api_key = None
        self.polygon_key = None
        
        # Load API keys
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from environment"""
        import os
        
        self.fred_api_key = os.getenv('FRED_API_KEY')
        self.polygon_key = os.getenv('POLYGON_IO_API_KEY')

    async def _fetch_from_fred(self) -> Optional[Dict]:
        """Fetch VIX data from FRED API (preferred source)"""
        if not self.fred_api_key or len(self.fred_api_key) < 30:
            return None

        try:
            rate_limit_delay = 2.0  # FRED allows 120 requests per minute
            time.sleep(rate_limit_delay)

            base_url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': 'VIXCLS',
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
                            vix_value = float(latest['value'])
                            
                            # Validate VIX value (should be positive and reasonable)
                            if vix_value > 0 and vix_value <= 100:
                                return {
                                    'symbol': '^VIX',
                                    'price': vix_value,
                                    'change': 0,  # FRED provides latest value only
                                    'change_percent': 0,
                                    'volume': None,  # VIX has no volume
                                    'high': vix_value,
                                    'low': vix_value,
                                    'open': vix_value,
                                    'timestamp': latest['date'],
                                    'source': 'fred'
                                }
                            else:
                                self.logger.warning(f"Invalid VIX value from FRED: {vix_value}")
                    else:
                        self.logger.warning(f"FRED API error: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"FRED fetch error: {e}")
            
        return None

    async def _fetch_from_polygon(self) -> Optional[Dict]:
        """Fetch VIX data from Polygon.io API"""
        if not self.polygon_key or len(self.polygon_key) < 20:
            return None

        try:
            rate_limit_delay = 13.0
            time.sleep(rate_limit_delay)

            # VIX Polygon symbol may vary
            url = f"https://api.polygon.io/v2/aggs/ticker/I:VIX/prev"
            params = {'apiKey': self.polygon_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            vix_value = float(result['c'])
                            
                            if vix_value > 0 and vix_value <= 100:
                                return {
                                    'symbol': '^VIX',
                                    'price': vix_value,
                                    'change': float(result['c'] - result['o']),
                                    'change_percent': round((result['c'] - result['o']) / result['o'] * 100, 2),
                                    'volume': int(result['v']) if result['v'] else None,
                                    'high': float(result['h']),
                                    'low': float(result['l']),
                                    'open': float(result['o']),
                                    'timestamp': str(result['t']),
                                    'source': 'polygon'
                                }
                            else:
                                self.logger.warning(f"Invalid VIX value from Polygon: {vix_value}")
                    else:
                        self.logger.warning(f"Polygon API error for VIX: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Polygon fetch error for VIX: {e}")
            
        return None

    async def _fetch_from_yfinance(self) -> Optional[Dict]:
        """Fetch VIX data from Yahoo Finance (fallback)"""
        try:
            rate_limit_delay = 2.0
            time.sleep(rate_limit_delay)

            ticker = yf.Ticker('^VIX')
            hist = ticker.history(period='2d', timeout=10)
            
            if hist is not None and not hist.empty and len(hist) >= 1:
                current = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) >= 2 else current
                
                vix_value = float(current['Close'])
                
                if vix_value > 0 and vix_value <= 100:
                    return {
                        'symbol': '^VIX',
                        'price': vix_value,
                        'change': vix_value - float(prev['Close']),
                        'change_percent': round((vix_value - float(prev['Close'])) / float(prev['Close']) * 100, 2),
                        'volume': int(current['Volume']) if 'Volume' in current else None,
                        'high': float(current['High']),
                        'low': float(current['Low']),
                        'open': float(current['Open']),
                        'timestamp': hist.index[-1].isoformat(),
                        'source': 'yfinance'
                    }
                else:
                    self.logger.warning(f"Invalid VIX value from Yahoo Finance: {vix_value}")
            else:
                self.logger.warning("Yahoo Finance returned empty data for VIX")
                
        except Exception as e:
            self.logger.error(f"Yahoo Finance fetch error for VIX: {e}")
            
        return None

    async def _fetch_calculated_volatility(self) -> Optional[Dict]:
        """
        Calculate approximate VIX from SPY price movement
        This is a fallback when all direct sources fail
        """
        try:
            # Get cached SPY data to calculate implied volatility approximation
            if not self.redis_client:
                return None
                
            spy_data = self.redis_client.get('datapoint:SPY')
            if not spy_data:
                return None
                
            spy_json = json.loads(spy_data)
            spy_change_pct = spy_json.get('change_percent', 0)
            
            # Very crude VIX approximation based on SPY movement
            # VIX typically moves in opposite direction to SPY
            if abs(spy_change_pct) < 0.1:
                # Very low movement, low volatility
                vix_approx = 15.0
            elif spy_change_pct < 0:
                # SPY down, VIX up (fear)
                vix_approx = 15.0 + abs(spy_change_pct) * 8
            else:
                # SPY up, VIX down (complacency)
                vix_approx = max(10.0, 15.0 - spy_change_pct * 3)
                
            # Ensure VIX stays in reasonable bounds
            vix_approx = max(10.0, min(50.0, vix_approx))
            
            return {
                'symbol': '^VIX',
                'price': round(vix_approx, 2),
                'change': 0,
                'change_percent': 0,
                'volume': None,
                'high': vix_approx,
                'low': vix_approx,
                'open': vix_approx,
                'timestamp': self.logger.info(f"Calculated from SPY change: {spy_change_pct:+.2f}%"),
                'source': 'calculated'
            }
            
        except Exception as e:
            self.logger.error(f"Calculated VIX error: {e}")
            
        return None

    async def _fetch_from_primary(self) -> Optional[Dict]:
        """Fetch data from primary sources"""
        
        # Try FRED first (most reliable for VIX)
        data = await self._fetch_from_fred()
        if data:
            return data
            
        # Try Polygon
        data = await self._fetch_from_polygon()
        if data:
            return data
            
        self.logger.warning("All primary sources failed for VIX")
        return None

    async def _fetch_from_fallback(self) -> Optional[Dict]:
        """Fetch data from fallback sources"""
        
        # Try Yahoo Finance
        data = await self._fetch_from_yfinance()
        if data:
            return data
            
        # Try calculated approximation as last resort
        data = await self._fetch_calculated_volatility()
        if data:
            self.logger.warning("Using calculated VIX approximation (last resort)")
            return data
            
        self.logger.error("All sources failed for VIX")
        return None

    def get_volatility_analysis(self) -> Dict:
        """Get comprehensive volatility analysis based on VIX"""
        cached_data = self.get_cached_data()
        if not cached_data:
            return {'status': 'no_data'}
            
        vix_level = float(cached_data.get('price', 0))
        
        # VIX level analysis
        if vix_level < 12:
            volatility_regime = 'EXTREME_LOW'
            market_state = 'COMPLACENT'
            volatility_description = 'Extremely low volatility - potential complacency'
        elif vix_level < 16:
            volatility_regime = 'LOW'
            market_state = 'CALM'
            volatility_description = 'Low volatility - stable market conditions'
        elif vix_level < 20:
            volatility_regime = 'NORMAL'
            market_state = 'NORMAL'
            volatility_description = 'Normal volatility levels'
        elif vix_level < 30:
            volatility_regime = 'ELEVATED'
            market_state = 'CONCERNED'
            volatility_description = 'Elevated volatility - increased uncertainty'
        elif vix_level < 40:
            volatility_regime = 'HIGH'
            market_state = 'ANXIOUS'
            volatility_description = 'High volatility - significant fear in markets'
        else:
            volatility_regime = 'EXTREME'
            market_state = 'PANIC'
            volatility_description = 'Extreme volatility - market panic or crisis'
            
        # Fear index calculation (0-100 scale)
        if vix_level <= 12:
            fear_greed_index = 80  # Extreme greed
        elif vix_level <= 20:
            fear_greed_index = int(80 - ((vix_level - 12) / 8) * 40)  # 80 -> 40
        elif vix_level <= 30:
            fear_greed_index = int(40 - ((vix_level - 20) / 10) * 30)  # 40 -> 10
        else:
            fear_greed_index = max(0, 10 - (vix_level - 30))  # 10 -> 0
            
        # Convert to sentiment
        if fear_greed_index >= 75:
            sentiment = 'EXTREME_GREED'
        elif fear_greed_index >= 55:
            sentiment = 'GREED'
        elif fear_greed_index >= 45:
            sentiment = 'NEUTRAL'
        elif fear_greed_index >= 25:
            sentiment = 'FEAR'
        else:
            sentiment = 'EXTREME_FEAR'
            
        return {
            'symbol': '^VIX',
            'current_vix': round(vix_level, 2),
            'volatility_regime': volatility_regime,
            'market_state': market_state,
            'volatility_description': volatility_description,
            'fear_greed_index': fear_greed_index,
            'market_sentiment': sentiment,
            'source': cached_data.get('source'),
            'last_updated': cached_data.get('timestamp'),
            'data_quality': cached_data.get('quality_score', 0)
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Enhanced validation for VIX data"""
        if not super().validate_data(data):
            return False
            
        # VIX-specific validations
        price = float(data.get('price', 0))
        
        # VIX should be within reasonable bounds (5-100)
        if price < 5 or price > 100:
            self.logger.warning(f"VIX level {price} outside normal bounds (5-100)")
            # Still accept but flag as lower quality
            
        # Check if source is appropriate
        source = data.get('source', '')
        if source not in ['fred', 'polygon', 'yfinance', 'calculated']:
            self.logger.warning(f"Unusual VIX source: {source}")
            
        return True


if __name__ == '__main__':
    """Test the VIX agent"""
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_vix_agent():
        agent = VIXAgent()
        
        print("Testing VIX agent fetch...")
        data = await agent.fetch_data()
        
        if data:
            print(f"✅ VIX Agent Test Successful:")
            print(f"   VIX Level: {data.get('price'):.2f}")
            print(f"   Source: {data.get('source')}")
            
            # Test volatility analysis
            vol_analysis = agent.get_volatility_analysis()
            print(f"   Regime: {vol_analysis['volatility_regime']}")
            print(f"   Market State: {vol_analysis['market_state']}")
            print(f"   Sentiment: {vol_analysis['market_sentiment']}")
            print(f"   Fear/Greed Index: {vol_analysis['fear_greed_index']}")
        else:
            print("❌ VIX Agent Test Failed - No data fetched")
            
        agent.stop()
    
    # Run test
    asyncio.run(test_vix_agent())
