# KJG CPC Slack Bot

FuiouPay 웹사이트에서 가맹점들의 CPC 잔액을 자동으로 크롤링하여 Slack 채널로 전송하는 서비스입니다.

## 기능

- 매일 오전 9시(한국시간)에 자동으로 FuiouPay에 로그인
- **모든 페이지의 가맹점 데이터를 완전히 수집** (현재 50개 가맹점, 3페이지)
- **신규 가맹점 자동 감지 및 알림**
- Slack의 `#kjg_cpcbalance` 채널로 결과 전송
- CPC 잔액 보유 가맹점과 소진완료 가맹점을 구분하여 보고
- 신규 가맹점은 🆕 이모지로 표시

## 설정

### 환경 변수

Render에서 다음 환경 변수를 설정해야 합니다:

- `SLACK_BOT_TOKEN`: Slack Bot Token (필수)

### 로그인 정보

현재 설정된 로그인 정보:
- 아이디: `E20250124156285`
- 비밀번호: `1234`

## 배포

### Render 배포

1. GitHub 저장소를 Render에 연결
2. `render.yaml` 파일을 사용하여 자동 배포
3. 환경 변수 `SLACK_BOT_TOKEN` 설정

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export SLACK_BOT_TOKEN="your_slack_bot_token"

# 실행
python cpcCrawl.py
```

## 파일 구조

- `cpcCrawl.py`: 메인 크롤링 스크립트
- `app.py`: Flask 웹 애플리케이션 (수동 실행용)
- `requirements.txt`: Python 의존성
- `Dockerfile`: Docker 컨테이너 설정
- `render.yaml`: Render 배포 설정

## 출력 형식

Slack 메시지 예시:
```
✅ (2024-01-25) CPC 잔액 현황

• 총 50개 가맹점 데이터 추출
• CPC 잔액 보유 가맹점: 13개
• 신규 가맹점: 2개

CPC 잔액 보유 가맹점 목록:
 - M1971요트투어: 4,920 RMB
 - 돔베돈: 3,000 RMB 🆕
 - 돈도칸 연동흑돼지 제주점: 2,881 RMB
 - 난드르바당: 2,491 RMB
 - 고국수: 2,140 RMB

CPC 잔액 소진완료 가맹점 목록:
 - 한라오름
 - 뒤뜰에한우
 - 크로엔젤 🆕

신규 가맹점 목록:
 - 돔베돈
 - 크로엔젤
```

## 주요 개선사항

- **전체 페이지 크롤링**: 모든 페이지를 자동으로 순회하여 완전한 데이터 수집
- **신규 가맹점 감지**: 기존 데이터와 비교하여 신규 가맹점 자동 감지
- **안정적인 페이지 이동**: JavaScript를 사용한 안정적인 페이지 네비게이션
- **상세한 로깅**: 각 페이지별 추출 현황을 상세히 기록 