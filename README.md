## **프로젝트 개요**
<br/>
암호화 압축파일로부터의 잠재 위협을 AI를 통해 구조적으로 해결할 수 있는 자동 보안 분석 API.
<br/>
<br/>
현대의 웹 환경에서는 블로그, 포럼, 문서 공유 플랫폼, 내부 포털 등 다양한 형태의 웹 콘텐츠에 사용자가 파일을 첨부하고 
<br/> 이를 공개하는 일이 매우 흔합니다. 
<br/>이 중에서도 비밀번호로 암호화된 압축파일(.zip, .7z 등)은 보안 상의 취약 지점으로 작용합니다. <br/>
일반적인 보안 솔루션은 내부 파일을 열람할 수 없기 때문에, <br/>악성코드 유포자는 이러한 구조를 악용하여 검열을 회피하고 위협을 유포하는 수단으로 사용하고 있습니다.<br/>

기존 엔드포인트 보안 솔루션에서는 암호화된 압축파일을 자동으로 분석하거나 선제적으로 차단하는 것이 어렵습니다.<br/>

이러한 문제를 해결하기 위해 본 프로젝트에서는 LLM(Large Language Model)을 활용한 웹 콘텐츠 문맥 분석 기술을 적용하여, 
<br/>업로드된 콘텐츠 내에서 압축파일의 비밀번호를 자동 추론하고, 해당 파일을 해제하여 동적/정적 분석을 수행한 뒤,<br/>
<br/>위협 여부를 자동 판별하는 API 기반 보안 분석 시스템 “ZipSentinel”을 개발하였습니다.<br/>



<img width="707" alt="image" src="https://github.com/user-attachments/assets/34a00cdf-b594-43a5-abab-164e540ee388" />




ZipSentinel은 다음과 같은 구조로 동작합니다: <br/>
문맥 분석: 웹 콘텐츠 내 자연어 표현을 기반으로 비밀번호를 추론<br/>
위협 진단: VirusTotal 연동 및 내부 평판 시스템으로 위협 등급 판별<br/>
자동 반영: 결과값을 통해 콘텐츠의 상태를 동적으로 조정하거나, 관리자에게 경고 전달<br/>
<br/>
이 시스템은 기존의 수동 대응 방식에서 벗어나 보안 자동화, AI 기반 분석 이라는 두 가지 핵심 방향을 실현하며, 
<br/> 향후 다양한 웹 플랫폼, 파일 공유 서비스, 내부 업무 시스템 등으로의 확장이 가능합니다.

<img width="605" alt="image" src="https://github.com/user-attachments/assets/0cdcbc25-471b-4a4f-8ea1-762fde2277d3" />



ZipSentinel-API 디렉토리 설정

```
📦 ZipSentinel-API
├── Dockerfile
├── requirements.txt
├── main.py                 # FastAPI 진입점, 라우터 통합
├── routers/                # 기능별 API 모듈
│   ├── input_receiver.py   # 게시글 수신 → 비밀번호 추론 → 다운로드 → 해제 → 분석
│   ├── file_extract.py     # 압축파일(.zip, .rar, .7z, .tar.gz) 해제 처리
│   ├── clovax_analyze.py   # ClovaX 기반 비밀번호 추론 API
│   ├── vt_analyzer.py      # VirusTotal 해시 분석 및 미등록 시 업로드
│   ├── risk_grader.py      # 악성파일 수 기반 위험도 등급 분류
│   ├── output_sender.py    # 최종 분석 결과 포맷 및 전달 처리
│   └── llama_analyze.py    # (예정) LLaMA 기반 추론 API
```


환경 변수 설정 (.env)
본 프로젝트는 외부 서비스 연동 시 API 키 및 민감한 설정 정보를 직접 코드에 포함하지 않고,
</br> .env 파일을 통해 관리하는 것을 권장합니다.
</br> 업로드한 본문에서는 테스트의 유동성을 위한 하드코딩되어 있지만, 
</br> 보안 이슈를 차단하기 위해 모두 센서처리 한 점을 참고 부탁드립니다.

```
# .env 예시
VT_API_KEY=your_virustotal_api_key
CLOVAX_API_KEY=your_clovax_api_key
CLOVAX_BASE_URL=https://clovastudio.stream.ntruss.com/v1/openai

.env 파일은 .gitignore에 반드시 포함하여 버전 관리에서 제외되어야 하며,
</br>외부에 유출되지 않도록 주의하세요.
```

```
#Python

import os
VT_API_KEY = os.getenv("VT_API_KEY")

```
