# terabox.py

import re
import requests
from urllib.parse import parse_qs, urlparse
from typing import Optional, Union
from tools import get_formatted_size  # Optional, used elsewhere

# List of supported domain patterns
SUPPORTED_DOMAINS = [
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

def check_url_patterns(url: str) -> bool:
    """Check if the URL matches any of the supported domains."""
    return any(re.search(pattern, url) for pattern in SUPPORTED_DOMAINS)


def get_urls_from_string(string: str) -> Optional[str]:
    """Extract the first supported URL from a string."""
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    supported = [url for url in urls if check_url_patterns(url)]
    return supported[0] if supported else None


def extract_surl_from_url(url: str) -> Union[str, bool]:
    """Extract the 'surl' parameter from the URL query."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", [])
    return surl[0] if surl else False


def get_data(url: str) -> Optional[dict]:
    """Call the TeraBox API to fetch file metadata and download links."""
    api_url = "https://terabox-downloader-direct-download-link-generator2.p.rapidapi.com/url"
    headers = {
        "x-rapidapi-host": "terabox-downloader-direct-download-link-generator2.p.rapidapi.com",
        "x-rapidapi-key": "e001039e2emshf6e499c6afe75f3p1723fdjsn1c9cc179bde0",  # ⚠️ Consider storing in env
    }
    try:
        response = requests.get(api_url, headers=headers, params={"url": url}, timeout=15)

        if response.status_code != 200:
            print(f"❌ API error: {response.status_code} - {response.text}")
            return None

        data = response.json()

        # If response is a list of dicts, extract the first dict
        if isinstance(data, list) and data and isinstance(data[0], dict):
            data = data[0]

        if not isinstance(data, dict) or "file_name" not in data:
            print(f"⚠️ Invalid API response: {data}")
            return None

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
        return None
