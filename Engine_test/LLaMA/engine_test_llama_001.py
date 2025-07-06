import json
import requests

API_URL = "API SERVER URL"  # 🔁 라마 모델 API URL로 교체하세요
INPUT_PATH = "test_001_pw_length.json"  # ✅ 입력 케이스 파일
OUTPUT_PATH = "results_llama_001.json"  # ✅ 라마 결과 저장 경로

def run_test():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    results = []
    print(f"📦 테스트 케이스 수: {len(test_cases)}")

    for case in test_cases:
        try:
            response = requests.post(API_URL, json={"post_text": case["input_text"]})
            print(f"[{case['id']}] 응답 상태 코드: {response.status_code}, 내용: {response.text}")

            if response.status_code == 200:
                predicted = response.json().get("password", "")
            else:
                predicted = "ERROR"

            results.append({
                "id": case["id"],
                "expected_password": case["expected_password"],
                "predicted": predicted,
                "match": predicted == case["expected_password"]
            })

        except Exception as e:
            results.append({
                "id": case["id"],
                "expected_password": case.get("expected_password", ""),
                "predicted": "EXCEPTION",
                "match": False,
                "error": str(e)
            })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ 완료: 결과가 {OUTPUT_PATH}에 저장되었습니다.")

if __name__ == "__main__":
    run_test()
