import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
PASSWORD = os.getenv("PASSWORD")

PRIVATE_CHAT_ID = int(os.getenv("PRIVATE_CHAT_ID"))
COOKIE = os.getenv("COOKIE", "")
ADMINS = [int(i) for i in os.getenv("ADMINS", "").split(",") if i]

BOT_USERNAME = os.getenv("BOT_USERNAME", "@Teracinee_bot")
FORCE_LINK = os.getenv("FORCE_LINK", "(https://t.me/TeracineeChannel)")
SHORTENER_API = os.getenv("SHORTENER_API", "https://tinyurl.com/api-create.php")
