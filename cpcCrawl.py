from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import os
from datetime import datetime
import schedule
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import sys

# --- 설정 ---
# 슬랙 설정
# 중요: 이 값들은 Railway의 Variables 탭에서 설정합니다.
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "#htag_cpcbalance"

# 엑셀/CSV 파일 경로 설정
EXCEL_FILE = "merchant_cpc_data.xlsx"
CSV_FILE = "merchant_cpc_data.csv"

# FuiouPay 인증 정보
# 중요: 이 값들은 Railway의 Variables 탭에서 설정합니다.
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# --- 슬랙 메시지 전송 함수 ---
def send_slack_notification(message):
    """주어진 메시지를 슬랙 채널로 전송합니다."""
    client = WebClient(token=SLACK_BOT_TOKEN)
    try:
        client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print("슬랙 메시지 전송 성공")
    except SlackApiError as e:
        print(f"슬랙 메시지 전송 실패: {e.response['error']}")


# --- 메인 크롤링 함수 ---
def run_crawler():
    """웹사이트를 크롤링하여 CPC 데이터를 추출하고, 결과를 요약하여 슬랙으로 전송합니다."""
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Chrome 옵션 설정 (Headless 모드 포함)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        # 1. 로그인
        print("로그인 페이지로 이동 중...")
        driver.get("https://web.fuioupay.co.kr/login?returnUrl=/index")
        time.sleep(3)
        
        print("로그인 시도...")
        driver.execute_script(f'document.getElementById("username").value = "{USERNAME}";')
        driver.execute_script(f'document.getElementById("password").value = "{PASSWORD}";')
        driver.execute_script('document.getElementById("btn-login").click();')
        time.sleep(5)

        if "login" in driver.current_url:
            raise Exception("로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.")
        
        # 2. 계약 페이지로 이동
        print("계약 페이지로 이동 중...")
        driver.get("https://web.fuioupay.co.kr/agent/dianping/contracts")
        time.sleep(5)
        
        if "contracts" not in driver.current_url:
            raise Exception(f"계약 페이지로 이동하지 못했습니다. 현재 URL: {driver.current_url}")
            
        print("계약 페이지 접속 완료, 데이터 추출 시작...")
        
        # 3. 데이터 추출
        all_merchant_data = []
        current_page = 1
        has_next_page = True
        
        while has_next_page:
            print(f"\n==== {current_page}번 페이지 데이터 추출 중 ====")
            wait = WebDriverWait(driver, 10)
            table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows[1:]: # 헤더 제외
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 6:
                    merchant_name = cells[2].text
                    cpc_balance = cells[5].text.replace(",", "")
                    all_merchant_data.append({
                        "가맹점명": merchant_name,
                        "CPC잔액": cpc_balance,
                        "페이지": current_page,
                        "추출날짜": current_date
                    })
            
            # 4. 다음 페이지로 이동
            try:
                pagination = driver.find_element(By.CLASS_NAME, "pagination")
                next_page_link = pagination.find_element(By.XPATH, f".//a[contains(text(), '{current_page + 1}')]")
                next_page_link.click()
                current_page += 1
                time.sleep(3)
            except:
                print("다음 페이지가 없습니다. 데이터 추출을 종료합니다.")
                has_next_page = False
                
        # 5. 데이터 처리 및 저장
        if not all_merchant_data:
            summary_message = f"✅ ({current_date}) CPC 잔액 데이터 없음\n\n추출된 데이터가 없습니다."
            print(summary_message)
            send_slack_notification(summary_message)
            return

        current_df = pd.DataFrame(all_merchant_data)
        df_to_save = current_df

        if os.path.exists(EXCEL_FILE):
            try:
                existing_df = pd.read_excel(EXCEL_FILE)
                combined_df = pd.concat([existing_df, current_df])
                combined_df['중복키'] = combined_df['가맹점명'] + '_' + combined_df['추출날짜']
                combined_df = combined_df.drop_duplicates(subset=['중복키'], keep='last').drop('중복키', axis=1)
                df_to_save = combined_df.sort_values(by=['추출날짜', '가맹점명'], ascending=[False, True])
            except Exception as e:
                print(f"기존 엑셀 파일 처리 오류: {e}. 새 데이터로 덮어씁니다.")

        # 파일 저장
        df_to_save.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
        df_to_save.to_excel(EXCEL_FILE, index=False, sheet_name="가맹점CPC잔액")
        print(f"총 {len(df_to_save)}개의 데이터를 파일에 저장했습니다.")
        
        # 6. 슬랙 메시지 생성 및 전송
        today_data = df_to_save[df_to_save['추출날짜'] == current_date]
        with_balance = today_data[pd.to_numeric(today_data['CPC잔액']) > 0]

        summary_message = (
            f"✅ *({current_date}) CPC 잔액 추출 완료*\n\n"
            f"• 총 {len(today_data)}개 가맹점 데이터 추출\n"
            f"• CPC 잔액 보유 가맹점: *{len(with_balance)}개*\n\n"
            "*CPC 잔액 보유 가맹점 목록:*\n"
        )
        
        if not with_balance.empty:
            sorted_balance = with_balance.sort_values(by='CPC잔액', key=pd.to_numeric, ascending=False)
            for _, row in sorted_balance.iterrows():
                summary_message += f" - {row['가맹점명']}: {int(float(row['CPC잔액'])):,} RMB\n"
        else:
            summary_message += " - 없음\n"
            
        send_slack_notification(summary_message)

    except Exception as e:
        print(f"오류 발생: {e}")
        error_message = f"❌ *CPC 잔액 크롤링 중 오류 발생* ❌\n\n`{e}`"
        send_slack_notification(error_message)
        driver.save_screenshot("error_screenshot.png")
        print("에러 스크린샷을 'error_screenshot.png'에 저장했습니다.")

    finally:
        print("크롤러를 종료합니다.")
        driver.quit()

# --- 스케줄링 작업 함수 ---
def job():
    """스케줄러에 의해 실행될 작업"""
    print(f"\n--- {datetime.now()}: 정기 CPC 잔액 크롤링 시작 ---")
    run_crawler()
    print(f"--- {datetime.now()}: 작업 완료. 다음 실행은 내일 아침 8시입니다. ---")

# --- 메인 실행 블록 ---
if __name__ == "__main__":
    # 프로그램 시작 시 가장 먼저 환경 변수를 확인합니다.
    if not all([SLACK_BOT_TOKEN, USERNAME, PASSWORD]):
        print("!!! 치명적 오류: 필수 환경변수(SLACK_BOT_TOKEN, USERNAME, PASSWORD)가 설정되지 않았습니다. !!!")
        print("Railway의 Variables 탭에서 변수들이 올바르게 설정되었는지 확인해주세요.")
        # 에러 로그를 남기고 비정상 종료 (코드를 1로 설정)
        sys.exit(1)
        
    print("🚀 CPC 잔액 자동 크롤러가 시작되었습니다.")
    send_slack_notification("🚀 CPC 잔액 자동 크롤러가 시작되었습니다.")

    # 매일 오전 8시에 job 함수를 실행하도록 스케줄 설정
    schedule.every().day.at("08:00").do(job)
    
    # 프로그램 시작 시 1회 즉시 실행 (테스트용)
    print(">> 프로그램 시작 기념으로 작업을 1회 즉시 실행합니다...")
    job()

    while True:
        schedule.run_pending()
        time.sleep(60) # 1분마다 다음 작업 시간을 확인
