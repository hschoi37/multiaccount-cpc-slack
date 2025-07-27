import os
import sys
import threading
import time
from datetime import datetime
import schedule

# cpcCrawl.py의 크롤링 함수들을 직접 import
from cpcCrawl import run_crawler, send_slack_notification, SLACK_BOT_TOKEN

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
        print("크롤링 작업을 시작합니다...")
        # cpcCrawl.py의 run_crawler 함수 직접 호출
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
    print("스케줄러가 백그라운드에서 실행 중입니다...")
    print("서비스 버전: v1.4 - Direct Import 모드로 변경")

if __name__ == '__main__':
    # 환경 변수 확인 및 디버깅
    print(f"환경 변수 확인 중...")
    
    # 직접 os.getenv로 확인
    direct_token = os.getenv("SLACK_BOT_TOKEN")
    print(f"os.getenv('SLACK_BOT_TOKEN') 존재 여부: {bool(direct_token)}")
    print(f"os.getenv('SLACK_BOT_TOKEN') 길이: {len(direct_token) if direct_token else 0}")
    print(f"os.getenv('SLACK_BOT_TOKEN') 시작 부분: {direct_token[:10] if direct_token else 'None'}...")
    
    # import된 변수 확인
    print(f"import된 SLACK_BOT_TOKEN 존재 여부: {bool(SLACK_BOT_TOKEN)}")
    print(f"import된 SLACK_BOT_TOKEN 길이: {len(SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else 0}")
    print(f"import된 SLACK_BOT_TOKEN 시작 부분: {SLACK_BOT_TOKEN[:10] if SLACK_BOT_TOKEN else 'None'}...")
    
    # 모든 환경 변수 출력 (디버깅용)
    print(f"모든 환경 변수:")
    for key, value in os.environ.items():
        if 'SLACK' in key or 'TOKEN' in key:
            print(f"  {key}: {value[:10] if value else 'None'}...")
    
    if not SLACK_BOT_TOKEN:
        print("!!! 치명적 오류: 필수 환경변수(SLACK_BOT_TOKEN)가 설정되지 않았습니다. !!!")
        print("Railway의 Variables 탭에서 변수들이 올바르게 설정되었는지 확인해주세요.")
        sys.exit(1)
    
    # 스케줄러 시작
    setup_scheduler()
    
    # Background Worker 모드: 무한 루프로 실행
    print("🚀 KJG CPC Slack Bot (Background Worker)이 시작되었습니다.")
    print("매일 한국시간 오전 10시에 자동으로 CPC 잔액을 확인하여 Slack으로 전송합니다.")
    
    # 시작 알림 전송
    try:
        send_slack_notification("🚀 KJG CPC Slack Bot이 Railway에서 시작되었습니다!")
        print("시작 알림을 Slack으로 전송했습니다.")
    except Exception as e:
        print(f"시작 알림 전송 실패: {e}")
        print(f"오류 타입: {type(e)}")
        print(f"오류 상세: {str(e)}")
    
    # 메인 스레드 유지
    try:
        while True:
            time.sleep(60)  # 1분마다 체크
    except KeyboardInterrupt:
        print("서비스가 종료됩니다.") 