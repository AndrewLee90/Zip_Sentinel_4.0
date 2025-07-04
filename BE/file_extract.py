from fastapi import APIRouter
from pydantic import BaseModel
import os
import hashlib
import tempfile
import requests
import shutil
import zipfile
import py7zr
import tarfile
import rarfile
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 📥 요청 모델
class FileExtractRequest(BaseModel):
    download_link: str
    password: str | None = None

# 📤 응답 모델
class FileExtractResponse(BaseModel):
    extracted_files: list[dict]

# ✅ Swagger 테스트용 API 엔드포인트
@router.post("/", response_model=FileExtractResponse, summary="파일 다운로드 및 압축 해제")
def extract_file_api(req: FileExtractRequest):
    extracted = extract_file(req.download_link, req.password)
    return {"extracted_files": extracted}

# ✅ 내부 해제 함수 (기존 그대로)
def extract_file(download_link: str, password: str = None):
    try:
        temp_dir = tempfile.mkdtemp()
        logger.info(f"📂 임시 디렉토리 생성됨: {temp_dir}")

        response = requests.get(download_link, stream=True)
        if response.status_code != 200:
            raise Exception(f"다운로드 실패 - 상태코드: {response.status_code}")

        archive_path = os.path.join(temp_dir, "downloaded_file")
        with open(archive_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"📥 파일 다운로드 완료: {archive_path}")

        extracted_files = []

        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path) as zip_ref:
                if password:
                    zip_ref.setpassword(password.encode())
                zip_ref.extractall(temp_dir)
                file_list = zip_ref.namelist()

        elif archive_path.endswith(".7z"):
            with py7zr.SevenZipFile(archive_path, mode='r', password=password) as z:
                z.extractall(path=temp_dir)
                file_list = z.getnames()

        elif archive_path.endswith(".rar"):
            with rarfile.RarFile(archive_path) as rf:
                if password:
                    rf.setpassword(password)
                rf.extractall(path=temp_dir)
                file_list = rf.namelist()

        elif archive_path.endswith(".tar.gz") or archive_path.endswith(".tgz"):
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(path=temp_dir)
                file_list = tf.getnames()

        else:
            raise Exception("지원되지 않는 압축 포맷입니다.")

        logger.info(f"📂 압축 해제 완료 - 포함 파일 수: {len(file_list)}")

        for file_name in file_list:
            file_path = os.path.join(temp_dir, file_name)
            if not os.path.isfile(file_path):
                continue

            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            file_info = {
                "file_name": file_name,
                "sha256": sha256_hash.hexdigest(),
                "size": os.path.getsize(file_path)
            }
            extracted_files.append(file_info)

        logger.info(f"📑 SHA256 해시 계산 완료 - 총 {len(extracted_files)}개 파일")
        return extracted_files

    except Exception as e:
        logger.error(f"[압축 해제 실패] {str(e)}")
        raise Exception(f"[압축 해제 실패] {str(e)}")

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"🧹 임시 디렉토리 삭제 완료: {temp_dir}")
