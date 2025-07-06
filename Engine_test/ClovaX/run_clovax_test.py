import requests
import json
from datetime import datetime

# === 설정 ===
INPUT_PATH = r"D:\Zip_sentinel\최종프로젝트\testing\final_testcases_400_tracking.json"
OUTPUT_PATH = r"D:\Zip_sentinel\최종프로젝트\testing\final_testcases_400_clovax_with_timing.json"
API_URL = "http://223.130.158.226:8000/clovax-analyze"

# === 데이터 로드 ===
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# === 처리 ===
for case in data:
    if case.get("predicted_password") is not None:
        continue

    payload = { "post_text": case["input_text"] }

    try:
        started_at = datetime.now()
        response = requests.post(API_URL, json=payload, timeout=20)
        response.raise_for_status()
        completed_at = datetime.now()

        result = response.json()
        predicted = result.get("password", "")

        case["predicted_password"] = predicted
        case["match"] = (predicted == case["expected_password"])
        case["completed_at"] = completed_at.isoformat()
        case["duration_ms"] = int((completed_at - started_at).total_seconds() * 1000)

        print(f"[{case['id']:03}] ✅ 예상={case['expected_password']} | 추론={predicted} | 일치={case['match']} | 시간={case['duration_ms']}ms")

    except Exception as e:
        completed_at = datetime.now()
        case["predicted_password"] = f"[ERROR] {str(e)}"
        case["match"] = False
        case["completed_at"] = completed_at.isoformat()
        case["duration_ms"] = int((completed_at - started_at).total_seconds() * 1000)

        print(f"[{case['id']:03}] ❌ 오류 발생: {str(e)} | 시간={case['duration_ms']}ms")

# === 결과 저장 ===
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ ClovaX 테스트 완료! 결과 저장됨: {OUTPUT_PATH}")