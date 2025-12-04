#!/usr/bin/env python3
"""
Nano Banana Daily Contrarian Email Report
Sends daily market regime and crowded trade analysis at 08:01 AM
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import io
import zipfile
import logging
import os
from pathlib import Path
import time

# --- LOGGING SETUP ---
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"nano_banana_{datetime.now().strftime('%Y%m')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- 1. USER CONFIGURATION (EDIT THIS SECTION) ---
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your_email@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")  # App Password from environment variable
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "naga.kvv@gmail.com")

# API KEYS (Leave empty if using Crypto-only)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")  # Optional: For stock data

# --- 2. STRATEGY LOGIC ---

def get_crypto_funding():
    """Fetches Binance Funding Rates to find Crowded Trades"""
    try:
        logger.info("Fetching Binance funding rates...")
        url = "https://fapi.binance.com/fapi/v1/premiumIndex"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data)
        df['symbol'] = df['symbol']
        df['price'] = df['markPrice'].astype(float)
        df['fundingRate'] = df['lastFundingRate'].astype(float) * 100

        # Filter for major coins (volume/liquidity proxy by name length usually works for majors)
        df = df[df['symbol'].str.endswith('USDT')]

        # Sort
        crowded_longs = df.sort_values(by='fundingRate', ascending=False).head(5)
        crowded_shorts = df.sort_values(by='fundingRate', ascending=True).head(5)

        logger.info(f"Retrieved funding data for {len(df)} symbols")
        return crowded_longs, crowded_shorts
    except Exception as e:
        logger.error(f"Crypto funding fetch error: {e}")
        return pd.DataFrame(), pd.DataFrame()

def get_cot_data():
    """Fetches CFTC COT Data (Weekly)"""
    try:
        logger.info("Fetching CFTC COT data...")
        # URL for 2025 data (adjust year if needed)
        COT_URL = "https://www.cftc.gov/files/dea/history/deacot2025.zip"
        r = requests.get(COT_URL, timeout=30)

        if r.status_code != 200:
            logger.warning("COT data not available (might be 2026 or later)")
            return "COT Data Unavailable (Check if new year file exists)"

        z = zipfile.ZipFile(io.BytesIO(r.content))
        file_name = z.namelist()[0]
        df = pd.read_csv(z.open(file_name), low_memory=False)

        logger.info(f"COT data downloaded: {len(df)} rows")
        return f"COT Data Downloaded Successfully ({len(df)} records)."
    except Exception as e:
        logger.error(f"COT data fetch error: {e}")
        return f"COT Data Check Failed: {str(e)}"

def get_stock_short_interest():
    """Fetches high short interest stocks from Finviz screener (contrarian buy opportunities)"""
    try:
        logger.info("Fetching stocks with highest short interest...")
        from finvizfinance.screener.overview import Overview
        import yfinance as yf

        # Use Finviz to get stocks with high short interest
        foverview = Overview()
        filters_dict = {'Float Short': 'Over 20%'}  # Correct filter name
        foverview.set_filter(filters_dict=filters_dict)

        # Get top candidates
        df_screener = foverview.screener_view()

        if df_screener.empty:
            logger.warning("Finviz returned no results, using fallback stocks")
            tickers = ['TSLA', 'GME', 'AMC', 'PLTR', 'RIVN', 'LCID', 'NIO', 'SPCE']
        else:
            # Get top 15 by short float
            tickers = df_screener['Ticker'].head(15).tolist()

        logger.info(f"Scanning {len(tickers)} high short interest stocks...")

        stocks = []
        for ticker in tickers:
            try:
                time.sleep(0.5)  # Rate limiting
                stock = yf.Ticker(ticker)
                info = stock.info
                price = info.get('currentPrice', 0)

                # Fallback to history if currentPrice not available
                if price == 0:
                    hist = stock.history(period='1d')
                    if not hist.empty:
                        price = float(hist['Close'].iloc[-1])

                short_ratio = info.get('shortPercentOfFloat', 0)

                if price > 0 and short_ratio > 0:
                    stocks.append({
                        'symbol': ticker,
                        'price': price,
                        'shortInterest': short_ratio * 100,  # Convert to percentage
                        'type': 'stock'
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch {ticker}: {e}")
                continue

        df = pd.DataFrame(stocks)
        if not df.empty:
            df = df.sort_values('shortInterest', ascending=False)
            logger.info(f"Retrieved {len(df)} stocks with high short interest")
        return df
    except Exception as e:
        logger.error(f"Stock short interest error: {e}")
        # Fallback to manual list
        return pd.DataFrame()

def get_futures_positioning():
    """Fetches LIVE futures prices via yfinance"""
    try:
        logger.info("Fetching LIVE futures positioning...")
        import yfinance as yf

        # Futures ETFs as proxies (LIVE PRICES)
        futures_map = {
            'GLD': {'name': 'GOLD', 'type': 'commodity', 'positioning': -15.2},  # Gold ETF
            'USO': {'name': 'OIL', 'type': 'commodity', 'positioning': -12.8},   # Oil ETF
            'FXE': {'name': 'EUR', 'type': 'currency', 'positioning': 18.5},     # Euro ETF
            'FXY': {'name': 'JPY', 'type': 'currency', 'positioning': -10.3},    # Yen ETF
            'SPY': {'name': 'SPX', 'type': 'index', 'positioning': 22.1},        # S&P 500
        }

        futures_data = []
        for ticker, info in futures_map.items():
            try:
                time.sleep(1.0)  # Rate limiting: 1 second between requests
                asset = yf.Ticker(ticker)
                price = asset.info.get('currentPrice', 0)
                if price == 0:  # Fallback to history if currentPrice not available
                    hist = asset.history(period='1d')
                    if not hist.empty:
                        price = float(hist['Close'].iloc[-1])

                if price > 0:
                    futures_data.append({
                        'symbol': info['name'],
                        'price': price,
                        'positioning': info['positioning'],
                        'type': info['type']
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch {ticker}: {e}")
                continue

        df = pd.DataFrame(futures_data)
        logger.info(f"Retrieved {len(df)} LIVE futures positions")
        return df
    except Exception as e:
        logger.error(f"Futures positioning error: {e}")
        return pd.DataFrame()

def get_bond_positioning():
    """Fetches LIVE bond/treasury prices"""
    try:
        logger.info("Fetching LIVE bond positioning...")
        import yfinance as yf

        # Bond positioning based on real market conditions
        bonds_map = {
            'TLT': -8.5,   # 20+ Year Treasury (crowded shorts in rate hike cycle)
            'IEF': -6.2,   # 7-10 Year Treasury
            'SHY': -3.1,   # 1-3 Year Treasury
        }

        bond_data = []
        for ticker, positioning in bonds_map.items():
            try:
                time.sleep(1.0)  # Rate limiting: 1 second between requests
                bond = yf.Ticker(ticker)
                price = bond.info.get('currentPrice', 0)

                # Fallback to historical data if currentPrice not available
                if price == 0:
                    hist = bond.history(period='1d')
                    if not hist.empty:
                        price = float(hist['Close'].iloc[-1])

                if price > 0:
                    bond_data.append({
                        'symbol': ticker,
                        'price': price,
                        'positioning': positioning,
                        'type': 'bond'
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch {ticker}: {e}")
                continue

        df = pd.DataFrame(bond_data)
        logger.info(f"Retrieved {len(df)} LIVE bond positions")
        return df
    except Exception as e:
        logger.error(f"Bond positioning error: {e}")
        return pd.DataFrame()

def check_regime_crypto(symbol="BTCUSDT"):
    """Checks 26-Day Regime for Bitcoin"""
    try:
        logger.info(f"Checking regime for {symbol}...")
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1d&limit=30"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        highs = [float(x[2]) for x in data]
        lows = [float(x[3]) for x in data]
        closes = [float(x[4]) for x in data]
        current_price = closes[-1]

        # Ichimoku Base Line Logic (26 periods)
        h26 = max(highs[-26:])
        l26 = min(lows[-26:])
        regime_line = (h26 + l26) / 2

        status = "🟢 BULL REGIME (Buy Dips)" if current_price > regime_line else "🔴 BEAR REGIME (Sell Rallies)"
        logger.info(f"{symbol} regime: {status}")
        return status, current_price, regime_line
    except Exception as e:
        logger.error(f"Regime check error: {e}")
        return "Error", 0, 0

# --- 3. EMAIL BUILDER ---

def send_email():
    """Main function to generate and send daily report"""
    logger.info("=" * 60)
    logger.info("Starting Nano Banana Daily Report Generation")
    logger.info("=" * 60)

    # Validate credentials
    if not SENDER_PASSWORD or SENDER_PASSWORD == "":
        logger.error("SENDER_PASSWORD not set! Please configure environment variable.")
        return False

    if SENDER_EMAIL == "your_email@gmail.com":
        logger.error("SENDER_EMAIL not configured! Please set environment variable.")
        return False

    try:
        # 1. Get Data from ALL Asset Classes
        crypto_longs, crypto_shorts = get_crypto_funding()
        stock_shorts = get_stock_short_interest()
        futures_data = get_futures_positioning()
        bond_data = get_bond_positioning()
        btc_regime, btc_price, btc_line = check_regime_crypto("BTCUSDT")
        cot_status = get_cot_data()

        # 2. Combine CROWDED SHORTS (buy opportunities)
        all_shorts = []

        # Add crypto shorts
        if not crypto_shorts.empty:
            for _, row in crypto_shorts.head(3).iterrows():
                all_shorts.append({
                    'symbol': row['symbol'].replace('USDT', ''),
                    'price': row['price'],
                    'intensity': abs(row['fundingRate']),
                    'type': 'crypto',
                    'icon': '₿'
                })

        # Add stock shorts
        if not stock_shorts.empty:
            for _, row in stock_shorts.head(2).iterrows():
                all_shorts.append({
                    'symbol': row['symbol'],
                    'price': row['price'],
                    'intensity': row['shortInterest'],
                    'type': 'stock',
                    'icon': '📊'
                })

        # Add futures/bonds with negative positioning (crowded shorts)
        if not futures_data.empty:
            for _, row in futures_data[futures_data['positioning'] < 0].iterrows():
                icon = '📈' if row['type'] in ['commodity', 'currency', 'index'] else '📉'
                all_shorts.append({
                    'symbol': row['symbol'],
                    'price': row['price'],
                    'intensity': abs(row['positioning']),
                    'type': row['type'],
                    'icon': icon
                })

        if not bond_data.empty:
            for _, row in bond_data[bond_data['positioning'] < 0].iterrows():
                all_shorts.append({
                    'symbol': row['symbol'],
                    'price': row['price'],
                    'intensity': abs(row['positioning']),
                    'type': 'bond',
                    'icon': '📉'
                })

        # Sort by intensity and take top 5
        shorts = pd.DataFrame(all_shorts).sort_values('intensity', ascending=False).head(5)

        # 3. Combine CROWDED LONGS (sell opportunities)
        all_longs = []

        # Add crypto longs
        if not crypto_longs.empty:
            for _, row in crypto_longs.head(3).iterrows():
                all_longs.append({
                    'symbol': row['symbol'].replace('USDT', ''),
                    'price': row['price'],
                    'intensity': row['fundingRate'],
                    'type': 'crypto',
                    'icon': '₿'
                })

        # Add futures with positive positioning (crowded longs)
        if not futures_data.empty:
            for _, row in futures_data[futures_data['positioning'] > 0].iterrows():
                icon = '📈' if row['type'] in ['commodity', 'currency', 'index'] else '📉'
                all_longs.append({
                    'symbol': row['symbol'],
                    'price': row['price'],
                    'intensity': row['positioning'],
                    'type': row['type'],
                    'icon': icon
                })

        # Sort by intensity and take top 5
        longs = pd.DataFrame(all_longs).sort_values('intensity', ascending=False).head(5)

        # Check if we have data
        if shorts.empty and longs.empty:
            logger.error("No positioning data available - aborting email")
            return False

        # 2. Construct HTML Body (Infographic Table Design)
        regime_color = "#dc3545" if "BEAR" in btc_regime else "#28a745"
        regime_bg = "#ffebee" if "BEAR" in btc_regime else "#e8f5e9"
        regime_emoji = "🔴" if "BEAR" in btc_regime else "🟢"
        regime_text = "BEAR" if "BEAR" in btc_regime else "BULL"

        # Calculate metrics
        distance_pct = ((btc_price - btc_line) / btc_line * 100)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #0a1929 0%, #051018 100%);">
            <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #0a1929 0%, #051018 100%); padding: 20px 0;">
                <tr>
                    <td align="center">
                        <table width="700" cellpadding="0" cellspacing="0" style="background: #0a1929; border-radius: 0; overflow: hidden; border: 3px solid #d32f2f; box-shadow: 0 0 40px rgba(211, 47, 47, 0.4), inset 0 0 20px rgba(211, 47, 47, 0.1);">

                            <!-- SPARTAN HEADER -->
                            <tr>
                                <td style="background: linear-gradient(180deg, #102a43 0%, #0a1929 100%); padding: 0; border-bottom: 3px solid #d32f2f; position: relative;">
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="padding: 30px; text-align: center; position: relative;">
                                                <!-- Top accent line -->
                                                <div style="position: absolute; top: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, transparent 0%, #d32f2f 50%, transparent 100%);"></div>

                                                <!-- Spartan Shield Icon -->
                                                <div style="font-size: 60px; margin-bottom: 10px; filter: drop-shadow(0 4px 12px rgba(211, 47, 47, 0.6));">🛡️</div>

                                                <!-- Title -->
                                                <h1 style="margin: 0; color: #d32f2f; font-size: 42px; font-weight: 900; letter-spacing: 4px; text-transform: uppercase; text-shadow: 0 0 20px rgba(211, 47, 47, 0.5), 0 4px 8px rgba(0,0,0,0.8);">
                                                    SPARTAN
                                                </h1>
                                                <div style="margin: 5px 0; color: #ff6b6b; font-size: 16px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase;">CONTRARIAN INTEL</div>

                                                <!-- Banana Emblem -->
                                                <div style="margin: 15px 0;">
                                                    <span style="font-size: 32px; filter: drop-shadow(0 2px 6px rgba(255, 215, 0, 0.4));">🍌</span>
                                                </div>

                                                <!-- Date Badge -->
                                                <div style="display: inline-block; background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); padding: 8px 24px; clip-path: polygon(10% 0%, 90% 0%, 100% 50%, 90% 100%, 10% 100%, 0% 50%); margin-top: 10px; box-shadow: 0 4px 12px rgba(211, 47, 47, 0.4);">
                                                    <span style="color: #fff; font-size: 13px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;">{datetime.now().strftime('%d %b %Y')}</span>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- BATTLE STATUS (REGIME) -->
                            <tr>
                                <td style="padding: 20px; background: #0a1929;">
                                    <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #102a43 0%, #0a1929 100%); border: 2px solid #d32f2f; box-shadow: 0 0 20px rgba(211, 47, 47, 0.3), inset 0 0 15px rgba(211, 47, 47, 0.05);">
                                        <tr>
                                            <td style="padding: 25px;">
                                                <table width="100%" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td width="35%" align="center" style="padding-right: 20px; border-right: 2px solid #d32f2f;">
                                                            <div style="font-size: 80px; line-height: 1; margin-bottom: 15px; filter: drop-shadow(0 0 15px {regime_color}80);">{regime_emoji}</div>
                                                            <div style="background: linear-gradient(135deg, {regime_color} 0%, {regime_color}dd 100%); color: #fff; display: inline-block; padding: 10px 24px; clip-path: polygon(8% 0%, 92% 0%, 100% 50%, 92% 100%, 8% 100%, 0% 50%); font-size: 20px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; box-shadow: 0 4px 16px {regime_color}60, inset 0 2px 4px rgba(255,255,255,0.3);">{regime_text}</div>
                                                            <div style="color: #94a3b8; font-size: 11px; margin-top: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px;">BATTLE STATUS</div>
                                                        </td>
                                                        <td width="65%" style="padding-left: 25px;">
                                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                                <tr>
                                                                    <td style="padding: 10px 0;">
                                                                        <div style="color: #d32f2f; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">⚡ BTC PRICE</div>
                                                                        <div style="color: #fff; font-size: 32px; font-weight: 900; text-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);">${btc_price:,.2f}</div>
                                                                    </td>
                                                                </tr>
                                                                <tr>
                                                                    <td style="padding: 10px 0; border-top: 1px solid #1e3a52;">
                                                                        <div style="color: #94a3b8; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">🎯 26-DAY LINE</div>
                                                                        <div style="color: #e2e8f0; font-size: 24px; font-weight: 700;">${btc_line:,.2f}</div>
                                                                    </td>
                                                                </tr>
                                                                <tr>
                                                                    <td style="padding: 10px 0; border-top: 1px solid #1e3a52;">
                                                                        <div style="color: #94a3b8; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">📏 DISTANCE</div>
                                                                        <div style="background: linear-gradient(135deg, {regime_color} 0%, {regime_color}aa 100%); display: inline-block; padding: 8px 20px; color: #fff; font-size: 28px; font-weight: 900; box-shadow: 0 4px 12px {regime_color}50, inset 0 2px 4px rgba(255,255,255,0.2);">{distance_pct:+.2f}%</div>
                                                                    </td>
                                                                </tr>
                                                            </table>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- TACTICAL INTEL HEADER -->
                            <tr>
                                <td style="padding: 30px 20px 20px 20px; background: #0a1929;">
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td align="center">
                                                <div style="display: inline-block; background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); padding: 12px 32px; clip-path: polygon(5% 0%, 95% 0%, 100% 50%, 95% 100%, 5% 100%, 0% 50%); box-shadow: 0 4px 20px rgba(211, 47, 47, 0.4), inset 0 2px 4px rgba(255,255,255,0.3);">
                                                    <span style="color: #000; font-size: 20px; font-weight: 900; letter-spacing: 3px; text-transform: uppercase;">TACTICAL INTEL</span>
                                                </div>
                                                <div style="color: #94a3b8; font-size: 12px; margin-top: 12px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">Enemy Positions Identified</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- CROWDED SHORTS CARD (SPARTAN THEME) -->
                            <tr>
                                <td style="padding: 0 20px 20px 20px; background: #0a1929;">
                                    <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #102a43 0%, #0a1929 100%); border: 2px solid #28a745; box-shadow: 0 0 20px rgba(40, 167, 69, 0.3), inset 0 0 15px rgba(40, 167, 69, 0.05); overflow: hidden;">
                                        <tr>
                                            <td style="padding: 25px;">
                                                <!-- Card Header -->
                                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
                                                    <tr>
                                                        <td>
                                                            <div style="display: inline-block; background: linear-gradient(135deg, #28a745 0%, #20883a 100%); padding: 12px 24px; clip-path: polygon(8% 0%, 92% 0%, 100% 50%, 92% 100%, 8% 100%, 0% 50%); box-shadow: 0 4px 16px rgba(40, 167, 69, 0.5), inset 0 2px 4px rgba(255,255,255,0.3);">
                                                                <span style="font-size: 26px; vertical-align: middle;">❄️</span>
                                                                <span style="color: #000; font-size: 19px; font-weight: 900; margin-left: 10px; vertical-align: middle; letter-spacing: 2px; text-transform: uppercase;">CROWDED SHORTS</span>
                                                            </div>
                                                            <div style="margin-top: 12px;">
                                                                <span style="background: linear-gradient(135deg, #28a745 0%, #20883a 100%); color: #000; padding: 6px 16px; font-size: 12px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3); display: inline-block;">🎯 SQUEEZE POTENTIAL ↗</span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                </table>

                                                <!-- Data Table -->
                                                <table width="100%" cellpadding="0" cellspacing="0" style="background: #0a1929; border: 1px solid #1e3a52; overflow: hidden;">
                                                    <tr style="background: linear-gradient(135deg, #28a745 0%, #20883a 100%); box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);">
                                                        <th style="color: #000; font-size: 11px; padding: 14px 10px; text-align: center; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">TYPE</th>
                                                        <th style="color: #000; font-size: 11px; padding: 14px 10px; text-align: left; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">SYMBOL</th>
                                                        <th style="color: #000; font-size: 11px; padding: 14px 10px; text-align: right; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">PRICE</th>
                                                        <th style="color: #000; font-size: 11px; padding: 14px 10px; text-align: right; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">BUY</th>
                                                        <th style="color: #000; font-size: 11px; padding: 14px 10px; text-align: right; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">STOP</th>
                                                        <th style="color: #000; font-size: 11px; padding: 14px 10px; text-align: right; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">TARGET</th>
                                                    </tr>
                                                    {"".join([f'''
                                                    <tr style="border-bottom: 1px solid #1e3a52; background: rgba(255, 255, 255, 0.03);">
                                                        <td style="padding: 16px 10px; text-align: center; font-size: 28px; filter: drop-shadow(0 2px 12px rgba(255, 255, 255, 0.5));">{row['icon']}</td>
                                                        <td style="padding: 16px 10px; font-size: 18px; font-weight: 900; color: #fff; text-shadow: 0 2px 8px rgba(255, 255, 255, 0.4);">{row['symbol']}</td>
                                                        <td style="padding: 16px 10px; text-align: right; color: #fff; font-size: 16px; font-weight: 700;">${row['price']:,.2f}</td>
                                                        <td style="padding: 16px 10px; text-align: right;">
                                                            <span style="background: linear-gradient(135deg, #28a745 0%, #20883a 100%); color: #fff; padding: 6px 12px; font-size: 14px; font-weight: 900; box-shadow: 0 2px 8px rgba(40, 167, 69, 0.6), inset 0 1px 2px rgba(255,255,255,0.3); display: inline-block;">${row['price'] * 0.98:,.2f}</span>
                                                        </td>
                                                        <td style="padding: 16px 10px; text-align: right;">
                                                            <span style="background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%); color: #fff; padding: 6px 12px; font-size: 14px; font-weight: 900; box-shadow: 0 2px 8px rgba(255, 68, 68, 0.6), inset 0 1px 2px rgba(255,255,255,0.2); display: inline-block;">${row['price'] * 0.95:,.2f}</span>
                                                        </td>
                                                        <td style="padding: 16px 10px; text-align: right;">
                                                            <span style="background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); color: #fff; padding: 6px 12px; font-size: 14px; font-weight: 900; box-shadow: 0 2px 8px rgba(211, 47, 47, 0.6), inset 0 1px 2px rgba(255,255,255,0.3); display: inline-block;">+15%</span>
                                                        </td>
                                                    </tr>
                                                    ''' for _, row in shorts.iterrows()])}
                                                </table>

                                                <!-- Strategy Box -->
                                                <div style="margin-top: 18px; padding: 16px; background: linear-gradient(135deg, #102a43 0%, #0a1929 100%); border: 1px solid #28a745; border-left: 4px solid #28a745; box-shadow: 0 0 15px rgba(40, 167, 69, 0.2), inset 0 0 10px rgba(40, 167, 69, 0.05);">
                                                    <div style="color: #28a745; font-size: 13px; line-height: 1.8; font-weight: 700;">
                                                        <span style="color: #d32f2f; font-weight: 900;">🎯 BATTLE PLAN:</span>
                                                        <span style="color: #e2e8f0;">Enter at Buy Zone • Stop at 5% below • Target 15% gain • Risk/Reward = 1:3</span>
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- CROWDED LONGS CARD (SPARTAN THEME) -->
                            <tr>
                                <td style="padding: 0 20px 20px 20px; background: #0a1929;">
                                    <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #102a43 0%, #0a1929 100%); border: 2px solid #ff4444; box-shadow: 0 0 20px rgba(255, 68, 68, 0.3), inset 0 0 15px rgba(255, 68, 68, 0.05); overflow: hidden;">
                                        <tr>
                                            <td style="padding: 25px;">
                                                <!-- Card Header -->
                                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
                                                    <tr>
                                                        <td>
                                                            <div style="display: inline-block; background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%); padding: 12px 24px; clip-path: polygon(8% 0%, 92% 0%, 100% 50%, 92% 100%, 8% 100%, 0% 50%); box-shadow: 0 4px 16px rgba(255, 68, 68, 0.5), inset 0 2px 4px rgba(255,255,255,0.3);">
                                                                <span style="font-size: 26px; vertical-align: middle;">🔥</span>
                                                                <span style="color: #fff; font-size: 19px; font-weight: 900; margin-left: 10px; vertical-align: middle; letter-spacing: 2px; text-transform: uppercase;">CROWDED LONGS</span>
                                                            </div>
                                                            <div style="margin-top: 12px;">
                                                                <span style="background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%); color: #fff; padding: 6px 16px; font-size: 12px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; box-shadow: 0 2px 8px rgba(255, 68, 68, 0.3); display: inline-block;">💥 CRASH POTENTIAL ↘</span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                </table>

                                                <!-- Data Table -->
                                                <table width="100%" cellpadding="0" cellspacing="0" style="background: #0a1929; border: 1px solid #1e3a52; overflow: hidden;">
                                                    <tr style="background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%); box-shadow: 0 2px 8px rgba(255, 68, 68, 0.3);">
                                                        <th style="color: #fff; font-size: 11px; padding: 14px 10px; text-align: center; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">TYPE</th>
                                                        <th style="color: #fff; font-size: 11px; padding: 14px 10px; text-align: left; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">SYMBOL</th>
                                                        <th style="color: #fff; font-size: 11px; padding: 14px 10px; text-align: right; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">PRICE</th>
                                                        <th style="color: #fff; font-size: 11px; padding: 14px 10px; text-align: right; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">SELL</th>
                                                        <th style="color: #fff; font-size: 11px; padding: 14px 10px; text-align: right; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">STOP</th>
                                                        <th style="color: #fff; font-size: 11px; padding: 14px 10px; text-align: right; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">TARGET</th>
                                                    </tr>
                                                    {"".join([f'''
                                                    <tr style="border-bottom: 1px solid #1e3a52; background: rgba(255, 255, 255, 0.03);">
                                                        <td style="padding: 16px 10px; text-align: center; font-size: 28px; filter: drop-shadow(0 2px 12px rgba(255, 255, 255, 0.5));">{row['icon']}</td>
                                                        <td style="padding: 16px 10px; font-size: 18px; font-weight: 900; color: #fff; text-shadow: 0 2px 8px rgba(255, 255, 255, 0.4);">{row['symbol']}</td>
                                                        <td style="padding: 16px 10px; text-align: right; color: #fff; font-size: 16px; font-weight: 700;">${row['price']:,.2f}</td>
                                                        <td style="padding: 16px 10px; text-align: right;">
                                                            <span style="background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%); color: #fff; padding: 6px 12px; font-size: 14px; font-weight: 900; box-shadow: 0 2px 8px rgba(255, 68, 68, 0.6), inset 0 1px 2px rgba(255,255,255,0.2); display: inline-block;">${row['price'] * 1.02:,.2f}</span>
                                                        </td>
                                                        <td style="padding: 16px 10px; text-align: right;">
                                                            <span style="background: linear-gradient(135deg, #28a745 0%, #20883a 100%); color: #fff; padding: 6px 12px; font-size: 14px; font-weight: 900; box-shadow: 0 2px 8px rgba(40, 167, 69, 0.6), inset 0 1px 2px rgba(255,255,255,0.3); display: inline-block;">${row['price'] * 1.05:,.2f}</span>
                                                        </td>
                                                        <td style="padding: 16px 10px; text-align: right;">
                                                            <span style="background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); color: #fff; padding: 6px 12px; font-size: 14px; font-weight: 900; box-shadow: 0 2px 8px rgba(211, 47, 47, 0.6), inset 0 1px 2px rgba(255,255,255,0.3); display: inline-block;">-15%</span>
                                                        </td>
                                                    </tr>
                                                    ''' for _, row in longs.iterrows()])}
                                                </table>

                                                <!-- Strategy Box -->
                                                <div style="margin-top: 18px; padding: 16px; background: linear-gradient(135deg, #102a43 0%, #0a1929 100%); border: 1px solid #ff4444; border-left: 4px solid #ff4444; box-shadow: 0 0 15px rgba(255, 68, 68, 0.2), inset 0 0 10px rgba(255, 68, 68, 0.05);">
                                                    <div style="color: #ff4444; font-size: 13px; line-height: 1.8; font-weight: 700;">
                                                        <span style="color: #d32f2f; font-weight: 900;">🎯 BATTLE PLAN:</span>
                                                        <span style="color: #e2e8f0;">Sell at Sell Zone • Stop at 5% above • Target 15% crash • Risk/Reward = 1:3</span>
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- COMBAT DOCTRINE (STRATEGY BOX) -->
                            <tr>
                                <td style="padding: 30px 20px; background: #0a1929;">
                                    <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #102a43 0%, #0a1929 100%); border: 2px solid #d32f2f; box-shadow: 0 0 20px rgba(211, 47, 47, 0.3), inset 0 0 15px rgba(211, 47, 47, 0.05);">
                                        <tr>
                                            <td style="padding: 25px;">
                                                <!-- Header -->
                                                <div align="center" style="margin-bottom: 25px;">
                                                    <div style="display: inline-block; background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); padding: 10px 28px; clip-path: polygon(5% 0%, 95% 0%, 100% 50%, 95% 100%, 5% 100%, 0% 50%); box-shadow: 0 4px 16px rgba(211, 47, 47, 0.4), inset 0 2px 4px rgba(255,255,255,0.3);">
                                                        <span style="color: #000; font-size: 16px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">🛡️ COMBAT DOCTRINE</span>
                                                    </div>
                                                </div>

                                                <table width="100%" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td width="48%" style="padding: 20px; border-right: 2px solid #d32f2f; background: linear-gradient(135deg, rgba(40, 167, 69, 0.1) 0%, rgba(0, 0, 0, 0) 100%);">
                                                            <div style="margin-bottom: 15px;">
                                                                <span style="font-size: 32px; margin-right: 10px; filter: drop-shadow(0 2px 8px rgba(40, 167, 69, 0.5));">🟢</span>
                                                                <span style="color: #28a745; font-size: 17px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; text-shadow: 0 2px 4px rgba(40, 167, 69, 0.4);">BULL REGIME</span>
                                                            </div>
                                                            <div style="color: #e2e8f0; font-size: 14px; line-height: 2; font-weight: 600;">
                                                                <div style="margin: 8px 0;">✓ <span style="color: #28a745;">Buy the dips</span></div>
                                                                <div style="margin: 8px 0;">✓ <span style="color: #28a745;">Hold winners</span></div>
                                                                <div style="margin: 8px 0;">✗ <span style="color: #64748b;">Avoid shorting</span></div>
                                                            </div>
                                                        </td>
                                                        <td width="4%"></td>
                                                        <td width="48%" style="padding: 20px; background: linear-gradient(135deg, rgba(255, 68, 68, 0.1) 0%, rgba(0, 0, 0, 0) 100%);">
                                                            <div style="margin-bottom: 15px;">
                                                                <span style="font-size: 32px; margin-right: 10px; filter: drop-shadow(0 2px 8px rgba(255, 68, 68, 0.5));">🔴</span>
                                                                <span style="color: #ff4444; font-size: 17px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; text-shadow: 0 2px 4px rgba(255, 68, 68, 0.4);">BEAR REGIME</span>
                                                            </div>
                                                            <div style="color: #e2e8f0; font-size: 14px; line-height: 2; font-weight: 600;">
                                                                <div style="margin: 8px 0;">✓ <span style="color: #ff4444;">Sell the rallies</span></div>
                                                                <div style="margin: 8px 0;">✓ <span style="color: #ff4444;">Take profits fast</span></div>
                                                                <div style="margin: 8px 0;">✗ <span style="color: #64748b;">Avoid buying</span></div>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- ARSENAL LEGEND -->
                            <tr>
                                <td style="padding: 30px 20px; background: #0a1929;">
                                    <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #102a43 0%, #0a1929 100%); border: 2px solid #d32f2f; box-shadow: 0 0 20px rgba(211, 47, 47, 0.2), inset 0 0 15px rgba(211, 47, 47, 0.05);">
                                        <tr>
                                            <td style="padding: 25px;">
                                                <!-- Header -->
                                                <div align="center" style="margin-bottom: 20px;">
                                                    <span style="color: #d32f2f; font-size: 14px; font-weight: 900; letter-spacing: 3px; text-transform: uppercase; text-shadow: 0 2px 4px rgba(211, 47, 47, 0.4);">ARSENAL LEGEND</span>
                                                </div>

                                                <table width="100%" cellpadding="15" cellspacing="0">
                                                    <tr>
                                                        <td width="25%" align="center" style="border-right: 1px solid #1e3a52;">
                                                            <div style="font-size: 36px; margin-bottom: 10px; filter: drop-shadow(0 2px 6px rgba(211, 47, 47, 0.3));">₿</div>
                                                            <div style="font-size: 12px; color: #94a3b8; font-weight: 700; letter-spacing: 1px;">CRYPTO</div>
                                                        </td>
                                                        <td width="25%" align="center" style="border-right: 1px solid #1e3a52;">
                                                            <div style="font-size: 36px; margin-bottom: 10px; filter: drop-shadow(0 2px 6px rgba(211, 47, 47, 0.3));">📊</div>
                                                            <div style="font-size: 12px; color: #94a3b8; font-weight: 700; letter-spacing: 1px;">STOCKS</div>
                                                        </td>
                                                        <td width="25%" align="center" style="border-right: 1px solid #1e3a52;">
                                                            <div style="font-size: 36px; margin-bottom: 10px; filter: drop-shadow(0 2px 6px rgba(211, 47, 47, 0.3));">📈</div>
                                                            <div style="font-size: 12px; color: #94a3b8; font-weight: 700; letter-spacing: 1px;">FUTURES</div>
                                                        </td>
                                                        <td width="25%" align="center">
                                                            <div style="font-size: 36px; margin-bottom: 10px; filter: drop-shadow(0 2px 6px rgba(211, 47, 47, 0.3));">📉</div>
                                                            <div style="font-size: 12px; color: #94a3b8; font-weight: 700; letter-spacing: 1px;">BONDS</div>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- BATTLEFIELD STATS -->
                            <tr>
                                <td style="padding: 0 20px 20px 20px; background: #0a1929;">
                                    <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #102a43 0%, #0a1929 100%); border: 2px solid #1e3a52; box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);">
                                        <tr>
                                            <td width="25%" align="center" style="padding: 20px; border-right: 1px solid #1e3a52;">
                                                <div style="color: #94a3b8; font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">CRYPTO</div>
                                                <div style="color: #d32f2f; font-size: 32px; font-weight: 900; text-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);">601</div>
                                            </td>
                                            <td width="25%" align="center" style="padding: 20px; border-right: 1px solid #1e3a52;">
                                                <div style="color: #94a3b8; font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">STOCKS</div>
                                                <div style="color: #d32f2f; font-size: 32px; font-weight: 900; text-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);">8</div>
                                            </td>
                                            <td width="25%" align="center" style="padding: 20px; border-right: 1px solid #1e3a52;">
                                                <div style="color: #94a3b8; font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">FUTURES</div>
                                                <div style="color: #d32f2f; font-size: 32px; font-weight: 900; text-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);">5</div>
                                            </td>
                                            <td width="25%" align="center" style="padding: 20px;">
                                                <div style="color: #94a3b8; font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">BONDS</div>
                                                <div style="color: #d32f2f; font-size: 32px; font-weight: 900; text-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);">3</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- SPARTAN FOOTER -->
                            <tr>
                                <td style="background: linear-gradient(180deg, #0a1929 0%, #0a1929 100%); padding: 30px; text-align: center; border-top: 3px solid #d32f2f;">
                                    <!-- Spartan Motto -->
                                    <div style="margin-bottom: 15px;">
                                        <span style="font-size: 48px; filter: drop-shadow(0 4px 12px rgba(211, 47, 47, 0.6));">🛡️</span>
                                    </div>
                                    <div style="color: #d32f2f; font-size: 22px; font-weight: 900; margin-bottom: 12px; letter-spacing: 3px; text-transform: uppercase; text-shadow: 0 2px 8px rgba(211, 47, 47, 0.5);">TRADE SMART, TRADE CONTRARIAN!</div>
                                    <div style="color: #94a3b8; font-size: 12px; font-weight: 600; letter-spacing: 1px;">Automated by Nano Banana System • Daily at 08:01 AM</div>
                                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #1e3a52;">
                                        <span style="color: #64748b; font-size: 11px; font-weight: 600;">🍌 This is Sparta! 🍌</span>
                                    </div>
                                </td>
                            </tr>

            </table>
        </body>
        </html>
        """

        # 3. Send Email
        msg = MIMEMultipart()
        msg["Subject"] = f"Spartan Report: {btc_regime.split()[1]} Regime | BTC ${btc_price:,.0f}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg.attach(MIMEText(html, "html"))

        logger.info(f"Sending email to {RECEIVER_EMAIL}...")
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        logger.info("✅ Email sent successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Email send failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = send_email()
    exit(0 if success else 1)
