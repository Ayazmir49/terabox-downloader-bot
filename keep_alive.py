# keep_alive.py
from flask import Flask, send_from_directory, request
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

# ✅ Serve Android App Links file from .well-known
@app.route('/.well-known/assetlinks.json')
def serve_assetlinks():
    return send_from_directory(
        os.path.join(os.getcwd(), '.well-known'),
        'assetlinks.json',
        mimetype='application/json'
    )

# ✅ Add route to handle /watch
@app.route('/watch')
def handle_watch():
    video_url = request.args.get("url")
    return f"""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="font-family:sans-serif; text-align:center; margin-top:50px;">
            <h2>🎬 Opening in Teracinee App...</h2>
            <p>If the app doesn't open automatically, copy this link and paste it into the app:</p>
            <code style="display:block; margin-top:1em;">{video_url}</code>
        </body>
    </html>
    """

# ✅ Add route to handle /download
@app.route('/download')
def handle_download():
    video_url = request.args.get("url")
    return f"""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="font-family:sans-serif; text-align:center; margin-top:50px;">
            <h2>⬇️ Opening in Teracinee App...</h2>
            <p>If the app doesn't open automatically, copy this link and paste it into the app:</p>
            <code style="display:block; margin-top:1em;">{video_url}</code>
        </body>
    </html>
    """

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_flask).start()
