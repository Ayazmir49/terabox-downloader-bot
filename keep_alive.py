# keep_alive.py
from flask import Flask
from threading import Thread
import subprocess
import os

app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def run_ngrok():
    # 🛠️ Replace the path below with the actual path to your ngrok.exe
    ngrok_path = "D:\\ngrok-v3-stable-windows-amd64\\ngrok.exe"
    subprocess.Popen([ngrok_path, "http", "8080"])

def keep_alive():
    Thread(target=run_flask).start()
    Thread(target=run_ngrok).start()
