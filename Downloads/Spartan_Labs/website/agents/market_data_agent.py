#!/usr/bin/env python3
"""
MARKET DATA AUTONOMOUS AGENT
=============================

Dedicated agent for equities, commodities, and ETF data.
Ensures all market instruments have genuine real-time data.

Data Sources:
- Yahoo Finance: Stocks, ETFs, Commodities, Indices
- Polygon.io: Real-time quotes (fallback)
"""

import asyncio
import redis
import json
import yfinance as yf
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketDataAgent:
    """Autonomous agent for market data (stocks, ETFs, commodities)"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )

        self.check_interval = 300  # 5 minutes
        self.cache_ttl = 300  # 5 minutes

        # Critical symbols to monitor
        self.symbols = {
            'indices': ['SPY', 'QQQ', 'DIA', 'IWM'],
            'commodities': ['GLD', 'USO', 'CPER'],  # Gold, Oil, Copper ETFs
            'bonds': ['HYG', 'LQD', 'TLT', 'SHY'],
            'sectors': ['XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLP'],
            'global': ['EFA', 'EEM', 'FXI', 'EWJ']
        }

    def fetch_symbol_data(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time data for a single symbol"""
        try:
            ticker = yf.Ticker(symbol)

            # Get latest price data
            hist = ticker.history(period='2d')
            if hist.empty:
                logger.warning(f"No data for {symbol}")
                return None

            current_price = float(hist['Close'].iloc[-1])
            prev_price = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else current_price

            # Calculate change
            change = current_price - prev_price
            change_pct = (change / prev_price * 100) if prev_price != 0 else 0

            # Get volume
            volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0

            # Get additional info
            info = ticker.info
            market_cap = info.get('marketCap', 0)

            data = {
                'symbol': symbol,
                'price': round(current_price, 2),
                'change': round(change, 2),
                'changePct': round(change_pct, 2),
                'volume': volume,
                'marketCap': market_cap,
                'timestamp': datetime.now().isoformat(),
                'source': 'yfinance'
            }

            return data

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None

    async def update_category(self, category: str, symbols: List[str]):
        """Update all symbols in a category"""
        results = {}

        for symbol in symbols:
            data = self.fetch_symbol_data(symbol)
            if data:
                # Store individual symbol
                key = f"market:symbol:{symbol}"
                self.redis_client.setex(
                    key,
                    self.cache_ttl,
                    json.dumps(data)
                )
                results[symbol] = data

        # Store category aggregate
        if results:
            category_key = f"market:category:{category}"
            self.redis_client.setex(
                category_key,
                self.cache_ttl,
                json.dumps(results)
            )

            logger.info(f"✅ Updated {len(results)}/{len(symbols)} symbols in {category}")
        else:
            logger.warning(f"⚠️ No data fetched for {category}")

        return results

    async def update_all_markets(self):
        """Fetch and update all market data"""
        logger.info("🔄 Fetching market data...")

        all_results = {}

        for category, symbols in self.symbols.items():
            results = await self.update_category(category, symbols)
            all_results[category] = results
            await asyncio.sleep(2)  # Rate limiting between categories

        # Create summary
        total_symbols = sum(len(symbols) for symbols in self.symbols.values())
        total_fetched = sum(len(results) for results in all_results.values())

        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_symbols': total_symbols,
            'successful': total_fetched,
            'success_rate': round(total_fetched / total_symbols * 100, 1) if total_symbols > 0 else 0,
            'categories': list(self.symbols.keys())
        }

        self.redis_client.setex(
            'market:summary',
            self.cache_ttl,
            json.dumps(summary)
        )

        logger.info(f"✅ Market data update complete: {total_fetched}/{total_symbols} symbols ({summary['success_rate']}%)")

        return all_results

    async def run_forever(self):
        """Continuously update market data"""
        logger.info("🚀 Market Data Agent started")

        while True:
            try:
                await self.update_all_markets()
                logger.info(f"💤 Sleeping for {self.check_interval} seconds...")
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                await asyncio.sleep(60)


if __name__ == '__main__':
    agent = MarketDataAgent()
    asyncio.run(agent.run_forever())
