#!/usr/bin/env python3
"""
COT Scanner API - CFTC Open Interest Percentile Analysis
Scans all CFTC commodities and displays those at 5% and 95% percentiles
Based on Open Interest positioning
"""

from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import requests
import zipfile
import io
from datetime import datetime, timedelta
import logging
import numpy as np

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CFTC Legacy Data URLs (updates weekly on Friday)
CFTC_FUTURES_URL = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
CFTC_CURRENT_YEAR = datetime.now().year
LOOKBACK_WEEKS = 52  # 1 year for percentile calculation

# Cache for CFTC data (refresh every 6 hours)
cftc_cache = {
    'data': None,
    'timestamp': None,
    'percentiles': None
}

def fetch_cftc_futures_data():
    """Download and parse CFTC Futures Legacy data"""
    try:
        logger.info("⏳ Downloading CFTC Futures Legacy Data...")

        # Try current year first
        url = CFTC_FUTURES_URL.format(year=CFTC_CURRENT_YEAR)

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except:
            # Fallback to previous year if current year fails
            logger.warning(f"Failed to fetch {CFTC_CURRENT_YEAR} data, trying {CFTC_CURRENT_YEAR - 1}...")
            url = CFTC_FUTURES_URL.format(year=CFTC_CURRENT_YEAR - 1)
            response = requests.get(url, timeout=30)
            response.raise_for_status()

        # Extract CSV from zip
        z = zipfile.ZipFile(io.BytesIO(response.content))
        file_name = [name for name in z.namelist() if name.endswith('.txt')][0]

        # Read CSV (tab-delimited)
        df = pd.read_csv(z.open(file_name), delimiter=',', low_memory=False)

        # Clean column names
        df.columns = [x.strip() for x in df.columns]

        # Convert date column
        df['Report_Date_as_YYYY-MM-DD'] = pd.to_datetime(df['Report_Date_as_YYYY-MM-DD'])

        # Sort by date
        df = df.sort_values(by='Report_Date_as_YYYY-MM-DD')

        # Filter to last year of data
        cutoff_date = datetime.now() - timedelta(weeks=LOOKBACK_WEEKS)
        df = df[df['Report_Date_as_YYYY-MM-DD'] >= cutoff_date]

        logger.info(f"✅ Downloaded {len(df)} records from {df['Report_Date_as_YYYY-MM-DD'].min()} to {df['Report_Date_as_YYYY-MM-DD'].max()}")
        return df

    except Exception as e:
        logger.error(f"❌ Failed to fetch CFTC data: {e}")
        return None

def calculate_oi_percentiles(df):
    """
    Calculate Open Interest percentiles for each market

    Returns dict of markets with:
    - Current OI percentile (0-100)
    - Net Positions percentile
    - Long/Short percentiles
    """
    try:
        results = []

        # Get unique markets
        markets = df['Market_and_Exchange_Names'].unique()

        for market in markets:
            # Skip if market name is NaN or empty
            if pd.isna(market) or market == '':
                continue

            # Filter data for this market
            market_data = df[df['Market_and_Exchange_Names'] == market].copy()

            if len(market_data) < 10:  # Skip markets with insufficient data
                continue

            # Sort by date
            market_data = market_data.sort_values('Report_Date_as_YYYY-MM-DD')

            # Get latest record
            latest = market_data.iloc[-1]

            # Calculate Open Interest percentile
            oi_values = market_data['Open_Interest_All'].values
            oi_values = oi_values[~np.isnan(oi_values)]  # Remove NaN values

            if len(oi_values) == 0:
                continue

            current_oi = latest['Open_Interest_All']

            if pd.isna(current_oi):
                continue

            # Calculate percentile rank (0-100)
            oi_percentile = (np.sum(oi_values <= current_oi) / len(oi_values)) * 100

            # Calculate Net Commercial Position percentile (using Dealer positions)
            try:
                comm_long = market_data['Dealer_Positions_Long_All'].fillna(0)
                comm_short = market_data['Dealer_Positions_Short_All'].fillna(0)
                net_comm = comm_long - comm_short

                current_net_comm = comm_long.iloc[-1] - comm_short.iloc[-1]
                net_comm_percentile = (np.sum(net_comm.values <= current_net_comm) / len(net_comm)) * 100
            except:
                net_comm_percentile = 50.0  # Default to neutral

            # Calculate Speculator Net Position percentile (using Non-Reportable positions)
            try:
                spec_long = market_data['NonRept_Positions_Long_All'].fillna(0)
                spec_short = market_data['NonRept_Positions_Short_All'].fillna(0)
                net_spec = spec_long - spec_short

                current_net_spec = spec_long.iloc[-1] - spec_short.iloc[-1]
                net_spec_percentile = (np.sum(net_spec.values <= current_net_spec) / len(net_spec)) * 100
            except:
                net_spec_percentile = 50.0

            # CONTRARIAN INVESTING LOGIC
            # Commercials (smart money) at extremes = fade the crowd
            # Low Comm Net % = They're bearish = WE GO LONG (contrarian bullish)
            # High Comm Net % = They're bullish = WE GO SHORT (contrarian bearish)
            signal = 'NEUTRAL'

            if oi_percentile >= 95:
                # High Open Interest - overcrowded market
                if net_comm_percentile >= 80:
                    # Smart money heavily long = crowd is long = FADE IT
                    signal = '🔴 SELL - Overcrowded Long'
                elif net_comm_percentile <= 20:
                    # Smart money heavily short = crowd is short = FADE IT
                    signal = '🟢 BUY - Overcrowded Short'
                else:
                    signal = '⚪ High OI - Watch'

            elif oi_percentile <= 5:
                # Low Open Interest - quiet market (best contrarian opportunities)
                if net_comm_percentile >= 80:
                    # Smart money quietly accumulating long = crowd bearish = FADE IT
                    signal = '🔴 SELL - Quiet Accumulation'
                elif net_comm_percentile <= 20:
                    # Smart money quietly shorting = crowd bullish = FADE IT
                    signal = '🟢 BUY - Quiet Distribution'
                else:
                    signal = '⚪ Low OI - Watch'

            results.append({
                'market': market,
                'oi_percentile': round(oi_percentile, 2),
                'net_comm_percentile': round(net_comm_percentile, 2),
                'net_spec_percentile': round(net_spec_percentile, 2),
                'current_oi': int(current_oi),
                'signal': signal,
                'report_date': latest['Report_Date_as_YYYY-MM-DD'].strftime('%Y-%m-%d'),
                'comm_long': int(latest['Dealer_Positions_Long_All']) if pd.notna(latest['Dealer_Positions_Long_All']) else 0,
                'comm_short': int(latest['Dealer_Positions_Short_All']) if pd.notna(latest['Dealer_Positions_Short_All']) else 0,
                'spec_long': int(latest['NonRept_Positions_Long_All']) if pd.notna(latest['NonRept_Positions_Long_All']) else 0,
                'spec_short': int(latest['NonRept_Positions_Short_All']) if pd.notna(latest['NonRept_Positions_Short_All']) else 0,
            })

        logger.info(f"✅ Calculated percentiles for {len(results)} markets")
        return results

    except Exception as e:
        logger.error(f"❌ Error calculating percentiles: {e}")
        return []

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'COT Scanner API',
        'cftc_data_cached': cftc_cache['data'] is not None,
        'cache_timestamp': cftc_cache['timestamp'].isoformat() if cftc_cache['timestamp'] else None,
        'markets_cached': len(cftc_cache['percentiles']) if cftc_cache['percentiles'] else 0
    })

@app.route('/api/cot-scanner/all', methods=['GET'])
def get_all_markets():
    """Get all markets with OI percentiles"""
    try:
        # Check cache (refresh if older than 6 hours)
        now = datetime.now()
        if cftc_cache['data'] is None or \
           (cftc_cache['timestamp'] and (now - cftc_cache['timestamp']).seconds > 21600):
            logger.info("🔄 Refreshing CFTC data cache...")
            cftc_cache['data'] = fetch_cftc_futures_data()
            cftc_cache['timestamp'] = now

            if cftc_cache['data'] is not None:
                cftc_cache['percentiles'] = calculate_oi_percentiles(cftc_cache['data'])

        if cftc_cache['percentiles'] is None:
            return jsonify({'error': 'Failed to fetch CFTC data'}), 500

        return jsonify({
            'success': True,
            'markets': cftc_cache['percentiles'],
            'total_markets': len(cftc_cache['percentiles']),
            'lookback_weeks': LOOKBACK_WEEKS,
            'last_updated': cftc_cache['timestamp'].isoformat() if cftc_cache['timestamp'] else None
        })

    except Exception as e:
        logger.error(f"Error in get_all_markets: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cot-scanner/extremes', methods=['GET'])
def get_extremes():
    """Get markets at 5% and 95% OI percentiles"""
    try:
        # Check cache
        now = datetime.now()
        if cftc_cache['data'] is None or \
           (cftc_cache['timestamp'] and (now - cftc_cache['timestamp']).seconds > 21600):
            cftc_cache['data'] = fetch_cftc_futures_data()
            cftc_cache['timestamp'] = now

            if cftc_cache['data'] is not None:
                cftc_cache['percentiles'] = calculate_oi_percentiles(cftc_cache['data'])

        if cftc_cache['percentiles'] is None:
            return jsonify({'error': 'Failed to fetch CFTC data'}), 500

        # Filter to extreme percentiles (<=5% or >=95%)
        extremes = [
            m for m in cftc_cache['percentiles']
            if m['oi_percentile'] <= 5 or m['oi_percentile'] >= 95
        ]

        # Sort by OI percentile (ascending)
        extremes.sort(key=lambda x: x['oi_percentile'])

        return jsonify({
            'success': True,
            'markets': extremes,
            'total_extremes': len(extremes),
            'lookback_weeks': LOOKBACK_WEEKS,
            'last_updated': cftc_cache['timestamp'].isoformat() if cftc_cache['timestamp'] else None
        })

    except Exception as e:
        logger.error(f"Error in get_extremes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cot-scanner/market/<market_name>', methods=['GET'])
def get_market(market_name):
    """Get specific market OI percentile data"""
    try:
        # Check cache
        now = datetime.now()
        if cftc_cache['data'] is None or \
           (cftc_cache['timestamp'] and (now - cftc_cache['timestamp']).seconds > 21600):
            cftc_cache['data'] = fetch_cftc_futures_data()
            cftc_cache['timestamp'] = now

            if cftc_cache['data'] is not None:
                cftc_cache['percentiles'] = calculate_oi_percentiles(cftc_cache['data'])

        if cftc_cache['percentiles'] is None:
            return jsonify({'error': 'Failed to fetch CFTC data'}), 500

        # Find market
        market_data = [m for m in cftc_cache['percentiles'] if m['market'].upper() == market_name.upper()]

        if not market_data:
            return jsonify({'error': f'Market {market_name} not found'}), 404

        return jsonify({
            'success': True,
            'market': market_data[0]
        })

    except Exception as e:
        logger.error(f"Error in get_market: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting COT Scanner API Server...")
    logger.info(f"📊 Analyzing CFTC Futures markets")
    logger.info(f"🔄 Data refreshes every 6 hours")
    logger.info(f"📡 CFTC Source: {CFTC_FUTURES_URL.format(year=CFTC_CURRENT_YEAR)}")

    # Pre-load data on startup
    logger.info("⏳ Pre-loading CFTC data...")
    cftc_cache['data'] = fetch_cftc_futures_data()
    cftc_cache['timestamp'] = datetime.now()

    if cftc_cache['data'] is not None:
        cftc_cache['percentiles'] = calculate_oi_percentiles(cftc_cache['data'])
        logger.info(f"✅ COT Scanner API Ready! Tracking {len(cftc_cache['percentiles'])} markets")
    else:
        logger.warning("⚠️ Failed to pre-load data. Will retry on first request.")

    app.run(host='0.0.0.0', port=5009, debug=False)
