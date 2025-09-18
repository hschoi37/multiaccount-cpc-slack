import os
import sys
import threading
import time
from datetime import datetime
from flask import Flask, jsonify
import schedule

# Flask 앱 생성
app = Flask(__name__)

# cpcCrawl.py의 크롤링 함수들을 직접 import
from cpcCrawl import run_crawler, send_slack_notification

# 환경 변수 직접 가져오기 (여러 이름 시도)
def get_slack_token():
    """Slack 토큰을 여러 방법으로 시도하여 가져옵니다."""
    possible_names = [
        "SLACK_TOKEN",
        "SLACK_BOT_TOKEN", 
        "BOT_TOKEN",
        "TOKEN"
    ]
    
    for name in possible_names:
        token = os.getenv(name)
        if token:
            print(f"토큰 발견: {name}")
            return token
    
    return None

# 크롤링 상태를 저장할 변수
crawler_status = {
    "is_running": False,
    "completed": False,
    "start_time": None,
    "end_time": None,
    "message": "",
    "has_error": False
}

# 계정 정보 리스트
accounts = [
    {
        "name": "kjg",
        "username": "E20250124156285",
        "password": "1234",
        "slack_channel": "#kjg_cpcbalance",
        "excel_file": "merchant_cpc_data_kjg.xlsx",
        "csv_file": "merchant_cpc_data_kjg.csv"
    },
    {
        "name": "htag",
        "username": "E20240626154518",
        "password": "1234",
        "slack_channel": "#htag_cpcbalance",
        "excel_file": "merchant_cpc_data_htag.xlsx",
        "csv_file": "merchant_cpc_data_htag.csv"
    },
    {
        "name": "gpr",
        "username": "E20250124156283",
        "password": "1234",
        "slack_channel": "#gpr_cpcbalance",
        "excel_file": "merchant_cpc_data_gpr.xlsx",
        "csv_file": "merchant_cpc_data_gpr.csv"
    },
    {
        "name": "smd",
        "username": "E20220210100006",
        "password": "1234",
        "slack_channel": "#smd_cpcbalance",
        "excel_file": "merchant_cpc_data_smd.xlsx",
        "csv_file": "merchant_cpc_data_smd.csv"
    },
    {
        "name": "zen",
        "username": "E20250124156292",
        "password": "1234",
        "slack_channel": "#zen_cpcbalance",
        "excel_file": "merchant_cpc_data_zen.xlsx",
        "csv_file": "merchant_cpc_data_zen.csv"
    }
]

def run_crawler_job():
    """모든 계정에 대해 크롤러 작업 실행"""
    if crawler_status["is_running"]:
        print("크롤러가 이미 실행 중입니다.")
        return
    crawler_status["is_running"] = True
    crawler_status["completed"] = False
    crawler_status["start_time"] = time.time()
    crawler_status["end_time"] = None
    crawler_status["message"] = "크롤러가 실행 중입니다..."
    crawler_status["has_error"] = False
    try:
        print("크롤링 작업을 시작합니다...")
        for acc in accounts:
            print(f"\n==== [{acc['name']}] 계정 크롤링 시작 ====")
            from cpcCrawl import run_crawler
            run_crawler(
                acc["username"],
                acc["password"],
                slack_token,
                acc["slack_channel"],
                acc["excel_file"],
                acc["csv_file"]
            )
        crawler_status["is_running"] = False
        crawler_status["completed"] = True
        crawler_status["end_time"] = time.time()
        crawler_status["message"] = "모든 계정 크롤링이 성공적으로 완료되었습니다."
        print("모든 계정 크롤링이 성공적으로 완료되었습니다.")
    except Exception as e:
        crawler_status["is_running"] = False
        crawler_status["completed"] = True
        crawler_status["end_time"] = time.time()
        crawler_status["message"] = f"예상치 못한 오류: {e}"
        crawler_status["has_error"] = True
        print(f"예상치 못한 오류: {e}")

# 스케줄러 설정
def setup_scheduler():
    """스케줄러를 설정합니다."""
    # schedule 라이브러리를 사용한 더 안정적인 스케줄링
    # 한국시간 오전 9시 = UTC 00:00 (한국은 UTC+9)
    schedule.every().day.at("00:00").do(run_crawler_job)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 스케줄 확인
    
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("스케줄러가 시작되었습니다. 매일 한국시간 오전 9시(UTC 00:00)에 크롤링이 실행됩니다.")
    print(f"현재 시간: {datetime.now()}")
    print("다음 예정된 실행:", schedule.next_run())

# Flask 라우트 정의
@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>KJG CPC Slack Bot</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .status { padding: 15px; margin: 20px 0; border-radius: 5px; }
            .status.running { background-color: #e3f2fd; border: 1px solid #2196f3; }
            .status.completed { background-color: #e8f5e8; border: 1px solid #4caf50; }
            .status.error { background-color: #ffebee; border: 1px solid #f44336; }
            .info { background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 KJG CPC Slack Bot</h1>
            
            <div class="info">
                <h3>서비스 정보</h3>
                <p><strong>기능:</strong> FuiouPay에서 CPC 잔액을 자동으로 크롤링하여 Slack으로 전송</p>
                <p><strong>실행 시간:</strong> 매일 한국시간 오전 9시 (UTC 00:00)</p>
                <p><strong>계정 수:</strong> 5개 (kjg, htag, gpr, smd, zen)</p>
                <p><strong>상태:</strong> 정상 실행 중</p>
            </div>
            
            <div class="info">
                <h3>최근 실행 기록</h3>
                <p>서비스가 정상적으로 실행되고 있습니다. 매일 한국시간 오전 9시에 자동으로 CPC 잔액을 확인하여 Slack으로 전송합니다.</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "KJG CPC Slack Bot",
        "crawler_status": crawler_status
    })

@app.route('/status')
def status():
    return jsonify(crawler_status)

@app.route('/run-now')
def run_now():
    """수동으로 크롤링을 실행하는 엔드포인트"""
    if crawler_status["is_running"]:
        return jsonify({
            "status": "error",
            "message": "크롤러가 이미 실행 중입니다."
        })
    
    # 별도 스레드에서 실행
    threading.Thread(target=run_crawler_job).start()
    return jsonify({
        "status": "success", 
        "message": "크롤링 작업이 시작되었습니다."
    })

if __name__ == '__main__':
    print("🚀 KJG CPC Slack Bot 시작 중...")
    
    # 환경 변수 확인
    slack_token = get_slack_token()
    if not slack_token:
        print("❌ SLACK_TOKEN 환경 변수가 설정되지 않았습니다.")
        print("Railway Variables에서 SLACK_TOKEN을 설정해주세요.")
        sys.exit(1)
    
    print(f"✅ 토큰 확인 완료: {slack_token[:10]}...")
    
    # 스케줄러 시작
    setup_scheduler()
    
    # 시작 알림 전송 (모든 계정별 채널에)
    try:
        from cpcCrawl import send_slack_notification
        for acc in accounts:
            send_slack_notification(f"🚀 {acc['name'].upper()} CPC Slack Bot이 Railway에서 시작되었습니다!", slack_token, acc["slack_channel"])
        print("✅ 시작 알림을 Slack으로 전송했습니다.")
    except Exception as e:
        print(f"❌ 시작 알림 전송 실패: {e}")
    
    print("🚀 KJG CPC Slack Bot이 정상적으로 시작되었습니다.")
    print("매일 한국시간 오전 9시에 자동으로 모든 계정의 CPC 잔액을 확인하여 Slack으로 전송합니다.")
    
    # 테스트용 즉시 실행 코드는 제거됨 (정기 스케줄링만 사용)
    
    # Flask 서버 시작 (Railway 헬스체크용)
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 웹 서버가 포트 {port}에서 시작됩니다.")
    app.run(debug=False, host='0.0.0.0', port=port) 