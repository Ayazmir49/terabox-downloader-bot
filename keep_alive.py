# keep_alive.py

from flask import Flask, send_from_directory, request
from threading import Thread
from urllib.parse import urlparse, quote
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Teracinee server is running!"

# ✅ Serve Android App Links file from .well-known
@app.route('/.well-known/assetlinks.json')
def serve_assetlinks():
    return send_from_directory(
        os.path.join(os.getcwd(), '.well-known'),
        'assetlinks.json',
        mimetype='application/json'
    )

# ✅ Helper to validate incoming URLs
def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https'] and parsed.netloc != ''
    except:
        return False

# ✅ /watch route redirects to app with custom scheme
@app.route('/watch')
def handle_watch():
    video_url = request.args.get("url", "")
    if not is_valid_url(video_url):
        return "❌ Invalid or missing URL", 400

    encoded_url = quote(video_url, safe='')
    return f"""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta http-equiv="refresh" content="0; url=teracinee://video?url={encoded_url}">
        </head>
        <body style="font-family:sans-serif; text-align:center; margin-top:50px;">
            <h2>🎬 Opening in Teracinee App...</h2>
            <p>If the app doesn’t open automatically, copy this link and paste it into the app:</p>
            <code style="display:block; margin-top:1em;">{video_url}</code>
        </body>
    </html>
    """

# ✅ /download route redirects to app with custom scheme
@app.route('/download')
def handle_download():
    video_url = request.args.get("url", "")
    if not is_valid_url(video_url):
        return "❌ Invalid or missing URL", 400

    encoded_url = quote(video_url, safe='')
    return f"""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta http-equiv="refresh" content="0; url=teracinee://video?url={encoded_url}">
        </head>
        <body style="font-family:sans-serif; text-align:center; margin-top:50px;">
            <h2>⬇️ Opening in Teracinee App...</h2>
            <p>If the app doesn’t open automatically, copy this link and paste it into the app:</p>
            <code style="display:block; margin-top:1em;">{video_url}</code>
        </body>
    </html>
    """

# ✅ Run Flask server in a background thread
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_flask).start()
