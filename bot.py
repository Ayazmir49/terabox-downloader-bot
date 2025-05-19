# bot.py

import asyncio
import logging
import time
from threading import Thread

import humanreadable as hr
from telethon.sync import TelegramClient, events
from telethon.tl.custom.message import Message

from config import ADMINS, API_HASH, API_ID, BOT_TOKEN
from redis_db import db
from send_media import VideoSender
from tools import extract_code_from_url, get_urls_from_string
from keep_alive import keep_alive
from terabox import get_data

# Start uptime server
keep_alive()

# Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("TeraBoxBot")

bot = TelegramClient("main", API_ID, API_HASH)


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

    # Anti-spam
    if (is_spam := db.get(str(m.sender_id))) and m.sender_id not in ADMINS:
        ttl = db.ttl(str(m.sender_id))
        wait = hr.Time(str(ttl), default_unit=hr.Time.Unit.SECOND)
        return await hm.edit(
            f"⏳ You're spamming. Please wait {wait.to_humanreadable()} and try again.",
            parse_mode="markdown",
        )

    shorturl = extract_code_from_url(url)
    if not shorturl:
        return await hm.edit("❌ Invalid TeraBox link provided.")

    # Cache check
    fileid = db.get(shorturl)
    if fileid:
        uid = db.get(f"mid_{fileid}")
        if uid:
            check = await VideoSender.forward_file(file_id=fileid, message=m, client=bot, edit_message=hm, uid=uid)
            if check:
                return

    # API fetch
    try:
        data = get_data(url)
    except Exception as e:
        log.error(f"Error in get_data: {e}")
        return await hm.edit("⚠️ API error or broken link.")

    if not data:
        return await hm.edit("⚠️ Could not fetch the file. It may be expired or removed.")

    # Set rate limit (60 sec)
    db.set(str(m.sender_id), time.monotonic(), ex=60)

    # File size restriction
    if int(data["sizebytes"]) > 524_288_000 and m.sender_id not in ADMINS:
        return await hm.edit(
            f"❌ File too large. Only files up to 500MB allowed.\n"
            f"Size: {data['size']}\n\nTry direct link:\n{data.get('direct_link', data.get('link', 'N/A'))}",
            parse_mode="markdown",
        )

    # Send media
    sender = VideoSender(client=bot, data=data, message=m, edit_message=hm, url=url)
    asyncio.create_task(sender.send_video())


# Flask + Telegram bot
def start_bot_and_flask():
    def run_flask():
        from keep_alive import app
        app.run(host='0.0.0.0', port=8080)

    Thread(target=run_flask).start()

    try:
        print("🤖 Starting Telegram bot...")
        bot.start(bot_token=BOT_TOKEN)
        bot.run_until_disconnected()
    except Exception as e:
        log.error(f"Bot failed to start: {e}")


if __name__ == "__main__":
    start_bot_and_flask()
