import requests
import json

BASE_URL = 'http://localhost:8888'

def test_symbol_endpoint(symbol):
    url = f"{BASE_URL}/api/market/symbol/{symbol}"
    print(f"Testing: {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: {symbol}")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ FAILED: {symbol} - {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_symbol_endpoint("AAPL")
    test_symbol_endpoint("SPY")
    test_symbol_endpoint("INVALID_SYMBOL")
