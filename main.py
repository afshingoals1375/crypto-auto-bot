import ccxt
import pandas as pd
import numpy as np
import requests
import mplfinance as mpf
from io import BytesIO

# تنظیمات
TOKEN = "7881646413:AAF0xarvW2kfenlyvO-qalInehTCfH2F03w"
CHAT_ID = "720745494"
TIMEFRAME = "4h"
LIMIT = 150
THRESHOLD_PERCENT = 2.0

def send_telegram_chart(df, symbol, level_type, level_price):
    buf = BytesIO()
    df = df.set_index('Date')
    addplot = [mpf.make_addplot([level_price]*len(df), color='g' if level_type == 'حمایت' else 'r')]
    mpf.plot(df, type='candle', style='charles', addplot=addplot, volume=True, savefig=buf)
    buf.seek(0)

    tv_symbol = symbol.replace("/", "")  # مثل BTCUSDT
    tv_link = f"https://www.tradingview.com/chart/?symbol=BINANCE:{tv_symbol}"

    caption = f"""
🚨 هشدار تکنیکال!
🪙 ارز: {symbol}
⏰ تایم‌فریم: 4h
📌 ناحیه: {level_type} ({round(level_price, 2)})

🔗 [مشاهده در تریدینگ‌ویو]({tv_link})
"""

    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {'photo': buf}
    data = {
        'chat_id': CHAT_ID,
        'caption': caption,
        'parse_mode': 'Markdown'
    }
    requests.post(url, files=files, data=data)

def get_swing_levels(df):
    highs = df['High']
    lows = df['Low']
    resistance = highs[(highs.shift(1) < highs) & (highs.shift(-1) < highs)]
    support = lows[(lows.shift(1) > lows) & (lows.shift(-1) > lows)]
    return support.dropna().values[-3:], resistance.dropna().values[-3:]

def is_near_level(price, level, threshold_percent):
    threshold = level * (threshold_percent / 100)
    return abs(price - level) <= threshold

def analyze_pair(symbol):
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

# اجرای برنامه
exchange = ccxt.kucoin()  # از کوکوین استفاده می‌کنیم چون محدودیت آی‌پی نداره
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
    analyze_pair(sym)
