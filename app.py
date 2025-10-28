from flask import Flask
import threading
import os
import monitor

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Polymarket Monitor is running!"

def start_monitor():
    print("[Monitor] Starting Polymarket monitor service...")
    try:
        monitor_thread = threading.Thread(target=monitor.main_loop, daemon=True)
        monitor_thread.start()
        print("[Monitor] Background monitoring thread started.")
    except Exception as e:
        print(f"[Monitor] Failed to start monitoring thread: {e}")

if __name__ == "__main__":
    start_monitor()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
