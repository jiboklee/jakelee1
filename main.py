import os
import hashlib, hmac, time
import requests  # Binance API 호출을 위해 requests 사용
from flask import Flask, request, jsonify

app = Flask(__name__)

# 환경 변수에서 API 키 읽기 (없으면 None 반환)
API_KEY = os.environ.get('API_KEY')
API_SECRET = os.environ.get('API_SECRET')

# 환경 변수 확인: 없을 경우 오류 로그 및 기본값 처리
if not API_KEY or not API_SECRET:
    print("ERROR: API_KEY or API_SECRET is not set. Please configure environment variables.")
    # 필요한 경우 기본값 설정 (빈 문자열) - Binance 호출 시 오류 예상됨
    API_KEY = API_KEY or ""
    API_SECRET = API_SECRET or ""

# Binance API URL 설정 (선물 시장의 경우 fapi, 현물은 api)
BINANCE_API_URL = "https://api.binance.com/api/v3/order"  # 현물 시장 API 예시 엔드포인트
# 만약 선물 시장 롱/숏 포지션 진입을 의도한다면:
# BINANCE_API_URL = "https://fapi.binance.com/fapi/v1/order"

@app.route('/webhook', methods=['POST'])
def webhook():
    # 1) 웹훅 JSON 데이터 파싱
    data = request.get_json()
    if not data:
        # 유효한 JSON이 아니거나 Content-Type 문제가 있는 경우
        return jsonify({"error": "Invalid JSON payload"}), 400

    # 2) 필수 데이터 추출
    symbol = data.get('symbol')
    action = data.get('action')
    amount = data.get('amount')  # 수량 (예: 코인 수량 또는 USD 기준 수량)

    # 3) 필드 검증
    if not symbol or not action or amount is None:
        return jsonify({"error": "Missing required fields (symbol/action/amount)"}), 400

    # 4) 매매 동작에 따라 매수/매도 결정 (롱=매수, 숏=매도)
    side = 'BUY' if str(action).lower() == 'buy' else 'SELL'

    # 5) Binance 주문 요청 파라미터 및 서명 생성
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",       # 시장가 주문 (예시)
        "quantity": amount,     # 주문 수량
        "timestamp": timestamp
    }
    # 쿼리 문자열 생성 ("key=value&..." 형식)
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    # HMAC SHA256 서명 (환경 변수 키 사용)
    signature = ""
    if API_SECRET:
        signature = hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    else:
        # API_SECRET가 설정되어 있지 않으면 주문 진행 중단
        return jsonify({"error": "API secret key not configured"}), 500

    # 6) Binance API로 주문 요청 보내기
    headers = {"X-MBX-APIKEY": API_KEY}
    try:
        response = requests.post(f"{BINANCE_API_URL}?{query_string}&signature={signature}", headers=headers)
        result = response.json()  # Binance API의 응답 결과
        print("Binance API response:", result)  # 콘솔에 결과 출력 (로그용)
    except Exception as e:
        print("Error during Binance API request:", e)
        return jsonify({"error": "Failed to place order to Binance"}), 500

    # 7) TradingView에 성공 응답 전송 (200 OK)
    return jsonify({"status": "success", "binance_order": result}), 200

# Render 플랫폼에서는 PORT 환경변수를 통해 포트를 받아서 실행
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
