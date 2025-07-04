# 🐍 Python 3.10 slim 베이스 이미지
FROM python:3.10-slim

# 📁 작업 디렉토리 설정
WORKDIR /app

# ✅ 환경 변수 설정
ENV TMPDIR=/app/tmp

# ✅ 디렉토리 생성
RUN mkdir -p /app/tmp /root/final/ZipSentinel-Docker-BE/logs /app/models/llama-2

# 🔧 시스템 패키지 및 압축 도구 설치
RUN apt-get update && \
    apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    unzip \
    gnupg \
    software-properties-common \
    p7zip-full && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 🔓 .rar 압축 해제를 위한 non-free 저장소 추가 후 unrar 설치
RUN echo "deb http://deb.debian.org/debian bookworm main contrib non-free" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y unrar && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 📦 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 📂 애플리케이션 전체 복사
COPY . .

# 📥 LLaMA 모델 디렉토리 복사 (선택 사항)
COPY models/llama-2 /app/models/llama-2

# 🌐 포트 노출
EXPOSE 8000

# 🛡️ Gunicorn + Uvicorn으로 실행, 로그는 /root/... 경로에 저장
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300", \
     "--workers", "2", \
     "--access-logfile", "/root/final/ZipSentinel-Docker-BE/logs/gunicorn_access.log", \
     "--error-logfile", "/root/final/ZipSentinel-Docker-BE/logs/gunicorn_error.log"]
