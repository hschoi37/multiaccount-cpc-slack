FROM python:3.11-slim

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    --no-install-recommends

# Chrome 최신 안정 버전 설치
RUN wget -O- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-linux-signing-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable

# ChromeDriver 자동 설치 (Chrome 버전과 호환되는 최신 버전)
RUN CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+') && \
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%%.*}") && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip && \
    echo "Chrome version: $CHROME_VERSION, ChromeDriver version: $CHROMEDRIVER_VERSION"

# 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 소스 복사
COPY . .

CMD ["python", "main.py"] 