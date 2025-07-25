import ccxt
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import requests
from io import BytesIO
from datetime import datetime, timedelta

# توکن و چت آیدی تلگرام از سکرت GitHub گرفته میشه
import os
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_photo(image_bytes, caption=""):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {"photo": image_bytes}
    data = {"chat_id": CHAT_ID, "caption": caption}
    response = requests.post(url, files=files, data=data)
    return response.json()

def detect_support_resistance(prices, tolerance=0.002):
    supports = []
    resistances = []
    for i in range(2, len(prices) - 2):
        if prices[i] < prices[i-1] and prices[i] < prices[i+1]:
            supports.append(prices[i])
        if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
            resistances.append(prices[i])
    return supports, resistances

def plot_chart(df, support_levels, resistance_levels, symbol):
    mc = mpf.make_marketcolors(up='g', down='r')
    s  = mpf.make_mpf_style(marketcolors=mc)

    add_plot = []
    for lvl in support_levels:
        add_plot.append(mpf.make_addplot([lvl]*len(df), color='green'))
    for lvl in resistance_levels:
        add_plot.append(mpf.make_addplot([lvl]*len(df), color='red'))

    buf = BytesIO()
    mpf.plot(df, type='candle', style=s, addplot=add_plot, volume=True, savefig=buf)
    buf.seek(0)
    return buf

def analyze_symbol(symbol):
    exchange = ccxt.kucoin()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='4h', limit=100)
    df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)

    prices = df['Close'].tolist()
    support_levels, resistance_levels = detect_support_resistance(prices)

    last_price = prices[-1]
    nearest_support = min(support_levels, key=lambda x: abs(x - last_price)) if support_levels else None
    nearest_resistance = min(resistance_levels, key=lambda x: abs(x - last_price)) if resistance_levels else None

    if nearest_support and abs(last_price - nearest_support) / last_price < 0.01:
        buf = plot_chart(df, [nearest_support], [], symbol)
        send_telegram_photo(buf, f"{symbol} نزدیک حمایت {nearest_support}")
    elif nearest_resistance and abs(last_price - nearest_resistance) / last_price < 0.01:
        buf = plot_chart(df, [], [nearest_resistance], symbol)
        send_telegram_photo(buf, f"{symbol} نزدیک مقاومت {nearest_resistance}")

# فقط ارزهای معروف
symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
for sym in symbols:
    try:
        analyze_symbol(sym)
    except Exception as e:
        print(f"خطا برای {sym}:", e)
