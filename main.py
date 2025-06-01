# main.py
from flask import Flask, request
import hmac, hashlib, time, requests, os

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    symbol = data['symbol']
    side = data['action'].upper()
    amount = 30  # USDT 고정

    order = place_order(symbol, side, amount)
    return {'status': 'ok', 'detail': order}

def place_order(symbol, side, amount_usdt):
    url = 'https://fapi.binance.com/fapi/v1/order'
    timestamp = int(time.time() * 1000)
    price = get_price(symbol)
    quantity = round(amount_usdt / price, 3)

    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': timestamp
    }

    query = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature
    headers = {"X-MBX-APIKEY": API_KEY}

    res = requests.post(url, params=params, headers=headers)
    return res.json()

def get_price(symbol):
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
    res = requests.get(url)
    return float(res.json()['price'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
