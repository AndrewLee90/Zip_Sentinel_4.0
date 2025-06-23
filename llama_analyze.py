from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# ✅ LLaMA 모델 경로 (복사된 .gguf 파일 위치)
model_path = os.path.abspath("./models/llama-2/llama-2-7b-chat.Q2_K.gguf")

# ✅ LLaMA 모델 초기화
llm = None
try:
    if os.path.exists(model_path):
        from llama_cpp import Llama
        llm = Llama(
            model_path=model_path,
            n_ctx=1024,
            n_threads=8
        )
        logger.info(f"✅ LLaMA 모델 로드 완료: {model_path}")
    else:
        logger.warning(f"❌ LLaMA 모델 경로가 존재하지 않음: {model_path}")
except Exception as e:
    logger.error(f"❌ LLaMA 초기화 실패: {e}")

# 📥 입력 모델
class LLaMARequest(BaseModel):
    post_text: str

# 📤 출력 모델
class LLaMAResponse(BaseModel):
    password: str

# 📡 API 라우트
@router.post("/analyze", response_model=LLaMAResponse, summary="LLaMA LLM 비밀번호 추론")
async def analyze_with_llama(request: LLaMARequest):
    if llm is None:
        raise HTTPException(
            status_code=503,
            detail="LLaMA 모델이 초기화되지 않았습니다. 서버에 모델 파일이 없거나 로딩에 실패했습니다."
        )

    try:
        # ✅ 프롬프트: 예시 기반으로 유도 + 출력 강제
        prompt = f"""
다음 문장에서 압축파일 비밀번호로 사용된 정확한 문자열을 그대로 출력해. 다른 말은 절대 하지 마.
예시 입력: "비밀번호는 Yahoo123이야" → 출력: Yahoo123
예시 입력: "압축파일 비밀번호는 8765야" → 출력: 8765
예시 입력: "{request.post_text}" → 출력:
"""

        result = llm(
            prompt=prompt,
            max_tokens=32,
            stop=["\n", "</s>", "출력:"],
            temperature=0.3
        )

        # ✅ 결과 전처리: 첫 줄만 추출
        raw_answer = result["choices"][0]["text"].strip()
        password = raw_answer.splitlines()[0].strip()

        logger.info(f"📌 LLaMA 추론 결과: {password}")
        return LLaMAResponse(password=password)

    except Exception as e:
        logger.error(f"❌ LLaMA 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"LLaMA 분석 오류: {e}")
