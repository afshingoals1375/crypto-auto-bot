import ccxt
import pandas as pd
import telegram
import json
import os

# اطلاعات تلگرام
TOKEN = '7881646413:AAF0xarvW2kfenlyvO-qalInehTCfH2F03w'
CHAT_ID = '720745494'

# محدوده نزدیکی به سطح
THRESHOLD = 0.003

# فایل هشدارهای قبلی
ALERTS_FILE = 'alerts.json'
if not os.path.exists(ALERTS_FILE):
    with open(ALERTS_FILE, 'w') as f:
        json.dump({}, f)

exchange = ccxt.kucoin()

def get_ohlcv(symbol='BTC/USDT', timeframe='4h', limit=200):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def find_support_resistance(df, window=2):
    supports, resistances = [], []
    for i in range(window, len(df)-window):
        low = df['low']
        high = df['high']
        if all(low[i] < low[i - j] and low[i] < low[i + j] for j in range(1, window+1)):
            supports.append(round(low[i], 2))
        if all(high[i] > high[i - j] and high[i] > high[i + j] for j in range(1, window+1)):
            resistances.append(round(high[i], 2))
    return list(set(supports))[-3:], list(set(resistances))[-3:]

def get_current_price(symbol='BTC/USDT'):
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']

def send_telegram_alert(message):
    bot = telegram.Bot(token=TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)

def load_alerts():
    with open(ALERTS_FILE, 'r') as f:
        return json.load(f)

def save_alerts(alerts):
    with open(ALERTS_FILE, 'w') as f:
        json.dump(alerts, f)

def main():
    symbol = 'BTC/USDT'
    df = get_ohlcv(symbol)
    supports, resistances = find_support_resistance(df)
    price = get_current_price(symbol)
    alerts = load_alerts()
    if symbol not in alerts:
        alerts[symbol] = []

    for level in supports + resistances:
        diff = abs(price - level) / price
        if diff < THRESHOLD and str(level) not in alerts[symbol]:
            level_type = 'حمایت' if level in supports else 'مقاومت'
            message = f"🚨 هشدار {level_type} در {symbol}\nقیمت فعلی: {price}\nنزدیک به سطح {level}"
            send_telegram_alert(message)
            alerts[symbol].append(str(level))

    save_alerts(alerts)

if __name__ == '__main__':
    main()
