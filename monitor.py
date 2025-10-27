# monitor.py
import time
import requests
import os
import json
import threading
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask

# Flask app for Render web service
app = Flask(__name__)

# Load .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

# Config
CHECK_INTERVAL_SECONDS = 60  # check every 1 minute for testing
CHANGE_THRESHOLD = 0.02                  # 2% (relative change)
MARKETS_URL = "https://api.polymarket.com/gamma/markets"
LAST_PRICES_FILE = "last_prices.json"
REQUEST_TIMEOUT = 20                     # seconds

# Helper: persist last prices between runs
def load_last_prices():
    if os.path.exists(LAST_PRICES_FILE):
        try:
            with open(LAST_PRICES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_last_prices(d):
    with open(LAST_PRICES_FILE, "w") as f:
        json.dump(d, f, indent=2)

# Send Telegram message via Bot API
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Telegram send failed: {e}")
        return False

def fetch_markets():
    try:
        r = requests.get(MARKETS_URL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return data.get("markets", data)
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Error fetching markets: {e}")
        return []

def format_price(p):
    try:
        return f"{float(p)*100:.2f}%"
    except Exception:
        return str(p)

def monitor_loop():
    """Background thread to continuously check market updates."""
    last_prices = load_last_prices()
    print(f"[{datetime.utcnow().isoformat()}] Starting monitor. Loaded {len(last_prices)} stored prices.")

    while True:
        try:
            markets = fetch_markets()
            if not markets:
                print(f"[{datetime.utcnow().isoformat()}] No markets received.")

            for m in markets:
                market_id = m.get("id") or m.get("marketAddress") or m.get("conditionId") or m.get("slug")
                title = m.get("title") or m.get("name") or m.get("slug") or "Untitled Market"
                slug = m.get("slug") or market_id
                outcomes = m.get("outcomes") or m.get("pairs") or []

                for out in outcomes:
                    outcome_name = out.get("name") or out.get("label") or out.get("title") or "Outcome"
                    price = out.get("price") or out.get("lastPrice") or out.get("last_price") or out.get("last")
                    if price is None:
                        continue
                    try:
                        price = float(price)
                    except Exception:
                        continue

                    key = f"{market_id}||{outcome_name}"
                    old_price = last_prices.get(key)
                    last_prices[key] = price

                    if old_price is not None and old_price != 0:
                        change = (price - old_price) / old_price
                        if abs(change) >= CHANGE_THRESHOLD:
                            pct = change * 100.0
                            time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                            msg = (
                                f"*Polymarket Update — {title}*\n"
                                f"_Checked at:_ {time_str}\n"
                                f"*Outcome:* {outcome_name}\n"
                                f"*Old odds:* {format_price(old_price)}\n"
                                f"*New odds:* {format_price(price)}\n"
                                f"*Change:* {pct:+.2f}%\n"
                                f"[Open market](https://polymarket.com/markets/{slug})"
                            )
                            print(f"[{time_str}] Significant change detected for {title} / {outcome_name}: {pct:+.2f}%")
                            send_telegram_message(msg)

            save_last_prices(last_prices)
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Unexpected error in monitor loop: {e}")

        print(f"[{datetime.utcnow().isoformat()}] Sleeping for {CHECK_INTERVAL_SECONDS/60:.0f} minutes...\n")
        time.sleep(CHECK_INTERVAL_SECONDS)

@app.route('/')
def home():
    return "✅ Polymarket Monitor is active and running."

def main():
    """Entry point for Render — starts the monitor in a background thread."""
    print("[Monitor] Starting Polymarket monitor service...")

    # Send Telegram startup message
    try:
        send_telegram_message("✅ Polymarket Monitor started successfully 🚀")
    except Exception as e:
        print(f"[Monitor] Failed to send Telegram startup message: {e}")

    # Start background monitoring in a separate thread
    threading.Thread(target=main_loop, daemon=True).start()
    print("[Monitor] Background monitoring thread started.")

    # Keep Flask alive for Render
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

