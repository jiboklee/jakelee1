from flask import Flask, request, jsonify
import hmac
import hashlib
import time
import requests
import os

app = Flask(__name__)

# 🔐 환경변수에서 API 키 불러오기 (Render에서는 환경설정에 등록)
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# 바이낸스 URL
BASE_URL = "https://fapi.binance.com"

def place_order(symbol, side, quantity):
    try:
        # 바이낸스 파라미터 구성
        endpoint = "/fapi/v1/order"
        url = BASE_URL + endpoint

        timestamp = int(time.time() * 1000)
        params = f"symbol={symbol}&side={side.upper()}&type=MARKET&quantity={quantity}&timestamp={timestamp}"
        signature = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()

        final_url = f"{url}?{params}&signature={signature}"
        headers = {"X-MBX-APIKEY": API_KEY}

        response = requests.post(final_url, headers=headers)
        return response.json()
    except Exception as e:
        print("🚨 주문 실패:", str(e))
        return {"error": str(e)}

@app.route('/')
def home():
    return "✅ Binance Futures Auto Trade Server Running"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        if not data:
            return "⚠️ No JSON received", 400

        symbol = data.get('symbol')
        action = data.get('action')  # long 또는 short
        amount = float(data.get('amount', 0))

        if not all([symbol, action, amount]):
            return "⚠️ Missing one or more required fields", 400

        # 롱/숏 구분
        side = "BUY" if action.lower() == "long" else "SELL"
        result = place_order(symbol.upper(), side, amount)

        print(f"📤 주문 요청: {symbol} | {action} | {amount}")
        print("📥 응답:", result)

        return jsonify(result)

    except Exception as e:
        print("❌ 오류 발생:", str(e))
        return str(e), 500

if __name__ == '__main__':
    app.run()
