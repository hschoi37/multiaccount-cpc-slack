import os
import sys
import subprocess
import threading
import time
from datetime import datetime

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
    """매일 오전 10시에 실행될 작업"""
    print(f"\n--- {datetime.now()}: 정기 CPC 잔액 크롤링 시작 ---")
    run_crawler_job()
    print(f"--- {datetime.now()}: 작업 완료. 다음 실행은 내일 한국시간 오전 10시입니다. ---")

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
            print("크롤링이 성공적으로 완료되었습니다.")
        else:
            crawler_status["message"] = f"크롤링 중 오류가 발생했습니다.\n{stderr}"
            crawler_status["has_error"] = True
            print(f"크롤링 중 오류가 발생했습니다.\n{stderr}")
            
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
    def run_scheduler():
        last_run_date = None
        while True:
            now = datetime.now()
            current_date = now.date()
            
            # 한국시간 오전 10시 (UTC 01:00) 체크
            if now.hour == 1 and now.minute == 0:
                # 같은 날 중복 실행 방지
                if last_run_date != current_date:
                    print(f"\n--- {now}: 정기 CPC 잔액 크롤링 시작 ---")
                    run_crawler_job()
                    last_run_date = current_date
                    print(f"--- {now}: 작업 완료. 다음 실행은 내일 한국시간 오전 10시입니다. ---")
                    # 중복 실행 방지를 위해 1분 대기
                    time.sleep(60)
            time.sleep(30)  # 30초마다 확인
    
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("스케줄러가 시작되었습니다. 매일 한국시간 오전 10시(UTC 01:00)에 크롤링이 실행됩니다.")
    print(f"현재 시간: {datetime.now()}")
    print("스케줄러가 백그라운드에서 실행 중입니다...")
    print("서비스 버전: v1.3 - Background Worker 모드로 변경")

if __name__ == '__main__':
    # 스케줄러 시작
    setup_scheduler()
    
    # Background Worker 모드: 무한 루프로 실행
    print("🚀 KJG CPC Slack Bot (Background Worker)이 시작되었습니다.")
    print("매일 한국시간 오전 10시에 자동으로 CPC 잔액을 확인하여 Slack으로 전송합니다.")
    
    # 메인 스레드 유지
    try:
        while True:
            time.sleep(60)  # 1분마다 체크
    except KeyboardInterrupt:
        print("서비스가 종료됩니다.") 