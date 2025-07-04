## **프로젝트 개요**
<br/>
암호화 압축파일로부터의 잠재 위협을 AI를 통해 구조적으로 해결할 수 있는 자동 보안 분석 API.
<br/>
<br/>
현대의 웹 환경에서는 블로그, 포럼, 문서 공유 플랫폼, 내부 포털 등 다양한 형태의 웹 콘텐츠에 사용자가 파일을 첨부하고 
<br/> 이를 공개하는 일이 매우 흔합니다. 
<br/>이 중에서도 비밀번호로 암호화된 압축파일(.zip, .7z 등)은 보안 상의 취약 지점으로 작용합니다. 
<br/>일반적인 보안 솔루션은 내부 파일을 열람할 수 없기 때문에, 
<br/>악성코드 유포자는 이러한 구조를 악용하여 검열을 회피하고 위협을 유포하는 수단으로 사용하고 있습니다.<br/>

기존 엔드포인트 보안 솔루션에서는 암호화된 압축파일을 자동으로 분석하거나 선제적으로 차단하는 것이 어렵습니다.<br/>

이러한 문제를 해결하기 위해 본 프로젝트에서는 LLM(Large Language Model)을 활용한 웹 콘텐츠 문맥 분석 기술을 적용하여, 
<br/>업로드된 콘텐츠 내에서 압축파일의 비밀번호를 자동 추론하고, 해당 파일을 해제하여 동적/정적 분석을 수행한 뒤,<br/>
<br/>위협 여부를 자동 판별하는 API 기반 보안 분석 시스템 “ZipSentinel”을 개발하였습니다.<br/>



<img width="707" alt="image" src="https://github.com/user-attachments/assets/34a00cdf-b594-43a5-abab-164e540ee388" />




ZipSentinel API는 다음과 같은 구조로 동작합니다: <br/>
문맥 분석: 웹 콘텐츠 내 자연어 표현을 기반으로 비밀번호를 추론<br/>
위협 진단: VirusTotal 연동 및 내부 평판 시스템으로 위협 등급 판별<br/>
자동 반영: 결과값을 통해 콘텐츠의 상태를 동적으로 조정하거나, 관리자에게 경고 전달<br/>
<br/>
이 시스템은 기존의 수동 대응 방식에서 벗어나 보안 자동화, AI 기반 분석 이라는 두 가지 핵심 방향을 실현하며, 
<br/> 향후 다양한 웹 플랫폼, 파일 공유 서비스, 내부 업무 시스템 등으로의 확장이 가능합니다.


## Back-End

<img width="605" alt="image" src="https://github.com/user-attachments/assets/0cdcbc25-471b-4a4f-8ea1-762fde2277d3" />

</br>

ZipSentinel-API 디렉토리 설정
</br>

```
📦 ZipSentinel-API
├── Dockerfile
├── requirements.txt
├── main.py                 # FastAPI 진입점, 라우터 통합
├── routers/                # 기능별 API 모듈
│   ├── input_receiver.py   # 게시글 수신 → 비밀번호 추론 → 다운로드 → 해제 → 분석
│   ├── file_extract.py     # 압축파일(.zip, .rar, .7z, .tar.gz) 해제 처리
│   ├── clovax_analyze.py   # ClovaX 기반 비밀번호 추론 API (Default 설정. main.py 에서 변경 가능)
│   ├── vt_analyzer.py      # VirusTotal 해시 분석 및 미등록 시 업로드
│   ├── risk_grader.py      # 악성파일 수 기반 위험도 등급 분류
│   ├── output_sender.py    # 최종 분석 결과 포맷 및 전달 처리
│   └── llama_analyze.py    # LLaMA 기반 추론 API (Docker에 모델이 업로드 되어 있어야 사용 가능)
```
</br>

환경 변수 설정 (.env)
본 프로젝트는 외부 서비스 연동 시 API 키 및 민감한 설정 정보를 직접 코드에 포함하지 않고,
</br> .env 파일을 통해 관리하는 것을 권장합니다.</br>
</br> 업로드한 본문에서는 테스트의 유동성을 위해 하드코딩되어 있지만, 
</br> 보안 이슈를 차단하기 위해 모두 센서 처리 하였고, 
</br> .env 방식으로 보안을 강화하는 것을 제안드립니다.

```
# .env 예시
VT_API_KEY=your_virustotal_api_key
CLOVAX_API_KEY=your_clovax_api_key
CLOVAX_BASE_URL=https://clovastudio.stream.ntruss.com/v1/openai

.env 파일은 .gitignore에 반드시 포함하여 버전 관리에서 제외되어야 하며,
</br>외부에 유출되지 않도록 주의하세요.
```

Example]

```
#Python

import os
VT_API_KEY = os.getenv("VT_API_KEY")


```

## Front-End

본 API는 PHP 및 WordPress 기반의 CMS 게시판 환경에서 테스트되었으며, 
</br>게시글 작성 시점부터 자동 분석이 연동되는 구조로 설계되었습니다. 사용자가 게시글을 작성하면, 
</br>해당 내용은 CMS 플러그인을 통해 백엔드 API로 전달되고, 
</br>API는 첨부된 다운로드 링크와 게시글 본문을 분석하여 보안 위험 여부를 판단합니다. 
</br>분석 결과에 따라 CMS는 해당 게시글을 자동으로 공개하거나 비공개 처리하여, 실시간 보안 연동 기능을 제공합니다.

<img width="461" alt="image" src="https://github.com/user-attachments/assets/b7dc1b0c-f908-4b2f-ad8a-4a91aa47ab4b" />
</br>
</br>
<img width="449" alt="image" src="https://github.com/user-attachments/assets/6ea3cc53-cc12-40fb-bd9d-5a401dae2916" />
</br>
</br>
<img width="457" alt="image" src="https://github.com/user-attachments/assets/1f9cceec-4eff-48c0-8323-135515a58249" />
</br>
</br>


</br>
</br>프로젝트 요약
</br>
</br>ZipSentinel은 비밀번호로 보호된 압축파일의 보안 위협을 AI 기반으로 자동 분석하여, 
</br>웹 콘텐츠의 안전성을 실시간으로 판별하는 지능형 보안 게이트웨이 시스템입니다.</br>
</br>
</br>
</br>핵심 기능 요약</br>
</br>구성 요소	기능 설명
</br> 문맥 기반 추론	게시글 본문에서 비밀번호를 LLM(ClovaX, LLaMA 등)으로 자동 추론
</br> 압축 해제 엔진	zip, rar, 7z, tar.gz 등 다양한 포맷을 안전하게 해제
</br> VirusTotal 연동	해시 기반 악성 분석 및 평판 조회 (자동 업로드 포함)
</br> 위험도 등급화	악성 개수 기반 등급 분류: 양호, 주의, 위험, 미분석
</br> CMS 실시간 연동	게시글 작성 시 자동 분석 → 공개 여부 자동 조정
</br>
</br> 프로젝트 특징</br>
</br> AI 기반 자동 보안 분석
</br>
</br> 도커 기반 API 서버 및 플러그인 연동
</br>
</br> CMS, 포럼, 기업 내부 시스템까지 확장 가능
</br>






