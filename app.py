from flask import Flask
import threading
import monitor

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Polymarket Monitor is running on Render!"

# Background thread to run the monitoring loop
def start_monitor():
    monitor_thread = threading.Thread(target=monitor.main_loop, daemon=True)
    monitor_thread.start()

if __name__ == '__main__':
    start_monitor()
    app.run(host='0.0.0.0', port=10000)
