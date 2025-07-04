from fastapi import APIRouter, HTTPException, Request, Depends, Path
from pydantic import BaseModel
from typing import Optional
import logging

from routers.clovax_analyze import analyze_with_clovax
from routers.file_extract import extract_file
from routers.vt_analyzer import analyze_hashes_with_virustotal as analyze_with_virustotal
from routers.risk_grader import grade_virustotal_results
from routers.output_sender import send_output_data

router = APIRouter()
logger = logging.getLogger(__name__)

# ✅ API Key 검증 함수
def verify_api_key(request: Request):
    auth_header = request.headers.get("authorization")
    logger.info(f"[AUTH] 받은 인증 헤더: {auth_header}")
    if auth_header != "API KEY":
        raise HTTPException(
            status_code=403,
            detail="❌ 유효하지 않은 API Key입니다. Swagger 상단 Authorize 버튼에 정확한 키값을 입력하세요."
        )

# 📥 입력 데이터 모델
class InputData(BaseModel):
    post_id: int
    post_text: str
    download_link: str

# 📤 출력 데이터 모델
class OutputData(BaseModel):
    status: str
    post_id: int
    risk_level: str
    risk_level_readable: str
    vt_report_url: str
    malicious_count: int
    total_files: int

# 📌 게시글 수신 → 분석 전체 파이프라인
@router.post("/receive", dependencies=[Depends(verify_api_key)], summary="게시글 수신 및 전체 분석 파이프라인 실행")
async def receive_input(data: InputData):

    try:
        logger.info(f"[1단계] 게시글 수신 완료 - ID: {data.post_id}")

        logger.info("[2단계] ClovaX 추론 시작")
        inferred_password = await analyze_with_clovax(data.post_text)
        logger.info(f"[2단계] ClovaX 추론 완료: {inferred_password}")

        logger.info("[3단계] 압축 해제 시작")
        extracted_files = extract_file(data.download_link, password=inferred_password)

        logger.info("[4단계] VirusTotal 해시 분석 시작")
        sha256_list = [f["sha256"] for f in extracted_files if isinstance(f, dict) and "sha256" in f]
        for f in extracted_files:
            if not isinstance(f, dict) or "sha256" not in f:
                logger.warning(f"❗ SHA256 정보가 누락된 항목: {f}")
        if not sha256_list:
            raise Exception("해시 리스트가 비어 있습니다.")

        vt_results = analyze_with_virustotal(sha256_list)

        logger.info("[5단계] 위험도 등급 평가 시작")
        risk_results = grade_virustotal_results(vt_results)

        logger.info("[6단계] 최종 응답 처리 시작")
        sha256 = sha256_list[0] if sha256_list else ""
        level = risk_results["level"]
        output_payload = OutputData(
            status="completed",
            post_id=data.post_id,
            risk_level=level.replace("🟢 ", "").replace("🟠 ", "").replace("🔴 ", "").replace("🟡 ", ""),
            risk_level_readable=level,
            vt_report_url=f"https://www.virustotal.com/gui/file/{sha256}",
            malicious_count=risk_results["malicious_count"],
            total_files=risk_results["total_files"]
        )

        return send_output_data(output_payload)

    except Exception as e:
        logger.error(f"[❌ 예외 발생] 게시글 처리 실패 - ID: {data.post_id}")
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

# 📤 게시글 처리 상태 조회 API
@router.get(
    "/receive/result/{post_id}",
    tags=["Input Receiver"],
    summary="게시글 처리 결과 상태 조회"
)
def receive_result_status(
    post_id: int = Path(..., description="처리 상태를 조회할 게시글 ID")
):
    """
    📤 게시글 처리 상태 조회 API

    - 게시글 ID를 기반으로 처리 상태를 반환합니다.
    - 현재는 예시 목적상 항상 "completed" 상태로 반환합니다.
    - 향후 DB나 상태 캐시 연동 시 동적 상태 반환 가능.
    """
    return {
        "post_id": post_id,
        "status": "completed",
        "message": f"게시글 {post_id}에 대한 처리가 완료되었습니다."
    }
