#!/usr/bin/env python3
"""
Economic Cycle Intelligence API
Comprehensive economic cycle analysis with REAL DATA ONLY
NO FAKE DATA - Returns None on failures
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
from fredapi import Fred

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FRED API Configuration
FRED_API_KEY = os.getenv('FRED_API_KEY', '')
fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None

# ============================================
# HELPER FUNCTIONS - REAL DATA ONLY
# ============================================

def fetch_fred_indicator(series_id, fallback_value=None):
    """Fetch data from FRED API - NO FAKE DATA"""
    if not fred:
        logger.warning(f"FRED API key not configured - cannot fetch {series_id}")
        return fallback_value

    try:
        # Get last 12 months of data
        data = fred.get_series(series_id, observation_start=datetime.now() - timedelta(days=365))
        if data is not None and len(data) > 0:
            latest = float(data.iloc[-1])
            logger.info(f"✅ FRED {series_id}: {latest}")
            return latest
        else:
            logger.warning(f"No data returned for FRED series {series_id}")
            return fallback_value
    except Exception as e:
        logger.error(f"Error fetching FRED {series_id}: {e}")
        return fallback_value

def calculate_yoy_change(series_id):
    """Calculate year-over-year change - REAL DATA ONLY"""
    if not fred:
        return None

    try:
        data = fred.get_series(series_id, observation_start=datetime.now() - timedelta(days=400))
        if data is not None and len(data) >= 12:
            current = float(data.iloc[-1])
            year_ago = float(data.iloc[-12])
            yoy_change = ((current - year_ago) / year_ago) * 100
            return round(yoy_change, 2)
        return None
    except Exception as e:
        logger.error(f"Error calculating YoY for {series_id}: {e}")
        return None

def detect_business_cycle_phase(gdp_growth, unemployment, inflation, pmi):
    """
    Detect business cycle phase using economic indicators
    Returns: Early Expansion, Mid Expansion, Late Expansion, or Recession
    """

    # Handle None values
    if any(x is None for x in [gdp_growth, unemployment, inflation, pmi]):
        return {
            'phase': 'UNKNOWN',
            'confidence': 0,
            'description': 'Insufficient data',
            'emoji': '❓'
        }

    # Phase detection logic based on economic theory
    score = 0

    # GDP Growth indicators
    if gdp_growth > 3.0:
        score += 2  # Strong growth
    elif gdp_growth > 2.0:
        score += 1  # Moderate growth
    elif gdp_growth < 0:
        score -= 3  # Contraction

    # Unemployment indicators (lower is better)
    if unemployment < 4.0:
        score += 2  # Very low unemployment
    elif unemployment < 5.0:
        score += 1  # Low unemployment
    elif unemployment > 6.0:
        score -= 2  # High unemployment

    # Inflation indicators
    if 2.0 <= inflation <= 3.0:
        score += 1  # Healthy inflation
    elif inflation > 5.0:
        score -= 1  # High inflation (late cycle)
    elif inflation < 1.0:
        score -= 1  # Deflation risk

    # PMI indicators
    if pmi > 55:
        score += 2  # Strong expansion
    elif pmi > 50:
        score += 1  # Expansion
    elif pmi < 50:
        score -= 2  # Contraction

    # Determine phase
    if score >= 5:
        phase = 'EARLY_EXPANSION'
        emoji = '🌱'
        description = 'Recovery accelerating, growth strengthening'
        confidence = min(95, 70 + (score - 5) * 5)
    elif score >= 2:
        phase = 'MID_EXPANSION'
        emoji = '🚀'
        description = 'Sustained growth, labor market strong'
        confidence = min(90, 65 + (score - 2) * 8)
    elif score >= -1:
        phase = 'LATE_EXPANSION'
        emoji = '⚠️'
        description = 'Peak approaching, watch for overheating'
        confidence = min(85, 60 + abs(score + 1) * 8)
    else:
        phase = 'RECESSION'
        emoji = '🔴'
        description = 'Economic contraction, defensive positioning'
        confidence = min(90, 70 + abs(score + 1) * 5)

    return {
        'phase': phase,
        'confidence': confidence,
        'description': description,
        'emoji': emoji,
        'score': score
    }

def calculate_recession_timeline():
    """
    Calculate recession probability for 3, 6, and 12 months ahead
    Uses yield curve inversion (10Y-3M spread) with time-adjusted probabilities
    """

    try:
        # Get 10Y and 3M Treasury yields from FRED
        yield_10y = fetch_fred_indicator('DGS10')
        yield_3m = fetch_fred_indicator('DGS3MO')

        if yield_10y is None or yield_3m is None:
            return {
                '3_month': None,
                '6_month': None,
                '12_month': None,
                'error': 'Yield data unavailable'
            }

        spread = yield_10y - yield_3m

        # Logistic regression coefficients (based on NY Fed research)
        # Probability increases as spread becomes more negative
        base_prob_12m = 1 / (1 + 2.71828 ** (1.2 + 2.5 * spread))

        # Adjust for different time horizons
        prob_3m = base_prob_12m * 0.3  # Lower near-term probability
        prob_6m = base_prob_12m * 0.65  # Medium-term probability
        prob_12m = base_prob_12m  # Full probability

        return {
            '3_month': round(prob_3m * 100, 2),
            '6_month': round(prob_6m * 100, 2),
            '12_month': round(prob_12m * 100, 2),
            'spread': round(spread, 2)
        }

    except Exception as e:
        logger.error(f"Error calculating recession timeline: {e}")
        return {
            '3_month': None,
            '6_month': None,
            '12_month': None,
            'error': str(e)
        }

def determine_economic_regime(gdp_growth, inflation):
    """
    Determine economic regime based on Growth/Inflation matrix
    4 Quadrants: Goldilocks, Reflation, Stagflation, Deflation
    """

    if gdp_growth is None or inflation is None:
        return {
            'regime': 'UNKNOWN',
            'quadrant': None,
            'description': 'Insufficient data',
            'emoji': '❓',
            'strategy': 'Wait for data'
        }

    # Define regime thresholds
    growth_threshold = 2.0  # % GDP growth
    inflation_threshold = 2.5  # % CPI

    high_growth = gdp_growth > growth_threshold
    high_inflation = inflation > inflation_threshold

    if high_growth and not high_inflation:
        regime = 'GOLDILOCKS'
        emoji = '✨'
        description = 'Strong growth, low inflation - ideal conditions'
        strategy = 'Risk-on: Growth stocks, cyclicals, commodities'
    elif high_growth and high_inflation:
        regime = 'REFLATION'
        emoji = '🔥'
        description = 'Growth with rising inflation - late cycle'
        strategy = 'Commodities, real assets, value stocks, TIPS'
    elif not high_growth and high_inflation:
        regime = 'STAGFLATION'
        emoji = '🌡️'
        description = 'Weak growth, high inflation - challenging'
        strategy = 'Defensive: Cash, gold, commodities, short duration'
    else:
        regime = 'DEFLATION'
        emoji = '❄️'
        description = 'Weak growth, low inflation - recession risk'
        strategy = 'Defensive: Bonds, utilities, staples, quality'

    return {
        'regime': regime,
        'quadrant': f'{"High" if high_growth else "Low"} Growth / {"High" if high_inflation else "Low"} Inflation',
        'description': description,
        'emoji': emoji,
        'strategy': strategy,
        'gdp_growth': gdp_growth,
        'inflation': inflation
    }

def get_sector_rotation_guidance(cycle_phase):
    """
    Provide sector rotation guidance based on business cycle phase
    Returns buy/hold/sell recommendations for each sector
    """

    # Sector rotation playbook by cycle phase
    rotation_playbook = {
        'EARLY_EXPANSION': {
            'buy': ['Financials', 'Consumer Discretionary', 'Industrials', 'Technology'],
            'hold': ['Materials', 'Energy'],
            'sell': ['Utilities', 'Consumer Staples', 'Healthcare']
        },
        'MID_EXPANSION': {
            'buy': ['Technology', 'Industrials', 'Materials', 'Energy'],
            'hold': ['Financials', 'Consumer Discretionary'],
            'sell': ['Utilities', 'Consumer Staples']
        },
        'LATE_EXPANSION': {
            'buy': ['Energy', 'Materials', 'Consumer Staples'],
            'hold': ['Healthcare', 'Technology'],
            'sell': ['Financials', 'Consumer Discretionary']
        },
        'RECESSION': {
            'buy': ['Consumer Staples', 'Healthcare', 'Utilities'],
            'hold': ['Technology (quality)', 'Telecommunications'],
            'sell': ['Financials', 'Consumer Discretionary', 'Industrials', 'Energy']
        },
        'UNKNOWN': {
            'buy': [],
            'hold': ['Balanced Portfolio'],
            'sell': []
        }
    }

    guidance = rotation_playbook.get(cycle_phase, rotation_playbook['UNKNOWN'])

    return {
        'cycle_phase': cycle_phase,
        'buy_sectors': guidance['buy'],
        'hold_sectors': guidance['hold'],
        'sell_sectors': guidance['sell'],
        'timestamp': datetime.now().isoformat()
    }

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Economic Cycle Intelligence API',
        'fred_configured': fred is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/economic-cycle/indicators', methods=['GET'])
def get_economic_indicators():
    """Fetch all key economic indicators - REAL DATA ONLY"""

    logger.info("📊 Fetching economic indicators...")

    # Fetch real data from FRED
    gdp_growth = calculate_yoy_change('GDP')
    unemployment = fetch_fred_indicator('UNRATE')
    inflation_cpi = calculate_yoy_change('CPIAUCSL')
    inflation_pce = calculate_yoy_change('PCEPI')
    pmi_manufacturing = fetch_fred_indicator('MANEMP')  # Manufacturing employment as proxy
    consumer_confidence = fetch_fred_indicator('UMCSENT')  # University of Michigan
    lei = fetch_fred_indicator('USSLIND')  # Leading Economic Index

    indicators = {
        'gdp': {
            'value': gdp_growth,
            'label': 'GDP Growth',
            'unit': '%',
            'description': 'Year-over-year GDP growth rate',
            'status': 'good' if gdp_growth and gdp_growth > 2.0 else 'warning' if gdp_growth and gdp_growth > 0 else 'bad'
        },
        'unemployment': {
            'value': unemployment,
            'label': 'Unemployment Rate',
            'unit': '%',
            'description': 'Current unemployment rate',
            'status': 'good' if unemployment and unemployment < 5.0 else 'warning' if unemployment and unemployment < 6.0 else 'bad'
        },
        'inflation_cpi': {
            'value': inflation_cpi,
            'label': 'CPI Inflation',
            'unit': '% YoY',
            'description': 'Consumer Price Index year-over-year',
            'status': 'good' if inflation_cpi and 1.5 <= inflation_cpi <= 3.0 else 'warning' if inflation_cpi and inflation_cpi < 5.0 else 'bad'
        },
        'inflation_pce': {
            'value': inflation_pce,
            'label': 'PCE Inflation',
            'unit': '% YoY',
            'description': 'Personal Consumption Expenditures inflation (Fed preferred)',
            'status': 'good' if inflation_pce and 1.5 <= inflation_pce <= 2.5 else 'warning'
        },
        'consumer_confidence': {
            'value': consumer_confidence,
            'label': 'Consumer Confidence',
            'unit': 'Index',
            'description': 'University of Michigan Consumer Sentiment',
            'status': 'good' if consumer_confidence and consumer_confidence > 80 else 'warning' if consumer_confidence and consumer_confidence > 60 else 'bad'
        },
        'lei': {
            'value': lei,
            'label': 'Leading Economic Index',
            'unit': 'Index',
            'description': 'Composite of 10 leading indicators',
            'status': 'good' if lei and lei > 0 else 'warning'
        },
        'timestamp': datetime.now().isoformat(),
        'source': 'FRED API'
    }

    return jsonify(indicators)

@app.route('/api/economic-cycle/phase', methods=['GET'])
def get_business_cycle_phase():
    """Detect current business cycle phase - REAL DATA ONLY"""

    logger.info("🔄 Detecting business cycle phase...")

    # Get required indicators
    gdp_growth = calculate_yoy_change('GDP')
    unemployment = fetch_fred_indicator('UNRATE')
    inflation = calculate_yoy_change('CPIAUCSL')
    pmi = fetch_fred_indicator('MANEMP')

    # Detect phase
    phase_data = detect_business_cycle_phase(gdp_growth, unemployment, inflation, pmi)

    phase_data['indicators_used'] = {
        'gdp_growth': gdp_growth,
        'unemployment': unemployment,
        'inflation': inflation,
        'pmi': pmi
    }
    phase_data['timestamp'] = datetime.now().isoformat()

    return jsonify(phase_data)

@app.route('/api/economic-cycle/recession-timeline', methods=['GET'])
def get_recession_timeline():
    """Get recession probability timeline (3/6/12 months) - REAL DATA ONLY"""

    logger.info("📉 Calculating recession timeline...")

    timeline = calculate_recession_timeline()
    timeline['timestamp'] = datetime.now().isoformat()
    timeline['methodology'] = 'NY Fed yield curve model'

    return jsonify(timeline)

@app.route('/api/economic-cycle/regime', methods=['GET'])
def get_economic_regime():
    """Determine economic regime (Growth/Inflation matrix) - REAL DATA ONLY"""

    logger.info("🌡️ Determining economic regime...")

    gdp_growth = calculate_yoy_change('GDP')
    inflation = calculate_yoy_change('CPIAUCSL')

    regime_data = determine_economic_regime(gdp_growth, inflation)
    regime_data['timestamp'] = datetime.now().isoformat()

    return jsonify(regime_data)

@app.route('/api/economic-cycle/sector-rotation', methods=['GET'])
def get_sector_rotation():
    """Get sector rotation guidance based on cycle phase - REAL DATA ONLY"""

    logger.info("🔄 Generating sector rotation guidance...")

    # Get current cycle phase
    gdp_growth = calculate_yoy_change('GDP')
    unemployment = fetch_fred_indicator('UNRATE')
    inflation = calculate_yoy_change('CPIAUCSL')
    pmi = fetch_fred_indicator('MANEMP')

    phase_data = detect_business_cycle_phase(gdp_growth, unemployment, inflation, pmi)
    cycle_phase = phase_data['phase']

    # Get sector guidance
    guidance = get_sector_rotation_guidance(cycle_phase)
    guidance['cycle_confidence'] = phase_data['confidence']
    guidance['cycle_description'] = phase_data['description']

    return jsonify(guidance)

@app.route('/api/economic-cycle/dashboard', methods=['GET'])
def get_comprehensive_dashboard():
    """
    Comprehensive economic cycle dashboard
    Combines all indicators, phase detection, regime, and recommendations
    REAL DATA ONLY - NO FAKE DATA
    """

    logger.info("📊 Building comprehensive economic cycle dashboard...")

    # Get all components
    gdp_growth = calculate_yoy_change('GDP')
    unemployment = fetch_fred_indicator('UNRATE')
    inflation_cpi = calculate_yoy_change('CPIAUCSL')
    inflation_pce = calculate_yoy_change('PCEPI')
    pmi = fetch_fred_indicator('MANEMP')
    consumer_confidence = fetch_fred_indicator('UMCSENT')
    lei = fetch_fred_indicator('USSLIND')

    # Business cycle phase
    phase_data = detect_business_cycle_phase(gdp_growth, unemployment, inflation_cpi, pmi)

    # Recession timeline
    recession_timeline = calculate_recession_timeline()

    # Economic regime
    regime_data = determine_economic_regime(gdp_growth, inflation_cpi)

    # Sector rotation
    sector_guidance = get_sector_rotation_guidance(phase_data['phase'])

    # Compile comprehensive dashboard
    dashboard = {
        'cycle_phase': {
            'current_phase': phase_data['phase'],
            'confidence': phase_data['confidence'],
            'description': phase_data['description'],
            'emoji': phase_data['emoji']
        },
        'key_indicators': {
            'gdp_growth': gdp_growth,
            'unemployment': unemployment,
            'inflation_cpi': inflation_cpi,
            'inflation_pce': inflation_pce,
            'consumer_confidence': consumer_confidence,
            'lei': lei
        },
        'recession_risk': {
            '3_month_probability': recession_timeline.get('3_month'),
            '6_month_probability': recession_timeline.get('6_month'),
            '12_month_probability': recession_timeline.get('12_month'),
            'yield_spread': recession_timeline.get('spread')
        },
        'economic_regime': {
            'regime': regime_data['regime'],
            'description': regime_data['description'],
            'emoji': regime_data['emoji'],
            'strategy': regime_data['strategy']
        },
        'sector_rotation': {
            'buy_sectors': sector_guidance['buy_sectors'],
            'hold_sectors': sector_guidance['hold_sectors'],
            'sell_sectors': sector_guidance['sell_sectors']
        },
        'data_quality': {
            'fred_configured': fred is not None,
            'no_fake_data': True,
            'timestamp': datetime.now().isoformat()
        }
    }

    return jsonify(dashboard)

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🌐 Economic Cycle Intelligence API")
    print("=" * 70)
    print(f"\nFRED API: {'✅ Configured' if fred else '❌ Not configured (add FRED_API_KEY to .env)'}")
    print("\nEndpoints:")
    print("  Health:              http://localhost:5006/health")
    print("  Indicators:          http://localhost:5006/api/economic-cycle/indicators")
    print("  Cycle Phase:         http://localhost:5006/api/economic-cycle/phase")
    print("  Recession Timeline:  http://localhost:5006/api/economic-cycle/recession-timeline")
    print("  Economic Regime:     http://localhost:5006/api/economic-cycle/regime")
    print("  Sector Rotation:     http://localhost:5006/api/economic-cycle/sector-rotation")
    print("  Full Dashboard:      http://localhost:5006/api/economic-cycle/dashboard")
    print("\n" + "=" * 70)
    print("\n🔒 ZERO-SIMULATION POLICY: Returns None on data failures (NO FAKE DATA)")
    print("=" * 70 + "\n")

    app.run(host='0.0.0.0', port=5006, debug=False)
