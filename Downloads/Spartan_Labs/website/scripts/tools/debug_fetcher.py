import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

try:
    from data_fetcher_fallback import fetch_stock_price
    print("Import successful")
    
    print("Fetching AAPL...")
    result = fetch_stock_price('AAPL', 5)
    print("Result:", result)
    
except Exception as e:
    import traceback
    traceback.print_exc()
