import os
import re
import traceback
import uuid
from contextlib import suppress
from io import BytesIO
from urllib.parse import parse_qs, urlparse

import requests
from PIL import Image
from telethon import TelegramClient

from config import BOT_USERNAME, SHORTENER_API
from redis_db import db


def check_url_patterns(url: str) -> bool:
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


def extract_code_from_url(url: str) -> str | None:
    pattern1 = r"/s/(\w+)"
    pattern2 = r"surl=(\w+)"

    for pattern in (pattern1, pattern2):
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_urls_from_string(string: str) -> str | None:
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    urls = [url for url in urls if check_url_patterns(url)]
    return urls[0] if urls else None


def extract_surl_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", [])
    return surl[0] if surl else False


def get_formatted_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        size = size_bytes / (1024 * 1024)
        unit = "MB"
    elif size_bytes >= 1024:
        size = size_bytes / 1024
        unit = "KB"
    else:
        size = size_bytes
        unit = "b"
    return f"{size:.2f} {unit}"


def convert_seconds(seconds: int) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining = seconds % 60

    if hours > 0:
        return f"{hours}h:{minutes}m:{remaining}s"
    elif minutes > 0:
        return f"{minutes}m:{remaining}s"
    else:
        return f"{remaining}s"


async def is_user_on_chat(bot: TelegramClient, chat_id: int, user_id: int) -> bool:
    try:
        check = await bot.get_permissions(chat_id, user_id)
        return check
    except Exception:
        return False


async def download_file(url: str, filename: str, callback=None) -> str | bool:
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with suppress(requests.exceptions.ChunkedEncodingError):
            with open(filename, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
                    if callback:
                        downloaded_size = file.tell()
                        total_size = int(response.headers.get("content-length", 0))
                        await callback(downloaded_size, total_size, "Downloading")
        return filename
    except Exception as e:
        traceback.print_exc()
        print(f"Error downloading file: {e}")
        raise Exception(e)


def save_image_from_bytesio(image_bytesio, filename):
    try:
        image_bytesio.seek(0)
        image = Image.open(image_bytesio)
        image.save(filename)
        image.close()
        return filename
    except Exception as e:
        print(f"Error saving image: {e}")
        return False


def download_image_to_bytesio(url: str, filename: str) -> BytesIO | None:
    try:
        response = requests.get(url)
        content = BytesIO()
        content.name = filename
        if response.status_code == 200:
            for chunk in response.iter_content(chunk_size=1024):
                content.write(chunk)
        else:
            return None
        content.seek(0)
        return content
    except Exception:
        return None


def remove_all_videos():
    video_extensions = [".mp4", ".mkv", ".webm"]
    current_directory = os.getcwd()

    try:
        for file_name in os.listdir(current_directory):
            if any(file_name.lower().endswith(ext) for ext in video_extensions):
                os.remove(os.path.join(current_directory, file_name))
    except Exception as e:
        print(f"Error: {e}")


def generate_shortenedUrl(sender_id: int) -> str | None:
    try:
        uid = str(uuid.uuid4())
        long_url = f"https://t.me/{BOT_USERNAME}?start=token_{uid}"

        response = requests.get(SHORTENER_API, params={"url": long_url})
        response.raise_for_status()

        short_url = response.text.strip()
        if "http" in short_url:
            db.set(f"token_{uid}", f"{sender_id}|{short_url}", ex=21600)
            return short_url
        return None
    except Exception as e:
        print(f"Error shortening URL: {e}")
        return None
