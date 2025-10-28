# app.py
from flask import Flask
import threading
import os
import monitor  # your monitoring logic file

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Polymarket Monitor is running on Render."

def start_monitor():
    print("[Monitor] Starting Polymarket monitor service...")
    try:
        t = threading.Thread(target=monitor.main_loop, daemon=True)
        t.start()
        print("[Monitor] Background monitor thread started successfully.")
    except Exception as e:
        print(f"[Monitor] Failed to start monitoring thread: {e}")

if __name__ == "__main__":
    start_monitor()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
