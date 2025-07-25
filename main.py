import ccxt
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import datetime
import requests
import os

# دریافت توکن و چت‌آیدی از مخفی‌سازی گیت‌هاب
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# اتصال به کوکوین
exchange = ccxt.kucoin()

def send_telegram_message(message, image_path=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

    if image_path:
        photo_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        with open(image_path, 'rb') as f:
            requests.post(photo_url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"photo": f})

def get_symbols():
    markets = exchange.load_markets()
    return [symbol for symbol in markets if '/USDT' in symbol]

def fetch_candles(symbol):
    since = exchange.parse8601((datetime.datetime.utcnow() - datetime.timedelta(days=5)).isoformat())
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='4h', since=since)
    df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)
    return df

def find_support_resistance(df):
    support = df['Low'].min()
    resistance = df['High'].max()
    return support, resistance

def check_and_notify(symbol):
    try:
        df = fetch_candles(symbol)
        support, resistance = find_support_resistance(df)
        current_price = df['Close'].iloc[-1]

        if abs(current_price - support) / support < 0.01 or abs(current_price - resistance) / resistance < 0.01:
            image_path = f"{symbol.replace('/', '_')}.png"
            mpf.plot(df[-50:], type='candle', style='binance', savefig=image_path)
            send_telegram_message(f"{symbol}\nقیمت نزدیک {'حمایت' if current_price < resistance else 'مقاومت'} هست.\nقیمت فعلی: {current_price}", image_path)
    except Exception as e:
        print(f"خطا در بررسی {symbol}: {e}")

def main():
    symbols = get_symbols()[:10]  # فقط ۱۰ ارز اول برای شروع
    for symbol in symbols:
        check_and_notify(symbol)

main()
