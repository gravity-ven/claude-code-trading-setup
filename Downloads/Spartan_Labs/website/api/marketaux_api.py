import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_news():
    """
    Fetches news from the Marketaux API.
    """
    api_key = os.getenv("MARKETAUX_API_KEY")
    if not api_key:
        return {"error": "Marketaux API key not found. Please add it to your .env file."}

    # API endpoint for general market news, you can customize this
    url = f"https://api.marketaux.com/v1/news/all?symbols=TSLA,AMZN,MSFT&filter_entities=true&language=en&api_token={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch news from Marketaux: {e}"}
