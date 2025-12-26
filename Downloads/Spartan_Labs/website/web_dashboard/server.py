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

# Install deps if missing
WINDOWS_LIBS_AVAILABLE = False
try:
    import cv2
    import numpy as np
    import pyautogui
    import win32gui
    import win32ui
    import win32con
    WINDOWS_LIBS_AVAILABLE = True
except ImportError:
    print("CRITICAL: Windows dependencies (pywin32, opencv, pyautogui) not found. Real-time data capture disabled.")

app = Flask(__name__, template_folder='templates')
CORS(app)

# ============ CONFIGURATION ============ 
LIVE_UPDATE_INTERVAL = 300.0   # Update visible charts every 1s
BG_UPDATE_INTERVAL = 300.0    # Update background charts every 10s (Reduces flicker)
DEEP_SCAN_INTERVAL = 300.0    # Scan for new windows every 60s

class Agent:
    def __init__(self, key, symbol, timeframe, source="LIVE"):
        self.key = key
        self.symbol = symbol
        self.timeframe = timeframe
        self.pattern = "Scanning..."
        self.confidence = 0.0
        self.trend = "WAIT"
        self.last_update = 0 # Initialize to 0 to force first update
        self.history = deque(maxlen=20)
        self.source = source 

    def update(self, bull_score, source="LIVE"):
        self.source = source
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

        bulls = sum(1 for x in self.history if "BULL" in x)
        bears = sum(1 for x in self.history if "BEAR" in x)
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
        
        # Try standard capture first (less flicker potential)
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
        if result == 0: 
            # Fallback to full content (more likely to flicker but catches chrome-based UIs)
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
        # --- THROTTLE LOGIC ---
        # Check if we should skip this update to reduce load
        if k in state['agents']:
            last_up = state['agents'][k].last_update
            elapsed = time.time() - last_up
            if c['mode'] == 'BG' and elapsed < BG_UPDATE_INTERVAL: return # Skip BG
            if c['mode'] == 'LIVE' and elapsed < LIVE_UPDATE_INTERVAL: return # Skip LIVE
        
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
    last_scan = 0
    logged_error = False
    
    while state['running']:
        if not WINDOWS_LIBS_AVAILABLE:
            if not logged_error:
                log("CRITICAL: Windows libraries missing. Cannot capture real-time data.")
                log("Please run on Windows with pywin32 installed.")
                logged_error = True
            time.sleep(5.0)
            continue

        now = time.time()
        # Deep scan less frequently
        if now - last_scan > DEEP_SCAN_INTERVAL:
            log("Scanning windows...")
            new = scan_windows_deep()
            if new: 
                state['cached_charts'] = new
                state['total_charts'] = len(new)
                log(f"Found {len(new)} unique charts.")
            last_scan = now
        
        if state['cached_charts']:
            # Lower worker count to prevent thread storming during PrintWindow calls
            workers = min(6, max(2, len(state['cached_charts'])//4))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for c in state['cached_charts']: pool.submit(update_chart, c)
        
        # Main loop can run faster, individual chart throttling is handled in update_chart
        time.sleep(0.5)
