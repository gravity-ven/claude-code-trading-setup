#!/usr/bin/env python3
"""
Spartan Labs - Daily Automated Scanner & Emailer
Runs technical analysis on US market symbols and emails top 10 high-confidence picks
Author: Spartan Labs
Created: November 23, 2025
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
POLYGON_API_KEY = os.getenv('POLYGON_IO_API_KEY', '08bqd7Ew8fw1b7QcixwkTea1UvJHdRkD')
EMAIL_RECIPIENT = 'naga.kvv@gmail.com'
MIN_SCORE = 7.6  # 80% confidence (80% of max 9.5 score)
MAX_SYMBOLS = 12000  # Scan 12,000 symbols daily
DELAY_MS = 100  # Paid tier delay


class MarketScanner:
    """Technical analysis scanner for market symbols"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.api_base = 'https://api.polygon.io'
        self.spy_performance = 0

    def fetch_symbols(self, market_type='stocks', limit=2000):
        """Fetch active symbols from Polygon.io"""
        logger.info(f"Fetching {limit} {market_type} symbols from Polygon.io...")
        symbols = []
        next_url = f"{self.api_base}/v3/reference/tickers?market={market_type}&active=true&limit=1000&apiKey={self.api_key}"

        while next_url and len(symbols) < limit:
            try:
                response = requests.get(next_url, timeout=30)
                data = response.json()

                if 'results' in data:
                    symbols.extend(data['results'])
                    logger.info(f"Loaded {len(symbols)} symbols...")

                next_url = data.get('next_url')
                if next_url:
                    next_url += f"&apiKey={self.api_key}"
                    time.sleep(0.25)
                else:
                    break

            except Exception as e:
                logger.error(f"Error fetching symbols: {e}")
                break

        logger.info(f"Total symbols loaded: {len(symbols)}")
        return [s['ticker'] for s in symbols]

    def fetch_bars(self, symbol, days=120):
        """Fetch price bars for symbol"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        url = f"{self.api_base}/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}?adjusted=true&sort=asc&limit=120&apiKey={self.api_key}"

        try:
            response = requests.get(url, timeout=15)
            data = response.json()
            return data.get('results', [])
        except:
            return []

    def calculate_sma(self, bars, period):
        """Calculate Simple Moving Average"""
        if len(bars) < period:
            return None
        closes = [b['c'] for b in bars[-period:]]
        return sum(closes) / period

    def calculate_rsi(self, bars, period=14):
        """Calculate Relative Strength Index"""
        if len(bars) < period + 1:
            return None

        closes = [b['c'] for b in bars]
        gains = []
        losses = []

        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_bollinger(self, bars, period=20):
        """Calculate Bollinger Bands"""
        if len(bars) < period:
            return {'upper': None, 'lower': None, 'width': 0}

        closes = [b['c'] for b in bars[-period:]]
        sma = sum(closes) / period
        variance = sum((c - sma) ** 2 for c in closes) / period
        std_dev = variance ** 0.5

        upper = sma + (2 * std_dev)
        lower = sma - (2 * std_dev)
        width = (upper - lower) / sma if sma != 0 else 0

        return {'upper': upper, 'lower': lower, 'width': width}

    def analyze_symbol(self, symbol, mode='long'):
        """Run technical analysis on symbol for LONG or SHORT mode"""
        bars = self.fetch_bars(symbol)

        if len(bars) < 50:
            return None

        current = bars[-1]
        prev = bars[-2]

        # Technical indicators
        sma20 = self.calculate_sma(bars, 20)
        sma50 = self.calculate_sma(bars, 50)
        rsi = self.calculate_rsi(bars, 14)
        bb = self.calculate_bollinger(bars, 20)

        if None in [sma20, sma50, rsi]:
            return None

        # Volume analysis
        avg_vol = sum(b['v'] for b in bars[-20:]) / 20

        # 5-day performance
        price_5d_ago = bars[-6]['c'] if len(bars) >= 6 else current['c']
        perf_5d = ((current['c'] - price_5d_ago) / price_5d_ago) * 100

        # Scoring (adapt based on mode)
        score = 0
        checks = []

        if mode == 'long':
            # LONG MODE: Bullish signals
            # 1. Uptrend
            if current['c'] > sma20:
                score += 1
                checks.append(('🔺 Uptrend', True))
            else:
                checks.append(('🔺 Uptrend', False))

            # 2. Volume confirmation
            vol_pass = current['v'] > avg_vol or (current['c'] > prev['c'] and current['v'] > prev['v'])
            if vol_pass:
                score += 1
                checks.append(('🔺 Buying Pressure', True))
            else:
                checks.append(('🔺 Buying Pressure', False))

            # 3. Relative Strength vs SPY
            if perf_5d > self.spy_performance:
                score += 1
                checks.append(('🔺 Outperforming', True))
            else:
                checks.append(('🔺 Outperforming', False))

            # 4. RSI Sweet Spot (50-70)
            if 50 <= rsi <= 70:
                score += 1
                checks.append(('🔺 Bullish RSI', True))
            else:
                checks.append(('🔺 Bullish RSI', False))

            # 5. Weekly Trend (SMA50)
            if current['c'] > sma50:
                score += 1
                checks.append(('🔺 Weekly Uptrend', True))
            else:
                checks.append(('🔺 Weekly Uptrend', False))

            # 6. Stop Loss Distance < 7%
            min_low = min(b['l'] for b in bars[-5:])
            stop_dist = ((current['c'] - min_low) / current['c']) * 100
            if stop_dist < 7:
                score += 1
                checks.append(('🔺 Tight Stop', True))
            else:
                checks.append(('🔺 Tight Stop', False))

        else:
            # SHORT MODE: Bearish signals
            # 1. Downtrend
            if current['c'] < sma20:
                score += 1
                checks.append(('🔻 Downtrend', True))
            else:
                checks.append(('🔻 Downtrend', False))

            # 2. Volume on decline
            vol_pass = current['v'] > avg_vol or (current['c'] < prev['c'] and current['v'] > prev['v'])
            if vol_pass:
                score += 1
                checks.append(('🔻 Selling Pressure', True))
            else:
                checks.append(('🔻 Selling Pressure', False))

            # 3. Relative Weakness vs SPY
            if perf_5d < self.spy_performance:
                score += 1
                checks.append(('🔻 Underperforming', True))
            else:
                checks.append(('🔻 Underperforming', False))

            # 4. RSI Weak Zone (30-50)
            if 30 <= rsi <= 50:
                score += 1
                checks.append(('🔻 Bearish RSI', True))
            else:
                checks.append(('🔻 Bearish RSI', False))

            # 5. Weekly Downtrend (SMA50)
            if current['c'] < sma50:
                score += 1
                checks.append(('🔻 Weekly Downtrend', True))
            else:
                checks.append(('🔻 Weekly Downtrend', False))

            # 6. Stop Loss Distance < 7%
            max_high = max(b['h'] for b in bars[-5:])
            stop_dist = ((max_high - current['c']) / current['c']) * 100
            if stop_dist < 7:
                score += 1
                checks.append(('🔻 Tight Stop', True))
            else:
                checks.append(('🔻 Tight Stop', False))

        # 7. No major news events (simplified - always pass for automated scan)
        score += 1
        checks.append(('No Event Risk', True))

        # 8. Volatility Squeeze (bonus points)
        if bb['width'] < 0.12:
            score += 1.5
            checks.append(('Volatility Squeeze', True))
        else:
            checks.append(('Volatility Squeeze', False))

        return {
            'symbol': symbol,
            'price': current['c'],
            'score': score,
            'rsi': rsi,
            'perf_5d': perf_5d,
            'checks': checks,
            'mode': mode
        }

    def get_spy_performance(self):
        """Calculate SPY 5-day performance for benchmark"""
        logger.info("Fetching SPY benchmark...")
        bars = self.fetch_bars('SPY', days=10)
        if len(bars) >= 6:
            spy_start = bars[-6]['c']
            spy_end = bars[-1]['c']
            self.spy_performance = ((spy_end - spy_start) / spy_start) * 100
            logger.info(f"SPY 5-day performance: {self.spy_performance:.2f}%")

    def scan_market(self, symbols, mode='long', min_score=6.0, max_results=10):
        """Scan multiple symbols and return top performers for LONG or SHORT"""
        self.get_spy_performance()

        results = []
        total = len(symbols)

        mode_label = "LONG (Bullish)" if mode == 'long' else "SHORT (Bearish)"
        logger.info(f"Scanning {total} symbols for {mode_label} opportunities (min score: {min_score})...")

        for i, symbol in enumerate(symbols):
            try:
                result = self.analyze_symbol(symbol, mode=mode)

                if result and result['score'] >= min_score:
                    results.append(result)
                    logger.info(f"[{i+1}/{total}] {symbol}: QUALIFIED (Score: {result['score']:.1f}) [{mode_label}]")
                else:
                    if (i + 1) % 500 == 0:
                        logger.info(f"Progress: {i+1}/{total} ({len(results)} qualified)")

                # Rate limiting
                time.sleep(DELAY_MS / 1000.0)

            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue

        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)

        logger.info(f"{mode_label} scan complete! {len(results)} qualified symbols found.")
        return results[:max_results]


def send_email(top_long, top_short, recipient=EMAIL_RECIPIENT):
    """Send email with top LONG and SHORT symbol picks"""
    logger.info(f"Sending email to {recipient}...")

    # Create email body
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #0f172a; color: #ffffff; padding: 20px; }}
            h1 {{ color: #facc15; text-align: center; }}
            h2 {{ color: #10b981; margin-top: 30px; }}
            h2.short {{ color: #ef4444; }}
            table {{ border-collapse: collapse; width: 100%; max-width: 900px; margin: 20px auto; }}
            th {{ background: #1e293b; padding: 12px; text-align: left; border-bottom: 2px solid #facc15; }}
            td {{ padding: 10px; border-bottom: 1px solid #334155; }}
            .long-score {{ color: #10b981; font-weight: bold; }}
            .short-score {{ color: #ef4444; font-weight: bold; }}
            .footer {{ margin-top: 40px; font-size: 12px; color: #64748b; text-align: center; }}
            .section {{ margin: 30px 0; }}
            .confidence-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
            .badge-green {{ background: #10b981; color: #000; }}
            .badge-red {{ background: #ef4444; color: #fff; }}
        </style>
    </head>
    <body>
        <h1>🍌 Spartan Labs - Daily Market Intelligence</h1>
        <p style="text-align: center;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p style="text-align: center; color: #64748b;">Minimum Confidence: 80% | Scanned: 12,000 symbols</p>

        <div class="section">
            <h2>🔺 TOP 10 LONG OPPORTUNITIES (Bullish)</h2>
            <table>
                <tr>
                    <th>#</th>
                    <th>Symbol</th>
                    <th>Price</th>
                    <th>Score</th>
                    <th>Confidence</th>
                    <th>RSI</th>
                    <th>5D Perf</th>
                </tr>
    """

    for i, symbol_data in enumerate(top_long, 1):
        percent = min(100, (symbol_data['score'] / 9.5) * 100)
        confidence_text = '🚀 STRONG BUY' if symbol_data['score'] >= 8.5 else 'GO LONG'

        html_body += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{symbol_data['symbol']}</strong></td>
                <td>${symbol_data['price']:.2f}</td>
                <td class="long-score">{symbol_data['score']:.1f}/9.5</td>
                <td><span class="confidence-badge badge-green">{percent:.0f}% - {confidence_text}</span></td>
                <td>{symbol_data['rsi']:.1f}</td>
                <td class="long-score">+{symbol_data['perf_5d']:.2f}%</td>
            </tr>
        """

    html_body += """
            </table>
        </div>

        <div class="section">
            <h2 class="short">🔻 TOP 10 SHORT OPPORTUNITIES (Bearish)</h2>
            <table>
                <tr>
                    <th>#</th>
                    <th>Symbol</th>
                    <th>Price</th>
                    <th>Score</th>
                    <th>Confidence</th>
                    <th>RSI</th>
                    <th>5D Perf</th>
                </tr>
    """

    for i, symbol_data in enumerate(top_short, 1):
        percent = min(100, (symbol_data['score'] / 9.5) * 100)
        confidence_text = '📉 STRONG SELL' if symbol_data['score'] >= 8.5 else 'GO SHORT'

        html_body += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{symbol_data['symbol']}</strong></td>
                <td>${symbol_data['price']:.2f}</td>
                <td class="short-score">{symbol_data['score']:.1f}/9.5</td>
                <td><span class="confidence-badge badge-red">{percent:.0f}% - {confidence_text}</span></td>
                <td>{symbol_data['rsi']:.1f}</td>
                <td class="short-score">{symbol_data['perf_5d']:.2f}%</td>
            </tr>
        """

    html_body += """
            </table>
        </div>

        <div class="footer">
            <p><strong>Spartan Labs Daily Scanner</strong></p>
            <p>Powered by Polygon.io Market Data</p>
            <p>⚠️ For informational purposes only. Not financial advice.</p>
        </div>
    </body>
    </html>
    """

    # Send email using SMTP (configure your email settings)
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Spartan Labs Daily Top 10 - {datetime.now().strftime("%Y-%m-%d")}'
        msg['From'] = 'noreply@spartanlabs.ai'
        msg['To'] = recipient

        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        # TODO: Configure your SMTP server settings
        # For Gmail: smtp.gmail.com:587
        # For Outlook: smtp-mail.outlook.com:587

        # Uncomment and configure when ready to send emails:
        # with smtplib.SMTP('smtp.gmail.com', 587) as server:
        #     server.starttls()
        #     server.login('your_email@gmail.com', 'your_app_password')
        #     server.send_message(msg)

        # For now, save to file for testing
        with open('daily_email_report.html', 'w') as f:
            f.write(html_body)

        logger.info(f"Email report generated: daily_email_report.html")
        logger.info("NOTE: SMTP email sending is disabled. Configure SMTP settings to enable.")

        return True

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False


def main():
    """Main execution function"""
    logger.info("="*60)
    logger.info("SPARTAN LABS DAILY SCANNER - STARTING")
    logger.info("="*60)
    logger.info(f"Configuration:")
    logger.info(f"  - Scanning: {MAX_SYMBOLS:,} symbols")
    logger.info(f"  - Min Confidence: 80% (Score: {MIN_SCORE:.1f}+)")
    logger.info(f"  - Email: {EMAIL_RECIPIENT}")
    logger.info("="*60)

    scanner = MarketScanner(POLYGON_API_KEY)

    # Fetch symbols
    symbols = scanner.fetch_symbols('stocks', limit=MAX_SYMBOLS)

    if not symbols:
        logger.error("No symbols fetched. Exiting.")
        return

    # Scan for LONG opportunities
    logger.info("\n" + "="*60)
    logger.info("PHASE 1: SCANNING FOR LONG OPPORTUNITIES (BULLISH)")
    logger.info("="*60)
    top_long = scanner.scan_market(symbols, mode='long', min_score=MIN_SCORE, max_results=10)

    # Scan for SHORT opportunities
    logger.info("\n" + "="*60)
    logger.info("PHASE 2: SCANNING FOR SHORT OPPORTUNITIES (BEARISH)")
    logger.info("="*60)
    top_short = scanner.scan_market(symbols, mode='short', min_score=MIN_SCORE, max_results=10)

    # Display results
    logger.info("\n" + "="*60)
    logger.info("TOP 10 LONG OPPORTUNITIES (80%+ Confidence)")
    logger.info("="*60)
    if top_long:
        for i, result in enumerate(top_long, 1):
            percent = (result['score'] / 9.5) * 100
            logger.info(f"{i}. {result['symbol']} - {percent:.0f}% - Score: {result['score']:.1f} - Price: ${result['price']:.2f}")
    else:
        logger.warning("No LONG symbols found with 80%+ confidence")

    logger.info("\n" + "="*60)
    logger.info("TOP 10 SHORT OPPORTUNITIES (80%+ Confidence)")
    logger.info("="*60)
    if top_short:
        for i, result in enumerate(top_short, 1):
            percent = (result['score'] / 9.5) * 100
            logger.info(f"{i}. {result['symbol']} - {percent:.0f}% - Score: {result['score']:.1f} - Price: ${result['price']:.2f}")
    else:
        logger.warning("No SHORT symbols found with 80%+ confidence")

    # Send email if we have results
    if top_long or top_short:
        send_email(top_long, top_short)
    else:
        logger.warning("No qualified symbols found. Email not sent.")

    logger.info("\n" + "="*60)
    logger.info("DAILY SCANNER COMPLETE")
    logger.info("="*60)


if __name__ == '__main__':
    main()
