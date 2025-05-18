import re
import requests
from urllib.parse import parse_qs, urlparse
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
    Calls the working RapidAPI endpoint to fetch TeraBox file info.
    """
    try:
        # Normalize domain to avoid issues
        parsed_url = urlparse(url)
        clean_url = url.replace(parsed_url.netloc, "terabox.com")

        headers = {
            "X-RapidAPI-Key": "e001039e2emshf6e499c6afe75f3p1723fdjsn1c9cc179bde0",  # Replace with your key
            "X-RapidAPI-Host": "terabox-api1.p.rapidapi.com",
        }

        response = requests.get(
            "https://terabox-api1.p.rapidapi.com/api/v1/terabox-downloader",
            headers=headers,
            params={"url": clean_url},
            timeout=15
        )

        if response.status_code != 200:
            print(f"API error: {response.status_code}")
            return False

        json_data = response.json()
        if not json_data or not isinstance(json_data, list):
            return False

        result = json_data[0]

        return {
            "file_name": result.get("file_name"),
            "link": result.get("link"),
            "direct_link": result.get("direct_link"),
            "thumb": result.get("thumb"),
            "size": result.get("size"),
            "sizebytes": int(result.get("sizebytes", 0)),
        }

    except Exception as e:
        print(f"Error in get_data: {e}")
        return False
