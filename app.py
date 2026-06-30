from flask import Flask, render_template_string, request
import random

app = Flask(__name__)

# --- 1. МАҒЗИ ҲИСОБ - БЕ LIBRARY ---
def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_ema(prices, period):
    if len(prices) < period: return prices[-1]
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = price * k + ema * (1 - k)
    return ema

# --- 2. СИСТЕМАИ 8 ИНДИКАТОР ---
def get_signal(coin):
    base_price = {'BTC': 67000, 'ETH': 3500, 'LTC': 90, 'TRX': 0.15, 'SOL': 150}.get(coin, 100)
    prices = [base_price + random.uniform(-base_price*0.02, base_price*0.02) for _ in range(200)]
    current_price = prices[-1]

    rsi = calc_rsi(prices, 14) # 1. RSI
    ema20 = calc_ema(prices, 20) # 3. EMA20
    ema50 = calc_ema(prices, 50) # 3. EMA50
    vwap = sum(prices[-20:]) / 20 # 4. VWAP
    bb_mid = sum(prices[-20:]) / 20 # 5. BB
    bb_std = (sum((p - bb_mid)**2 for p in prices[-20:]) / 20) ** 0.5
    bb_lower = bb_mid - 2 * bb_std
    macd = calc_ema(prices, 12) - calc_ema(prices, 26) # 2. MACD
    atr = max(prices[-14:]) - min(prices[-14:]) # 8. ATR

    score = 0
    if rsi < 30: score += 2
    if rsi > 70: score -= 2
    if macd > 0: score += 2
    if ema20 > ema50: score += 2
    if current_price > vwap: score += 1
    if current_price < bb_lower: score += 2
    if current_price > ema50: score += 1

    if score >= 5: signal, color = "🟢 ПОКУПАТЬ СИЛЬНО", "#00ff88"
    elif score >= 2: signal, color = "🟢 ПОКУПАТЬ", "#66ff66"
    elif score <= -5: signal, color = "🔴 ПРОДАВАТЬ СИЛЬНО", "#ff4444"
    elif score <= -2: signal, color = "🔴 ПРОДАВАТЬ", "#ff6666"
    else: signal, color = "🟡 ЖДАТЬ", "#ffaa00"

    return current_price, rsi, ema20, ema50, macd, atr, signal, color, score

# --- 3. ЛИБАСИ САЙТ ---
HTML = '''
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Signals PRO</title>
<style>
body{background:#0a0a0a;color:#fff;font-family:Arial;text-align:center;padding:15px}
.card{background:#1a1a1a;margin:15px auto;padding:20px;border-radius:15px;max-width:420px;border:2px solid #00ff88}
h1{color:#00ff88}.price{font-size:36px;font-weight:bold;margin:10px 0;color:#00ff88}
.signal{font-size:22px;font-weight:bold;padding:15px;border-radius:10px;margin:10px 0}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;text-align:left;margin:15px 0;font-size:14px}
.stat{background:#222;padding:8px;border-radius:6px}
button{background:#00ff88;color:#000;border:none;padding:10px 18px;border-radius:8px;font-weight:bold;margin:4px;cursor:pointer}
</style></head><body>
<h1>🤖 AI Signals PRO v8.0</h1>
<div class="card">
    <h2>{{coin}}</h2>
    <div class="price">${{price:.2f}}</div>
    <div class="signal" style="background:{{color}};color:#000">{{signal}} | Score: {{score}}/10</div>
    <div class="stats">
        <div class="stat">RSI 14: {{rsi:.1f}}</div>
        <div class="stat">MACD: {{macd:.2f}}</div>
        <div class="stat">EMA20: {{ema20:.2f}}</div>
        <div class="stat">EMA50: {{ema50:.2f}}</div>
        <div class="stat">ATR 14: {{atr:.2f}}</div>
        <div class="stat">Trend: {% if ema20 > ema50 %}BULL{% else %}BEAR{% endif %}</div>
    </div>
    <form method="get">
        <button name="coin" value="BTC">BTC</button>
        <button name="coin" value="ETH">ETH</button>
        <button name="coin" value="TRX">TRX</button>
        <button name="coin" value="SOL">SOL</button>
        <button name="coin" value="LTC">LTC</button>
    </form>
</div></body></html>
'''

@app.route('/')
def home():
    coin = request.args.get('coin', 'BTC')
    price, rsi, ema20, ema50, macd, atr, signal, color, score = get_signal(coin)
    return render_template_string(HTML, coin=coin, price=price, rsi=rsi, ema20=ema20, ema50=ema50, macd=macd, atr=atr, signal=signal, color=color, score=score)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)