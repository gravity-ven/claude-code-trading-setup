#!/usr/bin/env python3
"""
COT API - CFTC Legacy Data Service
Fetches and serves real Commitment of Traders data from CFTC
"""

from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import requests
import zipfile
import io
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CFTC Legacy Data URL (updates weekly on Friday)
CFTC_URL = "https://www.cftc.gov/files/dea/history/deacot2024.zip"
LOOKBACK_WEEKS = 26  # 26 weeks for COT Index calculation

# Market Mapping: Frontend ticker -> CFTC Market Name
MARKET_MAP = {
    # PRECIOUS METALS
    'GC=F': 'GOLD',
    'SI=F': 'SILVER',
    'HG=F': 'COPPER',
    'PL=F': 'PLATINUM',
    'PA=F': 'PALLADIUM',

    # ENERGY
    'CL=F': 'CRUDE OIL, LIGHT SWEET',
    'NG=F': 'NATURAL GAS',
    'RB=F': 'GASOLINE',
    'HO=F': 'NY HARBOR ULSD',  # Heating Oil (Ultra-Low Sulfur Diesel)

    # AGRICULTURE (Grains & Oilseeds)
    'ZC=F': 'CORN',
    'ZS=F': 'SOYBEANS',
    'ZW=F': 'WHEAT',
    'ZL=F': 'SOYBEAN OIL',
    'ZM=F': 'SOYBEAN MEAL',
    'KE=F': 'WHEAT-HRW',  # Kansas Hard Red Winter Wheat

    # AGRICULTURE (Softs)
    'CT=F': 'COTTON',
    'SB=F': 'SUGAR',
    'CC=F': 'COCOA',
    'KC=F': 'COFFEE',
    'LBS=F': 'LUMBER',

    # AGRICULTURE (Livestock)
    'LE=F': 'LIVE CATTLE',
    'HE=F': 'LEAN HOGS',

    # CRYPTOCURRENCY
    'BTC-USD': 'BITCOIN',
    'ETH-USD': 'ETHER',

    # INDICES
    'ES=F': 'E-MINI S&P 500',
    'NQ=F': 'NASDAQ',
    'YM=F': 'DOW JONES',
    'RTY=F': 'RUSSELL 2000',
    'VIX=F': 'VIX',

    # CURRENCIES
    '6E=F': 'EURO FX',
    '6J=F': 'JAPANESE YEN',
    '6B=F': 'BRITISH POUND',
    '6A=F': 'AUSTRALIAN DOLLAR',
    '6C=F': 'CANADIAN DOLLAR',
    '6S=F': 'SWISS FRANC',
    # '6N=F': 'NEW ZEALAND DOLLAR',  # Not available in CFTC Legacy data
    '6M=F': 'MEXICAN PESO',

    # TREASURIES
    'ZB=F': 'UST BOND',         # 30-Year U.S. Treasury Bond
    'ZN=F': 'UST 10Y NOTE',     # 10-Year U.S. Treasury Note
    'ZF=F': 'UST 5Y NOTE',      # 5-Year U.S. Treasury Note
    'ZT=F': 'UST 2Y NOTE'       # 2-Year U.S. Treasury Note
}

# Cache for CFTC data (refresh every hour)
cftc_cache = {
    'data': None,
    'timestamp': None
}

def fetch_cftc_data():
    """Download and parse CFTC Legacy data"""
    try:
        logger.info("⏳ Downloading CFTC Legacy Data...")

        # Download zip file
        response = requests.get(CFTC_URL, timeout=30)
        response.raise_for_status()

        # Extract CSV from zip
        z = zipfile.ZipFile(io.BytesIO(response.content))
        file_name = z.namelist()[0]

        # Read CSV
        df = pd.read_csv(z.open(file_name), low_memory=False)

        # Clean column names (strip whitespace)
        df.columns = [x.strip() for x in df.columns]

        # Convert date column
        df['As of Date in Form YYYY-MM-DD'] = pd.to_datetime(df['As of Date in Form YYYY-MM-DD'])

        # Sort by date
        df = df.sort_values(by='As of Date in Form YYYY-MM-DD')

        logger.info(f"✅ Downloaded {len(df)} records")
        return df

    except Exception as e:
        logger.error(f"❌ Failed to fetch CFTC data: {e}")
        return None

def calculate_cot_index(df, market_name):
    """
    Calculate COT Index for a specific market

    Formula: (Current Net Position - Min Net Position) / (Max Net Position - Min Net Position) × 100

    Net Position = Commercial Long - Commercial Short
    """
    try:
        # Filter data for this market
        mask = df['Market and Exchange Names'].str.contains(market_name, case=False, na=False)
        subset = df[mask].copy()

        if subset.empty:
            return None

        # Resample to weekly data (take last value of each week)
        subset = subset.set_index('As of Date in Form YYYY-MM-DD').resample('W').last().ffill()

        # Calculate Commercial Net Position
        subset['Net_Comm'] = subset['Commercial Positions-Long (All)'] - subset['Commercial Positions-Short (All)']

        # Calculate rolling min/max over lookback period
        subset['Min_Pos'] = subset['Net_Comm'].rolling(window=LOOKBACK_WEEKS).min()
        subset['Max_Pos'] = subset['Net_Comm'].rolling(window=LOOKBACK_WEEKS).max()

        # Calculate COT Index
        denominator = (subset['Max_Pos'] - subset['Min_Pos'])
        denominator = denominator.replace(0, 1)  # Avoid division by zero

        subset['COT_Index'] = ((subset['Net_Comm'] - subset['Min_Pos']) / denominator) * 100

        # Get latest values
        latest = subset.iloc[-1]

        return {
            'cot_index': float(latest['COT_Index']) if pd.notna(latest['COT_Index']) else None,
            'net_position': int(latest['Net_Comm']) if pd.notna(latest['Net_Comm']) else None,
            'comm_long': int(latest['Commercial Positions-Long (All)']) if pd.notna(latest['Commercial Positions-Long (All)']) else None,
            'comm_short': int(latest['Commercial Positions-Short (All)']) if pd.notna(latest['Commercial Positions-Short (All)']) else None,
            'report_date': latest.name.strftime('%Y-%m-%d') if pd.notna(latest.name) else None
        }

    except Exception as e:
        logger.error(f"Error calculating COT Index for {market_name}: {e}")
        return None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'COT API',
        'cftc_data_cached': cftc_cache['data'] is not None,
        'cache_timestamp': cftc_cache['timestamp']
    })

@app.route('/api/cot/markets', methods=['GET'])
def get_all_markets():
    """Get COT Index for all markets"""
    try:
        # Check cache (refresh if older than 1 hour)
        now = datetime.now()
        if cftc_cache['data'] is None or \
           (cftc_cache['timestamp'] and (now - cftc_cache['timestamp']).seconds > 3600):
            logger.info("🔄 Refreshing CFTC data cache...")
            cftc_cache['data'] = fetch_cftc_data()
            cftc_cache['timestamp'] = now

        df = cftc_cache['data']

        if df is None:
            return jsonify({'error': 'Failed to fetch CFTC data'}), 500

        # Calculate COT Index for all markets
        results = {}

        for ticker, market_name in MARKET_MAP.items():
            logger.info(f"📊 Calculating COT Index for {market_name}...")
            cot_data = calculate_cot_index(df, market_name)

            if cot_data:
                results[ticker] = cot_data

        return jsonify({
            'success': True,
            'markets': results,
            'report_date': results[list(results.keys())[0]]['report_date'] if results else None,
            'lookback_weeks': LOOKBACK_WEEKS
        })

    except Exception as e:
        logger.error(f"Error in get_all_markets: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cot/market/<ticker>', methods=['GET'])
def get_market(ticker):
    """Get COT Index for a specific market"""
    try:
        # Check cache
        now = datetime.now()
        if cftc_cache['data'] is None or \
           (cftc_cache['timestamp'] and (now - cftc_cache['timestamp']).seconds > 3600):
            cftc_cache['data'] = fetch_cftc_data()
            cftc_cache['timestamp'] = now

        df = cftc_cache['data']

        if df is None:
            return jsonify({'error': 'Failed to fetch CFTC data'}), 500

        # Get market name
        market_name = MARKET_MAP.get(ticker)

        if not market_name:
            return jsonify({'error': f'Market {ticker} not found'}), 404

        # Calculate COT Index
        cot_data = calculate_cot_index(df, market_name)

        if not cot_data:
            return jsonify({'error': f'No COT data found for {market_name}'}), 404

        return jsonify({
            'success': True,
            'ticker': ticker,
            'market_name': market_name,
            'data': cot_data
        })

    except Exception as e:
        logger.error(f"Error in get_market: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting COT API Server...")
    logger.info(f"📊 Monitoring {len(MARKET_MAP)} markets")
    logger.info(f"🔄 Data refreshes every hour")
    logger.info(f"📡 CFTC Source: {CFTC_URL}")

    # Pre-load data on startup
    logger.info("⏳ Pre-loading CFTC data...")
    cftc_cache['data'] = fetch_cftc_data()
    cftc_cache['timestamp'] = datetime.now()

    if cftc_cache['data'] is not None:
        logger.info("✅ COT API Ready!")
    else:
        logger.warning("⚠️ Failed to pre-load data. Will retry on first request.")

    app.run(host='0.0.0.0', port=5005, debug=False)
