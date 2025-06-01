import os
import hashlib, hmac, time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 기본 루트 라우트 추가 → Render 헬스체크 통과 목적
@app.route('/')
def index():
    return 'Webhook server is running.'

# 환경 변수에서 API 키 읽기
API_KEY = os.environ.get('API_KEY')
API_SECRET = os.environ.get('API_SECRET')

if not API_KEY or not API_SECRET:
    print("❌ ERROR: API_KEY or API_SECRET is not set.")
    exit(1)

BINANCE_API_URL = "https://api.binance.com/api/v3/order"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    symbol = data.get('symbol')
    action = data.get('action')
    amount = data.get('amount')

    if not symbol or not action or amount is None:
        return jsonify({"error": "Missing required fields (symbol/action/amount)"}), 400

    side = 'BUY' if str(action).lower() == 'buy' else 'SELL'

    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": amount,
        "timestamp": timestamp
    }

    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    headers = {"X-MBX-APIKEY": API_KEY}
    try:
        response = requests.post(f"{BINANCE_API_URL}?{query_string}&signature={signature}", headers=headers)
        result = response.json()
        print("✅ Binance API response:", result)
    except Exception as e:
        print("❌ Error during Binance API request:", e)
        return jsonify({"error": "Failed to place order to Binance"}), 500

    return jsonify({"status": "success", "binance_order": result}), 200

# 반드시 Render가 지정한 포트로 실행
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
