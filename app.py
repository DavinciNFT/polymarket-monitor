# app.py
import os
from flask import Flask
from monitor import start_monitor   # import from your monitor.py

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Polymarket Monitor is active and running."

# Start background monitoring thread **before** starting Flask
start_monitor()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
