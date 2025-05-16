# api_integration.py
import requests

def get_data(url):
    api_url = "YOUR_API_ENDPOINT_HERE"  # Terabox API endpoint
    headers = {
        'Authorization': 'Bearer YOUR_API_KEY'  # Use your API key if required
    }

    response = requests.get(api_url, params={"url": url}, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None
