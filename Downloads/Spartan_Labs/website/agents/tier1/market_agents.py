#!/usr/bin/env python3
"""
Tier 1 Critical Market Data Agents
===================================

14 autonomous agents for core market data:
- Agent 1: SPY (S&P 500 ETF)
- Agent 2: Dollar Index (UUP)
- Agent 3: Treasury 10Y (^TNX → DGS10)
- Agent 4: Gold (GLD)
- Agent 5: Oil (USO)
- Agent 6: VIX (^VIX → VIXCLS)
- Agent 7: Bitcoin (BTC-USD)
- Agent 8: Ethereum (ETH-USD)
- Agent 9: Solana (SOL-USD)
- Agent 10: AUD/JPY Forex
- Agent 11: HYG (High Yield Bonds)
- Agent 12: Treasury 3M (^IRX → DTB3)
- Agent 13: Recession Calculator (uses Agent 3 + 12 data)
- Agent 14: Market Narrative (composite analysis)
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import math
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autonomous_agent_base import AutonomousDataAgent
import yfinance as yf


# =============================================================================
# TIER 1 AGENTS - Market Data (yfinance)
# =============================================================================

class SPYAgent(AutonomousDataAgent):
    """Agent 1: SPY (S&P 500 ETF) - Most critical market indicator"""

    def __init__(self):
        super().__init__(
            name="SPY Agent",
            symbol="SPY",
            source="scanner",
            update_interval=900,  # 15 minutes
            redis_key_prefix="market",
            critical=True  # Critical for website
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch SPY data from existing scanner cache.
        Uses data_guardian_agent_full.py which is already running.
        """
        try:
            # FIRST: Check if data guardian scanner already has it
            if self.redis_client:
                # Try scanner's key format
                scanner_key = f'market:symbol:{self.symbol}'
                cached = self.redis_client.get(scanner_key)

                if cached:
                    data = json.loads(cached)
                    self.logger.debug(f"✅ Retrieved {self.symbol} from scanner cache")
                    return data

            # FALLBACK: Fetch directly from yfinance with rate limiting
            await asyncio.sleep(2)  # Rate limit: 2 seconds between requests

            ticker = yf.Ticker(self.symbol)
            hist = ticker.history(period='5d')

            if hist.empty:
                self.logger.warning(f"⚠️  yfinance returned empty data for {self.symbol}")
                return None

            current_price = float(hist['Close'][-1])
            prev_close = float(hist['Close'][-2]) if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            # 5-day change
            change_5d_pct = 0
            if len(hist) >= 5:
                price_5d_ago = float(hist['Close'][-5])
                change_5d_pct = ((current_price - price_5d_ago) / price_5d_ago * 100)

            return {
                'symbol': 'SPY',
                'price': current_price,
                'change': change,
                'changePercent': change_pct,
                'changePercent5d': change_5d_pct,
                'volume': int(hist['Volume'][-1]),
                'timestamp': hist.index[-1].isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch SPY: {e}")
            return None


class DollarIndexAgent(AutonomousDataAgent):
    """Agent 2: Dollar Index (UUP) - Dollar strength indicator"""

    def __init__(self):
        super().__init__(
            name="Dollar Index Agent",
            symbol="UUP",
            source="yfinance",
            update_interval=900,
            redis_key_prefix="market",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch UUP (Dollar ETF) data"""
        try:
            ticker = yf.Ticker("UUP")
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            current_price = float(hist['Close'][-1])
            prev_close = float(hist['Close'][-2]) if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            change_5d_pct = 0
            if len(hist) >= 5:
                price_5d_ago = float(hist['Close'][-5])
                change_5d_pct = ((current_price - price_5d_ago) / price_5d_ago * 100)

            return {
                'symbol': 'UUP',
                'price': current_price,
                'change': change,
                'changePercent': change_pct,
                'changePercent5d': change_5d_pct,
                'volume': int(hist['Volume'][-1]),
                'timestamp': hist.index[-1].isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch UUP: {e}")
            return None


class GoldAgent(AutonomousDataAgent):
    """Agent 4: Gold (GLD) - Safe haven indicator"""

    def __init__(self):
        super().__init__(
            name="Gold Agent",
            symbol="GLD",
            source="yfinance",
            update_interval=900,
            redis_key_prefix="market",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch GLD data"""
        try:
            ticker = yf.Ticker("GLD")
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            current_price = float(hist['Close'][-1])
            prev_close = float(hist['Close'][-2]) if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            change_5d_pct = 0
            if len(hist) >= 5:
                price_5d_ago = float(hist['Close'][-5])
                change_5d_pct = ((current_price - price_5d_ago) / price_5d_ago * 100)

            return {
                'symbol': 'GLD',
                'price': current_price,
                'change': change,
                'changePercent': change_pct,
                'changePercent5d': change_5d_pct,
                'volume': int(hist['Volume'][-1]),
                'timestamp': hist.index[-1].isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch GLD: {e}")
            return None


class OilAgent(AutonomousDataAgent):
    """Agent 5: Oil (USO) - Energy/commodity indicator"""

    def __init__(self):
        super().__init__(
            name="Oil Agent",
            symbol="USO",
            source="yfinance",
            update_interval=900,
            redis_key_prefix="market",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch USO data"""
        try:
            ticker = yf.Ticker("USO")
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            current_price = float(hist['Close'][-1])
            prev_close = float(hist['Close'][-2]) if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            change_5d_pct = 0
            if len(hist) >= 5:
                price_5d_ago = float(hist['Close'][-5])
                change_5d_pct = ((current_price - price_5d_ago) / price_5d_ago * 100)

            return {
                'symbol': 'USO',
                'price': current_price,
                'change': change,
                'changePercent': change_pct,
                'changePercent5d': change_5d_pct,
                'volume': int(hist['Volume'][-1]),
                'timestamp': hist.index[-1].isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch USO: {e}")
            return None


class BitcoinAgent(AutonomousDataAgent):
    """Agent 7: Bitcoin (BTC-USD) - Crypto indicator"""

    def __init__(self):
        super().__init__(
            name="Bitcoin Agent",
            symbol="BTC-USD",
            source="coingecko",
            update_interval=900,
            redis_key_prefix="market",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch BTC-USD data from multiple sources"""
        try:
            # FIRST: Check if data guardian scanner already has it
            if self.redis_client:
                scanner_key = f'market:symbol:{self.symbol}'
                cached = self.redis_client.get(scanner_key)

                if cached:
                    data = json.loads(cached)
                    self.logger.debug(f"✅ Retrieved {self.symbol} from scanner cache")
                    return data

            # SECOND: Try CoinGecko API (free, no key required)
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    url = "https://api.coingecko.com/api/v3/simple/price"
                    params = {
                        'ids': 'bitcoin',
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true',
                        'include_24hr_vol': 'true'
                    }

                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()

                            if 'bitcoin' in data:
                                btc = data['bitcoin']
                                current_price = btc['usd']
                                change_pct = btc.get('usd_24h_change', 0)
                                volume = btc.get('usd_24h_vol', 0)

                                self.logger.info(f"✅ Retrieved BTC-USD from CoinGecko: ${current_price:,.2f}")

                                return {
                                    'symbol': 'BTC-USD',
                                    'price': current_price,
                                    'change': (current_price * change_pct / 100),
                                    'changePercent': change_pct,
                                    'volume': int(volume),
                                    'timestamp': datetime.now().isoformat(),
                                    'source': 'coingecko'
                                }
            except Exception as e:
                self.logger.debug(f"CoinGecko failed for BTC-USD: {e}")

            # THIRD: Fallback to yfinance
            await asyncio.sleep(2)  # Rate limit
            ticker = yf.Ticker("BTC-USD")
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            current_price = float(hist['Close'][-1])
            prev_close = float(hist['Close'][-2]) if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            change_5d_pct = 0
            if len(hist) >= 5:
                price_5d_ago = float(hist['Close'][-5])
                change_5d_pct = ((current_price - price_5d_ago) / price_5d_ago * 100)

            self.logger.info(f"✅ Retrieved BTC-USD from yfinance: ${current_price:,.2f}")

            return {
                'symbol': 'BTC-USD',
                'price': current_price,
                'change': change,
                'changePercent': change_pct,
                'changePercent5d': change_5d_pct,
                'volume': int(hist['Volume'][-1]),
                'timestamp': hist.index[-1].isoformat(),
                'source': 'yfinance'
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch BTC-USD from all sources: {e}")
            return None


class EthereumAgent(AutonomousDataAgent):
    """Agent 8: Ethereum (ETH-USD) - Crypto indicator"""

    def __init__(self):
        super().__init__(
            name="Ethereum Agent",
            symbol="ETH-USD",
            source="coingecko",
            update_interval=900,
            redis_key_prefix="market",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch ETH-USD data from multiple sources"""
        try:
            # FIRST: Check if data guardian scanner already has it
            if self.redis_client:
                scanner_key = f'market:symbol:{self.symbol}'
                cached = self.redis_client.get(scanner_key)

                if cached:
                    data = json.loads(cached)
                    self.logger.debug(f"✅ Retrieved {self.symbol} from scanner cache")
                    return data

            # SECOND: Try CoinGecko API (free, no key required)
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    url = "https://api.coingecko.com/api/v3/simple/price"
                    params = {
                        'ids': 'ethereum',
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true',
                        'include_24hr_vol': 'true'
                    }

                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()

                            if 'ethereum' in data:
                                eth = data['ethereum']
                                current_price = eth['usd']
                                change_pct = eth.get('usd_24h_change', 0)
                                volume = eth.get('usd_24h_vol', 0)

                                self.logger.info(f"✅ Retrieved ETH-USD from CoinGecko: ${current_price:,.2f}")

                                return {
                                    'symbol': 'ETH-USD',
                                    'price': current_price,
                                    'change': (current_price * change_pct / 100),
                                    'changePercent': change_pct,
                                    'volume': int(volume),
                                    'timestamp': datetime.now().isoformat(),
                                    'source': 'coingecko'
                                }
            except Exception as e:
                self.logger.debug(f"CoinGecko failed for ETH-USD: {e}")

            # THIRD: Fallback to yfinance
            await asyncio.sleep(2)  # Rate limit
            ticker = yf.Ticker("ETH-USD")
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            current_price = float(hist['Close'][-1])
            prev_close = float(hist['Close'][-2]) if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            change_5d_pct = 0
            if len(hist) >= 5:
                price_5d_ago = float(hist['Close'][-5])
                change_5d_pct = ((current_price - price_5d_ago) / price_5d_ago * 100)

            self.logger.info(f"✅ Retrieved ETH-USD from yfinance: ${current_price:,.2f}")

            return {
                'symbol': 'ETH-USD',
                'price': current_price,
                'change': change,
                'changePercent': change_pct,
                'changePercent5d': change_5d_pct,
                'volume': int(hist['Volume'][-1]),
                'timestamp': hist.index[-1].isoformat(),
                'source': 'yfinance'
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch ETH-USD from all sources: {e}")
            return None


class SolanaAgent(AutonomousDataAgent):
    """Agent 9: Solana (SOL-USD) - Crypto indicator"""

    def __init__(self):
        super().__init__(
            name="Solana Agent",
            symbol="SOL-USD",
            source="coingecko",
            update_interval=900,
            redis_key_prefix="market",
            critical=False
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch SOL-USD data from multiple sources"""
        try:
            # FIRST: Check if data guardian scanner already has it
            if self.redis_client:
                scanner_key = f'market:symbol:{self.symbol}'
                cached = self.redis_client.get(scanner_key)

                if cached:
                    data = json.loads(cached)
                    self.logger.debug(f"✅ Retrieved {self.symbol} from scanner cache")
                    return data

            # SECOND: Try CoinGecko API (free, no key required)
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    url = "https://api.coingecko.com/api/v3/simple/price"
                    params = {
                        'ids': 'solana',
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true',
                        'include_24hr_vol': 'true'
                    }

                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()

                            if 'solana' in data:
                                sol = data['solana']
                                current_price = sol['usd']
                                change_pct = sol.get('usd_24h_change', 0)
                                volume = sol.get('usd_24h_vol', 0)

                                self.logger.info(f"✅ Retrieved SOL-USD from CoinGecko: ${current_price:,.2f}")

                                return {
                                    'symbol': 'SOL-USD',
                                    'price': current_price,
                                    'change': (current_price * change_pct / 100),
                                    'changePercent': change_pct,
                                    'volume': int(volume),
                                    'timestamp': datetime.now().isoformat(),
                                    'source': 'coingecko'
                                }
            except Exception as e:
                self.logger.debug(f"CoinGecko failed for SOL-USD: {e}")

            # THIRD: Fallback to yfinance
            await asyncio.sleep(2)  # Rate limit
            ticker = yf.Ticker("SOL-USD")
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            current_price = float(hist['Close'][-1])
            prev_close = float(hist['Close'][-2]) if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            change_5d_pct = 0
            if len(hist) >= 5:
                price_5d_ago = float(hist['Close'][-5])
                change_5d_pct = ((current_price - price_5d_ago) / price_5d_ago * 100)

            self.logger.info(f"✅ Retrieved SOL-USD from yfinance: ${current_price:,.2f}")

            return {
                'symbol': 'SOL-USD',
                'price': current_price,
                'change': change,
                'changePercent': change_pct,
                'changePercent5d': change_5d_pct,
                'volume': int(hist['Volume'][-1]),
                'timestamp': hist.index[-1].isoformat(),
                'source': 'yfinance'
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch SOL-USD from all sources: {e}")
            return None


class AUDJPYAgent(AutonomousDataAgent):
    """Agent 10: AUD/JPY Forex - Risk appetite indicator"""

    def __init__(self):
        super().__init__(
            name="AUD/JPY Agent",
            symbol="AUDJPY=X",
            source="exchangerate-api",
            update_interval=900,
            redis_key_prefix="market",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch AUDJPY=X data from multiple sources"""
        try:
            # FIRST: Check scanner cache
            if self.redis_client:
                scanner_key = f'market:symbol:{self.symbol}'
                cached = self.redis_client.get(scanner_key)

                if cached:
                    data = json.loads(cached)
                    self.logger.debug(f"✅ Retrieved {self.symbol} from scanner cache")
                    return data

            # SECOND: Try exchangerate-api.com (free, no API key)
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    # Get AUD to JPY rate
                    url = "https://open.er-api.com/v6/latest/AUD"

                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()

                            if 'rates' in data and 'JPY' in data['rates']:
                                rate = data['rates']['JPY']

                                # Calculate change (store previous rate in Redis for comparison)
                                prev_rate_key = 'forex:prev:AUDJPY'
                                prev_rate_str = self.redis_client.get(prev_rate_key) if self.redis_client else None
                                prev_rate = float(prev_rate_str) if prev_rate_str else rate

                                change = rate - prev_rate
                                change_pct = (change / prev_rate * 100) if prev_rate != 0 else 0

                                # Store current rate for next comparison
                                if self.redis_client:
                                    self.redis_client.setex(prev_rate_key, 3600, str(rate))

                                self.logger.info(f"✅ Retrieved AUDJPY from exchangerate-api: {rate:.4f}")

                                return {
                                    'symbol': 'AUDJPY=X',
                                    'price': rate,
                                    'change': change,
                                    'changePercent': change_pct,
                                    'timestamp': datetime.now().isoformat(),
                                    'source': 'exchangerate-api'
                                }
            except Exception as e:
                self.logger.debug(f"exchangerate-api failed for AUDJPY: {e}")

            # THIRD: Try fxratesapi.com (another free API)
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    url = "https://api.fxratesapi.com/latest?base=AUD&symbols=JPY"

                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()

                            if 'rates' in data and 'JPY' in data['rates']:
                                rate = data['rates']['JPY']

                                self.logger.info(f"✅ Retrieved AUDJPY from fxratesapi: {rate:.4f}")

                                return {
                                    'symbol': 'AUDJPY=X',
                                    'price': rate,
                                    'change': 0,
                                    'changePercent': 0,
                                    'timestamp': datetime.now().isoformat(),
                                    'source': 'fxratesapi'
                                }
            except Exception as e:
                self.logger.debug(f"fxratesapi failed for AUDJPY: {e}")

            # FOURTH: Fallback to yfinance
            await asyncio.sleep(2)  # Rate limit
            ticker = yf.Ticker("AUDJPY=X")
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            current_price = float(hist['Close'][-1])
            prev_close = float(hist['Close'][-2]) if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            change_5d_pct = 0
            if len(hist) >= 5:
                price_5d_ago = float(hist['Close'][-5])
                change_5d_pct = ((current_price - price_5d_ago) / price_5d_ago * 100)

            self.logger.info(f"✅ Retrieved AUDJPY from yfinance: {current_price:.4f}")

            return {
                'symbol': 'AUDJPY=X',
                'price': current_price,
                'change': change,
                'changePercent': change_pct,
                'changePercent5d': change_5d_pct,
                'timestamp': hist.index[-1].isoformat(),
                'source': 'yfinance'
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch AUDJPY=X from all sources: {e}")
            return None


class HYGAgent(AutonomousDataAgent):
    """Agent 11: HYG (High Yield Bonds) - Credit risk indicator"""

    def __init__(self):
        super().__init__(
            name="HYG Agent",
            symbol="HYG",
            source="yfinance",
            update_interval=900,
            redis_key_prefix="market",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch HYG data"""
        try:
            ticker = yf.Ticker("HYG")
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            current_price = float(hist['Close'][-1])
            prev_close = float(hist['Close'][-2]) if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            change_5d_pct = 0
            if len(hist) >= 5:
                price_5d_ago = float(hist['Close'][-5])
                change_5d_pct = ((current_price - price_5d_ago) / price_5d_ago * 100)

            return {
                'symbol': 'HYG',
                'price': current_price,
                'change': change,
                'changePercent': change_pct,
                'changePercent5d': change_5d_pct,
                'volume': int(hist['Volume'][-1]),
                'timestamp': hist.index[-1].isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch HYG: {e}")
            return None


# =============================================================================
# TIER 1 AGENTS - FRED Data
# =============================================================================

class Treasury10YAgent(AutonomousDataAgent):
    """Agent 3: Treasury 10Y Yield (DGS10 from FRED)"""

    def __init__(self):
        super().__init__(
            name="Treasury 10Y Agent",
            symbol="DGS10",
            source="scanner",
            update_interval=3600,  # 1 hour (FRED updates daily)
            redis_key_prefix="fundamental:economic",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch DGS10 from FRED via existing comprehensive scanner cache"""
        try:
            # Check if comprehensive scanner already cached this
            if self.redis_client:
                # Try multiple key formats
                key_formats = [
                    'economic:DGS10',            # Current scanner format
                    'fundamental:economic:DGS10', # Alternative format
                    'fred:DGS10'                 # Direct format
                ]

                for key in key_formats:
                    cached = self.redis_client.get(key)
                    if cached:
                        data = json.loads(cached)
                        self.logger.info(f"✅ Retrieved DGS10 from cache ({key}): {data.get('value')}")
                        return data

            # If not in cache, log warning (comprehensive scanner should handle)
            self.logger.warning("⚠️  DGS10 not in cache - comprehensive scanner may not be running")
            return None

        except Exception as e:
            self.logger.error(f"Failed to fetch DGS10: {e}")
            return None


class Treasury3MAgent(AutonomousDataAgent):
    """Agent 12: Treasury 3M Yield (DTB3 from FRED)"""

    def __init__(self):
        super().__init__(
            name="Treasury 3M Agent",
            symbol="DTB3",
            source="scanner",
            update_interval=3600,
            redis_key_prefix="fundamental:economic",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch DTB3 from FRED via existing comprehensive scanner cache"""
        try:
            if self.redis_client:
                # Try multiple key formats
                key_formats = [
                    'economic:DTB3',
                    'fundamental:economic:DTB3',
                    'fred:DTB3'
                ]

                for key in key_formats:
                    cached = self.redis_client.get(key)
                    if cached:
                        data = json.loads(cached)
                        self.logger.info(f"✅ Retrieved DTB3 from cache ({key}): {data.get('value')}")
                        return data

            self.logger.warning("⚠️  DTB3 not in cache - comprehensive scanner may not be running")
            return None

        except Exception as e:
            self.logger.error(f"Failed to fetch DTB3: {e}")
            return None


class VIXAgent(AutonomousDataAgent):
    """Agent 6: VIX (VIXCLS from FRED)"""

    def __init__(self):
        super().__init__(
            name="VIX Agent",
            symbol="VIXCLS",
            source="scanner",
            update_interval=3600,
            redis_key_prefix="fundamental:economic",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch VIXCLS from FRED via existing comprehensive scanner cache"""
        try:
            if self.redis_client:
                # Try multiple key formats
                key_formats = [
                    'economic:VIXCLS',
                    'fundamental:economic:VIXCLS',
                    'fred:VIXCLS'
                ]

                for key in key_formats:
                    cached = self.redis_client.get(key)
                    if cached:
                        data = json.loads(cached)
                        self.logger.info(f"✅ Retrieved VIXCLS from cache ({key}): {data.get('value')}")
                        return data

            self.logger.warning("⚠️  VIXCLS not in cache - comprehensive scanner may not be running")
            return None

        except Exception as e:
            self.logger.error(f"Failed to fetch VIXCLS: {e}")
            return None


# =============================================================================
# TIER 1 COMPOSITE AGENTS
# =============================================================================

class RecessionCalculatorAgent(AutonomousDataAgent):
    """
    Agent 13: Recession Probability Calculator

    Uses yield curve spread (10Y - 3M) to calculate recession probability.
    Depends on Agent 3 (DGS10) and Agent 12 (DTB3).
    """

    def __init__(self):
        super().__init__(
            name="Recession Calculator Agent",
            symbol="RECESSION_PROB",
            source="calculated",
            update_interval=3600,  # 1 hour
            redis_key_prefix="composite",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Calculate recession probability from yield curve"""
        try:
            if not self.redis_client:
                return None

            # Get 10Y yield - try multiple key formats
            yield_10y = None
            for key in ['economic:DGS10', 'fundamental:economic:DGS10', 'fred:DGS10']:
                dgs10_data = self.redis_client.get(key)
                if dgs10_data:
                    yield_10y = json.loads(dgs10_data).get('value')
                    break

            if not yield_10y:
                self.logger.warning("⚠️  DGS10 data not available")
                return None

            # Get 3M yield - try multiple key formats
            yield_3m = None
            for key in ['economic:DTB3', 'fundamental:economic:DTB3', 'fred:DTB3']:
                dtb3_data = self.redis_client.get(key)
                if dtb3_data:
                    yield_3m = json.loads(dtb3_data).get('value')
                    break

            if not yield_3m:
                self.logger.warning("⚠️  DTB3 data not available")
                return None

            # Calculate spread
            spread = yield_10y - yield_3m

            # Logistic regression for recession probability
            k = 2.0  # Steepness
            threshold = 0.0  # Inversion threshold
            probability = 100 / (1 + math.exp(k * (spread - threshold)))

            # Determine risk level
            if probability < 15:
                risk_level = "LOW"
                risk_emoji = "🟢"
                risk_desc = "Low risk - normal yield curve"
            elif probability < 30:
                risk_level = "MODERATE"
                risk_emoji = "🟡"
                risk_desc = "Moderate risk - yield curve flattening"
            elif probability < 50:
                risk_level = "ELEVATED"
                risk_emoji = "🟠"
                risk_desc = "Elevated risk - yield curve near inversion"
            elif probability < 70:
                risk_level = "HIGH"
                risk_emoji = "🔴"
                risk_desc = "High risk - yield curve inverted"
            else:
                risk_level = "CRITICAL"
                risk_emoji = "🚨"
                risk_desc = "Critical risk - deep inversion"

            return {
                'symbol': 'RECESSION_PROB',
                'spread': spread,
                'probability': round(probability, 1),
                'risk_level': risk_level,
                'risk_emoji': risk_emoji,
                'risk_desc': risk_desc,
                'yield_10y': yield_10y,
                'yield_3m': yield_3m
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate recession probability: {e}")
            return None


class MarketNarrativeAgent(AutonomousDataAgent):
    """
    Agent 14: Market Narrative Generator

    Analyzes market conditions to determine regime:
    - RISK_ON: Stocks up, VIX low, Dollar weak
    - RISK_OFF: Stocks down, VIX high, Dollar strong
    - FLIGHT_TO_SAFETY: Gold up, VIX high
    - CONSOLIDATION: Low volatility, range-bound
    - TRANSITION: Mixed signals
    """

    def __init__(self):
        super().__init__(
            name="Market Narrative Agent",
            symbol="MARKET_NARRATIVE",
            source="calculated",
            update_interval=900,  # 15 minutes
            redis_key_prefix="composite",
            critical=True
        )

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        """Generate market narrative from current conditions"""
        try:
            if not self.redis_client:
                return None

            # Get market data
            spy_data = self.redis_client.get('market:symbol:SPY')
            uup_data = self.redis_client.get('market:symbol:UUP')
            gld_data = self.redis_client.get('market:symbol:GLD')

            # Get VIX - try multiple key formats
            vix_data = None
            for key in ['economic:VIXCLS', 'fundamental:economic:VIXCLS', 'fred:VIXCLS']:
                vix_data = self.redis_client.get(key)
                if vix_data:
                    break

            if not all([spy_data, uup_data, gld_data]):
                self.logger.warning("⚠️  Insufficient data for narrative")
                return None

            # Parse data
            spy = json.loads(spy_data)
            uup = json.loads(uup_data)
            gld = json.loads(gld_data)

            spy_change = spy.get('changePercent', 0)
            uup_change = uup.get('changePercent', 0)
            gld_change = gld.get('changePercent', 0)

            # VIX might not be available
            vix_value = 20  # Default mid-range
            if vix_data:
                vix = json.loads(vix_data)
                vix_value = vix.get('value', 20)

            # Determine regime
            regime = "CONSOLIDATION"
            narrative = ""
            confidence = 0.5

            if spy_change > 0.5 and vix_value < 20 and uup_change < 0:
                regime = "RISK_ON"
                narrative = f"Risk-On: Equities rising (+{spy_change:.1f}%), VIX low ({vix_value:.1f}), Dollar weak"
                confidence = 0.85
            elif spy_change < -0.5 and vix_value > 25:
                regime = "RISK_OFF"
                narrative = f"Risk-Off: Equities falling ({spy_change:.1f}%), VIX elevated ({vix_value:.1f})"
                confidence = 0.85
            elif gld_change > 0.5 and vix_value > 20:
                regime = "FLIGHT_TO_SAFETY"
                narrative = f"Flight to Safety: Gold rising (+{gld_change:.1f}%), VIX {vix_value:.1f}"
                confidence = 0.75
            elif abs(spy_change) < 0.3 and vix_value < 20:
                regime = "CONSOLIDATION"
                narrative = f"Consolidation: Markets range-bound, VIX {vix_value:.1f}"
                confidence = 0.7
            else:
                regime = "TRANSITION"
                narrative = f"Transition: Mixed signals - SPY {spy_change:+.1f}%, VIX {vix_value:.1f}"
                confidence = 0.6

            return {
                'symbol': 'MARKET_NARRATIVE',
                'narrative': narrative,
                'regime': regime,
                'confidence': confidence,
                'spy_change': spy_change,
                'vix_value': vix_value,
                'dollar_change': uup_change,
                'gold_change': gld_change
            }

        except Exception as e:
            self.logger.error(f"Failed to generate market narrative: {e}")
            return None
