import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

message = "✅ تست موفق! این پیام از GitHub به تلگرام ارسال شد."

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = {"chat_id": CHAT_ID, "text": message}

response = requests.post(url, data=data)
print("Telegram response:", response.text)
