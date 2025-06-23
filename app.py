from flask import Flask, render_template, request, jsonify
import subprocess
import os
import sys
import threading
import time

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_crawler', methods=['POST'])
def run_crawler():
    # 이미 실행 중이면 메시지 반환
    if crawler_status["is_running"]:
        return jsonify({"status": "error", "message": "크롤러가 이미 실행 중입니다."})

    # 상태 초기화
    crawler_status["is_running"] = True
    crawler_status["completed"] = False
    crawler_status["start_time"] = time.time()
    crawler_status["end_time"] = None
    crawler_status["message"] = "크롤러가 실행 중입니다..."
    crawler_status["has_error"] = False
    
    # 크롤러 스크립트 실행을 별도 스레드에서 실행
    def run_script():
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
                # 엑셀 파일 경로 추가
                excel_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'merchant_cpc_data.xlsx')
                if os.path.exists(excel_file):
                    crawler_status["message"] += f"\n데이터가 '{excel_file}' 파일에 저장되었습니다."
            else:
                crawler_status["message"] = f"크롤링 중 오류가 발생했습니다.\n{stderr}"
                crawler_status["has_error"] = True
                
        except Exception as e:
            crawler_status["is_running"] = False
            crawler_status["completed"] = True
            crawler_status["end_time"] = time.time()
            crawler_status["message"] = f"예상치 못한 오류: {e}"
            crawler_status["has_error"] = True
    
    # 스레드 시작
    thread = threading.Thread(target=run_script)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 