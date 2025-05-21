# keep_alive.py
from flask import Flask, send_from_directory
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

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run_flask).start()
