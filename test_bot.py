import requests

TELEGRAM_BOT_TOKEN = "8258966671:AAHz9TTQHUCT7bSsgmUmrVNrGyP8z19C8R8"
TELEGRAM_CHAT_ID = "-1003273059320"

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": "✅ Test message from Polymarket Monitor bot!"
}

r = requests.post(url, json=payload)
print(r.text)
