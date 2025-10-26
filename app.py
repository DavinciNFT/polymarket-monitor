from flask import Flask
import threading
import time
import os
from monitor import main as monitor_main  # assuming your script's entry point is main()

app = Flask(__name__)

def background_task():
    while True:
        print("[Flask Worker] Running monitor check...")
        try:
            monitor_main()  # call your monitoring function
        except Exception as e:
            print(f"[Error] {e}")
        time.sleep(15 * 60)  # wait 15 minutes

@app.route('/')
def home():
    return "✅ Polymarket Monitor is running on Render."

if __name__ == '__main__':
    # Start the monitoring thread
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()
    
    # Start Flask server
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
