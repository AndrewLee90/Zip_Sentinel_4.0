import json
import random
import os

def generate_ndjson_log(filename: str, start_post_id: int = 151):
    virus_ids = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    size_list = [100, 200, 300, 400, 500]
    lines = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, filename)

    post_id = start_post_id

    for virus in virus_ids:
        malicious_count = random.randint(10, 80)  # 각 바이러스 유형마다 동일하게 유지
        for i, size in enumerate(size_list):
            elapsed = round(random.uniform(3, 5) + i * 2.5, 3)

            if size <= 400:
                vt_success = True
            else:
                vt_success = random.random() < 0.6  # 60% 성공 확률

            line_index = {"index": {"_index": "zipsentinel_logs"}}
            log_entry = {
                "post_id": post_id,
                "file_size_MB": size,
                "clovax_success": True,
                "extract_success": True,
                "vt_success": vt_success,
                "malicious_count": malicious_count,
                "total_files": 2,  # 항상 2개
                "elapsed_time_sec": elapsed
            }

            lines.append(json.dumps(line_index))
            lines.append(json.dumps(log_entry, ensure_ascii=False))
            post_id += 1

    with open(output_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"✅ 50개 NDJSON 로그 생성 완료: {output_path}")

if __name__ == "__main__":
    generate_ndjson_log("virus_all_logs_50.ndjson", start_post_id=151)
