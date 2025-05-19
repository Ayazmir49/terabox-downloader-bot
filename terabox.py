# terabox.py

import re
import requests
from urllib.parse import parse_qs, urlparse
from tools import get_formatted_size  # Optional

# Check supported domains
def check_url_patterns(url):
    patterns = [
        r"ww\.mirrobox\.com",
        r"www\.nephobox\.com",
        r"freeterabox\.com",
        r"www\.freeterabox\.com",
        r"1024tera\.com",
        r"4funbox\.co",
        r"www\.4funbox\.com",
        r"mirrobox\.com",
        r"nephobox\.com",
        r"terabox\.app",
        r"terabox\.com",
        r"www\.terabox\.ap",
        r"www\.terabox\.com",
        r"www\.1024tera\.co",
        r"www\.momerybox\.com",
        r"teraboxapp\.com",
        r"momerybox\.com",
        r"tibibox\.com",
        r"www\.tibibox\.com",
        r"www\.teraboxapp\.com",
    ]
    return any(re.search(pattern, url) for pattern in patterns)

# Extract URL
def get_urls_from_string(string: str) -> str:
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    urls = [url for url in urls if check_url_patterns(url)]
    return urls[0] if urls else ""

# Extract surl param
def extract_surl_from_url(url: str) -> str | None:
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", [])
    return surl[0] if surl else False

# Get download info from API
def get_data(url: str):
    try:
        parsed_url = urlparse(url)
        clean_url = url.replace(parsed_url.netloc, "terabox.com")

        headers = {
            "X-RapidAPI-Key": "e001039e2emshf6e499c6afe75f3p1723fdjsn1c9cc179bde0",  # Replace with your own key
            "X-RapidAPI-Host": "terabox-api1.p.rapidapi.com",
        }

        response = requests.get(
            "https://terabox-api1.p.rapidapi.com/api/v1/terabox-downloader",
            headers=headers,
            params={"url": clean_url},
            timeout=15
        )

        if response.status_code != 200:
            print(f"❌ API error: {response.status_code} - {response.text}")
            return False

        json_data = response.json()

        # Handle possible error response
        if isinstance(json_data, dict) and json_data.get("status") == "error":
            print(f"❌ API error response: {json_data.get('message')}")
            return False

        # Determine structure
        if isinstance(json_data, list) and json_data:
            result = json_data[0]
        elif isinstance(json_data, dict) and "file_name" in json_data:
            result = json_data
        else:
            print("⚠️ Unexpected JSON format:", json_data)
            return False

        return {
            "file_name": result.get("file_name"),
            "link": result.get("link") or result.get("url"),
            "direct_link": result.get("direct_link"),
            "thumb": result.get("thumb"),
            "size": result.get("size"),
            "sizebytes": int(result.get("sizebytes", 0)),
        }

    except Exception as e:
        print(f"❌ Exception in get_data: {e}")
        return False
