from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# ✅ 위험도 등급에 따른 이모지 변환 함수
def convert_to_emoji(level: str) -> str:
    if level == "양호":
        return "🟢 양호"
    elif level == "주의":
        return "🟠 주의"
    elif level == "위험":
        return "🔴 위험"
    else:
        return "🟡 미분석"

# ✅ FE로 보낼 응답 데이터 모델
class OutputData(BaseModel):
    post_id: int
    risk_level: str               # "양호", "주의", "위험"
    vt_report_url: str
    malicious_count: int
    total_files: int

# ✅ 내부 처리 함수
def send_output_data(data: OutputData) -> dict:
    try:
        print(f"[INFO] 게시글 ID {data.post_id} 처리 완료")
        print(f"[INFO] 위험도 등급: {data.risk_level}")
        print(f"[INFO] VirusTotal 리포트 링크: {data.vt_report_url}")

        return {
            "status": "completed",
            "post_id": data.post_id,
            "risk_level": data.risk_level,
            "risk_level_readable": convert_to_emoji(data.risk_level),
            "vt_report_url": data.vt_report_url,
            "malicious_count": data.malicious_count,
            "total_files": data.total_files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Output 전송 실패: {str(e)}")

# ✅ 외부 요청용 라우터 (Swagger 테스트용 등)
@router.post("/send", summary="게시글 분석 결과를 최종 응답 포맷으로 반환")
def send_output(data: OutputData):
    return send_output_data(data)