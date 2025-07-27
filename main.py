import os
import sys
import threading
import time
from datetime import datetime

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
        print("크롤링 작업을 시작합니다...")
        run_crawler()
        
        # 완료 상태 업데이트
        crawler_status["is_running"] = False
        crawler_status["completed"] = True
        crawler_status["end_time"] = time.time()
        crawler_status["message"] = "크롤링이 성공적으로 완료되었습니다."
        print("크롤링이 성공적으로 완료되었습니다.")
            
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
    
    # 시작 알림 전송
    try:
        send_slack_notification("🚀 KJG CPC Slack Bot이 Railway에서 시작되었습니다!")
        print("✅ 시작 알림을 Slack으로 전송했습니다.")
    except Exception as e:
        print(f"❌ 시작 알림 전송 실패: {e}")
    
    print("🚀 KJG CPC Slack Bot이 정상적으로 시작되었습니다.")
    print("매일 한국시간 오전 10시에 자동으로 CPC 잔액을 확인하여 Slack으로 전송합니다.")
    
    # 즉시 크롤링 실행 (테스트용)
    print("🔍 즉시 크롤링을 실행합니다...")
    try:
        run_crawler_job()
        print("✅ 즉시 크롤링이 완료되었습니다.")
    except Exception as e:
        print(f"❌ 즉시 크롤링 실패: {e}")
    
    # 메인 스레드 유지
    try:
        while True:
            time.sleep(60)  # 1분마다 체크
    except KeyboardInterrupt:
        print("서비스가 종료됩니다.") 