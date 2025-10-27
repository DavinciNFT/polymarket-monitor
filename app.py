from flask import Flask
import threading
import monitor
import os  # 👈 Add this line

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Polymarket Monitor is running!"

def start_monitor():
    print("[Monitor] Starting Polymarket monitor service...")
    monitor_thread = threading.Thread(target=monitor.main, daemon=True)
    monitor_thread.start()

if __name__ == "__main__":
    start_monitor()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
