import asyncio
import os
import time
from pathlib import Path
from uuid import uuid4

import telethon
from telethon import Button, TelegramClient, events
from telethon.events.newmessage import NewMessage
from telethon.tl.custom.message import Message
from telethon.tl.functions.channels import GetMessagesRequest
from telethon.tl.types import Document
from telethon.types import UpdateEditMessage

from cansend import CanSend
from config import BOT_USERNAME, PRIVATE_CHAT_ID
from FastTelethon import upload_file
from redis_db import db
from tools import (
    convert_seconds,
    download_file,
    download_image_to_bytesio,
    extract_code_from_url,
    get_formatted_size,
)
from terabox import get_data

# 🔁 Constants
BASE_URL = "https://teracinee.com"
CHANNEL_URL = "https://t.me/TeracineeChannel"
GROUP_URL = "https://t.me/+EtHQEItJyzE4YzU0"


class VideoSender:

    def __init__(self, client: TelegramClient, message: NewMessage.Event,
                 edit_message: UpdateEditMessage, url: str, data):
        self.client = client
        self.message = message
        self.edit_message = edit_message
        self.url = url
        self.data = data
        self.uuid = str(uuid4())
        self.task = None
        self.thumbnail = self.get_thumbnail()
        self.can_send = CanSend()
        self.start_time = time.time()
        self.client.add_event_handler(
            self.stop, events.CallbackQuery(pattern=f"^stop{self.uuid}")
        )

        self.caption = f"""
🎬 **File Name:** `{self.data['file_name']}`
📦 **Size:** **{self.data['size']}**

@{BOT_USERNAME}
        """

        self.caption2 = f"""
📥 **Downloading:** `{self.data['file_name']}`
📦 **Size:** **{self.data['size']}**

@{BOT_USERNAME}
        """

    async def progress_bar(self, current, total, state="Sending"):
        if not self.can_send.can_send():
            return

        percent = current / total if total else 0
        bar = "█" * int(percent * 20) + "░" * (20 - int(percent * 20))
        speed = current / (time.time() - self.start_time) if self.start_time else 0
        remaining = (total - current) / speed if speed else 0

        msg = f"""
🚀 {state} `{self.data['file_name']}`
[{bar}] {percent:.2%}
⚡️ Speed: **{get_formatted_size(speed)}/s**
⏳ Time Remaining: `{convert_seconds(remaining)}`
📦 Size: **{get_formatted_size(current)}** / **{get_formatted_size(total)}**
        """

        await self.edit_message.edit(
            msg.strip(),
            parse_mode="markdown",
            buttons=[Button.inline("🛑 Stop", data=f"stop{self.uuid}")],
        )

    async def send_media(self, shorturl):
        app_watch_url = f"{BASE_URL}/watch?url={self.url}"
        app_download_url = f"{BASE_URL}/download?url={self.url}"

        try:
            if self.thumbnail:
                self.thumbnail.seek(0)

            media_file = (
                await self.client._file_to_media(
                    self.data["direct_link"],
                    supports_streaming=True,
                    progress_callback=self.progress_bar,
                    thumb=self.thumbnail,
                )
            )[1]
            media_file.spoiler = True

            file = await self.client.send_file(
                self.message.chat.id,
                file=media_file,
                caption=self.caption,
                reply_to=self.message.id,
                parse_mode="markdown",
                supports_streaming=True,
                buttons=[
                    [
                        Button.url("📥 Download", url=app_download_url),
                        Button.url("▶️ Watch", url=app_watch_url),
                    ],
                    [
                        Button.url("📢 Channel", url=CHANNEL_URL),
                        Button.url("💬 Group", url=GROUP_URL),
                    ],
                ],
            )

            try:
                if self.edit_message:
                    await self.edit_message.delete()
            except Exception:
                pass

        except telethon.errors.rpcerrorlist.WebpageCurlFailedError:
            await self.handle_fallback(shorturl)
        except Exception as e:
            print(f"[ERROR] send_media failed: {e}")
            await self.handle_failed_download()
        else:
            await self.save_forward_file(file, shorturl)

    async def handle_fallback(self, shorturl):
        app_watch_url = f"{BASE_URL}/watch?url={self.url}"
        app_download_url = f"{BASE_URL}/download?url={self.url}"

        path = Path(self.data["file_name"])
        try:
            download = path if path.exists() else await download_file(
                self.data["direct_link"], self.data["file_name"], self.progress_bar
            )

            if not download or not Path(download).exists():
                raise FileNotFoundError("Downloaded file not found")

            self.download = Path(download)

            with open(self.download, "rb") as out:
                uploaded = await upload_file(
                    self.client, out, self.progress_bar, self.data["file_name"]
                )

            file = await self.client.send_file(
                self.message.chat.id,
                file=uploaded,
                caption=self.caption,
                reply_to=self.message.id,
                parse_mode="markdown",
                supports_streaming=True,
                thumb=self.thumbnail,
                buttons=[
                    [
                        Button.url("📥 Download", url=app_download_url),
                        Button.url("▶️ Watch", url=app_watch_url),
                    ],
                    [
                        Button.url("📢 Channel", url=CHANNEL_URL),
                        Button.url("💬 Group", url=GROUP_URL),
                    ],
                ],
            )
            await self.save_forward_file(file, shorturl)
        except Exception as e:
            print(f"[ERROR] Fallback upload failed: {e}")
            await self.handle_failed_download()

    async def handle_failed_download(self):
        app_watch_url = f"{BASE_URL}/watch?url={self.url}"
        app_download_url = f"{BASE_URL}/download?url={self.url}"

        try:
            await self.edit_message.edit(
                f"❌ Download Failed. You can try [Download]({app_download_url}) or [Watch]({app_watch_url}).",
                parse_mode="markdown",
                buttons=[
                    Button.url("📥 Download", url=app_download_url),
                    Button.url("▶️ Watch", url=app_watch_url),
                ],
            )
        except Exception:
            pass

    async def save_forward_file(self, file, shorturl):
        forwarded = await self.client.forward_messages(
            PRIVATE_CHAT_ID,
            [file],
            from_peer=self.message.chat.id,
            background=True,
        )
        msg_id = forwarded[0].id
        if msg_id:
            db.set_key(self.uuid, msg_id)
            db.set_key(f"mid_{msg_id}", self.uuid)
            db.set_key(shorturl, msg_id)
        self.client.remove_event_handler(
            self.stop, events.CallbackQuery(pattern=f"^stop{self.uuid}")
        )
        try:
            await self.edit_message.delete()
        except Exception:
            pass
        for file_path in [self.data["file_name"], getattr(self, "download", "")]:
            try:
                os.unlink(file_path)
            except Exception:
                pass

    async def send_video(self):
        self.thumbnail = download_image_to_bytesio(self.data["thumb"], "thumb.png")
        shorturl = extract_code_from_url(self.url)
        if not shorturl:
            return await self.edit_message.edit("⚠️ Invalid URL.")
        self.edit_message = await self.message.reply(
            self.caption2, file=self.thumbnail, parse_mode="markdown"
        )
        self.task = asyncio.create_task(self.send_media(shorturl))

    async def stop(self, event):
        if self.task:
            self.task.cancel()
        await event.answer("🛑 Process stopped.")
        try:
            await self.edit_message.delete()
        except Exception:
            pass
        for file_path in [self.data["file_name"], getattr(self, "download", "")]:
            try:
                os.unlink(file_path)
            except Exception:
                pass

    def get_thumbnail(self):
        return download_image_to_bytesio(self.data["thumb"], "thumb.png")

    @staticmethod
    async def forward_file(client: TelegramClient, file_id: int, message: Message,
                           edit_message: UpdateEditMessage = None, uid: str = None):
        if edit_message:
            try:
                await edit_message.delete()
            except Exception:
                pass

        result = await client(GetMessagesRequest(channel=PRIVATE_CHAT_ID, id=[int(file_id)]))
        msg: Message = result.messages[0] if result and result.messages else None
        if not msg:
            return False
        media: Document = (
            msg.media.document if hasattr(msg, "media") and msg.media.document else None
        )

        try:
            await message.reply(
                message=msg.message,
                file=media,
                reply_to=message.id,
                parse_mode="markdown",
                buttons=[
                    [Button.url("📥 Download", url=f"https://{BOT_USERNAME}.t.me?start={uid}")],
                ],
            )
            return True
        except Exception:
            return False


async def send_media(shorturl: str):
    try:
        data = await get_data(shorturl)
        if not data or not data.get("file_name"):
            return None
        return {
            "title": data.get("file_name"),
            "download_link": data.get("direct_link"),
            "watch_link": data.get("link"),
            "thumbnail_url": data.get("thumb"),
            "data": data,
        }
    except Exception as e:
        print(f"[ERROR] get_data failed: {e}")
        return None
