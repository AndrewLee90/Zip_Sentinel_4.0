# logger.py
import logging

logger = logging.getLogger("zipsentinel")
logger.setLevel(logging.INFO)

# 파일 핸들러 설정
file_handler = logging.FileHandler("/root/final/ZipSentinel-Docker-BE/logs/zipsentinel.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)

# 로그 포맷 지정
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s:%(message)s")
file_handler.setFormatter(formatter)

# 핸들러 등록 (중복 방지)
if not logger.handlers:
    logger.addHandler(file_handler)
