#!/usr/bin/env python3
"""
SPY ETF AGENT - S&P 500 INDEX DATA POINT
==========================================

Dedicated agent responsible for SPY (S&P 500 ETF) data availability.
Ensures continuous, genuine data with specialized fallback strategies.

Data Sources:
1. Primary: Polygon.io (paid, most reliable for ETFs)
2. Primary: Yahoo Finance (free, excellent backup)
3. Fallback: Alpha Vantage (paid)
4. Fallback: Twelve Data (paid, rate limited)
5. Fallback: Finnhub (paid, reliable for major ETFs)
6. Emergency: Yahoo Finance (if all paid fail)
"""

import asyncio
from typing import Dict, Optional
import yfinance as yf
import aiohttp
import time
from decimal import Decimal

from base_data_point_agent import DataPointAgent


class SPYAgent(DataPointAgent):
    """Dedicated agent for SPY (S&P 500 ETF) data point"""

    def __init__(self):
        super().__init__(
            agent_id='spy_agent',
            data_point='SPY',
            data_type='etf'
        )

    def _initialize_data_sources(self):
        """Initialize SPY-specific data source configuration"""
        
        # SPY optimal API priority: Paid APIs first, Free APIs as backup
        self.primary_sources = ['polygon', 'yfinance', 'alpha_vantage']
        self.fallback_sources = ['twelve_data', 'finnhub']
        
        # SPY-specific configuration
        self.symbols = {
            'polygon': 'SPY',
            'yfinance': 'SPY',
            'alpha_vantage': 'SPY',
            'twelve_data': 'SPY',
            'finnhub': 'SPY'
        }
        
        # API keys (paid APIs)
        self.polygon_key = None
        self.alpha_vantage_key = None
        self.twelve_data_key = None
        self.finnhub_key = None
        
        # Load API keys
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from environment"""
        import os
        
        self.polygon_key = os.getenv('POLYGON_IO_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY') 
        self.twelve_data_key = os.getenv('TWELVE_DATA_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')

    async def _fetch_from_polygon(self) -> Optional[Dict]:
        """Fetch SPY data from Polygon.io API (PAID - highest quality)"""
        if not self.polygon_key or len(self.polygon_key) < 20:
            return None

        try:
            rate_limit_delay = 13.0  # Polygon free tier rate limit
            time.sleep(rate_limit_delay)

            url = f"https://api.polygon.io/v2/aggs/ticker/SPY/prev"
            params = {'apiKey': self.polygon_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            
                            return {
                                'symbol': 'SPY',
                                'price': float(result['c']),  # Close price
                                'change': float(result['c'] - result['o']),  # Change
                                'change_percent': round((result['c'] - result['o']) / result['o'] * 100, 2),
                                'volume': int(result['v']),
                                'high': float(result['h']),
                                'low': float(result['l']),
                                'open': float(result['o']),
                                'timestamp': str(result['t']),
                                'source': 'polygon'
                            }
                    else:
                        self.logger.warning(f"Polygon API error: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Polygon fetch error: {e}")
            
        return None

    async def _fetch_from_yfinance(self) -> Optional[Dict]:
        """Fetch SPY data from Yahoo Finance (FREE - reliable backup)"""
        try:
            rate_limit_delay = 1.0  # Conservative rate limiting for yfinance
            time.sleep(rate_limit_delay)

            ticker = yf.Ticker('SPY')
            hist = ticker.history(period='2d', timeout=15)
            
            if hist is not None and not hist.empty and len(hist) >= 1:
                current = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) >= 2 else current
                
                price = float(current['Close'])
                prev_price = float(prev['Close'])
                
                return {
                    'symbol': 'SPY',
                    'price': price,
                    'change': price - prev_price,
                    'change_percent': round((price - prev_price) / prev_price * 100, 2),
                    'volume': int(current['Volume']),
                    'high': float(current['High']),
                    'low': float(current['Low']),
                    'open': float(current['Open']),
                    'timestamp': hist.index[-1].isoformat(),
                    'source': 'yfinance'
                }
            else:
                self.logger.warning("Yahoo Finance returned empty data")
                
        except Exception as e:
            self.logger.error(f"Yahoo Finance fetch error: {e}")
            
        return None

    async def _fetch_from_twelve_data(self) -> Optional[Dict]:
        """Fetch SPY data from Twelve Data API"""
        if not self.twelve_data_key or len(self.twelve_data_key) < 20:
            return None

        try:
            rate_limit_delay = 60.0  # Twelve Data very rate limited
            time.sleep(rate_limit_delay)

            url = "https://api.twelvedata.com/quote"
            params = {
                'symbol': 'SPY',
                'apikey': self.twelve_data_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'close' in data and data.get('close'):
                            price = float(data['close'])
                            
                            return {
                                'symbol': 'SPY',
                                'price': price,
                                'change': float(data.get('change', 0)),
                                'change_percent': float(data.get('percent_change', 0)),
                                'volume': int(data.get('volume', 0)),
                                'high': float(data.get('fifty_two_week_high', 0)),
                                'low': float(data.get('fifty_two_week_low', 0)),
                                'timestamp': data.get('timestamp', ''),
                                'source': 'twelve_data'
                            }
                    else:
                        self.logger.warning(f"Twelve Data API error: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Twelve Data fetch error: {e}")
            
        return None

    async def _fetch_from_finnhub(self) -> Optional[Dict]:
        """Fetch SPY data from Finnhub API"""
        if not self.finnhub_key or len(self.finnhub_key) < 15:
            return None

        try:
            rate_limit_delay = 1.5
            time.sleep(rate_limit_delay)

            url = "https://finnhub.io/api/v1/quote"
            params = {
                'symbol': 'SPY',
                'token': self.finnhub_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'c' in data and data['c'] > 0:
                            price = float(data['c'])  # Current price
                            prev_close = float(data['pc'])  # Previous close
                            
                            return {
                                'symbol': 'SPY',
                                'price': price,
                                'change': price - prev_close,
                                'change_percent': round((price - prev_close) / prev_close * 100, 2),
                                'volume': 0,  # Not available in free tier
                                'high': price,  # Not available, using current
                                'low': price,   # Not available, using current
                                'open': price,  # Not available, using current
                                'timestamp': '',
                                'source': 'finnhub'
                            }
                    else:
                        self.logger.warning(f"Finnhub API error: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Finnhub fetch error: {e}")
            
        return None

    async def _fetch_from_alpha_vantage(self) -> Optional[Dict]:
        """Fetch SPY data from Alpha Vantage API"""
        if not self.alpha_vantage_key or len(self.alpha_vantage_key) < 10:
            return None

        try:
            rate_limit_delay = 13.0
            time.sleep(rate_limit_delay)

            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'SPY',
                'apikey': self.alpha_vantage_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data.get('Global Quote', {})
                        
                        if quote and '05. price' in quote:
                            price = float(quote['05. price'])
                            change = float(quote['09. change'])
                            
                            return {
                                'symbol': 'SPY',
                                'price': price,
                                'change': change,
                                'change_percent': float(quote['10. change percent'].rstrip('%')),
                                'volume': int(quote['06. volume']),
                                'high': float(quote.get('03. high', price)),
                                'low': float(quote.get('04. low', price)),
                                'open': float(quote.get('02. open', price)),
                                'timestamp': quote.get('07. latest trading day', ''),
                                'source': 'alpha_vantage'
                            }
                    else:
                        self.logger.warning(f"Alpha Vantage API error: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Alpha Vantage fetch error: {e}")
            
        return None

    async def _fetch_from_yfinance(self) -> Optional[Dict]:
        """Fetch SPY data from Yahoo Finance (emergency fallback)"""
        try:
            rate_limit_delay = 2.0
            time.sleep(rate_limit_delay)

            ticker = yf.Ticker('SPY')
            hist = ticker.history(period='2d', timeout=10)
            
            if hist is not None and not hist.empty and len(hist) >= 1:
                current = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) >= 2 else current
                
                price = float(current['Close'])
                prev_price = float(prev['Close'])
                
                return {
                    'symbol': 'SPY',
                    'price': price,
                    'change': price - prev_price,
                    'change_percent': round((price - prev_price) / prev_price * 100, 2),
                    'volume': int(current['Volume']),
                    'high': float(current['High']),
                    'low': float(current['Low']),
                    'open': float(current['Open']),
                    'timestamp': hist.index[-1].isoformat(),
                    'source': 'yfinance'
                }
            else:
                self.logger.warning("Yahoo Finance returned empty data")
                
        except Exception as e:
            self.logger.error(f"Yahoo Finance fetch error: {e}")
            
        return None

    async def _fetch_from_primary(self) -> Optional[Dict]:
        """Fetch data from primary sources (Paid APIs first, FREE as backup)"""
        
        # Try Polygon first (PAID - highest quality for ETFs)
        data = await self._fetch_from_polygon()
        if data:
            return data
            
        # Try Yahoo Finance (FREE - excellent backup)
        data = await self._fetch_from_yfinance()
        if data:
            return data
            
        # Try Alpha Vantage (PAID)
        data = await self._fetch_from_alpha_vantage()
        if data:
            return data
            
        self.logger.warning("All primary sources failed for SPY")
        return None

    async def _fetch_from_fallback(self) -> Optional[Dict]:
        """Fetch data from fallback sources (paid APIs)"""
        
        # Try Twelve Data (PAID, rate limited)
        data = await self._fetch_from_twelve_data()
        if data:
            return data
            
        # Try Finnhub (PAID)
        data = await self._fetch_from_finnhub()
        if data:
            return data
            
        self.logger.error("All sources failed for SPY")
        return None

    def get_detailed_health(self) -> Dict:
        """Get extended health status specific to SPY"""
        base_health = self.get_health_status()
        
        # Add SPY-specific health indicators
        spy_health = {
            **base_health,
            'data_point_importance': 'CRITICAL',  # SPY is a core market indicator
            'market_hours_relevant': True,
            'preferred_source': 'polygon',
            'emergency_sources_available': ['yfinance'],
            'last_24h_performance': self._calculate_24h_performance()
        }
        
        return spy_health

    def _calculate_24h_performance(self) -> Optional[Dict]:
        """Calculate 24-hour performance metrics"""
        try:
            cached_data = self.get_cached_data()
            if not cached_data:
                return None
                
            price = cached_data.get('price', 0)
            change_pct = cached_data.get('change_percent', 0)
            
            # Performance categorization
            if change_pct > 2:
                performance_level = 'STRONG_BULLISH'
            elif change_pct > 0.5:
                performance_level = 'BULLISH'
            elif change_pct > -0.5:
                performance_level = 'NEUTRAL'
            elif change_pct > -2:
                performance_level = 'BEARISH'
            else:
                performance_level = 'STRONG_BEARISH'
                
            return {
                'current_price': price,
                'daily_change_percent': change_pct,
                'performance_level': performance_level,
                'market_sentiment': 'RISK_ON' if change_pct > 0 else 'RISK_OFF'
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating 24h performance: {e}")
            return None


if __name__ == '__main__':
    """Test the SPY agent"""
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_spy_agent():
        agent = SPYAgent()
        
        print("Testing SPY agent fetch...")
        data = await agent.fetch_data()
        
        if data:
            print(f"✅ SPY Agent Test Successful:")
            print(f"   Price: ${data.get('price')}")
            print(f"   Change: {data.get('change_percent')}%")
            print(f"   Source: {data.get('source')}")
            print(f"   Quality Score: {agent.calculate_data_quality_score(data):.1f}")
        else:
            print("❌ SPY Agent Test Failed - No data fetched")
            
        # Test health status
        health = agent.get_health_status()
        print(f"   Health Status: {health['health_status']}")
        print(f"   Consecutive Failures: {health['consecutive_failures']}")
        
        agent.stop()
    
    # Run test
    asyncio.run(test_spy_agent())
