# full_engine_test.py
import os, json, time, csv, requests, tempfile, pyzipper, re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "test_inputs_1000.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "engine_full_test_log.csv")
API_ENDPOINT = "REST API HOST" # API input 주소값
AUTH_KEY = "REST API KEY" # API 키
TIMEOUT = 180
SLEEP_INTERVAL = 30  # VT 무료 API 제한 회피용 간격
MAX_MB = 30
LOG_PATH = "/zipsentinel.log" #로그 생성 경로
RESULT_RE = re.compile(r"\[✅ FE 전송 결과\] *(?P<json>\{.*\})")

def get_inner_zip_under_30mb(zip_path, password="infected"):
    try:
        with pyzipper.AESZipFile(zip_path) as zf:
            zf.pwd = password.encode()
            candidates = [i for i in zf.infolist() if i.file_size / 1024 / 1024 < MAX_MB and i.filename.endswith((".zip", ".rar", ".7z", ".tar.gz"))]
            if candidates:
                chosen = sorted(candidates, key=lambda x: x.file_size)[0]
                out_path = os.path.join(tempfile.gettempdir(), os.path.basename(chosen.filename))
                with open(out_path, "wb") as f:
                    f.write(zf.read(chosen))
                return out_path, chosen.filename
    except Exception as e:
        print(f"[⚠️ 내부 ZIP 추출 실패] {e}")
    return None, None

def wait_for_result(post_id, timeout=TIMEOUT):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with open(LOG_PATH, encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if "[✅ FE 전송 결과]" in line:
                        match = RESULT_RE.search(line)
                        if match:
                            json_text = match.group("json")
                            try:
                                result_obj = json.loads(json_text.replace("'", '"'))
                                if result_obj.get("post_id") == post_id:
                                    return result_obj
                            except json.JSONDecodeError:
                                continue
        except FileNotFoundError:
            print(f"[❌ 로그파일 없음] {LOG_PATH}")
        time.sleep(3)
    return {}

with open(INPUT_JSON, encoding="utf-8") as f:
    tests = json.load(f)

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as csvf:
    writer = csv.writer(csvf)
    writer.writerow(["No", "post_id", "file_name", "analyzed", "risk_level", "malicious_count", "total_files", "vt_url", "elapsed_s", "status", "error"])

    for idx, test in enumerate(tests, 1):
        post_id = test["post_id"]
        post_text = test["post_text"]
        download_link = test["download_link"]
        t0 = time.time()
        analyzed = False
        result = {}
        error, status, file_name = "", "미수행", ""

        print(f"[{idx:02}] 🚀 Post ID={post_id} 다운로드 시작")
        try:
            response = requests.get(download_link, stream=True, timeout=30)
            response.raise_for_status()
            temp_path = tempfile.NamedTemporaryFile(delete=False).name
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[{idx:02}] ✅ 다운로드 완료: {round(os.path.getsize(temp_path)/(1024*1024), 2)}MB")

            inner_path, file_name = get_inner_zip_under_30mb(temp_path)
            if not inner_path:
                error = "분석 가능한 내부파일 없음"
                print(f"[{idx:02}] ⚠️ {error}")
                raise RuntimeError(error)

            print(f"[{idx:02}] ✅ 내부 파일 분석 대상 선택 완료: {file_name}")

            res = requests.post(API_ENDPOINT,
                                headers={"Authorization": AUTH_KEY},
                                json={"post_id": post_id, "post_text": post_text, "download_link": download_link},
                                timeout=10)
            if res.status_code != 200:
                raise RuntimeError(f"API 오류: {res.status_code}, {res.text}")

            result = wait_for_result(post_id, timeout=TIMEOUT)
            if result:
                analyzed = True
                status = result.get("status", "completed")
            else:
                raise TimeoutError("결과 수신 시간 초과")

            risk = result.get("risk_level", "미분석")
            count = result.get("malicious_count", 0)
            total = result.get("total_files", 0)
            vturl = result.get("vt_report_url", "")

            print(f"[{idx:02}] ✅ 엔진 테스트 성공: {risk} / 악성 {count}건")

        except Exception as e:
            risk, count, total, vturl = "에러", 0, 0, ""
            error = str(e)
            print(f"[{idx:02}] ❌ 실패: {error}")

        elapsed = round(time.time() - t0, 2)
        writer.writerow([idx, post_id, file_name, "Y" if analyzed else "N", risk, count, total, vturl, elapsed, status, error])
        print(f"[{idx:02}] 🧪 테스트 완료")
        print(f"[{idx:02}] ⏱️ 처리 시간: {elapsed}s\n")

        time.sleep(SLEEP_INTERVAL)
