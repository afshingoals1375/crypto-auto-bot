import ccxt
import pandas as pd
import datetime
import mplfinance as mpf
import requests
import matplotlib.pyplot as plt
import os

# مشخصات تلگرام
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# تابع ارسال عکس به تلگرام
def send_chart_to_telegram(filepath, symbol):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': open(filepath, 'rb')}
    data = {'chat_id': CHAT_ID, 'caption': f"{symbol} رسید به حمایت/مقاومت!"}
    response = requests.post(url, files=files, data=data)
    return response

# اتصال به کوکوین
exchange = ccxt.kucoin()
markets = exchange.load_markets()

def get_symbols():
    return [symbol for symbol in markets if symbol.endswith('/USDT')]

def fetch_ohlcv(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='4h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def detect_levels(df):
    close_prices = df['close']
    levels = []
    for i in range(2, len(close_prices)-2):
        if close_prices[i] < close_prices[i-1] and close_prices[i] < close_prices[i+1]:
            levels.append((df.index[i], close_prices[i]))  # حمایت
        elif close_prices[i] > close_prices[i-1] and close_prices[i] > close_prices[i+1]:
            levels.append((df.index[i], close_prices[i]))  # مقاومت
    return levels

def draw_chart(df, symbol, levels):
    figfile = f"{symbol.replace('/', '_')}.png"
    apds = [mpf.make_addplot(df['close'], color='blue')]
    hlines = [price for _, price in levels]
    mpf.plot(df, type='candle', style='charles', volume=False,
             addplot=apds, hlines=dict(hlines=hlines, colors='r', linestyle='--'),
             savefig=figfile)
    return figfile

def main():
    symbols = get_symbols()[:10]  # فقط ۱۰ ارز اول برای تست
    for symbol in symbols:
        df = fetch_ohlcv(symbol)
        if df is None or len(df) < 50:
            continue
        levels = detect_levels(df)
        if not levels:
            continue
        last_price = df['close'].iloc[-1]
        for _, lvl in levels:
            if abs(last_price - lvl) / last_price < 0.01:
                chart_path = draw_chart(df, symbol, levels)
                send_chart_to_telegram(chart_path, symbol)
                break

if __name__ == "__main__":
    main()
