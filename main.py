import ccxt
import pandas as pd
import numpy as np
import requests
import mplfinance as mpf
import os
from io import BytesIO

# دریافت توکن و چت آیدی از متغیرهای محیطی GitHub
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = "4h"
LIMIT = 150
THRESHOLD_PERCENT = 2.0

def send_telegram_chart(df, symbol, level_type, level_price):
    buf = BytesIO()
    df = df.set_index('Date')
    addplot = [mpf.make_addplot([level_price]*len(df), color='g' if level_type=='حمایت' else 'r')]
    mpf.plot(df, type='candle', style='charles', addplot=addplot, volume=True, savefig=buf)
    buf.seek(0)

    caption = f"🚨 هشدار تکنیکال!\n🪙 ارز: {symbol}\n⏰ تایم‌فریم: 4h\n📌 ناحیه: {level_type} ({round(level_price, 2)})"
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {'photo': buf}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    response = requests.post(url, files=files, data=data)
    print("Telegram response:", response.text)

def get_swing_levels(df):
    highs = df['High']
    lows = df['Low']
    resistance = highs[(highs.shift(1) < highs) & (highs.shift(-1) < highs)]
    support = lows[(lows.shift(1) > lows) & (lows.shift(-1) > lows)]
    return support.dropna().values[-3:], resistance.dropna().values[-3:]

def is_near_level(price, level, threshold_percent):
    threshold = level * (threshold_percent / 100)
    return abs(price - level) <= threshold

def analyze_pair(symbol, exchange):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=LIMIT)
        df = pd.DataFrame(ohlcv, columns=['Timestamp','Open','High','Low','Close','Volume'])
        df['Date'] = pd.to_datetime(df['Timestamp'], unit='ms')
        support_levels, resistance_levels = get_swing_levels(df)
        current_price = df['Close'].iloc[-1]

        for level in support_levels:
            if is_near_level(current_price, level, THRESHOLD_PERCENT):
                send_telegram_chart(df.copy(), symbol, "حمایت", level)
                break

        for level in resistance_levels:
            if is_near_level(current_price, level, THRESHOLD_PERCENT):
                send_telegram_chart(df.copy(), symbol, "مقاومت", level)
                break

    except Exception as e:
        print(f"❌ خطا در {symbol}: {e}")

def main():
    exchange = ccxt.kucoin()
    markets = exchange.load_markets()
    symbols = [s for s in markets if "/USDT" in s and markets[s]['active']]

    volatile_pairs = []
    for symbol in symbols:
        try:
            ticker = exchange.fetch_ticker(symbol)
            volume = ticker.get('baseVolume', 0)
            atr = ticker.get('high', 0) - ticker.get('low', 0)
            score = volume * atr
            volatile_pairs.append((symbol, score))
        except:
            continue

    top_pairs = sorted(volatile_pairs, key=lambda x: x[1], reverse=True)[:10]
    for sym, _ in top_pairs:
        analyze_pair(sym, exchange)

if __name__ == "__main__":
    main()
