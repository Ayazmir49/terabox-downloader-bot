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
        api_url = "https://terabox-downloader-direct-download-link-generator2.p.rapidapi.com/url"
        headers = {
            "x-rapidapi-host": "terabox-downloader-direct-download-link-generator2.p.rapidapi.com",
            "x-rapidapi-key": "e001039e2emshf6e499c6afe75f3p1723fdjsn1c9cc179bde0",
        }
        params = {"url": url}

        response = requests.get(api_url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            print(f"❌ API error: {response.status_code} - {response.text}")
            return False

        data = response.json()

        # Handle case where API returns a list with a dict inside
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            data = data[0]

        if not data or "file_name" not in data:
            print(f"⚠️ Unexpected API response: {data}")
            return False

        return {
            "file_name": data.get("file_name"),
            "link": data.get("link"),
            "direct_link": data.get("direct_link"),
            "thumb": data.get("thumb"),
            "size": data.get("size"),
            "sizebytes": int(data.get("sizebytes", 0)),
        }

    except Exception as e:
        print(f"❌ Exception in get_data: {e}")
        return False
