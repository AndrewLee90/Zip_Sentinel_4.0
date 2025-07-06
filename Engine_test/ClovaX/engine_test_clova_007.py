"""
ET-007: 압축파일 해제 성공률 테스트 스크립트
설명: 추론된 비밀번호를 사용하여 다양한 포맷의 압축파일(.zip, .rar, .7z 등)을 해제하고 성공 여부 및 처리 시간을 기록합니다.
"""

import os
import time
import logging
from routers.file_extract import extract_archive

# 테스트 파일 목록과 비밀번호 매핑 (예시)
test_cases = [
    {"file_path": "test_samples/test_1.zip", "password": "infected"},
    {"file_path": "test_samples/test_2.rar", "password": "Yahoo123"},
    {"file_path": "test_samples/test_3.7z", "password": "Yahoo123!"},
    {"file_path": "test_samples/test_4.tar.gz", "password": "infected"},
]

# 결과 기록
results = []

for case in test_cases:
    file_path = case["file_path"]
    password = case["password"]
    print(f"📂 테스트 시작: {file_path}")

    if not os.path.exists(file_path):
        print(f"❌ 파일 없음: {file_path}")
        results.append((file_path, "파일 없음", 0))
        continue

    try:
        t0 = time.time()
        extracted_files = extract_archive(file_path, password)
        elapsed = round(time.time() - t0, 2)
        print(f"✅ 해제 성공 ({elapsed}초): {file_path} → {len(extracted_files)}개 파일")
        results.append((file_path, "성공", elapsed))
    except Exception as e:
        print(f"❌ 해제 실패: {file_path} - {str(e)}")
        results.append((file_path, "실패", 0))

# 결과 출력
print("\n📊 테스트 결과 요약")
for r in results:
    print(f"{r[0]} | 상태: {r[1]} | 소요시간: {r[2]}초")
