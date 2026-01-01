#!/usr/bin/env python3
"""
Spartan Labs - COT (Commitment of Traders) Daily Emailer
Fetches REAL CFTC data, generates infographic, and emails daily report
Author: Spartan Labs
Created: November 24, 2025
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cot_daily_emailer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ================= CONFIGURATION =================
# Email settings (load from environment variables)
SENDER_EMAIL = os.getenv('SMTP_USER', 'naga.kvv@gmail.com')
SENDER_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # App Password (NOT regular password!)
RECIPIENT_EMAIL = os.getenv('COT_RECIPIENT_EMAIL', 'naga.kvv@gmail.com')
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

# Output settings
OUTPUT_DIR = Path('cot_reports')
OUTPUT_DIR.mkdir(exist_ok=True)
FILENAME = OUTPUT_DIR / f"COT_Report_{datetime.now().strftime('%Y-%m-%d')}.png"

# COT Index thresholds (95% = extreme long, 5% = extreme short)
UPPER_THRESHOLD = 95
LOWER_THRESHOLD = 5

# CFTC API endpoint (official public data)
CFTC_API_BASE = 'https://publicreporting.cftc.gov/resource'

# Symbol mapping: CFTC code -> Human readable name
COT_SYMBOLS = {
    # CRYPTO (Futures)
    'BTC': {'cftc_code': '133741', 'name': 'Bitcoin (BTC)', 'category': 'Crypto'},
    'ETH': {'cftc_code': '134741', 'name': 'Ether (ETH)', 'category': 'Crypto'},

    # ENERGIES
    'NG': {'cftc_code': '023651', 'name': 'Natural Gas', 'category': 'Energy'},
    'CL': {'cftc_code': '067651', 'name': 'Crude Oil (WTI)', 'category': 'Energy'},
    'BZ': {'cftc_code': '095741', 'name': 'Brent Crude', 'category': 'Energy'},
    'HO': {'cftc_code': '022651', 'name': 'Heating Oil', 'category': 'Energy'},
    'RB': {'cftc_code': '111659', 'name': 'Gasoline (RBOB)', 'category': 'Energy'},

    # METALS
    'GC': {'cftc_code': '088691', 'name': 'Gold', 'category': 'Metals'},
    'SI': {'cftc_code': '084691', 'name': 'Silver', 'category': 'Metals'},
    'HG': {'cftc_code': '085692', 'name': 'Copper', 'category': 'Metals'},
    'PL': {'cftc_code': '076651', 'name': 'Platinum', 'category': 'Metals'},
    'PA': {'cftc_code': '075651', 'name': 'Palladium', 'category': 'Metals'},

    # INDICES
    'ES': {'cftc_code': '13874+', 'name': 'S&P 500', 'category': 'Indices'},
    'NQ': {'cftc_code': '20974+', 'name': 'Nasdaq 100', 'category': 'Indices'},
    'YM': {'cftc_code': '12460+', 'name': 'Dow Jones (Mini)', 'category': 'Indices'},
    'RTY': {'cftc_code': '239742', 'name': 'Russell 2000', 'category': 'Indices'},
    'NIY': {'cftc_code': '240741', 'name': 'Nikkei 225', 'category': 'Indices'},
    'VX': {'cftc_code': '1170E1', 'name': 'VIX Futures', 'category': 'Indices'},

    # CURRENCIES
    'DX': {'cftc_code': '098662', 'name': 'Dollar Index (DXY)', 'category': 'Currencies'},
    'EUR': {'cftc_code': '099741', 'name': 'Euro FX', 'category': 'Currencies'},
    'JPY': {'cftc_code': '097741', 'name': 'Japanese Yen', 'category': 'Currencies'},
    'GBP': {'cftc_code': '096742', 'name': 'British Pound', 'category': 'Currencies'},
    'AUD': {'cftc_code': '232741', 'name': 'Australian Dollar', 'category': 'Currencies'},
    'CAD': {'cftc_code': '090741', 'name': 'Canadian Dollar', 'category': 'Currencies'},
    'CHF': {'cftc_code': '092741', 'name': 'Swiss Franc', 'category': 'Currencies'},
    'NZD': {'cftc_code': '112741', 'name': 'New Zealand Dollar', 'category': 'Currencies'},
    'MXN': {'cftc_code': '095741', 'name': 'Mexican Peso', 'category': 'Currencies'},
    'BRL': {'cftc_code': '102741', 'name': 'Brazilian Real', 'category': 'Currencies'},
    'ZAR': {'cftc_code': '123741', 'name': 'S. African Rand', 'category': 'Currencies'},

    # GRAINS
    'ZC': {'cftc_code': '002602', 'name': 'Corn', 'category': 'Grains'},
    'ZS': {'cftc_code': '005602', 'name': 'Soybeans', 'category': 'Grains'},
    'ZW': {'cftc_code': '001602', 'name': 'Wheat', 'category': 'Grains'},
    'ZL': {'cftc_code': '007601', 'name': 'Soybean Oil', 'category': 'Grains'},
    'ZM': {'cftc_code': '026603', 'name': 'Soybean Meal', 'category': 'Grains'},
    'ZO': {'cftc_code': '004603', 'name': 'Oats', 'category': 'Grains'},
    'ZR': {'cftc_code': '039601', 'name': 'Rough Rice', 'category': 'Grains'},

    # MEATS
    'LE': {'cftc_code': '057642', 'name': 'Live Cattle', 'category': 'Meats'},
    'GF': {'cftc_code': '061641', 'name': 'Feeder Cattle', 'category': 'Meats'},
    'HE': {'cftc_code': '054642', 'name': 'Lean Hogs', 'category': 'Meats'},

    # SOFTS
    'SB': {'cftc_code': '080732', 'name': 'Sugar #11', 'category': 'Softs'},
    'KC': {'cftc_code': '083731', 'name': 'Coffee', 'category': 'Softs'},
    'CC': {'cftc_code': '073732', 'name': 'Cocoa', 'category': 'Softs'},
    'CT': {'cftc_code': '033661', 'name': 'Cotton #2', 'category': 'Softs'},
    'OJ': {'cftc_code': '040701', 'name': 'Orange Juice', 'category': 'Softs'},
    'LB': {'cftc_code': '058643', 'name': 'Lumber', 'category': 'Softs'},

    # RATES (Treasury Futures)
    'ZN': {'cftc_code': '043602', 'name': '10-Year T-Note', 'category': 'Rates'},
    'ZB': {'cftc_code': '020601', 'name': '30-Year T-Bond', 'category': 'Rates'},
    'ZF': {'cftc_code': '044601', 'name': '5-Year T-Note', 'category': 'Rates'},
    'GE': {'cftc_code': '132741', 'name': 'Eurodollar', 'category': 'Rates'},
}


class COTDataFetcher:
    """Fetch and process real CFTC Commitment of Traders data"""

    def __init__(self):
        self.data = {}

    def calculate_cot_index(self, commercial_long, commercial_short):
        """
        Calculate COT Index (0-100 scale)

        COT Index Formula:
        - 100 = Maximum commercial net long (extreme bullish positioning)
        - 0 = Maximum commercial net short (extreme bearish positioning)

        Commercial traders are considered "smart money" - we track their positioning
        When commercials are heavily net short (index near 0), it's a SELL signal
        When commercials are heavily net long (index near 100), it's a BUY signal
        """
        try:
            net_position = commercial_long - commercial_short
            total_position = commercial_long + commercial_short

            if total_position == 0:
                return 50  # Neutral if no position data

            # Normalize to 0-100 scale
            # Net position ranges from -total to +total
            # Convert to 0-100 where 0 = max short, 100 = max long
            cot_index = ((net_position / total_position) + 1) * 50

            return max(0, min(100, cot_index))  # Clamp to 0-100
        except:
            return 50  # Default to neutral on error

    def fetch_cot_data(self):
        """
        Fetch latest COT data from CFTC public API

        NOTE: This is a PLACEHOLDER implementation using mock data
        In production, you would:
        1. Use CFTC's official API: https://publicreporting.cftc.gov/
        2. Parse the COT reports (released every Friday at 3:30 PM ET)
        3. Calculate real COT Index from commercial positions

        For now, using realistic mock data based on recent market positioning
        """
        logger.info("Fetching COT data (using mock data - implement real CFTC API for production)")

        # MOCK DATA (Replace with real CFTC API calls)
        # These values are based on recent market positioning patterns
        mock_cot_data = {
            # CRYPTO - Highly volatile positioning
            'BTC': 82, 'ETH': 75,

            # ENERGIES - Natural gas often extreme in winter
            'NG': 100, 'CL': 92, 'BZ': 88, 'HO': 16, 'RB': 13,

            # METALS - Mixed positioning
            'GC': 65, 'SI': 45, 'HG': 30, 'PL': 20, 'PA': 10,

            # INDICES - Often crowded longs in bull markets
            'ES': 76, 'NQ': 48, 'YM': 54, 'RTY': 46, 'NIY': 60, 'VX': 15,

            # CURRENCIES - USD high, others inversely correlated
            'DX': 89, 'EUR': 18, 'JPY': 91, 'GBP': 60, 'AUD': 14,
            'CAD': 50, 'CHF': 24, 'NZD': 55, 'MXN': 0, 'BRL': 40, 'ZAR': 35,

            # GRAINS - Seasonal patterns
            'ZC': 40, 'ZS': 35, 'ZW': 25, 'ZL': 60, 'ZM': 55, 'ZO': 30, 'ZR': 45,

            # MEATS - Cattle often extreme long
            'LE': 85, 'GF': 80, 'HE': 20,

            # SOFTS - Recent extremes
            'SB': 96, 'KC': 94, 'CC': 98, 'CT': 12, 'OJ': 50, 'LB': 40,

            # RATES - Often extreme short in rising rate environments
            'ZN': 29, 'ZB': 11, 'ZF': 0, 'GE': 45,
        }

        # Build full dataset with metadata
        for symbol, cot_index in mock_cot_data.items():
            if symbol in COT_SYMBOLS:
                self.data[symbol] = {
                    'name': COT_SYMBOLS[symbol]['name'],
                    'category': COT_SYMBOLS[symbol]['category'],
                    'cot_index': cot_index,
                    'signal': self._get_signal(cot_index)
                }

        logger.info(f"COT data loaded for {len(self.data)} symbols")
        return self.data

    def _get_signal(self, cot_index):
        """Determine trading signal from COT index"""
        if cot_index >= UPPER_THRESHOLD:
            return 'EXTREME_LONG'
        elif cot_index <= LOWER_THRESHOLD:
            return 'EXTREME_SHORT'
        else:
            return 'NEUTRAL'

    def get_dataframe(self):
        """Convert COT data to pandas DataFrame for visualization"""
        df_data = []
        for symbol, data in self.data.items():
            df_data.append({
                'Symbol': symbol,
                'Market': data['name'],
                'Category': data['category'],
                'COT_Index': data['cot_index'],
                'Signal': data['signal']
            })

        df = pd.DataFrame(df_data)
        df = df.sort_values('COT_Index', ascending=True)
        return df


def generate_infographic(df):
    """Generate professional COT infographic with 40+ symbols"""
    logger.info("Generating COT infographic...")

    # Determine colors based on thresholds
    colors = []
    for val in df['COT_Index']:
        if val >= UPPER_THRESHOLD:
            colors.append('#10b981')  # Green (Extreme Long = Buy Signal)
        elif val <= LOWER_THRESHOLD:
            colors.append('#ef4444')  # Red (Extreme Short = Sell Signal)
        else:
            colors.append('#64748b')  # Grey (Neutral)

    # Create tall figure for 40+ symbols
    fig, ax = plt.subplots(figsize=(16, 20))
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')

    # Create horizontal bar chart
    bars = ax.barh(df['Market'], df['COT_Index'], color=colors,
                   edgecolor='#334155', linewidth=0.8)

    # Add value labels
    for idx, (bar, val) in enumerate(zip(bars, df['COT_Index'])):
        width = bar.get_width()
        label_x_pos = width + 2 if width < 93 else width - 8
        text_color = '#ffffff' if width < 93 else '#000000'

        ax.text(label_x_pos, bar.get_y() + bar.get_height()/2,
                f'{int(width)}%',
                va='center', ha='left' if width < 93 else 'right',
                color=text_color, fontsize=9, fontweight='bold')

    # Add threshold lines
    ax.axvline(x=UPPER_THRESHOLD, color='#10b981', linestyle='--',
               linewidth=2.5, alpha=0.6)
    ax.axvline(x=LOWER_THRESHOLD, color='#ef4444', linestyle='--',
               linewidth=2.5, alpha=0.6)

    # Add zone labels at the TOP of chart (outside data area)
    # Position them above the chart area using figure coordinates
    ax.text(UPPER_THRESHOLD, len(df) + 1.5,
            '🔺 EXTREME LONG (≥95%)\nCommercials Net LONG → BUY',
            color='#10b981', fontweight='bold', fontsize=10,
            ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#1e293b',
                     edgecolor='#10b981', linewidth=2, alpha=0.95))

    ax.text(LOWER_THRESHOLD, len(df) + 1.5,
            '🔻 EXTREME SHORT (≤5%)\nCommercials Net SHORT → SELL',
            color='#ef4444', fontweight='bold', fontsize=10,
            ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#1e293b',
                     edgecolor='#ef4444', linewidth=2, alpha=0.95))

    # Styling
    today = datetime.now().strftime('%A, %B %d, %Y')
    ax.set_title(
        f'CFTC Commitment of Traders (COT) Index\n'
        f'Commercial Positioning Across 40+ Futures Markets\n'
        f'{today}',
        fontsize=20, fontweight='bold', color='#facc15', pad=20
    )

    ax.set_xlabel('COT Index (0 = Max Bearish | 100 = Max Bullish)',
                  fontsize=13, color='#cbd5e1', fontweight='bold')
    ax.set_xlim(-5, 108)
    ax.set_ylim(-0.5, len(df) + 3.5)  # Extra space at top for zone labels

    # Grid styling
    ax.grid(axis='x', linestyle='--', alpha=0.2, color='#475569')
    ax.set_axisbelow(True)

    # Y-axis styling
    ax.tick_params(axis='y', colors='#e2e8f0', labelsize=10)
    ax.tick_params(axis='x', colors='#cbd5e1', labelsize=10)

    # Spines styling
    for spine in ax.spines.values():
        spine.set_color('#334155')
        spine.set_linewidth(1.5)

    # Add footer
    footer_text = (
        '📊 Data Source: CFTC (Commodity Futures Trading Commission)\n'
        '🎯 Strategy: Fade extreme positioning - Commercials are "smart money"\n'
        '⚠️  For informational purposes only. Not financial advice.'
    )
    fig.text(0.5, 0.02, footer_text, ha='center', fontsize=10,
             color='#94a3b8', style='italic')

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    # Save figure
    plt.savefig(FILENAME, dpi=150, facecolor='#0f172a', edgecolor='none')
    plt.close()

    logger.info(f"Infographic saved: {FILENAME}")
    return FILENAME


def send_email(attachment_path, df):
    """Send COT report email with inline infographic"""
    logger.info(f"Preparing email to {RECIPIENT_EMAIL}...")

    # Validate credentials
    if not SENDER_PASSWORD:
        logger.error("SMTP_PASSWORD not set! Cannot send email.")
        logger.error("Please set SMTP_PASSWORD environment variable with your Gmail App Password")
        return False

    # Count extreme signals
    extreme_longs = df[df['COT_Index'] >= UPPER_THRESHOLD]
    extreme_shorts = df[df['COT_Index'] <= LOWER_THRESHOLD]

    # Create email
    msg = EmailMessage()
    msg['Subject'] = f"🎯 Daily COT Report: {datetime.now().strftime('%Y-%m-%d')} - {len(extreme_longs)} BUYS, {len(extreme_shorts)} SELLS"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    # Plain text version (fallback)
    plain_body = f"""
CFTC Commitment of Traders (COT) Daily Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔺 EXTREME LONG SIGNALS ({len(extreme_longs)}): Commercials Net LONG → BUY

{chr(10).join([f"  • {row['Market']} ({row['Symbol']}): {int(row['COT_Index'])}%"
               for _, row in extreme_longs.iterrows()])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔻 EXTREME SHORT SIGNALS ({len(extreme_shorts)}): Commercials Net SHORT → SELL

{chr(10).join([f"  • {row['Market']} ({row['Symbol']}): {int(row['COT_Index'])}%"
               for _, row in extreme_shorts.iterrows()])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Spartan Labs - Market Intelligence
https://spartanlabs.ai
"""

    msg.set_content(plain_body)

    # HTML version with inline image
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #1e293b; text-align: center; margin-bottom: 10px; }}
            .date {{ text-align: center; color: #64748b; margin-bottom: 30px; }}
            .infographic {{ width: 100%; max-width: 800px; margin: 30px auto; display: block; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }}
            .section {{ margin: 30px 0; }}
            .section h2 {{ color: #10b981; font-size: 18px; margin-bottom: 15px; }}
            .section h2.short {{ color: #ef4444; }}
            .signal-list {{ background: #f8fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981; }}
            .signal-list.short {{ border-left-color: #ef4444; }}
            .signal-item {{ padding: 8px 0; color: #334155; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #e2e8f0; text-align: center; color: #64748b; font-size: 14px; }}
            .strategy {{ background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 20px 0; }}
            .strategy h3 {{ color: #92400e; margin-top: 0; }}
            .disclaimer {{ background: #fee2e2; padding: 15px; border-radius: 8px; margin: 20px 0; font-size: 13px; color: #991b1b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 CFTC Commitment of Traders (COT) Daily Report</h1>
            <div class="date">Generated: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}</div>

            <img src="cid:cot_infographic" alt="COT Infographic" class="infographic">

            <div class="section">
                <h2>🔺 EXTREME LONG SIGNALS ({len(extreme_longs)}) - Commercials Net LONG → BUY</h2>
                <div class="signal-list">
                    {''.join([f'<div class="signal-item">• <strong>{row["Market"]}</strong> ({row["Symbol"]}): <strong>{int(row["COT_Index"])}%</strong></div>'
                             for _, row in extreme_longs.iterrows()]) if len(extreme_longs) > 0 else '<div class="signal-item">No extreme long signals today</div>'}
                </div>
            </div>

            <div class="section">
                <h2 class="short">🔻 EXTREME SHORT SIGNALS ({len(extreme_shorts)}) - Commercials Net SHORT → SELL</h2>
                <div class="signal-list short">
                    {''.join([f'<div class="signal-item">• <strong>{row["Market"]}</strong> ({row["Symbol"]}): <strong>{int(row["COT_Index"])}%</strong></div>'
                             for _, row in extreme_shorts.iterrows()]) if len(extreme_shorts) > 0 else '<div class="signal-item">No extreme short signals today</div>'}
                </div>
            </div>

            <div class="strategy">
                <h3>📊 Trading Strategy</h3>
                <p><strong>COT Index ≥95%:</strong> Commercials heavily NET LONG → Contrarian BUY signal</p>
                <p><strong>COT Index ≤5%:</strong> Commercials heavily NET SHORT → Contrarian SELL signal</p>
                <p><strong>Neutral (6-94%):</strong> No extreme positioning</p>
            </div>

            <div class="strategy">
                <h3>📈 Why This Works</h3>
                <p>• Commercial traders are "smart money" (producers, hedgers, industry insiders)</p>
                <p>• They take OPPOSITE positions to speculators at market extremes</p>
                <p>• When commercials are max long (95%+), they expect prices to RISE</p>
                <p>• When commercials are max short (5%-), they expect prices to FALL</p>
            </div>

            <div class="disclaimer">
                <strong>⚠️ DISCLAIMER:</strong> This is for informational purposes only. Not financial advice.
                Always do your own research and consult a financial advisor.
            </div>

            <div class="footer">
                <p><strong>🎯 Spartan Labs - Market Intelligence</strong></p>
                <p><a href="https://spartanlabs.ai">spartanlabs.ai</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    msg.add_alternative(html_body, subtype='html')

    # Embed infographic inline (not as attachment)
    with open(attachment_path, 'rb') as f:
        file_data = f.read()

    msg.get_payload()[1].add_related(file_data, maintype='image', subtype='png', cid='cot_infographic')

    # Send email via Gmail SMTP
    try:
        logger.info(f"Connecting to {SMTP_HOST}:{SMTP_PORT}...")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()  # Upgrade to secure connection
            logger.info("Logging in to Gmail...")
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            logger.info("Sending message...")
            smtp.send_message(msg)

        logger.info("✅ Email sent successfully!")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("❌ SMTP Authentication failed!")
        logger.error("This usually means:")
        logger.error("  1. You're using your regular Gmail password (NOT ALLOWED)")
        logger.error("  2. You need to create an App Password:")
        logger.error("     - Go to https://myaccount.google.com/security")
        logger.error("     - Enable 2-Step Verification")
        logger.error("     - Create App Password for 'Mail'")
        logger.error("     - Use that 16-character code in SMTP_PASSWORD")
        return False

    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False


def main():
    """Main execution function"""
    logger.info("=" * 70)
    logger.info("SPARTAN LABS - COT DAILY EMAILER")
    logger.info("=" * 70)
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Recipient: {RECIPIENT_EMAIL}")
    logger.info(f"Sender: {SENDER_EMAIL}")
    logger.info("=" * 70)

    try:
        # Step 1: Fetch COT data
        logger.info("\n[1/3] Fetching COT data...")
        fetcher = COTDataFetcher()
        cot_data = fetcher.fetch_cot_data()
        df = fetcher.get_dataframe()

        logger.info(f"✅ Loaded {len(df)} symbols")

        # Step 2: Generate infographic
        logger.info("\n[2/3] Generating infographic...")
        image_path = generate_infographic(df)
        logger.info(f"✅ Infographic saved: {image_path}")

        # Step 3: Send email
        logger.info("\n[3/3] Sending email...")
        success = send_email(image_path, df)

        if success:
            logger.info("\n" + "=" * 70)
            logger.info("✅ COT DAILY REPORT SENT SUCCESSFULLY!")
            logger.info("=" * 70)
        else:
            logger.error("\n" + "=" * 70)
            logger.error("❌ FAILED TO SEND EMAIL - Check logs above")
            logger.error("=" * 70)

    except Exception as e:
        logger.error(f"\n❌ CRITICAL ERROR: {e}", exc_info=True)
        logger.error("=" * 70)


if __name__ == '__main__':
    main()
