from flask import Flask, request, jsonify
import requests
import hmac
import hashlib
import time
import os

app = Flask(__name__)

# 바이낸스 API 키 (직접 입력하거나 Render 환경변수로 설정)
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

BASE_URL = 'https://fapi.binance.com'  # 선물 API endpoint

# 시그니처 생성 함수
def create_signature(query_string):
    return hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()

# 실제 바이낸스 주문 전송 함수
def place_order(symbol, side, quantity):
    path = '/fapi/v1/order'
    timestamp = int(time.time() * 1000)

    params = {
        'symbol': symbol.upper(),
        'side': 'BUY' if side.lower() == 'long' else 'SELL',
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': timestamp
    }

    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = create_signature(query_string)
    params['signature'] = signature

    headers = {
        'X-MBX-APIKEY': API_KEY
    }

    response = requests.post(BASE_URL + path, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(response.text)

@app.route('/')
def home():
    return '🔥 Binance Futures Auto Trader is Running!'

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("📩 Webhook received:", data)

        symbol = data.get('symbol')
        action = data.get('action')  # "long" or "short"
        amount = float(data.get('amount'))

        if not symbol or not action or not amount:
            raise ValueError("Missing required field(s)")

        result = place_order(symbol, action, amount)
        print("✅ Order success:", result)
        return jsonify({'status': 'success', 'order': result})

    except Exception as e:
        print("❌ Error occurred:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
