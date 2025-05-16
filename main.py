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
from terabox import get_data
from tools import extract_code_from_url, get_urls_from_string
from keep_alive import keep_alive  # Keeps bot alive on hosting

# Keep bot alive on Render/Vercel/etc.
keep_alive()

bot = TelegramClient("main", API_ID, API_HASH)
log = logging.getLogger(__name__)

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
        return await m.reply("❌ Please enter a valid URL.")

    hm = await m.reply("📥 Fetching media, please wait...")

    # Anti-spam check
    is_spam = db.get(str(m.sender_id))
    if is_spam and m.sender_id not in ADMINS:
        ttl = db.ttl(str(m.sender_id))
        t = hr.Time(str(ttl), default_unit=hr.Time.Unit.SECOND)
        return await hm.edit(
            f"⏳ You're spamming. Please wait {t.to_humanreadable()} and try again.",
            parse_mode="markdown",
        )

    shorturl = extract_code_from_url(url)
    if not shorturl:
        return await hm.edit("❌ Invalid link provided.")

    # Check cache
    fileid = db.get(shorturl)
    if fileid:
        uid = db.get(f"mid_{fileid}")
        if uid:
            check = await VideoSender.forward_file(file_id=fileid, message=m, client=bot, edit_message=hm, uid=uid)
            if check:
                return

    # Fetch media info from API
    try:
        data = get_data(url)
    except Exception:
        return await hm.edit("⚠️ API error or broken link.")

    if not data:
        return await hm.edit("⚠️ Could not fetch the file.")

    # Rate limit this user (60 seconds)
    db.set(str(m.sender_id), time.monotonic(), ex=60)

    # File size check
    if int(data["sizebytes"]) > 524_288_000 and m.sender_id not in ADMINS:
        return await hm.edit(
            f"❌ File too large. Only files up to 500MB allowed.\n"
            f"This file: {data['size']}\n\nTry direct link:\n{data['url']}",
            parse_mode="markdown",
        )

    # Send media
    sender = VideoSender(client=bot, data=data, message=m, edit_message=hm, url=url)
    asyncio.create_task(sender.send_video())

# Start both Flask server and Telegram bot
def start_bot_and_flask():
    loop = asyncio.get_event_loop()

    def run_flask():
        from keep_alive import app
        app.run(host='0.0.0.0', port=8080)

    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    bot.start(bot_token=BOT_TOKEN)
    bot.run_until_disconnected()

if __name__ == "__main__":
    start_bot_and_flask()
