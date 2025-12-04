"""
Claude AI Engine - The brain of the Spartan Trading Agent.

This module handles all interactions with Claude AI for:
- Market analysis
- Strategy generation
- Trade decision making
- Risk assessment
- Portfolio management
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import anthropic
from anthropic.types import Message
import structlog

from ..utils.config import ClaudeConfig


logger = structlog.get_logger()


class ClaudeEngine:
    """
    Main Claude AI engine for trading decisions.

    This class manages all Claude API interactions and provides
    high-level methods for different trading tasks.
    """

    def __init__(self, config: ClaudeConfig):
        """
        Initialize Claude engine.

        Args:
            config: Claude configuration
        """
        self.config = config
        self.client = anthropic.AsyncAnthropic(api_key=config.api_key)
        self.conversation_history: List[Dict[str, str]] = []

        logger.info(
            "claude_engine_initialized",
            model=config.model,
            max_tokens=config.max_tokens
        )

    async def analyze_market(
        self,
        market_data: Dict[str, Any],
        news: Optional[List[str]] = None,
        sentiment: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze current market conditions using Claude.

        Args:
            market_data: Current market data (prices, volumes, indicators)
            news: Recent news articles
            sentiment: Sentiment analysis data

        Returns:
            Market analysis with regime detection, trends, and opportunities
        """
        prompt = self._build_market_analysis_prompt(market_data, news, sentiment)

        response = await self._call_claude(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["market_analysis"]
        )

        analysis = self._parse_json_response(response)

        logger.info(
            "market_analysis_completed",
            regime=analysis.get("market_regime"),
            trend=analysis.get("overall_trend")
        )

        return analysis

    async def generate_trading_signals(
        self,
        market_analysis: Dict[str, Any],
        portfolio: Dict[str, Any],
        strategy_type: str = "momentum"
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on market analysis.

        Args:
            market_analysis: Output from analyze_market()
            portfolio: Current portfolio state
            strategy_type: Type of strategy to use

        Returns:
            List of trading signals with reasoning
        """
        prompt = self._build_signal_generation_prompt(
            market_analysis,
            portfolio,
            strategy_type
        )

        response = await self._call_claude(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["signal_generation"]
        )

        signals = self._parse_json_response(response)

        logger.info(
            "signals_generated",
            num_signals=len(signals.get("signals", [])),
            strategy=strategy_type
        )

        return signals.get("signals", [])

    async def assess_trade_risk(
        self,
        trade: Dict[str, Any],
        portfolio: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess risk for a proposed trade.

        Args:
            trade: Proposed trade details
            portfolio: Current portfolio state
            market_conditions: Current market conditions

        Returns:
            Risk assessment with score, warnings, and recommendations
        """
        prompt = self._build_risk_assessment_prompt(
            trade,
            portfolio,
            market_conditions
        )

        response = await self._call_claude(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["risk_assessment"]
        )

        risk_assessment = self._parse_json_response(response)

        logger.info(
            "risk_assessed",
            symbol=trade.get("symbol"),
            risk_score=risk_assessment.get("risk_score"),
            approved=risk_assessment.get("approved")
        )

        return risk_assessment

    async def optimize_portfolio(
        self,
        current_portfolio: Dict[str, Any],
        market_conditions: Dict[str, Any],
        available_capital: float
    ) -> Dict[str, Any]:
        """
        Optimize portfolio allocation using Claude.

        Args:
            current_portfolio: Current positions and allocations
            market_conditions: Current market analysis
            available_capital: Available cash for rebalancing

        Returns:
            Optimized portfolio allocations with reasoning
        """
        prompt = self._build_portfolio_optimization_prompt(
            current_portfolio,
            market_conditions,
            available_capital
        )

        response = await self._call_claude(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["portfolio_optimization"]
        )

        optimization = self._parse_json_response(response)

        logger.info(
            "portfolio_optimized",
            num_changes=len(optimization.get("recommended_changes", []))
        )

        return optimization

    async def explain_decision(
        self,
        trade: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Get a human-readable explanation for a trading decision.

        Args:
            trade: Trade that was executed
            context: Context that led to the decision

        Returns:
            Natural language explanation
        """
        prompt = self._build_explanation_prompt(trade, context)

        response = await self._call_claude(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS["explanation"]
        )

        return response.content[0].text

    async def _call_claude(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Message:
        """
        Make an API call to Claude.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Optional max tokens override
            temperature: Optional temperature override

        Returns:
            Claude API response
        """
        try:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                # Enable extended thinking for complex decisions
                thinking={
                    "type": "enabled",
                    "budget_tokens": 10000
                } if self.config.extended_thinking else None
            )

            logger.debug(
                "claude_api_call",
                model=self.config.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens
            )

            return response

        except Exception as e:
            logger.error("claude_api_error", error=str(e))
            raise

    def _parse_json_response(self, response: Message) -> Dict[str, Any]:
        """
        Parse JSON from Claude's response.

        Args:
            response: Claude API response

        Returns:
            Parsed JSON data
        """
        try:
            # Extract text from response
            text = response.content[0].text

            # Find JSON in response (Claude often wraps it in markdown)
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                json_text = text[json_start:json_end].strip()
            elif "```" in text:
                json_start = text.find("```") + 3
                json_end = text.find("```", json_start)
                json_text = text[json_start:json_end].strip()
            else:
                json_text = text

            return json.loads(json_text)

        except json.JSONDecodeError as e:
            logger.error("json_parse_error", error=str(e), response=text[:500])
            # Return empty dict as fallback
            return {}

    def _build_market_analysis_prompt(
        self,
        market_data: Dict[str, Any],
        news: Optional[List[str]],
        sentiment: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for market analysis."""
        prompt_parts = [
            "Analyze the current market conditions based on the following data:",
            "",
            "## Market Data",
            json.dumps(market_data, indent=2),
        ]

        if news:
            prompt_parts.extend([
                "",
                "## Recent News",
                "\n".join(f"- {article}" for article in news[:10])
            ])

        if sentiment:
            prompt_parts.extend([
                "",
                "## Sentiment Data",
                json.dumps(sentiment, indent=2)
            ])

        prompt_parts.extend([
            "",
            "Provide your analysis in JSON format with the following structure:",
            "```json",
            "{",
            '  "market_regime": "bullish|bearish|neutral|volatile",',
            '  "overall_trend": "uptrend|downtrend|sideways",',
            '  "volatility_level": "low|medium|high|extreme",',
            '  "key_observations": ["observation1", "observation2"],',
            '  "opportunities": [{"symbol": "XXX", "reason": "..."}],',
            '  "risks": ["risk1", "risk2"],',
            '  "confidence": 0.0-1.0',
            "}",
            "```"
        ])

        return "\n".join(prompt_parts)

    def _build_signal_generation_prompt(
        self,
        market_analysis: Dict[str, Any],
        portfolio: Dict[str, Any],
        strategy_type: str
    ) -> str:
        """Build prompt for trading signal generation."""
        return f"""
Based on the market analysis and current portfolio, generate trading signals using a {strategy_type} strategy.

## Market Analysis
{json.dumps(market_analysis, indent=2)}

## Current Portfolio
{json.dumps(portfolio, indent=2)}

## Strategy Type
{strategy_type}

Generate trading signals in JSON format:
```json
{{
  "signals": [
    {{
      "symbol": "AAPL",
      "action": "buy|sell|hold",
      "quantity": 100,
      "entry_price": 150.0,
      "stop_loss": 145.0,
      "take_profit": 160.0,
      "reasoning": "Detailed reasoning for this trade",
      "confidence": 0.8,
      "timeframe": "1h|1d|1w",
      "risk_reward_ratio": 2.0
    }}
  ],
  "overall_strategy": "Description of overall strategy",
  "market_assumption": "Assumptions about market conditions"
}}
```
"""

    def _build_risk_assessment_prompt(
        self,
        trade: Dict[str, Any],
        portfolio: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> str:
        """Build prompt for risk assessment."""
        return f"""
Assess the risk of the following proposed trade:

## Proposed Trade
{json.dumps(trade, indent=2)}

## Current Portfolio
{json.dumps(portfolio, indent=2)}

## Market Conditions
{json.dumps(market_conditions, indent=2)}

Provide risk assessment in JSON format:
```json
{{
  "risk_score": 0.0-1.0,
  "approved": true/false,
  "risk_factors": [
    {{
      "factor": "concentration_risk",
      "severity": "low|medium|high",
      "description": "..."
    }}
  ],
  "warnings": ["warning1", "warning2"],
  "recommendations": ["recommendation1", "recommendation2"],
  "position_size_adjustment": 1.0,
  "reasoning": "Detailed reasoning"
}}
```
"""

    def _build_portfolio_optimization_prompt(
        self,
        current_portfolio: Dict[str, Any],
        market_conditions: Dict[str, Any],
        available_capital: float
    ) -> str:
        """Build prompt for portfolio optimization."""
        return f"""
Optimize the portfolio allocation based on current market conditions.

## Current Portfolio
{json.dumps(current_portfolio, indent=2)}

## Market Conditions
{json.dumps(market_conditions, indent=2)}

## Available Capital
${available_capital:,.2f}

Provide optimization recommendations in JSON format:
```json
{{
  "recommended_changes": [
    {{
      "symbol": "AAPL",
      "action": "increase|decrease|exit",
      "current_allocation": 0.15,
      "target_allocation": 0.20,
      "reasoning": "..."
    }}
  ],
  "rebalancing_trades": [
    {{
      "symbol": "AAPL",
      "action": "buy|sell",
      "quantity": 50,
      "reasoning": "..."
    }}
  ],
  "overall_strategy": "Description of optimization approach",
  "expected_impact": "Expected impact on risk/return"
}}
```
"""

    def _build_explanation_prompt(
        self,
        trade: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for trade explanation."""
        return f"""
Provide a clear, human-readable explanation for why this trade was made.

## Trade Details
{json.dumps(trade, indent=2)}

## Context
{json.dumps(context, indent=2)}

Explain in 2-3 paragraphs:
1. What market conditions led to this decision
2. What the strategy was trying to achieve
3. What risks were considered

Write in a clear, professional style suitable for a trading journal.
"""


# System prompts for different tasks
SYSTEM_PROMPTS = {
    "market_analysis": """You are a world-class quantitative analyst and market expert.
Your job is to analyze market data and provide actionable insights for trading decisions.

You have deep expertise in:
- Technical analysis (price patterns, indicators, volume analysis)
- Fundamental analysis (economic data, company financials)
- Market microstructure and sentiment analysis
- Risk assessment and position sizing

Always provide data-driven analysis with specific reasoning. Be honest about uncertainty.
When market conditions are unclear, acknowledge it and suggest caution.""",

    "signal_generation": """You are an expert algorithmic trader specializing in systematic strategies.
Your job is to generate high-probability trading signals based on market analysis.

You excel at:
- Identifying trade setups with favorable risk/reward ratios
- Timing entries and exits precisely
- Setting appropriate stop-losses and take-profits
- Managing position sizing based on volatility

Only suggest trades when you have strong conviction. Quality over quantity.
Every trade should have clear entry, exit, and risk management parameters.""",

    "risk_assessment": """You are a strict risk manager protecting trading capital.
Your job is to evaluate every trade for potential risks and prevent costly mistakes.

You focus on:
- Position sizing relative to account size
- Portfolio concentration and correlation risks
- Market condition risks (volatility, liquidity)
- Drawdown protection

You are conservative and prioritize capital preservation. When in doubt, reduce risk or reject the trade.
A missed opportunity is better than a significant loss.""",

    "portfolio_optimization": """You are a portfolio manager focused on optimal capital allocation.
Your job is to maximize risk-adjusted returns through intelligent diversification.

You consider:
- Modern portfolio theory and diversification
- Market regime-dependent allocation
- Rebalancing strategies
- Tax efficiency and transaction costs

Strive for a balanced portfolio that performs well across different market conditions.
Avoid over-concentration and ensure proper risk distribution.""",

    "explanation": """You are a clear and concise communicator explaining trading decisions.
Your job is to make complex trading logic understandable to humans.

Write explanations that:
- Are clear and jargon-free (explain technical terms when used)
- Focus on the 'why' not just the 'what'
- Acknowledge risks and uncertainties
- Provide context and reasoning

Your audience includes both novice and experienced traders. Be thorough but accessible."""
}
