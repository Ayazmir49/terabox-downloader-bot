import re
from urllib.parse import parse_qs, urlparse

import requests

from tools import get_formatted_size


def check_url_patterns(url):
    """
    Validates if a URL matches known TeraBox mirror domains.
    """
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

    for pattern in patterns:
        if re.search(pattern, url):
            return True
    return False


def get_urls_from_string(string: str) -> list[str]:
    """
    Extracts valid TeraBox URLs from a given string.
    """
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    urls = [url for url in urls if check_url_patterns(url)]
    if not urls:
        return []
    return urls[0]


def extract_surl_from_url(url: str) -> str | None:
    """
    Extracts the `surl` parameter from a TeraBox URL.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", [])
    if surl:
        return surl[0]
    else:
        return False


def get_data(url: str):
    """
    Calls the RapidAPI endpoint to fetch TeraBox file info and download URL.
    """
    api_url = "https://terabox-direct-download.p.rapidapi.com/"
    headers = {
        "X-RapidAPI-Key": "e001039e2emshf6e499c6afe75f3p1723fdjsn1c9cc179bde0",  # your API key
        "X-RapidAPI-Host": "terabox-direct-download.p.rapidapi.com"
    }
    params = {"link": url}

    try:
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code != 200:
            return False

        data = response.json()
    except Exception:
        return False

    file_url = data.get("url")
    file_name = data.get("fileName")
    file_size_bytes = data.get("fileSizeBytes")
    thumb = data.get("thumb")

    if not file_url or not file_name:
        return False

    return {
        "file_name": file_name,
        "link": file_url,
        "direct_link": file_url,
        "thumb": thumb,
        "size": get_formatted_size(int(file_size_bytes)) if file_size_bytes else None,
        "sizebytes": int(file_size_bytes) if file_size_bytes else None,
    }
