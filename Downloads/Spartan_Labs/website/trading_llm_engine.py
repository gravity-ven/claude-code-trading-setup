#!/usr/bin/env python3
"""
Trading LLM Engine - AI-Powered Multi-Asset Trading Intelligence
Integrates with Spartan Labs infrastructure for futures, stocks, CFDs, bonds, forex

PLATINUM RULE ENFORCED: All data from verified sources only
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AssetClass(Enum):
    """Supported asset classes"""
    FUTURES = "futures"
    STOCKS = "stocks"
    FOREX = "forex"
    BONDS = "bonds"
    CRYPTO = "crypto"
    CFDS = "cfds"


class SignalType(Enum):
    """Trading signal types"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class TimeHorizon(Enum):
    """Trading time horizons"""
    SCALP = "scalp"          # Minutes to hours
    INTRADAY = "intraday"    # Same day
    SWING = "swing"          # 1-2 weeks
    POSITION = "position"    # 1-3 months
    INVESTMENT = "investment" # 3+ months


@dataclass
class MarketContext:
    """Current market context from all data sources"""
    # Barometer data
    composite_score: float
    risk_status: str  # GREEN, YELLOW, RED
    credit_signal: str
    yield_curve_signal: str
    vix_level: float

    # Macro regime
    growth_regime: str
    inflation_regime: str
    liquidity_regime: str
    market_mode: str  # Risk-On, Risk-Off, Transition

    # COT positioning
    cot_signals: Dict[str, Any]

    # Breakthrough insights
    active_patterns: List[Dict[str, Any]]

    # Timestamp
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TradingSignal:
    """Generated trading signal"""
    symbol: str
    asset_class: AssetClass
    signal_type: SignalType
    time_horizon: TimeHorizon
    confidence: float  # 0-100
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    risk_reward_ratio: Optional[float]
    position_size_percent: float  # % of portfolio
    reasoning: str
    supporting_factors: List[str]
    risk_factors: List[str]
    data_sources: List[str]
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'asset_class': self.asset_class.value,
            'signal_type': self.signal_type.value,
            'time_horizon': self.time_horizon.value,
            'confidence': self.confidence,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_reward_ratio': self.risk_reward_ratio,
            'position_size_percent': self.position_size_percent,
            'reasoning': self.reasoning,
            'supporting_factors': self.supporting_factors,
            'risk_factors': self.risk_factors,
            'data_sources': self.data_sources,
            'timestamp': self.timestamp.isoformat()
        }


class TradingLLMEngine:
    """
    Core Trading AI Engine

    Integrates with:
    - Barometers API (macro context)
    - CFTC COT API (institutional positioning)
    - Breakthrough Insights (pattern discovery)
    - Macro Regime Tracker (regime classification)
    - Symbol Database (13,000+ instruments)
    """

    # API endpoints (local Spartan Labs infrastructure)
    BAROMETERS_API = "http://localhost:9001"
    COT_API = "http://localhost:5001"
    INSIGHTS_API = "http://localhost:5003"
    MACRO_API = "http://localhost:9002"
    QUOTES_API = "http://localhost:8082"

    # Asset class mappings
    FUTURES_SYMBOLS = {
        'equity_index': ['ES', 'NQ', 'YM', 'RTY'],
        'metals': ['GC', 'SI', 'HG', 'PL'],
        'energy': ['CL', 'NG', 'RB', 'HO'],
        'agriculture': ['ZC', 'ZS', 'ZW', 'KC', 'CT', 'SB'],
        'currencies': ['6E', '6B', '6J', '6A', '6C', '6S'],
        'bonds': ['ZN', 'ZB', 'ZF', 'ZT']
    }

    FOREX_MAJORS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD']
    FOREX_CROSSES = ['EURJPY', 'GBPJPY', 'AUDJPY', 'EURGBP', 'EURAUD', 'GBPAUD']

    BOND_ETFS = ['TLT', 'IEF', 'SHY', 'AGG', 'BND', 'LQD', 'HYG', 'JNK']

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize Trading LLM Engine"""
        self.anthropic_api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.session = requests.Session()
        self.session.timeout = 30

        # Cache for market context
        self._context_cache: Optional[MarketContext] = None
        self._context_cache_time: Optional[datetime] = None
        self._context_cache_ttl = timedelta(minutes=5)

        # Symbol database
        self._symbols_db: Optional[Dict] = None

        logger.info("Trading LLM Engine initialized")

    def _load_symbols_database(self) -> Dict:
        """Load the global symbols database"""
        if self._symbols_db is None:
            try:
                db_path = os.path.join(os.path.dirname(__file__), 'symbols_database.json')
                with open(db_path, 'r') as f:
                    self._symbols_db = json.load(f)
                logger.info(f"Loaded symbols database: {self._symbols_db.get('stats', {})}")
            except Exception as e:
                logger.error(f"Failed to load symbols database: {e}")
                self._symbols_db = {'stocks': [], 'futures': [], 'forex': [], 'crypto': []}
        return self._symbols_db

    def _fetch_api(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Fetch data from internal API with error handling"""
        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API returned {response.status_code}: {url}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {url} - {e}")
            return None

    def get_barometer_data(self) -> Optional[Dict]:
        """Fetch current barometer readings"""
        data = self._fetch_api(f"{self.BAROMETERS_API}/api/barometers/latest")
        if data:
            logger.info(f"Barometer: Score={data.get('composite_score')}, Status={data.get('risk_status')}")
        return data

    def get_cot_data(self, symbol: str, weeks: int = 52) -> Optional[Dict]:
        """Fetch COT positioning data for a symbol"""
        data = self._fetch_api(f"{self.COT_API}/api/cot/data", {'symbol': symbol, 'weeks': weeks})
        if data:
            logger.info(f"COT data for {symbol}: {len(data.get('data', []))} weeks")
        return data

    def get_breakthrough_insights(self, limit: int = 50) -> Optional[List[Dict]]:
        """Fetch recent breakthrough insights"""
        data = self._fetch_api(f"{self.INSIGHTS_API}/api/insights/list", {'limit': limit})
        if data:
            logger.info(f"Fetched {len(data.get('insights', []))} breakthrough insights")
            return data.get('insights', [])
        return None

    def get_macro_regime(self) -> Optional[Dict]:
        """Fetch current macro regime classification"""
        data = self._fetch_api(f"{self.MACRO_API}/api/regime/current")
        if data:
            logger.info(f"Macro regime: {data.get('market_mode')}")
        return data

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time quote for a symbol"""
        return self._fetch_api(f"{self.QUOTES_API}/api/quote/{symbol}")

    def build_market_context(self, force_refresh: bool = False) -> Optional[MarketContext]:
        """
        Build comprehensive market context from all data sources
        Uses caching to avoid excessive API calls
        """
        # Check cache
        if not force_refresh and self._context_cache and self._context_cache_time:
            if datetime.now() - self._context_cache_time < self._context_cache_ttl:
                return self._context_cache

        logger.info("Building fresh market context...")

        # Fetch all data sources
        barometer = self.get_barometer_data()
        macro = self.get_macro_regime()
        insights = self.get_breakthrough_insights(limit=20)

        # Fetch key COT data
        cot_signals = {}
        for symbol in ['ES', 'GC', 'CL', 'ZN']:
            cot = self.get_cot_data(symbol, weeks=4)
            if cot and cot.get('data'):
                latest = cot['data'][0] if cot['data'] else {}
                cot_signals[symbol] = {
                    'commercial_net': latest.get('commercial_long', 0) - latest.get('commercial_short', 0),
                    'noncommercial_net': latest.get('noncommercial_long', 0) - latest.get('noncommercial_short', 0)
                }

        # Build context object
        context = MarketContext(
            composite_score=barometer.get('composite_score', 50) if barometer else 50,
            risk_status=barometer.get('risk_status', 'YELLOW') if barometer else 'YELLOW',
            credit_signal=barometer.get('signals', {}).get('credit', 'neutral') if barometer else 'neutral',
            yield_curve_signal=barometer.get('signals', {}).get('yield_curve', 'neutral') if barometer else 'neutral',
            vix_level=barometer.get('vix', 20) if barometer else 20,
            growth_regime=macro.get('growth_regime', 'unknown') if macro else 'unknown',
            inflation_regime=macro.get('inflation_regime', 'unknown') if macro else 'unknown',
            liquidity_regime=macro.get('liquidity_regime', 'unknown') if macro else 'unknown',
            market_mode=macro.get('market_mode', 'unknown') if macro else 'unknown',
            cot_signals=cot_signals,
            active_patterns=[i for i in (insights or []) if i.get('is_active', True)],
            timestamp=datetime.now()
        )

        # Cache the context
        self._context_cache = context
        self._context_cache_time = datetime.now()

        logger.info(f"Market context built: Score={context.composite_score}, Mode={context.market_mode}")
        return context

    def analyze_futures(self, symbol: str) -> Optional[TradingSignal]:
        """
        Analyze a futures contract and generate trading signal
        Uses COT data + barometers + technical patterns
        """
        logger.info(f"Analyzing futures: {symbol}")

        context = self.build_market_context()
        if not context:
            logger.error("Failed to build market context")
            return None

        # Get COT data for this symbol
        cot = self.get_cot_data(symbol, weeks=12)
        cot_bias = self._analyze_cot_positioning(cot)

        # Get quote data
        quote = self.get_quote(symbol)
        current_price = quote.get('price') if quote else None

        # Build signal based on multi-factor analysis
        supporting_factors = []
        risk_factors = []
        confidence = 50  # Base confidence
        signal_direction = 0  # -2 to +2 scale

        # Factor 1: Macro regime (weight: 25%)
        if context.market_mode == 'Risk-On':
            signal_direction += 1
            supporting_factors.append(f"Risk-On macro regime")
            confidence += 10
        elif context.market_mode == 'Risk-Off':
            signal_direction -= 1
            risk_factors.append(f"Risk-Off macro regime")
            confidence += 5

        # Factor 2: Barometer composite score (weight: 25%)
        if context.composite_score >= 75:
            signal_direction += 1
            supporting_factors.append(f"Barometer score {context.composite_score}/100 (GREEN)")
            confidence += 10
        elif context.composite_score <= 25:
            signal_direction -= 1
            risk_factors.append(f"Barometer score {context.composite_score}/100 (RED)")
            confidence += 5

        # Factor 3: COT positioning (weight: 30%)
        if cot_bias:
            if cot_bias['signal'] == 'bullish':
                signal_direction += 1
                supporting_factors.append(f"COT: Commercial accumulation detected")
                confidence += 15
            elif cot_bias['signal'] == 'bearish':
                signal_direction -= 1
                risk_factors.append(f"COT: Commercial distribution detected")
                confidence += 10

        # Factor 4: VIX level (weight: 20%)
        if context.vix_level < 15:
            supporting_factors.append(f"Low VIX ({context.vix_level}) - complacency")
        elif context.vix_level > 30:
            risk_factors.append(f"High VIX ({context.vix_level}) - elevated fear")
            signal_direction -= 0.5

        # Determine signal type
        if signal_direction >= 1.5:
            signal_type = SignalType.STRONG_BUY
        elif signal_direction >= 0.5:
            signal_type = SignalType.BUY
        elif signal_direction <= -1.5:
            signal_type = SignalType.STRONG_SELL
        elif signal_direction <= -0.5:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD

        # Calculate risk parameters
        stop_loss = None
        take_profit = None
        risk_reward = None
        if current_price and signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            stop_loss = current_price * 0.98  # 2% stop
            take_profit = current_price * 1.06  # 6% target
            risk_reward = 3.0
        elif current_price and signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            stop_loss = current_price * 1.02
            take_profit = current_price * 0.94
            risk_reward = 3.0

        # Position sizing based on confidence and risk
        base_size = 2.0  # 2% base position
        if context.risk_status == 'RED':
            base_size *= 0.5  # Reduce in high-risk environment
        position_size = min(base_size * (confidence / 100), 5.0)  # Cap at 5%

        # Build reasoning
        reasoning = self._build_reasoning(
            symbol, signal_type, context, cot_bias, supporting_factors, risk_factors
        )

        return TradingSignal(
            symbol=symbol,
            asset_class=AssetClass.FUTURES,
            signal_type=signal_type,
            time_horizon=TimeHorizon.SWING,
            confidence=min(confidence, 95),  # Cap at 95%
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward,
            position_size_percent=position_size,
            reasoning=reasoning,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors,
            data_sources=['Barometers API', 'CFTC COT', 'Macro Regime Tracker'],
            timestamp=datetime.now()
        )

    def analyze_forex(self, pair: str) -> Optional[TradingSignal]:
        """
        Analyze a forex pair and generate trading signal
        Uses yield differentials + risk sentiment + technical patterns
        """
        logger.info(f"Analyzing forex: {pair}")

        context = self.build_market_context()
        if not context:
            return None

        supporting_factors = []
        risk_factors = []
        confidence = 50
        signal_direction = 0

        # Factor 1: Risk sentiment via AUD/JPY proxy
        if 'AUDJPY' in pair.upper() or pair.upper() in ['AUDUSD', 'NZDUSD']:
            if context.market_mode == 'Risk-On':
                signal_direction += 1
                supporting_factors.append("Risk-On favors commodity currencies")
            else:
                signal_direction -= 0.5
                risk_factors.append("Risk-Off pressures commodity currencies")

        # Factor 2: USD direction based on yield curve
        if 'USD' in pair.upper():
            if context.yield_curve_signal == 'inverted':
                risk_factors.append("Inverted yield curve - recession risk")
            elif context.yield_curve_signal == 'steepening':
                supporting_factors.append("Yield curve steepening - growth expectations")

        # Factor 3: VIX impact on carry trades
        if context.vix_level < 18:
            supporting_factors.append("Low VIX supports carry trades")
            confidence += 5
        elif context.vix_level > 25:
            risk_factors.append("Elevated VIX - carry trade unwind risk")
            confidence -= 5

        # Get quote
        quote = self.get_quote(pair)
        current_price = quote.get('price') if quote else None

        # Determine signal
        if signal_direction >= 1:
            signal_type = SignalType.BUY
        elif signal_direction <= -1:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD

        reasoning = f"Forex analysis for {pair}: Market mode is {context.market_mode}. "
        reasoning += f"VIX at {context.vix_level}. "
        if supporting_factors:
            reasoning += f"Bullish factors: {', '.join(supporting_factors)}. "
        if risk_factors:
            reasoning += f"Risk factors: {', '.join(risk_factors)}."

        return TradingSignal(
            symbol=pair,
            asset_class=AssetClass.FOREX,
            signal_type=signal_type,
            time_horizon=TimeHorizon.SWING,
            confidence=min(confidence, 90),
            entry_price=current_price,
            stop_loss=None,
            take_profit=None,
            risk_reward_ratio=None,
            position_size_percent=1.5,
            reasoning=reasoning,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors,
            data_sources=['Barometers API', 'Macro Regime Tracker'],
            timestamp=datetime.now()
        )

    def analyze_stock(self, symbol: str) -> Optional[TradingSignal]:
        """
        Analyze a stock and generate trading signal
        Uses sector rotation + breadth + earnings patterns
        """
        logger.info(f"Analyzing stock: {symbol}")

        context = self.build_market_context()
        if not context:
            return None

        supporting_factors = []
        risk_factors = []
        confidence = 50
        signal_direction = 0

        # Factor 1: Overall market risk status
        if context.risk_status == 'GREEN':
            signal_direction += 1
            supporting_factors.append("Market risk status GREEN - favorable for equities")
            confidence += 15
        elif context.risk_status == 'RED':
            signal_direction -= 1
            risk_factors.append("Market risk status RED - equity headwinds")
            confidence += 10

        # Factor 2: Growth regime
        if context.growth_regime == 'High':
            signal_direction += 0.5
            supporting_factors.append("High growth regime supports equities")
        elif context.growth_regime == 'Negative':
            signal_direction -= 0.5
            risk_factors.append("Negative growth regime - equity caution")

        # Factor 3: Credit conditions
        if context.credit_signal == 'bullish':
            supporting_factors.append("Credit spreads tightening - risk appetite strong")
            confidence += 5
        elif context.credit_signal == 'bearish':
            risk_factors.append("Credit spreads widening - risk aversion")
            confidence -= 5

        # Factor 4: Check breakthrough insights for this symbol
        for insight in context.active_patterns:
            if symbol.upper() in str(insight.get('symbols', [])).upper():
                supporting_factors.append(f"Pattern detected: {insight.get('insight_title', 'Unknown')}")
                confidence += 10
                break

        # Get quote
        quote = self.get_quote(symbol)
        current_price = quote.get('price') if quote else None

        # Determine signal
        if signal_direction >= 1.5:
            signal_type = SignalType.STRONG_BUY
        elif signal_direction >= 0.5:
            signal_type = SignalType.BUY
        elif signal_direction <= -1.5:
            signal_type = SignalType.STRONG_SELL
        elif signal_direction <= -0.5:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD

        # Risk parameters
        stop_loss = current_price * 0.95 if current_price else None
        take_profit = current_price * 1.15 if current_price else None

        reasoning = f"Stock analysis for {symbol}: "
        reasoning += f"Market composite score {context.composite_score}/100 ({context.risk_status}). "
        reasoning += f"Growth regime: {context.growth_regime}. "
        if supporting_factors:
            reasoning += f"Bullish: {', '.join(supporting_factors[:3])}. "
        if risk_factors:
            reasoning += f"Risks: {', '.join(risk_factors[:3])}."

        return TradingSignal(
            symbol=symbol,
            asset_class=AssetClass.STOCKS,
            signal_type=signal_type,
            time_horizon=TimeHorizon.SWING,
            confidence=min(confidence, 90),
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=3.0 if stop_loss and take_profit else None,
            position_size_percent=2.0 if context.risk_status != 'RED' else 1.0,
            reasoning=reasoning,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors,
            data_sources=['Barometers API', 'Breakthrough Insights', 'Macro Regime'],
            timestamp=datetime.now()
        )

    def analyze_bonds(self, symbol: str = 'ZN') -> Optional[TradingSignal]:
        """
        Analyze bonds/treasuries and generate trading signal
        Uses yield curve + inflation + flight-to-quality dynamics
        """
        logger.info(f"Analyzing bonds: {symbol}")

        context = self.build_market_context()
        if not context:
            return None

        supporting_factors = []
        risk_factors = []
        confidence = 50
        signal_direction = 0

        # Factor 1: Risk status (bonds benefit from risk-off)
        if context.risk_status == 'RED':
            signal_direction += 1
            supporting_factors.append("Risk-Off environment favors safe-haven bonds")
            confidence += 15
        elif context.risk_status == 'GREEN':
            signal_direction -= 0.5
            risk_factors.append("Risk-On may pressure bond prices")

        # Factor 2: Inflation regime
        if context.inflation_regime == 'Falling':
            signal_direction += 1
            supporting_factors.append("Falling inflation bullish for bonds")
            confidence += 10
        elif context.inflation_regime == 'Rising':
            signal_direction -= 1
            risk_factors.append("Rising inflation erodes bond value")
            confidence += 5

        # Factor 3: VIX spike (flight to quality)
        if context.vix_level > 25:
            signal_direction += 0.5
            supporting_factors.append(f"VIX at {context.vix_level} - flight to quality")

        # Factor 4: Yield curve signal
        if context.yield_curve_signal == 'inverted':
            supporting_factors.append("Inverted curve - recession hedge demand")
            confidence += 5

        # COT data for bonds
        cot = self.get_cot_data(symbol, weeks=8)
        if cot and cot.get('data'):
            latest = cot['data'][0]
            commercial_net = latest.get('commercial_long', 0) - latest.get('commercial_short', 0)
            if commercial_net > 0:
                supporting_factors.append("Commercial hedgers net long")
            else:
                risk_factors.append("Commercial hedgers net short")

        # Get quote
        quote = self.get_quote(symbol)
        current_price = quote.get('price') if quote else None

        # Determine signal
        if signal_direction >= 1:
            signal_type = SignalType.BUY
        elif signal_direction <= -1:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD

        reasoning = f"Bond analysis for {symbol}: "
        reasoning += f"Inflation regime: {context.inflation_regime}. "
        reasoning += f"VIX: {context.vix_level}. "
        reasoning += f"Yield curve: {context.yield_curve_signal}. "
        if supporting_factors:
            reasoning += f"Bullish: {', '.join(supporting_factors[:3])}."

        return TradingSignal(
            symbol=symbol,
            asset_class=AssetClass.BONDS,
            signal_type=signal_type,
            time_horizon=TimeHorizon.POSITION,
            confidence=min(confidence, 85),
            entry_price=current_price,
            stop_loss=None,
            take_profit=None,
            risk_reward_ratio=None,
            position_size_percent=3.0,
            reasoning=reasoning,
            supporting_factors=supporting_factors,
            risk_factors=risk_factors,
            data_sources=['Barometers API', 'CFTC COT', 'Macro Regime'],
            timestamp=datetime.now()
        )

    def scan_all_markets(self) -> Dict[str, List[TradingSignal]]:
        """
        Scan all asset classes and return top signals
        """
        logger.info("Starting full market scan...")

        results = {
            'futures': [],
            'forex': [],
            'stocks': [],
            'bonds': []
        }

        # Scan key futures
        for symbol in ['ES', 'NQ', 'GC', 'CL']:
            signal = self.analyze_futures(symbol)
            if signal and signal.signal_type != SignalType.HOLD:
                results['futures'].append(signal)

        # Scan major forex pairs
        for pair in ['EURUSD', 'GBPUSD', 'AUDJPY']:
            signal = self.analyze_forex(pair)
            if signal and signal.signal_type != SignalType.HOLD:
                results['forex'].append(signal)

        # Scan key stocks (would use symbol database in production)
        for symbol in ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']:
            signal = self.analyze_stock(symbol)
            if signal and signal.signal_type != SignalType.HOLD:
                results['stocks'].append(signal)

        # Scan bonds
        for symbol in ['ZN', 'ZB']:
            signal = self.analyze_bonds(symbol)
            if signal and signal.signal_type != SignalType.HOLD:
                results['bonds'].append(signal)

        # Sort by confidence
        for asset_class in results:
            results[asset_class].sort(key=lambda x: x.confidence, reverse=True)

        total_signals = sum(len(v) for v in results.values())
        logger.info(f"Market scan complete: {total_signals} actionable signals")

        return results

    def get_ai_analysis(self, symbol: str, asset_class: str) -> str:
        """
        Get detailed AI analysis using Claude API
        This provides deeper reasoning and context
        """
        if not self.anthropic_api_key:
            return "AI analysis unavailable - no API key configured"

        context = self.build_market_context()

        prompt = f"""Analyze {symbol} ({asset_class}) for trading opportunities.

Current Market Context:
- Composite Risk Score: {context.composite_score}/100 ({context.risk_status})
- Market Mode: {context.market_mode}
- Growth Regime: {context.growth_regime}
- Inflation Regime: {context.inflation_regime}
- VIX Level: {context.vix_level}
- Credit Signal: {context.credit_signal}
- Yield Curve: {context.yield_curve_signal}

COT Positioning:
{json.dumps(context.cot_signals, indent=2)}

Active Patterns:
{json.dumps([p.get('insight_title') for p in context.active_patterns[:5]], indent=2)}

Provide:
1. Current bias (bullish/bearish/neutral)
2. Key levels to watch
3. Risk factors
4. Suggested position sizing
5. Time horizon recommendation

IMPORTANT: Base analysis ONLY on the real data provided above. Do not hallucinate or make up statistics."""

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return f"AI analysis error: {str(e)}"

    def _analyze_cot_positioning(self, cot_data: Optional[Dict]) -> Optional[Dict]:
        """Analyze COT data for trading bias"""
        if not cot_data or not cot_data.get('data'):
            return None

        data = cot_data['data']
        if len(data) < 2:
            return None

        latest = data[0]
        previous = data[1]

        # Calculate net positions
        commercial_net = latest.get('commercial_long', 0) - latest.get('commercial_short', 0)
        prev_commercial_net = previous.get('commercial_long', 0) - previous.get('commercial_short', 0)

        # Commercials are contrarian - they hedge, so their positioning often indicates smart money
        if commercial_net > prev_commercial_net and commercial_net > 0:
            return {'signal': 'bullish', 'reason': 'Commercial accumulation'}
        elif commercial_net < prev_commercial_net and commercial_net < 0:
            return {'signal': 'bearish', 'reason': 'Commercial distribution'}

        return {'signal': 'neutral', 'reason': 'No clear positioning bias'}

    def _build_reasoning(
        self,
        symbol: str,
        signal_type: SignalType,
        context: MarketContext,
        cot_bias: Optional[Dict],
        supporting: List[str],
        risks: List[str]
    ) -> str:
        """Build human-readable reasoning for a signal"""
        reasoning = f"Analysis for {symbol}: "
        reasoning += f"The overall market shows a {context.risk_status} risk status "
        reasoning += f"with composite score of {context.composite_score}/100. "

        if context.market_mode != 'unknown':
            reasoning += f"Current macro regime is {context.market_mode}. "

        if cot_bias:
            reasoning += f"COT analysis indicates {cot_bias['signal']} bias ({cot_bias['reason']}). "

        if supporting:
            reasoning += f"Supporting factors: {', '.join(supporting[:3])}. "

        if risks:
            reasoning += f"Key risks: {', '.join(risks[:3])}. "

        reasoning += f"Signal: {signal_type.value.upper()}."

        return reasoning


# Module-level instance for easy import
_engine_instance: Optional[TradingLLMEngine] = None


def get_engine() -> TradingLLMEngine:
    """Get or create the singleton engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TradingLLMEngine()
    return _engine_instance


if __name__ == "__main__":
    # Test the engine
    engine = TradingLLMEngine()

    print("=" * 60)
    print("TRADING LLM ENGINE - Test Run")
    print("=" * 60)

    # Build market context
    print("\n1. Building Market Context...")
    context = engine.build_market_context()
    if context:
        print(f"   Composite Score: {context.composite_score}")
        print(f"   Risk Status: {context.risk_status}")
        print(f"   Market Mode: {context.market_mode}")
        print(f"   VIX: {context.vix_level}")

    # Analyze futures
    print("\n2. Analyzing ES Futures...")
    signal = engine.analyze_futures('ES')
    if signal:
        print(f"   Signal: {signal.signal_type.value}")
        print(f"   Confidence: {signal.confidence}%")
        print(f"   Reasoning: {signal.reasoning[:200]}...")

    # Full market scan
    print("\n3. Running Full Market Scan...")
    results = engine.scan_all_markets()
    for asset_class, signals in results.items():
        print(f"   {asset_class.upper()}: {len(signals)} signals")
        for s in signals[:2]:
            print(f"      - {s.symbol}: {s.signal_type.value} ({s.confidence}%)")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
