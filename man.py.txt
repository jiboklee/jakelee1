from flask import Flask, request, jsonify
import hmac
import hashlib
import time
import requests

app = Flask(__name__)

# --- 바이낸스 API 설정 (선물 전용) ---
BINANCE_API_KEY = "여기에_본인_API"
BINANCE_SECRET = "여기에_본인_SECRET"
BASE_URL = "https://fapi.binance.com"

# --- 진입 파라미터 ---
SYMBOL = "BTCUSDT"  # 또는 ETHUSDT 등 원하는 종목
QUANTITY = 0.01      # 진입 수량 (레버리지 고려해서 설정)


def get_headers(query_string):
    timestamp = int(time.time() * 1000)
    query_string += f"&timestamp={timestamp}"
    signature = hmac.new(BINANCE_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }
    return query_string + f"&signature={signature}", headers


def place_futures_order(side):
    query = f"symbol={SYMBOL}&side={side}&type=MARKET&quantity={QUANTITY}"
    signed_query, headers = get_headers(query)
    url = f"{BASE_URL}/fapi/v1/order?{signed_query}"
    res = requests.post(url, headers=headers)
    print(res.json())
    return res.json()


@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    signal = data.get("signal", "")

    if signal == "LONG_SIGNAL":
        result = place_futures_order("BUY")
        return jsonify({"result": result}), 200
    elif signal == "SHORT_SIGNAL":
        result = place_futures_order("SELL")
        return jsonify({"result": result}), 200
    else:
        return jsonify({"error": "Unknown signal"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
