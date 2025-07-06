from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

# ✅ 커스텀 로거 임포트
from logger import logger

# 라우터 모듈 임포트
from routers.clovax_analyze import router as clovax_analyze_router
from routers.vt_analyzer import router as vt_analyzer_router
from routers.risk_grader import router as risk_grader_router
from routers.input_receiver import router as input_receiver_router
from routers.output_sender import router as output_sender_router
from routers.llama_analyze import router as llama_analyze_router

# FastAPI 앱 생성
app = FastAPI(
    title="ZIPSentinel Final API",
    version="4.3",
    description="""
🚨 **API 인증 안내**

우측 상단의 🔑 Authorize 버튼을 클릭한 후, 아래 형식으로 API 키를 입력하세요:
정확한 인증이 이루어지지 않으면 대부분의 API가 `403` 또는 `401` 오류를 반환합니다.
""",
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(clovax_analyze_router, prefix="/clovax", tags=["ClovaX 추론"])
app.include_router(llama_analyze_router, prefix="/llama-analyze", tags=["LLaMA 추론"])
app.include_router(vt_analyzer_router, prefix="/vt-analyzer", tags=["VirusTotal 해시 분석"])
app.include_router(risk_grader_router, prefix="/risk", tags=["위험도 등급 평가"])
app.include_router(input_receiver_router, prefix="/input-receiver", tags=["Input Receiver"])
app.include_router(output_sender_router, prefix="/output-sender", tags=["Output Sender"])

# Swagger 문서 오버라이딩
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ✅ 앱 시작 로그 출력
logger.info("✅ ZIPSentinel API 서버가 시작되었습니다.")
