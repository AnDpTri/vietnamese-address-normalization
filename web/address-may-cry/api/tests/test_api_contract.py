"""Bộ kiểm thử hợp đồng API (API Contract Tests) cho Address May Cry.
Kiểm tra toàn diện:
1. GET /api/v1/health
2. POST /api/v1/normalize (đối chiếu trực tiếp với pipeline thật)
3. Xử lý Unicode NFD / NFC
4. Bắt lỗi xác thực: rỗng, quá 2048 ký tự, payload > 1MB, invalid JSON
5. POST /api/v1/batch (hỗn hợp hợp lệ + lỗi item, bảo toàn id/order)
6. 404 JSON cho route /api không tồn tại
7. CORS preflight OPTIONS

TUYỆT ĐỐI KHÔNG đọc dữ liệu test NLP. Chỉ dùng ví dụ tự tạo hoặc từ train.
"""

import json
import os
import sys
import time
import threading
import unicodedata
import urllib.error
import urllib.request
from dataclasses import asdict
from http import HTTPStatus
from pathlib import Path

# Thêm đường dẫn
TESTS_DIR = Path(__file__).resolve().parent
API_DIR = TESTS_DIR.parent
PROJECT_ROOT = API_DIR.parent.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from engine import NlpEngineAdapter
from server import create_server

TEST_HOST = "127.0.0.1"
TEST_PORT = 8089  # Dùng cổng 8089 cho test độc lập tránh xung đột với cổng 8080


class TestServerContext:
    def __init__(self, host=TEST_HOST, port=TEST_PORT):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None

    def __enter__(self):
        self.server = create_server(self.host, self.port)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(0.2)  # Đợi server sẵn sàng
        return f"http://{self.host}:{self.port}"

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.server:
            self.server.shutdown()
            self.server.server_close()


def http_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    req_data = None
    if data is not None:
        if isinstance(data, (dict, list)):
            req_data = json.dumps(data, ensure_ascii=False).encode("utf-8")
            headers.setdefault("Content-Type", "application/json; charset=utf-8")
        elif isinstance(data, (bytes, bytearray)):
            req_data = data
        elif isinstance(data, str):
            req_data = data.encode("utf-8")

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return resp.status, resp.headers, body
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, e.headers, body


def test_health(base_url):
    print("1. Kiểm tra GET /api/v1/health...")
    status, headers, body = http_request(f"{base_url}/api/v1/health")
    assert status == 200, f"Health code={status}"
    payload = json.loads(body.decode("utf-8"))
    assert payload["status"] in ("ok", "loading"), f"Trạng thái={payload['status']}"
    assert payload["target_date"] == "2025-07-01"
    assert payload["limits"]["max_chars"] == 2048
    assert payload["limits"]["max_batch"] == 100
    print(f"   [PASS] Health OK: engine='{payload['engine']}', status='{payload['status']}'")


def test_normalize_real_pipeline(base_url):
    print("2. Kiểm tra POST /api/v1/normalize & đối chứng pipeline thực...")
    eng = NlpEngineAdapter.get_instance()
    test_address = "Số 10 Lê Lợi, Phường Bến Nghé, Quận 1, TP Hồ Chí Minh"

    # 1. Gọi trực tiếp pipeline
    direct_res, direct_elapsed, direct_status = eng.normalize(test_address)

    # 2. Gọi qua HTTP API
    status, headers, body = http_request(
        f"{base_url}/api/v1/normalize",
        method="POST",
        data={"address": test_address},
    )
    assert status == 200, f"Normalize code={status}"
    payload = json.loads(body.decode("utf-8"))

    assert payload["input"] == test_address
    assert payload["status"] == direct_status
    assert "result" in payload
    assert payload["elapsed_ms"] > 0

    api_result = payload["result"]
    # So sánh trực tiếp từng trường cốt lõi
    for key in ("so_nha", "duong", "xa_phuong", "ma_xa", "tinh", "ma_tinh", "dia_chi_chuan"):
        assert api_result[key] == direct_res[key], f"Lệch trường {key}: API='{api_result[key]}' vs Direct='{direct_res[key]}'"

    print(f"   [PASS] Chuẩn hóa thực khớp 100% pipeline: dia_chi_chuan='{api_result['dia_chi_chuan']}' ({payload['elapsed_ms']}ms)")


def test_normalize_giai_thich(base_url):
    print("2b. Kiểm tra chế độ xem từng bước (giai_thich)...")
    dia_chi = "Số 10 Lê Lợi, Phường Bến Nghé, Quận 1, TP Hồ Chí Minh"

    # Mặc định không gửi các bước trung gian
    status, _, body = http_request(f"{base_url}/api/v1/normalize", method="POST", data={"address": dia_chi})
    assert status == 200
    thuong = json.loads(body.decode("utf-8"))
    assert "giai_thich" not in thuong

    # Chỉ đúng giá trị true mới bật
    status, _, body = http_request(f"{base_url}/api/v1/normalize", method="POST",
                                   data={"address": dia_chi, "giai_thich": "true"})
    assert "giai_thich" not in json.loads(body.decode("utf-8"))

    status, _, body = http_request(f"{base_url}/api/v1/normalize", method="POST",
                                   data={"address": dia_chi, "giai_thich": True})
    assert status == 200
    payload = json.loads(body.decode("utf-8"))
    gt = payload["giai_thich"]

    # Kết quả cuối giống hệt chế độ thường
    for key in ("so_nha", "duong", "xa_phuong", "ma_xa", "tinh", "ma_tinh", "dia_chi_chuan"):
        assert payload["result"][key] == thuong["result"][key], f"Lệch trường {key} khi bật giai_thich"

    for key in ("token", "vai_tro", "ung_vien", "so_gia_thuyet", "gia_thuyet", "duong", "chuyen_doi",
                "canh_bao_giua", "canh_bao_sau"):
        assert key in gt, f"Thiếu bước {key}"
    assert gt["token"], "Không có token"
    for vt in gt["vai_tro"]:
        assert payload["input"][vt["bat_dau"]:vt["ket_thuc"]] == vt["doan"], "Vị trí ký tự vai trò lệch chuỗi gốc"
    assert 0 < len(gt["gia_thuyet"]) <= 3
    assert gt["gia_thuyet"] == sorted(gt["gia_thuyet"], key=lambda g: -g["diem"]), "Giả thuyết chưa xếp theo điểm"
    assert gt["chuyen_doi"] and all(c["tinh_moi"] and c["tinh_moi"][0]["ten"] for c in gt["chuyen_doi"])
    print(f"   [PASS] giai_thich đủ các bước, {gt['so_gia_thuyet']} giả thuyết, kết quả không đổi.")


def test_unicode_nfd_nfc(base_url):
    print("3. Kiểm tra bảo toàn Unicode NFD và NFC...")
    raw_nfd = unicodedata.normalize("NFD", "123 Đường Trần Hưng Đạo, Phường 1, Thành phố Cà Mau")
    assert not unicodedata.is_normalized("NFC", raw_nfd), "Chuỗi phải ở dạng NFD phân rã"

    status, headers, body = http_request(
        f"{base_url}/api/v1/normalize",
        method="POST",
        data={"address": raw_nfd},
    )
    assert status == 200
    payload = json.loads(body.decode("utf-8"))
    assert payload["input"] == raw_nfd
    assert payload["result"]["duong"] != ""
    print(f"   [PASS] NFD Unicode xử lý chính xác, không lỗi mã hóa.")


def test_validation_errors(base_url):
    print("4. Kiểm tra các trường hợp validation và mã lỗi...")

    # 4a. Địa chỉ rỗng
    status, _, body = http_request(f"{base_url}/api/v1/normalize", method="POST", data={"address": "   "})
    assert status == 400
    err = json.loads(body.decode("utf-8"))["error"]
    assert err["code"] == "EMPTY_ADDRESS"

    # 4b. Quá 2048 ký tự
    long_addr = "Hà Nội " * 400
    status, _, body = http_request(f"{base_url}/api/v1/normalize", method="POST", data={"address": long_addr})
    assert status == 413
    err = json.loads(body.decode("utf-8"))["error"]
    assert err["code"] == "ADDRESS_TOO_LONG"

    # 4c. JSON sai cú pháp
    status, _, body = http_request(
        f"{base_url}/api/v1/normalize",
        method="POST",
        data="{invalid_json:",
        headers={"Content-Type": "application/json"},
    )
    assert status == 400
    err = json.loads(body.decode("utf-8"))["error"]
    assert err["code"] == "INVALID_JSON"

    # 4d. Payload > 1MB
    huge_data = "a" * (1024 * 1024 + 10)
    status, _, body = http_request(
        f"{base_url}/api/v1/normalize",
        method="POST",
        data=huge_data.encode("utf-8"),
        headers={"Content-Length": str(len(huge_data)), "Content-Type": "application/json"},
    )
    assert status == 413
    err = json.loads(body.decode("utf-8"))["error"]
    assert err["code"] == "PAYLOAD_TOO_LARGE"

    print("   [PASS] Tất cả các mã lỗi (EMPTY_ADDRESS, ADDRESS_TOO_LONG, INVALID_JSON, PAYLOAD_TOO_LARGE) đều chuẩn xác.")


def test_batch_endpoint(base_url):
    print("5. Kiểm tra POST /api/v1/batch (hỗn hợp hợp lệ và lỗi item)...")
    batch_input = {
        "addresses": [
            {"id": "b1", "address": "Số 1 Đường Tràng Tiền, Hoàn Kiếm, Hà Nội"},
            {"id": "b2", "address": ""},  # Item rỗng cố tình
            {"id": "b3", "address": "456 Đường Nguyễn Trãi, Quận 5, TP Hồ Chí Minh"},
        ]
    }
    status, headers, body = http_request(
        f"{base_url}/api/v1/batch",
        method="POST",
        data=batch_input,
    )
    assert status == 200, f"Batch code={status}"
    payload = json.loads(body.decode("utf-8"))

    items = payload["items"]
    assert len(items) == 3
    assert payload["elapsed_ms"] > 0

    # Item 1: thành công
    assert items[0]["id"] == "b1"
    assert items[0]["status"] in ("processed", "needs_review")
    assert "Hà Nội" in items[0]["result"]["tinh"]

    # Item 2: lỗi riêng item, không làm hỏng cả batch
    assert items[1]["id"] == "b2"
    assert items[1]["status"] == "error"
    assert items[1]["error"]["code"] == "EMPTY_ADDRESS"

    # Item 3: thành công
    assert items[2]["id"] == "b3"
    assert items[2]["status"] in ("processed", "needs_review")
    assert "Hồ Chí Minh" in items[2]["result"]["tinh"]

    print(f"   [PASS] Batch hỗn hợp thành công: 2 hợp lệ, 1 lỗi riêng biệt được cô lập, elapsed={payload['elapsed_ms']}ms.")


def test_404_json_and_cors(base_url):
    print("6. Kiểm tra route /api 404 JSON và CORS preflight OPTIONS...")

    # 6a. Route 404
    status, headers, body = http_request(f"{base_url}/api/v1/undefined_route")
    assert status == 404
    assert headers.get("Content-Type", "").startswith("application/json")
    payload = json.loads(body.decode("utf-8"))
    assert payload["error"]["code"] == "NOT_FOUND"

    # 6b. CORS Preflight OPTIONS
    status, headers, _ = http_request(f"{base_url}/api/v1/normalize", method="OPTIONS")
    assert status == 204
    assert headers.get("Access-Control-Allow-Origin") == "*"
    assert "POST" in headers.get("Access-Control-Allow-Methods", "")

    print("   [PASS] 404 trả về JSON đúng chuẩn; CORS preflight OPTIONS trả về 204.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 65)
    print("CHẠY BỘ KIỂM THỬ HỢP ĐỒNG API - ADDRESS MAY CRY")
    print("=" * 65)

    with TestServerContext() as base_url:
        print(f"Máy chủ kiểm thử đang chạy tại: {base_url}\n")
        test_health(base_url)
        test_normalize_real_pipeline(base_url)
        test_normalize_giai_thich(base_url)
        test_unicode_nfd_nfc(base_url)
        test_validation_errors(base_url)
        test_batch_endpoint(base_url)
        test_404_json_and_cors(base_url)

    print("\n" + "=" * 65)
    print("TẤT CẢ KIỂM THỬ HỢP ĐỒNG API ĐÃ HOÀN TẤT THÀNH CÔNG 100%!")
    print("=" * 65)


if __name__ == "__main__":
    main()
