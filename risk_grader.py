from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ✅ 응답 구조 모델 (Swagger 테스트용 입력 모델)
class VTResultInput(BaseModel):
    total: int
    positives: int
    sha256: str
    permalink: str

# ✅ 실제 위험도 평가에 사용하는 내부 모델 (입력값 매핑용)
class VTResult(BaseModel):
    total: int
    positives: int
    sha256: str
    permalink: str

# ✅ Swagger용 POST API 라우트
@router.post("/grade", summary="VirusTotal 결과 기반 위험도 등급 평가")
def risk_grade_api(results: List[VTResultInput]):
    try:
        vt_results = [VTResult(**r.dict()) for r in results]
        return grade_virustotal_results(vt_results)
    except Exception as e:
        logger.error(f"❌ 위험도 평가 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ✅ 위험도 평가 함수 (기존 그대로)
def grade_virustotal_results(results: list[VTResult]) -> dict:
    try:
        total_malicious = 0
        total_files = len(results)
        is_unanalyzed = False

        for result in results:
            if result.total == 0:
                logger.warning(f"⚠️ 분석되지 않은 파일 포함: {result.sha256}")
                is_unanalyzed = True
                continue

            try:
                total_malicious += result.positives
            except Exception as e:
                logger.warning(f"⚠️ 분석 결과 파싱 오류: {e}")

        if is_unanalyzed:
            level = "🟡 미분석"
        elif total_malicious >= 7:
            level = "🔴 위험"
        elif 3 <= total_malicious <= 6:
            level = "🟠 주의"
        else:
            level = "🟢 양호"

        logger.info(f"📊 위험도 등급 평가 완료 - 전체 {total_files}개 파일, 악성 {total_malicious}건 → {level}")

        return {
            "level": level,
            "malicious_count": total_malicious,
            "total_files": total_files
        }

    except Exception as e:
        logger.error(f"⚠️ Risk Grading 실패: {e}")
        raise ValueError(f"Risk Grading 실패: {e}")
