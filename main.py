from flask import Flask, render_template, request, jsonify
import subprocess
import os
import sys
import threading
import time
import schedule
from datetime import datetime

app = Flask(__name__)

# 크롤링 상태를 저장할 변수
crawler_status = {
    "is_running": False,
    "completed": False,
    "start_time": None,
    "end_time": None,
    "message": "",
    "has_error": False
}

# 스케줄링 작업 함수
def scheduled_job():
    """매일 오전 9시에 실행될 작업"""
    print(f"\n--- {datetime.now()}: 정기 CPC 잔액 크롤링 시작 ---")
    run_crawler_job()
    print(f"--- {datetime.now()}: 작업 완료. 다음 실행은 내일 아침 9시입니다. ---")

def run_crawler_job():
    """크롤러 작업 실행"""
    if crawler_status["is_running"]:
        print("크롤러가 이미 실행 중입니다.")
        return
    
    # 상태 초기화
    crawler_status["is_running"] = True
    crawler_status["completed"] = False
    crawler_status["start_time"] = time.time()
    crawler_status["end_time"] = None
    crawler_status["message"] = "크롤러가 실행 중입니다..."
    crawler_status["has_error"] = False
    
    try:
        # 현재 디렉토리에서 cpcCrawl.py 실행
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cpcCrawl.py')
        process = subprocess.Popen([sys.executable, script_path], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          text=True)
        
        # 프로세스 완료 대기
        stdout, stderr = process.communicate()
        
        # 완료 상태 업데이트
        crawler_status["is_running"] = False
        crawler_status["completed"] = True
        crawler_status["end_time"] = time.time()
        
        if process.returncode == 0:
            crawler_status["message"] = "크롤링이 성공적으로 완료되었습니다."
        else:
            crawler_status["message"] = f"크롤링 중 오류가 발생했습니다.\n{stderr}"
            crawler_status["has_error"] = True
            
    except Exception as e:
        crawler_status["is_running"] = False
        crawler_status["completed"] = True
        crawler_status["end_time"] = time.time()
        crawler_status["message"] = f"예상치 못한 오류: {e}"
        crawler_status["has_error"] = True

# 스케줄러 설정
def setup_scheduler():
    """스케줄러를 설정합니다."""
    
    def run_scheduler():
        last_run_date = None
        while True:
            now = datetime.now()
            current_date = now.date()
            
            # 한국시간 오전 9시 (UTC 00:00) 체크
            if now.hour == 0 and now.minute == 0:
                # 같은 날 중복 실행 방지
                if last_run_date != current_date:
                    print(f"\n--- {now}: 정기 CPC 잔액 크롤링 시작 ---")
                    run_crawler_job()
                    last_run_date = current_date
                    print(f"--- {now}: 작업 완료. 다음 실행은 내일 한국시간 오전 9시입니다. ---")
                    # 중복 실행 방지를 위해 1분 대기
                    time.sleep(60)
            
            time.sleep(30)  # 30초마다 확인
    
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("스케줄러가 시작되었습니다. 매일 한국시간 오전 9시(UTC 00:00)에 크롤링이 실행됩니다.")
    print(f"현재 시간: {datetime.now()}")
    print("스케줄러가 백그라운드에서 실행 중입니다...")

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
            button { background-color: #2196f3; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px; }
            button:hover { background-color: #1976d2; }
            button:disabled { background-color: #ccc; cursor: not-allowed; }
            .info { background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 KJG CPC Slack Bot</h1>
            
            <div class="info">
                <h3>서비스 정보</h3>
                <p><strong>기능:</strong> FuiouPay에서 CPC 잔액을 자동으로 크롤링하여 Slack으로 전송</p>
                <p><strong>실행 시간:</strong> 매일 오전 9시 (한국시간, UTC 00:00)</p>
                <p><strong>Slack 채널:</strong> #kjg_cpcbalance</p>
                <p><strong>가맹점 수:</strong> 50개 (3페이지)</p>
            </div>
            
            <div id="status" class="status">
                <h3>크롤러 상태</h3>
                <p id="statusMessage">확인 중...</p>
                <p id="statusDetails"></p>
            </div>
            
            <button onclick="runCrawler()" id="runBtn">수동 실행</button>
            <button onclick="checkStatus()" id="checkBtn">상태 확인</button>
            
            <div class="info">
                <h3>최근 실행 기록</h3>
                <p>서비스가 정상적으로 실행되고 있습니다. 매일 오전 9시에 자동으로 CPC 잔액을 확인하여 Slack으로 전송합니다.</p>
                <p><strong>마지막 실행:</strong> <span id="lastRun">확인 중...</span></p>
                <p><strong>다음 실행:</strong> 매일 오전 9시 (한국시간)</p>
            </div>
        </div>
        
        <script>
            function checkStatus() {
                fetch('/crawler_status')
                    .then(response => response.json())
                    .then(data => {
                        const statusDiv = document.getElementById('status');
                        const messageDiv = document.getElementById('statusMessage');
                        const detailsDiv = document.getElementById('statusDetails');
                        const runBtn = document.getElementById('runBtn');
                        
                        statusDiv.className = 'status';
                        
                        if (data.is_running) {
                            statusDiv.classList.add('running');
                            messageDiv.textContent = '🔄 크롤러가 실행 중입니다...';
                            runBtn.disabled = true;
                        } else if (data.completed) {
                            if (data.has_error) {
                                statusDiv.classList.add('error');
                                messageDiv.textContent = '❌ 크롤링 중 오류가 발생했습니다.';
                            } else {
                                statusDiv.classList.add('completed');
                                messageDiv.textContent = '✅ 크롤링이 완료되었습니다.';
                            }
                            runBtn.disabled = false;
                        } else {
                            messageDiv.textContent = '⏸️ 크롤러가 대기 중입니다.';
                            runBtn.disabled = false;
                        }
                        
                        if (data.message) {
                            detailsDiv.textContent = data.message;
                        }
                        
                        if (data.duration) {
                            detailsDiv.textContent += ` (소요시간: ${data.duration}초)`;
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('statusMessage').textContent = '❌ 상태 확인 중 오류가 발생했습니다.';
                    });
            }
            
            function runCrawler() {
                const runBtn = document.getElementById('runBtn');
                runBtn.disabled = true;
                runBtn.textContent = '실행 중...';
                
                fetch('/run_crawler', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            document.getElementById('statusMessage').textContent = '🚀 크롤러가 시작되었습니다.';
                            document.getElementById('status').className = 'status running';
                        } else {
                            document.getElementById('statusMessage').textContent = data.message;
                            runBtn.disabled = false;
                            runBtn.textContent = '수동 실행';
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('statusMessage').textContent = '❌ 크롤러 실행 중 오류가 발생했습니다.';
                        runBtn.disabled = false;
                        runBtn.textContent = '수동 실행';
                    });
            }
            
            // 페이지 로드 시 상태 확인
            checkStatus();
            
            // 30초마다 상태 확인
            setInterval(checkStatus, 30000);
        </script>
    </body>
    </html>
    """

@app.route('/run_crawler', methods=['POST'])
def run_crawler():
    # 이미 실행 중이면 메시지 반환
    if crawler_status["is_running"]:
        return jsonify({"status": "error", "message": "크롤러가 이미 실행 중입니다."})

    # 크롤러 작업을 별도 스레드에서 실행
    thread = threading.Thread(target=run_crawler_job)
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "success", "message": "크롤러가 백그라운드에서 실행 중입니다."})

@app.route('/crawler_status', methods=['GET'])
def get_crawler_status():
    duration = None
    if crawler_status["end_time"] and crawler_status["start_time"]:
        duration = round(crawler_status["end_time"] - crawler_status["start_time"])
    
    return jsonify({
        "is_running": crawler_status["is_running"],
        "completed": crawler_status["completed"],
        "message": crawler_status["message"],
        "has_error": crawler_status["has_error"],
        "duration": duration
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    # 스케줄러 시작
    setup_scheduler()
    
    # Render에서 포트를 환경 변수에서 가져오거나 기본값 사용
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 KJG CPC Slack Bot이 시작되었습니다. 포트: {port}")
    app.run(debug=False, host='0.0.0.0', port=port) 