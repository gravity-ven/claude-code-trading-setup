#!/usr/bin/env python3
"""
CRYPTO INTELLIGENCE AUTONOMOUS AGENT
=====================================

Dedicated agent for cryptocurrency data with on-chain metrics.
Ensures Bitcoin, Ethereum, and other crypto data is always genuine.

Data Sources:
- CoinGecko API: Prices, market cap, volume (no API key needed)
- Blockchain.info: Bitcoin on-chain metrics
- Yahoo Finance: Crypto pairs (BTC-USD, ETH-USD)
"""

import asyncio
import aiohttp
import redis
import json
import yfinance as yf
from datetime import datetime
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CryptoIntelligenceAgent:
    """Autonomous agent for cryptocurrency data"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )

        self.check_interval = 300  # 5 minutes
        self.cache_ttl = 300  # 5 minutes

        # Crypto symbols to monitor
        self.symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD']

        # CoinGecko IDs
        self.coingecko_ids = {
            'BTC-USD': 'bitcoin',
            'ETH-USD': 'ethereum',
            'SOL-USD': 'solana',
            'AVAX-USD': 'avalanche-2'
        }

    async def fetch_coingecko_data(self, coin_id: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Fetch comprehensive crypto data from CoinGecko"""
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false'
            }

            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    market_data = data.get('market_data', {})

                    return {
                        'price': market_data.get('current_price', {}).get('usd'),
                        'market_cap': market_data.get('market_cap', {}).get('usd'),
                        'volume_24h': market_data.get('total_volume', {}).get('usd'),
                        'price_change_24h': market_data.get('price_change_percentage_24h'),
                        'market_cap_rank': data.get('market_cap_rank'),
                        'circulating_supply': market_data.get('circulating_supply'),
                        'total_supply': market_data.get('total_supply'),
                        'ath': market_data.get('ath', {}).get('usd'),
                        'atl': market_data.get('atl', {}).get('usd')
                    }

                logger.warning(f"CoinGecko API returned {response.status} for {coin_id}")
                return None

        except Exception as e:
            logger.error(f"Error fetching CoinGecko data for {coin_id}: {e}")
            return None

    async def fetch_bitcoin_onchain_metrics(self, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Fetch Bitcoin on-chain metrics from Blockchain.info"""
        try:
            # Hashrate
            url_hashrate = "https://blockchain.info/q/hashrate"
            async with session.get(url_hashrate, timeout=10) as response:
                hashrate = None
                if response.status == 200:
                    hashrate_raw = await response.text()
                    hashrate = float(hashrate_raw) / 1_000_000  # Convert to EH/s

            # Market price
            url_price = "https://blockchain.info/q/24hrprice"
            async with session.get(url_price, timeout=10) as response:
                market_price = None
                if response.status == 200:
                    price_str = await response.text()
                    market_price = float(price_str)

            # Difficulty
            url_difficulty = "https://blockchain.info/q/getdifficulty"
            async with session.get(url_difficulty, timeout=10) as response:
                difficulty = None
                if response.status == 200:
                    diff_str = await response.text()
                    difficulty = float(diff_str) / 1_000_000_000_000  # Convert to trillions

            return {
                'hashrate_eh_s': round(hashrate, 2) if hashrate else None,
                'difficulty_t': round(difficulty, 2) if difficulty else None,
                'price_24h': round(market_price, 2) if market_price else None
            }

        except Exception as e:
            logger.error(f"Error fetching Bitcoin on-chain metrics: {e}")
            return None

    async def fetch_crypto_symbol(self, symbol: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Fetch comprehensive data for a crypto symbol"""
        try:
            # Get CoinGecko data
            coin_id = self.coingecko_ids.get(symbol)
            coingecko_data = await self.fetch_coingecko_data(coin_id, session) if coin_id else None

            # Get Yahoo Finance data as backup
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='2d')

            if hist.empty and not coingecko_data:
                logger.warning(f"No data available for {symbol}")
                return None

            # Prefer CoinGecko for price data (more reliable for crypto)
            if coingecko_data and coingecko_data.get('price'):
                price = coingecko_data['price']
                change_pct = coingecko_data.get('price_change_24h', 0)
            elif not hist.empty:
                price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else price
                change_pct = ((price - prev_price) / prev_price * 100) if prev_price != 0 else 0
            else:
                return None

            data = {
                'symbol': symbol,
                'price': round(price, 2),
                'changePct': round(change_pct, 2),
                'marketCap': coingecko_data.get('market_cap') if coingecko_data else None,
                'volume24h': coingecko_data.get('volume_24h') if coingecko_data else None,
                'circulatingSupply': coingecko_data.get('circulating_supply') if coingecko_data else None,
                'rank': coingecko_data.get('market_cap_rank') if coingecko_data else None,
                'timestamp': datetime.now().isoformat(),
                'source': 'coingecko+yfinance'
            }

            # Add Bitcoin-specific on-chain metrics
            if symbol == 'BTC-USD':
                onchain = await self.fetch_bitcoin_onchain_metrics(session)
                if onchain:
                    data['onchain'] = onchain

            return data

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None

    async def update_all_crypto(self):
        """Fetch and update all cryptocurrency data"""
        logger.info("🔄 Fetching crypto data...")

        async with aiohttp.ClientSession() as session:
            results = {}

            for symbol in self.symbols:
                data = await self.fetch_crypto_symbol(symbol, session)

                if data:
                    # Store in Redis
                    key = f"crypto:symbol:{symbol}"
                    self.redis_client.setex(
                        key,
                        self.cache_ttl,
                        json.dumps(data)
                    )
                    results[symbol] = data

                await asyncio.sleep(2)  # Rate limiting

            # Store summary
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_symbols': len(self.symbols),
                'successful': len(results),
                'symbols': list(results.keys())
            }

            self.redis_client.setex(
                'crypto:summary',
                self.cache_ttl,
                json.dumps(summary)
            )

            logger.info(f"✅ Crypto data update complete: {len(results)}/{len(self.symbols)} symbols")

            return results

    async def run_forever(self):
        """Continuously update crypto data"""
        logger.info("🚀 Crypto Intelligence Agent started")

        while True:
            try:
                await self.update_all_crypto()
                logger.info(f"💤 Sleeping for {self.check_interval} seconds...")
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                await asyncio.sleep(60)


if __name__ == '__main__':
    agent = CryptoIntelligenceAgent()
    asyncio.run(agent.run_forever())
