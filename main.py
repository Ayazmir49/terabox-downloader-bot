import asyncio
import logging
import time
from threading import Thread

import humanreadable as hr
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from telethon.tl.custom.button import Button

from config import ADMINS, API_HASH, API_ID, BOT_TOKEN
from redis_db import db
from send_media import send_media, VideoSender  # updated import
from terabox import get_data
from tools import extract_code_from_url, get_urls_from_string
from keep_alive import keep_alive

# Start web server for uptime
keep_alive()

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("TeraBot")

# Initialize Telegram bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    welcome_message = (
        "Hello! 👋\n"
        "I’m your Teracinee Video Downloader Bot — here to quickly fetch download links from Terabox for you.\n\n"
        "Simply send me a Terabox video link, and I’ll provide the direct download so you can enjoy your videos hassle-free.\n\n"
        "🚀 Fast, free, and accessible to everyone!\n\n"
        "Stay tuned — the Teracinee Android app is coming soon, featuring:\n"
        "- Video streaming & downloading\n"
        "- Rewarded ads for free users\n"
        "- Premium plans with no ads & unlimited downloads\n"
        "- Built on modern, user-friendly design with Firebase backend\n\n"
        "Try me out by sharing your Terabox link!"
    )

    buttons = [
        [Button.url("📢 Channel", "https://t.me/+LsECfdEyaVU4OGY8"),
         Button.url("💬 Group", "https://t.me/+EtHQEItJyzE4YzU0")]
    ]

    await event.reply(welcome_message, buttons=buttons, parse_mode="md")


@bot.on(
    events.NewMessage(
        incoming=True,
        outgoing=False,
        func=lambda message: message.text and get_urls_from_string(message.text) and message.is_private,
    )
)
async def get_message(m: Message):
    asyncio.create_task(handle_message(m))


async def handle_message(m: Message):
    url = get_urls_from_string(m.text)
    if not url:
        return await m.reply("❌ Please enter a valid TeraBox URL.")

    hm = await m.reply("📥 Fetching media, please wait...")

    # Anti-spam: 60s per user
    if (spam := db.get(str(m.sender_id))) and m.sender_id not in ADMINS:
        ttl = db.ttl(str(m.sender_id))
        wait = hr.Time(str(ttl), default_unit=hr.Time.Unit.SECOND)
        return await hm.edit(f"⏳ You're spamming. Please wait {wait.to_humanreadable()}.", parse_mode="markdown")

    shorturl = extract_code_from_url(url)
    if not shorturl:
        return await hm.edit("❌ Invalid TeraBox URL provided.")

    try:
        media = await send_media(shorturl)
        if media:
            title = media.get("title", "📹 Video")
            thumbnail_url = media.get("thumbnail_url")
            download_url = media.get("download_link")
            watch_url = media.get("watch_link")

            buttons = [
                [Button.url("▶️ Watch Video", watch_url)],
                [Button.url("⬇️ Download Video", download_url)],
            ]

            await bot.send_file(
                m.chat_id,
                file=thumbnail_url,
                caption=f"**{title}**\n\nSelect an option below 👇",
                buttons=buttons,
                parse_mode="md"
            )
            return await hm.delete()

    except Exception as e:
        log.warning(f"[Media Preview Fallback] {e}")

    # Fallback to legacy sender
    try:
        data = await get_data(url)
    except Exception as e:
        log.error(f"API call failed: {e}")
        return await hm.edit("⚠️ Error accessing TeraBox API. Please try again later.")

    if not data:
        return await hm.edit("⚠️ Could not fetch the file. Invalid or expired link?")

    db.set(str(m.sender_id), time.monotonic(), ex=60)

    if int(data["sizebytes"]) > 1_073_741_824 and m.sender_id not in ADMINS:
        return await hm.edit(
            f"❌ File too large. Limit is 1GB.\n"
            f"File size: {data['size']}\n\nTry direct link:\n{data.get('direct_link') or data.get('link', '')}",
            parse_mode="markdown"
        )

    # Send the video
    sender = VideoSender(client=bot, data=data, message=m, edit_message=hm, url=url)
    asyncio.create_task(sender.send_video())


# Run Flask + Telegram bot in parallel
def start_bot_and_flask():
    def run_flask():
        from keep_alive import app
        app.run(host="0.0.0.0", port=8080)

    Thread(target=run_flask).start()
    bot.run_until_disconnected()


if __name__ == "__main__":
    start_bot_and_flask()
