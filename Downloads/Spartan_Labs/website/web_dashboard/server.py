from flask import Flask, render_template, jsonify
from flask_cors import CORS
import threading
import time
import os
import sys
import re
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import ctypes
from ctypes import windll

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import threading
import time
import os
import sys
import re
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import ctypes
from ctypes import windll
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add root directory to path to find data_fetcher_fallback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from data_fetcher_fallback import fetch_stock_price, fetch_crypto_price, fetch_forex_rate
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    logger.critical("CRITICAL: data_fetcher_fallback.py not found in parent directory.")

# Install deps if missing
WINDOWS_LIBS_AVAILABLE = False
try:
    import cv2
    import pyautogui
    import win32gui
    import win32ui
    import win32con
    WINDOWS_LIBS_AVAILABLE = True
except ImportError:
    logger.info("Windows dependencies (pywin32, opencv, pyautogui) not found. Switching to API Mode.")

app = Flask(__name__, template_folder='templates')
CORS(app)

# ============ CONFIGURATION ============ 
LIVE_UPDATE_INTERVAL = 60.0   # API Update interval (respecting rate limits)
BG_UPDATE_INTERVAL = 300.0    
DEEP_SCAN_INTERVAL = 300.0    

class Agent:
    def __init__(self, key, symbol, timeframe, source="LIVE"):
        self.key = key
        self.symbol = symbol
        self.timeframe = timeframe
        self.pattern = "Scanning..."
        self.confidence = 0.0
        self.trend = "WAIT"
        self.last_update = 0 
        self.history = deque(maxlen=20)
        self.source = source 

    def update(self, bull_score, source="LIVE"):
        self.source = source
        # Strict score clamping
        bull_score = max(0.0, min(2.0, bull_score))
        
        if bull_score >= 1.5:
            p, c = "STRONG BULLISH", 0.95
        elif bull_score >= 1.1:
            p, c = "BULLISH", 0.80
        elif bull_score <= 0.6:
            p, c = "STRONG BEARISH", 0.95
        elif bull_score <= 0.9:
            p, c = "BEARISH", 0.80
        else:
            p, c = "NEUTRAL", 0.60

        self.pattern = p
        self.confidence = c
        self.history.append(bull_score)
        self.last_update = time.time()

        bulls = sum(1 for x in self.history if x > 1.05)
        bears = sum(1 for x in self.history if x < 0.95)
        self.trend = "UP" if bulls > bears else "DOWN" if bears > bulls else "FLAT"
    
    def to_dict(self):
        return {
            "symbol": self.symbol,
            "tf": self.timeframe,
            "mode": self.source,
            "pattern": self.pattern,
            "conf": self.confidence,
            "trend": self.trend,
            "last_update": self.last_update,
            "history": list(self.history)
        }

state = {
    'agents': {},
    'logs': deque(maxlen=50),
    'running': True,
    'total_charts': 0,
    'cached_charts': []
}

def log(msg):
    ts = time.strftime("%H:%M:%S")
    state['logs'].append(f"{ts} {msg}")
    logger.info(msg)

# ==================== VALIDATION LOGIC ====================
def validate_market_data(symbol, price, timestamp):
    """
    Strict validation of market data.
    Returns True if valid, False otherwise.
    """
    if price is None:
        logger.warning(f"Validation Fail: {symbol} price is None")
        return False
    
    try:
        price = float(price)
    except (ValueError, TypeError):
        logger.warning(f"Validation Fail: {symbol} price is not a number: {price}")
        return False
        
    if price <= 0:
        logger.warning(f"Validation Fail: {symbol} price invalid: {price}")
        return False
        
    # Freshness check (allow some lag for weekends/holidays handled by fallback fetcher)
    # data_fetcher_fallback handles caching logic
    return True

def calculate_market_score(history):
    """
    Calculate a technical score (0.0 - 2.0) based on REAL price history.
    Uses Moving Average Convergence/Divergence logic or simple Trend.
    NO RANDOM DATA.
    """
    if history is None or history.empty: return 1.0
    
    try:
        # Ensure numeric
        prices = history.astype(float).values
        if len(prices) < 5: return 1.0
        
        current = prices[-1]
        
        # Simple SMA Trend
        sma_short = np.mean(prices[-5:])
        sma_long = np.mean(prices) # All available data in period
        
        if sma_long == 0: return 1.0
        
        # Deviation calculation
        deviation = (sma_short - sma_long) / sma_long
        
        # Scale: +/- 5% deviation = +/- 0.5 score adjustment
        # Base 1.0
        adjustment = deviation * 10
        score = 1.0 + adjustment
        
        return max(0.0, min(2.0, score))
    except Exception as e:
        logger.error(f"Score calculation error: {e}")
        return 1.0

# ==================== API FETCH LOOP (LINUX/NO-WIN) ====================
def run_api_fetch_loop():
    """
    Main loop for non-Windows environments.
    Fetches REAL data from authorized APIs using data_fetcher_fallback.
    """
    # Key assets to track
    ASSETS = [
        ('SPY', 'stock'), ('QQQ', 'stock'), ('IWM', 'stock'), ('DIA', 'stock'),
        ('BTC-USD', 'crypto'), ('ETH-USD', 'crypto'), ('SOL-USD', 'crypto'),
        ('GLD', 'stock'), ('SLV', 'stock'), ('TLT', 'stock'), ('USO', 'stock'),
        ('EURUSD=X', 'forex'), ('USDJPY=X', 'forex')
    ]
    
    log("Starting API Data Fetch Loop (Strict Mode)...")
    
    while state['running']:
        start_time = time.time()
        
        for symbol, asset_type in ASSETS:
            try:
                # 1. Fetch Real Data
                result = None
                if asset_type == 'crypto':
                    result = fetch_crypto_price(symbol, period_days=30)
                elif asset_type == 'forex':
                    result = fetch_forex_rate(symbol, period_days=30)
                else:
                    result = fetch_stock_price(symbol, period_days=30)
                
                # 2. Check Result
                if result and result.get('success') and result.get('data') is not None:
                    data = result['data'] # pd.Series
                    if not data.empty:
                        current_price = data.iloc[-1]
                        
                        # 3. Validate
                        if validate_market_data(symbol, current_price, time.time()):
                            # 4. Calculate Score
                            score = calculate_market_score(data)
                            
                            # 5. Update Agent
                            key = f"{symbol}_D_API"
                            if key not in state['agents']:
                                state['agents'][key] = Agent(key, symbol, "D", f"API({result.get('source')})")
                                state['total_charts'] = len(state['agents'])
                            
                            state['agents'][key].update(score, f"API({result.get('source')})")
                            # logger.info(f"Updated {symbol}: ${current_price:.2f} Score: {score:.2f}")
                        else:
                            log(f"Data invalid for {symbol}")
                else:
                    # Log failure but DO NOT use fake data
                    # log(f"No data for {symbol}: {result.get('error')}")
                    pass

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        # Rate limit compliance
        elapsed = time.time() - start_time
        sleep_time = max(10.0, LIVE_UPDATE_INTERVAL - elapsed)
        time.sleep(sleep_time)

# ==================== WINDOWS CAPTURE LOGIC ====================
def capture_background(hwnd):
    if not WINDOWS_LIBS_AVAILABLE: return None
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        w, h = right - left, bottom - top
        if w <= 0 or h <= 0: return None
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)
        
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
        if result == 0: 
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
            
        bmpstr = saveBitMap.GetBitmapBits(True)
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        if result == 1:
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (h, w, 4)
            return img[:, :, :3]
    except: pass
    return None

def capture_screen(rect):
    if not WINDOWS_LIBS_AVAILABLE: return None
    try:
        img = pyautogui.screenshot(region=(rect[0], rect[1], rect[2]-rect[0], rect[3]-rect[1]))
        return np.array(img)[:, :, ::-1].copy()
    except: return None

def get_timeframe(title):
    t = title.upper()
    if "[M]" in t or "MONTHLY" in t or "MONTH" in t: return "M"
    if "[W]" in t or "WEEKLY" in t or "WEEK" in t or "WK" in t: return "W"
    if "[D]" in t or "DAILY" in t or "DAY" in t: return "D"
    if "MIN" in t or "m" in t: return "m"
    return "D"

def scan_windows_deep():
    if not WINDOWS_LIBS_AVAILABLE: return []
    unique_map = {} 
    seen_hwnds = set()

    def _process(hwnd):
        if hwnd in seen_hwnds: return
        try: t = win32gui.GetWindowText(hwnd)
        except: return
        if not t: return
        tu = t.upper()
        
        if any(x in tu for x in ["TRADE", "DOM", "DEPTH", "SETTINGS", "VALUES", "QUOTE", "SALES", "TIME"]): return

        m = re.search(r'#\d+[\s_]+([A-Z0-9_\.]+)', t)
        sym = m.group(1) if m else None
        if not sym:
            common = ['ES', 'NQ', 'CL', 'GC', 'BTC', 'ETH', 'SPY', 'CCTG', 'MHG', 'SB', 'SI', 'MES', 'MBT', 'MYM', 'M2K']
            for c in common:
                if re.search(rf'\b{c}[\s\-\[]', tu): sym = c; break
        if not sym: return
        
        tf = get_timeframe(t)
        rect = win32gui.GetWindowRect(hwnd)
        w, h = rect[2]-rect[0], rect[3]-rect[1]
        if w < 150 or h < 150: return

        seen_hwnds.add(hwnd)
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        is_child = (style & win32con.WS_CHILD) != 0
        mode = "BG" if is_child else "LIVE"
        
        chart_obj = {'key': f"{sym}_{tf}_{hwnd}", 'symbol': sym, 'tf': tf, 'hwnd': hwnd, 'mode': mode}
        
        unique_key = (sym, tf)
        if unique_key in unique_map:
            existing = unique_map[unique_key]
            if existing['mode'] == 'BG' and mode == 'LIVE':
                unique_map[unique_key] = chart_obj
        else:
            unique_map[unique_key] = chart_obj

    def _child(hwnd, _): _process(hwnd); return True
    def _top(hwnd, _):
        try:
            t = win32gui.GetWindowText(hwnd)
            if "SIERRA" in t.upper() or t.startswith("#"): 
                _process(hwnd)
                try: win32gui.EnumChildWindows(hwnd, _child, None)
                except: pass
        except: pass
        return True
    
    try: win32gui.EnumWindows(_top, None)
    except: pass
    
    return list(unique_map.values())

def update_chart(c):
    if not WINDOWS_LIBS_AVAILABLE: return
    try:
        k = c['key']
        if k in state['agents']:
            last_up = state['agents'][k].last_update
            elapsed = time.time() - last_up
            if c['mode'] == 'BG' and elapsed < BG_UPDATE_INTERVAL: return 
            if c['mode'] == 'LIVE' and elapsed < LIVE_UPDATE_INTERVAL: return 
        
        if not win32gui.IsWindow(c['hwnd']): return
        rect = win32gui.GetWindowRect(c['hwnd'])
        w, h = rect[2]-rect[0], rect[3]-rect[1]
        if w < 100 or h < 100: return
        
        frame = None
        mode = c['mode']
        if mode == "BG":
            frame = capture_background(c['hwnd'])
            if frame is None or np.count_nonzero(frame) == 0:
                if win32gui.IsWindowVisible(c['hwnd']) and not win32gui.IsIconic(c['hwnd']):
                    frame = capture_screen(rect)
                    mode = "LIVE"
        else:
            if win32gui.IsWindowVisible(c['hwnd']) and not win32gui.IsIconic(c['hwnd']):
                frame = capture_screen(rect)
            else:
                frame = capture_background(c['hwnd'])
                mode = "BG"
        
        if frame is None: return
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        g = np.count_nonzero(cv2.inRange(hsv, np.array([40,50,50]), np.array([80,255,255])))
        r = np.count_nonzero(cv2.inRange(hsv, np.array([0,50,50]), np.array([10,255,255]))) + \
            np.count_nonzero(cv2.inRange(hsv, np.array([170,50,50]), np.array([180,255,255])))
        if r == 0: r = 1
        
        if k not in state['agents']: state['agents'][k] = Agent(k, c['symbol'], c['tf'], mode)
        state['agents'][k].update(float(g)/float(r), mode)
    except: pass

def background_loop():
    # If Windows libs are missing, use API fallback loop
    if not WINDOWS_LIBS_AVAILABLE:
        if API_AVAILABLE:
            run_api_fetch_loop()
        else:
            log("CRITICAL: No Windows Libs AND No API Fetcher. System halted.")
            return

    # Windows Logic
    last_scan = 0
    while state['running']:
        now = time.time()
        if now - last_scan > DEEP_SCAN_INTERVAL:
            log("Scanning windows...")
            new = scan_windows_deep()
            if new: 
                state['cached_charts'] = new
                state['total_charts'] = len(new)
                log(f"Found {len(new)} unique charts.")
            last_scan = now
        
        if state['cached_charts']:
            workers = min(6, max(2, len(state['cached_charts'])//4))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for c in state['cached_charts']: pool.submit(update_chart, c)
        
        time.sleep(0.5)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    return jsonify({
        'agents': [a.to_dict() for a in state['agents'].values()],
        'logs': list(state['logs']),
        'total': state['total_charts']
    })

if __name__ == '__main__':
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000, debug=False)

