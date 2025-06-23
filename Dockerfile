# 1. 베이스 이미지: Python 3.12를 포함한 가벼운 Debian 이미지
FROM python:3.12-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. Google Chrome 설치에 필요한 패키지 및 Chrome 브라우저 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chrome에 필요한 라이브러리들
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    # Chrome 다운로드를 위한 wget
    wget \
    # Chrome 설치
    && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install \
    # 설치 후 정리
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 4. 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 프로젝트 코드 복사
COPY . .

# 6. 실행 명령어
# 컨테이너가 시작될 때 실행할 기본 명령어를 설정합니다.
CMD ["python", "cpcCrawl.py"] 