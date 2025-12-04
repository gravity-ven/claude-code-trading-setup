#!/usr/bin/env python3
"""
Simple test to verify Claude AI connection works.

This is a minimal test before running the full trading system.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_claude_api():
    """Test Claude API connection."""
    print("=" * 50)
    print("Testing Claude AI Connection")
    print("=" * 50)
    print()

    # Check if API key is set
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in .env file")
        print()
        print("Please:")
        print("1. Copy .env.example to .env")
        print("2. Add your Anthropic API key")
        print("3. Run this test again")
        return False

    if api_key.startswith("your_"):
        print("❌ ANTHROPIC_API_KEY is still the placeholder value")
        print()
        print("Please edit .env and add your real API key from:")
        print("https://console.anthropic.com/")
        return False

    print("✓ API key found")
    print()

    # Try to import anthropic
    try:
        import anthropic
        print("✓ Anthropic library installed")
    except ImportError:
        print("❌ Anthropic library not installed")
        print("Run: pip install anthropic")
        return False

    # Test API call
    print()
    print("Testing API call...")
    print()

    try:
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Analyze this market condition in one sentence: AAPL is up 2% with strong volume."
                }
            ]
        )

        response_text = message.content[0].text

        print("✓ API call successful!")
        print()
        print("Claude's response:")
        print("-" * 50)
        print(response_text)
        print("-" * 50)
        print()

        print("=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
        print()
        print("You're ready to start paper trading!")
        print("Run: python examples/basic_trading.py")
        print()

        return True

    except anthropic.AuthenticationError:
        print("❌ Authentication failed")
        print("Your API key is invalid. Please check:")
        print("1. You copied the full key (starts with sk-ant-)")
        print("2. The key is still active in your Anthropic account")
        return False

    except anthropic.RateLimitError:
        print("❌ Rate limit exceeded")
        print("You've made too many requests. Wait a moment and try again.")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_market_analysis():
    """Test a simple market analysis with Claude."""
    print()
    print("=" * 50)
    print("Testing Market Analysis")
    print("=" * 50)
    print()

    try:
        from src.core.claude_engine import ClaudeEngine
        from src.utils.config import ClaudeConfig

        api_key = os.getenv("ANTHROPIC_API_KEY")

        config = ClaudeConfig(
            model="claude-sonnet-4-5-20250929",
            api_key=api_key,
            max_tokens=1000
        )

        engine = ClaudeEngine(config)

        # Sample market data
        sample_market_data = {
            "AAPL": {
                "current_price": 178.50,
                "change_percent": 1.5,
                "volume": 45000000,
                "trend": "uptrend"
            },
            "MSFT": {
                "current_price": 395.20,
                "change_percent": -0.5,
                "volume": 23000000,
                "trend": "neutral"
            }
        }

        print("Asking Claude to analyze market conditions...")
        print()

        analysis = await engine.analyze_market(
            market_data=sample_market_data,
            news=["Tech stocks rally on positive earnings", "Fed holds rates steady"],
            sentiment={"overall": "positive", "score": 0.65}
        )

        print("✓ Market analysis complete!")
        print()
        print("Analysis Results:")
        print("-" * 50)
        print(f"Market Regime: {analysis.get('market_regime', 'unknown')}")
        print(f"Overall Trend: {analysis.get('overall_trend', 'unknown')}")
        print(f"Volatility: {analysis.get('volatility_level', 'unknown')}")
        print(f"Confidence: {analysis.get('confidence', 0):.2f}")

        if analysis.get('key_observations'):
            print()
            print("Key Observations:")
            for obs in analysis['key_observations'][:3]:
                print(f"  • {obs}")

        print("-" * 50)
        print()
        print("✅ Market analysis test passed!")
        print()

        return True

    except Exception as e:
        print(f"❌ Error during market analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print()

    # Test 1: Basic API connection
    api_test = await test_claude_api()

    if not api_test:
        print("⚠️  Fix the API connection before proceeding")
        return

    # Test 2: Market analysis
    await asyncio.sleep(2)  # Brief pause between tests
    analysis_test = await test_market_analysis()

    if analysis_test:
        print("=" * 50)
        print("🎉 All Systems Ready!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("1. Review config/config.yaml")
        print("2. Run: python examples/basic_trading.py")
        print("3. Watch Claude make trading decisions!")
        print()


if __name__ == "__main__":
    asyncio.run(main())
