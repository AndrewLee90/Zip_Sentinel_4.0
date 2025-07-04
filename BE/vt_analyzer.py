from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import logging
import requests

router = APIRouter()
logger = logging.getLogger(__name__)

# ✅ VirusTotal 설정
VT_API_KEY = 'Virus Total API KEY'
VT_BASE_URL = "https://www.virustotal.com/api/v3/files/"

# ✅ 결과 모델 정의
class VTResult(BaseModel):
    total: int
    positives: int
    sha256: str
    permalink: str

# ✅ 해시 리스트를 받아서 VirusTotal 분석
def analyze_hashes_with_virustotal(hashes: List[str]) -> List[VTResult]:
    if not hashes:
        raise ValueError("해시 리스트가 비어 있습니다.")

    results = []
    for sha256 in hashes:
        url = f"{VT_BASE_URL}{sha256}"
        headers = {"x-apikey": VT_API_KEY}

        logger.debug(f"📡 [VT 요청] {url}")
        response = requests.get(url, headers=headers)

        logger.debug(f"📥 [응답 상태] {response.status_code}")
        if response.status_code == 401:
            logger.error("❌ 잘못된 VirusTotal API 키입니다.")
            raise HTTPException(status_code=401, detail="VirusTotal API 인증 실패: 잘못된 API 키입니다.")

        elif response.status_code == 404:
            logger.warning(f"⚠️ VirusTotal에 등록되지 않은 파일: {sha256}")
            results.append(VTResult(
                total=0,
                positives=0,
                sha256=sha256,
                permalink=f"https://www.virustotal.com/gui/file/{sha256}"
            ))
            continue  # 🔁 예외 발생 없이 다음 해시로 진행

        elif response.status_code != 200:
            logger.error(f"❌ VirusTotal 요청 실패: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail="VirusTotal 요청 실패")

        try:
            data = response.json()
            stats = data["data"]["attributes"]["last_analysis_stats"]
            total = sum(stats.values())
            positives = stats.get("malicious", 0)
            permalink = f"https://www.virustotal.com/gui/file/{sha256}"

            results.append(VTResult(
                total=total,
                positives=positives,
                sha256=sha256,
                permalink=permalink
            ))

        except KeyError as e:
            logger.error(f"❌ VT 결과 파싱 실패: {e}")
            raise HTTPException(status_code=500, detail="VirusTotal 결과 파싱 오류")

    return results

# ✅ API 엔드포인트
@router.post("/vt-analyzer/analyze", summary="VT 해시 분석 API", response_model=List[VTResult])
async def vt_analyze_api(hashes: List[str]):
    return analyze_hashes_with_virustotal(hashes)
