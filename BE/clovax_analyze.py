from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from openai import OpenAI

router = APIRouter()

# 🔐 Clova Studio (OpenAI 호환 API)
client = OpenAI(
    api_key="ClovaX API KEY",
    base_url="https://clovastudio.stream.ntruss.com/v1/openai"
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# 📥 요청 모델
class ClovaXRequest(BaseModel):
    post_text: str

# 📤 응답 모델
class ClovaXResponse(BaseModel):
    password: str

# 🔍 내부 분석 함수 (직접 호출용)
async def analyze_with_clovax(post_text: str) -> str:
    try:
        logger.info("📨 ClovaX 분석 시작 (HCX 모델 사용)")

        prompt = f"""
        다음 게시글 비밀번호를 추론해줘.
        본문: {post_text}
        """

        response = client.chat.completions.create(
            model="HCX-005",
            messages=[
                {"role": "system", "content": "압축파일 비밀번호만 골라서 출력하세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=256
        )

        answer = response.choices[0].message.content.strip()
        logger.info(f"📌 ClovaX 결과: {answer}")
        return answer

    except Exception as e:
        logger.error(f"❌ ClovaX 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Clova 분석 오류: {e}")

# 🌐 API 라우트 (Swagger 및 외부 호출용)
@router.post("", response_model=ClovaXResponse, summary="ClovaX LLM 비밀번호 추론")
async def analyze_with_clovax_api(request: ClovaXRequest) -> ClovaXResponse:
    password = await analyze_with_clovax(request.post_text)
    return ClovaXResponse(password=password)
