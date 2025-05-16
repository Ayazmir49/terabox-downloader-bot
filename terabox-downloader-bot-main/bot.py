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
from api_integration import get_data  # Importing get_data from api_integration.py

keep_alive()  # Optional for replit or always-on apps

bot = TelegramClient("main", API_ID, API_HASH)

log = logging.getLogger(__name__)

@bot.on(
    events.NewMessage(
        incoming=True,
        outgoing=False,
        func=lambda message: message.text
        and get_urls_from_string(message.text)
        and message.is_private,
    )
)
async def get_message(m: Message):
    asyncio.create_task(handle_message(m))

async def handle_message(m: Message):
    url = get_urls_from_string(m.text)
    if not url:
        return await m.reply("Please enter a valid URL.")
    
    hm = await m.reply("Sending you the media... please wait...")

    # Anti-spam check
    is_spam = db.get(str(m.sender_id))
    if is_spam and m.sender_id not in ADMINS:
        ttl = db.ttl(str(m.sender_id))
        t = hr.Time(str(ttl), default_unit=hr.Time.Unit.SECOND)
        return await hm.edit(
            f"You are spamming.\n**Please wait {t.to_humanreadable()} and try again.**",
            parse_mode="markdown",
        )

    # Token check (optional, can be removed)
    if_token_avl = db.get(f"active_{m.sender_id}")
    if not if_token_avl and m.sender_id not in ADMINS:
        return await hm.edit(
            "Your account is deactivated. Send /gen to activate it again."
        )

    shorturl = extract_code_from_url(url)
    if not shorturl:
        return await hm.edit("Seems like your link is invalid.")
    
    fileid = db.get(shorturl)
    if fileid:
        uid = db.get(f"mid_{fileid}")
        if uid:
            check = await VideoSender.forward_file(
                file_id=fileid, message=m, client=bot, edit_message=hm, uid=uid
            )
            if check:
                return
    
    # Fetching data from Terabox API
    try:
        data = get_data(url)  # Calling the API to get data
    except Exception:
        return await hm.edit("Sorry! API is down or maybe your link is broken.")
    
    if not data:
        return await hm.edit("Sorry! API is down or maybe your link is broken.")
    
    db.set(str(m.sender_id), time.monotonic(), ex=60)

    # File size check
    if int(data["sizebytes"]) > 524288000 and m.sender_id not in ADMINS:
        return await hm.edit(
            f"Sorry! File is too big.\n**I can download only 500MB and this file is of {data['size']}**.\nRather you can download this file from the link below:\n{data['url']}",
            parse_mode="markdown",
        )

    sender = VideoSender(
        client=bot,
        data=data,
        message=m,
        edit_message=hm,
        url=url,
    )
    asyncio.create_task(sender.send_video())

# Start Flask server and Telegram bot
def start_bot_and_flask():
    loop = asyncio.get_event_loop()

    def run_flask():
        from keep_alive import app
        app.run(host='0.0.0.0', port=8080)

    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Running Telegram bot
    bot.start(bot_token=BOT_TOKEN)
    bot.run_until_disconnected()

if __name__ == "__main__":
    start_bot_and_flask()
