# monitor.py
import time
import requests
import os
import json
import threading
from datetime import datetime
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Polymarket API URL
MARKETS_URL = "https://api.polymarket.com/gamma/markets"

def test_api_connectivity():
    """Checks if Polymarket API is reachable and logs the result."""
    print("[Connectivity Test] Testing connection to Polymarket API...")
    try:
        r = requests.get(MARKETS_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        count = len(data.get("markets", data))
        print(f"[Connectivity Test] ✅ API reachable. Received {count} markets.")
        return True
    except Exception as e:
        print(f"[Connectivity Test] ❌ API NOT reachable: {e}")
        return False


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment or .env")

# Config
CHECK_INTERVAL_SECONDS = 15 * 60         # 15 minutes (900 seconds)
CHANGE_THRESHOLD = 0.005                 # 0.5% (relative change)
MARKETS_URL = "https://api.polymarket.com/gamma/markets"
LAST_PRICES_FILE = "last_prices.json"
REQUEST_TIMEOUT = 20                     # seconds

# Helper: persist last prices between runs
def load_last_prices():
    if os.path.exists(LAST_PRICES_FILE):
        try:
            with open(LAST_PRICES_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Failed to read last prices: {e}")
            return {}
    return {}

def save_last_prices(d):
    try:
        with open(LAST_PRICES_FILE, "w") as f:
            json.dump(d, f, indent=2)
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Failed to save last prices: {e}")

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
        # API may return {"markets": [...]} or a list directly
        return data.get("markets", data)
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Error fetching markets: {e}")
        return []

def format_price(p):
    try:
        return f"{float(p)*100:.2f}%"
    except Exception:
        return str(p)

def main_loop():
    """
    Main monitoring loop.
    Loads last_prices once, then continuously polls Polymarket and sends Telegram alerts.
    """
    last_prices = load_last_prices()   # key -> float price
    print(f"[{datetime.utcnow().isoformat()}] Starting monitor. Loaded {len(last_prices)} stored prices.")

    while True:
        try:
            markets = fetch_markets()
            if not markets:
                print(f"[{datetime.utcnow().isoformat()}] No markets received.")
            else:
                print(f"[{datetime.utcnow().isoformat()}] Fetched {len(markets)} markets.")

            for m in markets:
                # Identify market fields robustly
                market_id = m.get("id") or m.get("marketAddress") or m.get("conditionId") or m.get("slug")
                title = m.get("title") or m.get("name") or m.get("slug") or "Untitled Market"
                slug = m.get("slug") or market_id
                outcomes = m.get("outcomes") or m.get("pairs") or []

                for out in outcomes:
                    outcome_name = out.get("name") or out.get("label") or out.get("title") or "Outcome"
                    price = out.get("price")
                    if price is None:
                        price = out.get("lastPrice") or out.get("last_price") or out.get("last")
                    if price is None:
                        continue
                    try:
                        price = float(price)
                    except Exception:
                        continue

                    key = f"{market_id}||{outcome_name}"
                    old_price = last_prices.get(key)
                    last_prices[key] = price

                    # If we have a previous value, compute relative change
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

            # persist after processing batch
            save_last_prices(last_prices)

        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Unexpected error in main loop: {e}")

        # Sleep and loop again
        print(f"[{datetime.utcnow().isoformat()}] Sleeping for {CHECK_INTERVAL_SECONDS/60:.0f} minutes...\n")
        time.sleep(CHECK_INTERVAL_SECONDS)

def start_monitor():
    """
    Start the background monitor thread and send a startup message.
    This function does NOT start any web server; keep webserver in app.py.
    """
    print("[Monitor] Starting Polymarket monitor service...")
test_api_connectivity()
    try:
        send_telegram_message("✅ Polymarket Monitor started successfully 🚀")
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Failed to send startup Telegram message: {e}")

    t = threading.Thread(target=main_loop, daemon=True)
    t.start()
    print("[Monitor] Background monitoring thread started.")
