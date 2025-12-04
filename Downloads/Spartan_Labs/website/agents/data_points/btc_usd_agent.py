#!/usr/bin/env python3
"""
BITCOIN USD AGENT - BTC-USD CRYPTO DATA POINT
==============================================

Dedicated agent responsible for Bitcoin USD price data availability.
Ensures continuous, genuine crypto data with specialized fallback strategies.

Data Sources:
1. Primary: CoinGecko (free, reliable, no API key needed)
2. Fallback 1: Polygon.io (if crypto API available)
3. Fallback 2: Twelve Data (crypto coverage)
4. Fallback 3: Yahoo Finance (emergency)
"""

import asyncio
from typing import Dict, Optional
import yfinance as yf
import aiohttp
import time

from base_data_point_agent import DataPointAgent


class BTCUSDAgent(DataPointAgent):
    """Dedicated agent for Bitcoin USD price data point"""

    def __init__(self):
        super().__init__(
            agent_id='btc_usd_agent',
            data_point='BTC-USD',
            data_type='crypto'
        )

        # Crypto-specific price validation
        self.min_price = 1000      # Bitcoin won't go below $1,000
        self.max_price = 1000000   # Bitcoin won't exceed $1M (for now)

    def _initialize_data_sources(self):
        """Initialize Bitcoin-specific data source configuration"""
        
        # Bitcoin has excellent free data sources
        self.primary_sources = ['coingecko', 'yfinance']
        self.fallback_sources = ['alpha_vantage', 'twelve_data', 'polygon']
        
        # Bitcoin-specific configuration
        self.crypto_mappings = {
            'coingecko': 'bitcoin',
            'yfinance': 'BTC-USD',
            'alpha_vantage': 'BTC',
            'twelve_data': 'BTC/USD',
            'polygon': 'X:BTCUSD'
        }
        
        # API keys (optional)
        self.polygon_key = None
        self.twelve_data_key = None
        self.alpha_vantage_key = None
        
        # Load API keys
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from environment"""
        import os
        
        self.polygon_key = os.getenv('POLYGON_IO_API_KEY')
        self.twelve_data_key = os.getenv('TWELVE_DATA_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')

    async def _fetch_from_coingecko(self) -> Optional[Dict]:
        """Fetch Bitcoin data from CoinGecko API (FREE)"""
        try:
            rate_limit_delay = 1.5  # CoinGecko is generous with rate limits
            time.sleep(rate_limit_delay)

            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'bitcoin' in data:
                            btc_data = data['bitcoin']
                            
                            return {
                                'symbol': 'BTC-USD',
                                'price': btc_data['usd'],
                                'change': 0,  # Need to calculate from 24h change
                                'change_percent': btc_data.get('usd_24h_change', 0),
                                'volume': btc_data.get('usd_24h_vol', 0),
                                'market_cap': btc_data.get('usd_market_cap', 0),
                                'timestamp': '',
                                'source': 'coingecko'
                            }
                    else:
                        self.logger.warning(f"CoinGecko API error: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"CoinGecko fetch error: {e}")
            
        return None

    async def _fetch_from_polygon(self) -> Optional[Dict]:
        """Fetch Bitcoin data from Polygon.io API"""
        if not self.polygon_key or len(self.polygon_key) < 20:
            return None

        try:
            rate_limit_delay = 13.0
            time.sleep(rate_limit_delay)

            # Polygon uses X:BTCUSD for crypto pairs
            url = f"https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/prev"
            params = {'apiKey': self.polygon_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            
                            return {
                                'symbol': 'BTC-USD',
                                'price': float(result['c']),
                                'change': float(result['c'] - result['o']),
                                'change_percent': round((result['c'] - result['o']) / result['o'] * 100, 2),
                                'volume': int(result['v']),
                                'high': float(result['h']),
                                'low': float(result['l']),
                                'open': float(result['o']),
                                'timestamp': str(result['t']),
                                'source': 'polygon'
                            }
                    else:
                        self.logger.warning(f"Polygon API error for BTC: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Polygon fetch error for BTC: {e}")
            
        return None

    async def _fetch_from_twelve_data(self) -> Optional[Dict]:
        """Fetch Bitcoin data from Twelve Data API"""
        if not self.twelve_data_key or len(self.twelve_data_key) < 20:
            return None

        try:
            rate_limit_delay = 60.0  # Twelve Data very rate limited
            time.sleep(rate_limit_delay)

            url = "https://api.twelvedata.com/quote"
            params = {
                'symbol': 'BTC/USD',
                'apikey': self.twelve_data_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'close' in data and data.get('close'):
                            price = float(data['close'])
                            
                            return {
                                'symbol': 'BTC-USD',
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
                        self.logger.warning(f"Twelve Data API error for BTC: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Twelve Data fetch error for BTC: {e}")
            
        return None

    async def _fetch_from_alpha_vantage(self) -> Optional[Dict]:
        """Fetch Bitcoin data from Alpha Vantage API (if they support crypto)"""
        if not self.alpha_vantage_key or len(self.alpha_vantage_key) < 10:
            return None

        try:
            rate_limit_delay = 13.0
            time.sleep(rate_limit_delay)

            # Alpha Vantage may not support crypto in free tier
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': 'BTC',
                'to_currency': 'USD',
                'apikey': self.alpha_vantage_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        exchange_rate = data.get('Realtime Currency Exchange Rate', {})
                        
                        if exchange_rate and '5. Exchange Rate' in exchange_rate:
                            price = float(exchange_rate['5. Exchange Rate'])
                            
                            return {
                                'symbol': 'BTC-USD',
                                'price': price,
                                'change': 0,  # Not available in this endpoint
                                'change_percent': 0,
                                'volume': 0,
                                'high': 0,
                                'low': 0,
                                'open': 0,
                                'timestamp': exchange_rate.get('6. Last Refreshed', ''),
                                'source': 'alpha_vantage'
                            }
                    else:
                        self.logger.warning(f"Alpha Vantage API error for BTC: HTTP {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Alpha Vantage fetch error for BTC: {e}")
            
        return None

    async def _fetch_from_yfinance(self) -> Optional[Dict]:
        """Fetch Bitcoin data from Yahoo Finance (emergency fallback)"""
        try:
            rate_limit_delay = 2.0
            time.sleep(rate_limit_delay)

            ticker = yf.Ticker('BTC-USD')
            hist = ticker.history(period='2d', timeout=10)
            
            if hist is not None and not hist.empty and len(hist) >= 1:
                current = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) >= 2 else current
                
                price = float(current['Close'])
                prev_price = float(prev['Close'])
                
                return {
                    'symbol': 'BTC-USD',
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
                self.logger.warning("Yahoo Finance returned empty data for BTC")
                
        except Exception as e:
            self.logger.error(f"Yahoo Finance fetch error for BTC: {e}")
            
        return None

    async def _fetch_from_primary(self) -> Optional[Dict]:
        """Fetch data from primary sources (FREE APIs first)"""
        
        # Try CoinGecko first (FREE and most reliable for crypto)
        data = await self._fetch_from_coingecko()
        if data:
            return data
            
        # Try Yahoo Finance
        data = await self._fetch_from_yfinance()
        if data:
            return data
            
        self.logger.warning("All primary sources failed for BTC-USD")
        return None

    async def _fetch_from_fallback(self) -> Optional[Dict]:
        """Fetch data from fallback sources (paid APIs as optional)"""
        
        # Try Alpha Vantage
        data = await self._fetch_from_alpha_vantage()
        if data:
            return data
            
        # Try Twelve Data
        data = await self._fetch_from_twelve_data()
        if data:
            return data
            
        # Try Polygon as last resort
        data = await self._fetch_from_polygon()
        if data:
            return data
            
        self.logger.error("All sources failed for BTC-USD")
        return None

    def get_crypto_market_analysis(self) -> Dict:
        """Get Bitcoin-specific market analysis"""
        cached_data = self.get_cached_data()
        if not cached_data:
            return {'status': 'no_data'}
            
        price = cached_data.get('price', 0)
        change_pct = cached_data.get('change_percent', 0)
        
        # Key resistance/support levels (approximate)
        key_levels = {
            'resistance_1': 70000,
            'resistance_2': 75000,
            'support_1': 60000,
            'support_2': 55000,
            'current_price': price
        }
        
        # Crypto sentiment analysis
        if change_pct > 5:
            crypto_sentiment = 'EXTREME_GREED'
        elif change_pct > 2:
            crypto_sentiment = 'GREED'
        elif change_pct > -2:
            crypto_sentiment = 'NEUTRAL'
        elif change_pct > -5:
            crypto_sentiment = 'FEAR'
        else:
            crypto_sentiment = 'EXTREME_FEAR'
            
        # Calculate relative position to key levels
        nearest_level = min(key_levels.items(), key=lambda x: abs(x[1] - price)) if price > 0 else ('current_price', price)
        
        return {
            'symbol': 'BTC-USD',
            'crypto_sentiment': crypto_sentiment,
            'price_change_24h': f"{change_pct:+.2f}%",
            'current_price': price,
            'market_dominance': 'N/A',  # Would need additional API call
            'nearest_level': nearest_level[0],
            'distance_to_level': abs(price - nearest_level[1]),
            'source': cached_data.get('source'),
            'last_updated': cached_data.get('timestamp')
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Enhanced validation for Bitcoin data"""
        if not super().validate_data(data):
            return False
            
        # Bitcoin-specific validations
        price = float(data.get('price', 0))
        
        # Bitcoin price should be reasonable (between $1K and $1M)
        if price < 1000 or price > 1000000:
            self.logger.warning(f"Bitcoin price {price} outside reasonable bounds")
            return False
            
        # Check for valid crypto volume (should be substantial for BTC)
        if 'volume' in data and data['volume']:
            volume = float(data['volume'])
            if volume < 1000000:  # Less than $1M daily volume is suspicious for BTC
                self.logger.warning(f"Bitcoin volume {volume} seems too low")
                # Don't reject, but warn
            
        return True


if __name__ == '__main__':
    """Test the BTC-USD agent"""
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_btc_agent():
        agent = BTCUSDAgent()
        
        print("Testing BTC-USD agent fetch...")
        data = await agent.fetch_data()
        
        if data:
            print(f"✅ BTC-USD Agent Test Successful:")
            print(f"   Price: ${data.get('price'):,.2f}")
            print(f"   Change: {data.get('change_percent'):+.2f}%")
            print(f"   Source: {data.get('source')}")
            
            # Test crypto market analysis
            crypto_analysis = agent.get_crypto_market_analysis()
            print(f"   Crypto Sentiment: {crypto_analysis['crypto_sentiment']}")
        else:
            print("❌ BTC-USD Agent Test Failed - No data fetched")
            
        agent.stop()
    
    # Run test
    asyncio.run(test_btc_agent())
