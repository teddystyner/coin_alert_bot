import ccxt
import pandas as pd
import ta
import datetime
import telegram
import os

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)

SYMBOLS = ['DOGE/USDT', 'TRX/USDT', 'SHIB/USDT', 'AAVE/USDT', 'LINK/USDT',
           'ADA/USDT', 'BTC/USDT', 'SOL/USDT', 'XRP/USDT', 'ETH/USDT', 'LDO/USDT']
TIMEFRAMES = ['15m', '30m', '1h', '4h', '1d']

exchange = ccxt.bingx({
    'enableRateLimit': True
})

# 환경변수에서 CHAT_ID 가져오기 (쉼표로 구분된 여러 ID 처리)
chat_ids_raw = os.environ.get("CHAT_ID", "")
chat_ids = [int(chat_id.strip()) for chat_id in chat_ids_raw.split(",") if chat_id.strip()]

def fetch_and_check(symbol, timeframe):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        bb = ta.volatility.BollingerBands(df['close'], window=30)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()

        latest = df.iloc[-1]
        price = latest['close']
        rsi = latest['rsi']
        upper = latest['bb_upper']
        lower = latest['bb_lower']
        ema50 = latest['ema50']
        now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        if price > upper and rsi >= 75:
            send_alert(now, symbol, timeframe, '볼린저밴드 상단 돌파 + RSI≥75 + 가격<EMA50', rsi, price, ema50)
        elif price < lower and rsi <= 25:
            send_alert(now, symbol, timeframe, '볼린저밴드 하단 돌파 + RSI≤25 + 가격>EMA50', rsi, price, ema50)

    except Exception as e:
        print(f"{symbol}-{timeframe} 에러: {e}")

def send_alert(time_str, symbol, tf, condition, rsi, price, ema):
    msg = f"[{time_str}] {symbol} ({tf})\n{condition}, RSI: {round(rsi, 2)}, 가격: {round(price, 4)}, EMA50: {round(ema, 4)}"
    for chat_id in chat_ids:
        bot.send_message(chat_id=chat_id, text=msg)
    print(msg)

def check_all():
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            fetch_and_check(symbol, tf)

print("🚀 알림 시스템 실행 중...")
check_all()
