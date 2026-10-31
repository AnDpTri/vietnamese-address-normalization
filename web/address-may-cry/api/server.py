"""Máy chủ HTTP API cho Address May Cry.
Dùng standard library Python (http.server.ThreadingHTTPServer).
Hỗ trợ đầy đủ:
- GET /api/v1/health
- POST /api/v1/normalize
- POST /api/v1/batch
- POST /api/v1/feedback (người dùng báo kết quả sai; chỉ ghi khi AMC_LOG=1)
- POST /api/v1/excel/xem, POST /api/v1/excel/chay, GET /api/v1/excel/tien_do, GET /api/v1/excel/tai
  (chuẩn hóa một cột trong file .xlsx, chạy nền; xem excel_job.py)
- CORS preflight OPTIONS
- Xử lý lỗi JSON nhất quán (400, 404, 413, 503)
- Phục vụ static build từ web/address-may-cry/dist (SPA fallback an toàn)
- Thread-safe inference với NlpEngineAdapter singleton
"""

import json
import mimetypes
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

# Thiết lập đường dẫn
API_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = API_DIR.parent.parent.parent
DIST_DIR = API_DIR.parent / "dist"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from engine import NlpEngineAdapter
import nhat_ky
import excel_job

# Giới hạn kỹ thuật theo hợp đồng
MAX_BODY_BYTES = 1024 * 1024  # 1 MB
MAX_ADDRESS_CHARS = 2048      # 2048 ký tự
MAX_BATCH_SIZE = 100          # 100 phần tử/batch


class AddressMayCryApiHandler(BaseHTTPRequestHandler):
    """Bộ xử lý HTTP request tuân thủ CONTRACT.md."""

    server_version = "AddressMayCry-API/1.0"

    def _set_headers(
        self,
        status_code: int = HTTPStatus.OK,
        content_type: str = "application/json; charset=utf-8",
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        # CORS headers (cho phép Vite proxy hoặc direct fetch từ localhost)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-File-Name")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()

    def _send_json(self, data: Any, status_code: int = HTTPStatus.OK) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self._set_headers(
            status_code=status_code,
            content_type="application/json; charset=utf-8",
            extra_headers={"Content-Length": str(len(payload))},
        )
        self.wfile.write(payload)

    def _send_error_json(self, code: str, message: str, status_code: int) -> None:
        self._send_json({"error": {"code": code, "message": message}}, status_code=status_code)

    def do_OPTIONS(self) -> None:
        """Xử lý CORS preflight request."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-File-Name")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # 1. Endpoint /api/v1/health
        if path == "/api/v1/health":
            self._handle_health()
            return

        # Tiến độ và tải kết quả chuẩn hóa file Excel
        if path in ("/api/v1/excel/tien_do", "/api/v1/excel/tai"):
            self._handle_excel_get(path, parse_qs(parsed_url.query).get("job", [""])[0])
            return

        # 2. Các route /api/* không hợp lệ -> 404 JSON
        if path.startswith("/api/"):
            self._send_error_json("NOT_FOUND", "Endpoint API không tồn tại.", HTTPStatus.NOT_FOUND)
            return

        # 3. Phục vụ static production build nếu có
        self._serve_static_or_spa(path)

    def do_POST(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/api/v1/normalize":
            self._handle_normalize()
        elif path == "/api/v1/batch":
            self._handle_batch()
        elif path == "/api/v1/feedback":
            self._handle_feedback()
        elif path == "/api/v1/excel/xem":
            self._handle_excel_xem()
        elif path == "/api/v1/excel/chay":
            self._handle_excel_chay()
        elif path.startswith("/api/"):
            self._send_error_json("NOT_FOUND", "Endpoint API không tồn tại.", HTTPStatus.NOT_FOUND)
        else:
            self._send_error_json("METHOD_NOT_ALLOWED", "Phương thức không được hỗ trợ.", HTTPStatus.METHOD_NOT_ALLOWED)

    def _read_body_json(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Đọc và parse body JSON an toàn với giới hạn kích thước."""
        content_length_header = self.headers.get("Content-Length")
        if not content_length_header:
            return None, "Thiếu Content-Length trong yêu cầu."

        try:
            content_length = int(content_length_header)
        except ValueError:
            return None, "Content-Length không hợp lệ."

        if content_length > MAX_BODY_BYTES:
            return None, "PAYLOAD_TOO_LARGE"

        if content_length < 0:
            return None, "Content-Length âm."

        raw_data = self.rfile.read(content_length)
        try:
            data = json.loads(raw_data.decode("utf-8"))
            return data, None
        except Exception:
            return None, "INVALID_JSON"

    def _handle_excel_xem(self) -> None:
        """Nhận file .xlsx (body nhị phân, tên file ở header X-File-Name), trả sheet, tiêu đề, dòng mẫu."""
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n <= 0:
            self._send_error_json("EMPTY_FILE", "Chưa có file.", HTTPStatus.BAD_REQUEST)
            return
        if n > excel_job.MAX_FILE_BYTES:
            self._send_error_json("PAYLOAD_TOO_LARGE", "File vượt quá 10 MB.", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return
        du_lieu = self.rfile.read(n)
        try:
            self._send_json(excel_job.xem(du_lieu, unquote(self.headers.get("X-File-Name") or "dia_chi.xlsx")))
        except ValueError as e:
            self._send_error_json("INVALID_FILE", str(e), HTTPStatus.BAD_REQUEST)

    def _handle_excel_chay(self) -> None:
        eng = NlpEngineAdapter.get_instance()
        if not eng.is_ready():
            self._send_error_json("SERVICE_UNAVAILABLE", "Hệ thống chuẩn hóa địa chỉ chưa sẵn sàng.", HTTPStatus.SERVICE_UNAVAILABLE)
            return
        body, err = self._read_body_json()
        if err or not isinstance(body, dict) or not isinstance(body.get("cot"), int):
            self._send_error_json("INVALID_INPUT", "Cần file_id, sheet và cot (số thứ tự cột).", HTTPStatus.BAD_REQUEST)
            return

        def chuan_hoa(dia_chi: str) -> Dict[str, Any]:
            res, _, _ = eng.normalize(dia_chi[:MAX_ADDRESS_CHARS])
            res.pop("_chan_doan", None)
            return res

        def ghi_log(dia_chi: str, res: Dict[str, Any]) -> None:
            nhat_ky.ghi("chuan_hoa", {"nguon": "excel", "input": dia_chi, "engine": eng.engine_name, "result": res})

        try:
            job_id = excel_job.chay(str(body.get("file_id", "")), str(body.get("sheet", "")), body["cot"], chuan_hoa, ghi_log)
            self._send_json({"job_id": job_id})
        except ValueError as e:
            self._send_error_json("INVALID_INPUT", str(e), HTTPStatus.BAD_REQUEST)

    def _handle_excel_get(self, path: str, job_id: str) -> None:
        if path.endswith("tien_do"):
            td = excel_job.tien_do(job_id)
            if td is None:
                self._send_error_json("NOT_FOUND", "Không tìm thấy lượt xử lý (có thể đã hết hạn).", HTTPStatus.NOT_FOUND)
            else:
                self._send_json(td)
            return
        kq = excel_job.tai(job_id)
        if kq is None:
            self._send_error_json("NOT_FOUND", "Kết quả chưa sẵn sàng hoặc đã hết hạn.", HTTPStatus.NOT_FOUND)
            return
        from urllib.parse import quote
        self._set_headers(
            status_code=HTTPStatus.OK,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            extra_headers={"Content-Length": str(len(kq["du_lieu"])),
                           "Content-Disposition": f"attachment; filename*=UTF-8''{quote(kq['ten'])}"},
        )
        self.wfile.write(kq["du_lieu"])

    def _handle_health(self) -> None:
        eng = NlpEngineAdapter.get_instance()
        status_str = eng.status  # 'ok', 'loading', 'error'
        http_code = HTTPStatus.OK if status_str in ("ok", "loading") else HTTPStatus.SERVICE_UNAVAILABLE

        response_data = {
            "status": status_str,
            "engine": eng.engine_name,
            "target_date": eng.target_date,
            "limits": {
                "max_chars": MAX_ADDRESS_CHARS,
                "max_batch": MAX_BATCH_SIZE,
            },
            "message": eng.error_message or "Sẵn sàng chuẩn hóa địa chỉ Việt Nam theo mốc 01/07/2025.",
        }
        self._send_json(response_data, status_code=http_code)

    def _handle_normalize(self) -> None:
        eng = NlpEngineAdapter.get_instance()
        if not eng.is_ready():
            self._send_error_json(
                "SERVICE_UNAVAILABLE",
                eng.error_message or "Hệ thống chuẩn hóa địa chỉ đang tải hoặc gặp sự cố.",
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return

        body, err = self._read_body_json()
        if err == "PAYLOAD_TOO_LARGE":
            self._send_error_json("PAYLOAD_TOO_LARGE", "Dữ liệu yêu cầu vượt quá giới hạn 1MB.", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return
        if err == "INVALID_JSON" or body is None or not isinstance(body, dict):
            self._send_error_json("INVALID_JSON", "Định dạng JSON yêu cầu không hợp lệ.", HTTPStatus.BAD_REQUEST)
            return

        if "address" not in body or not isinstance(body["address"], str):
            self._send_error_json("INVALID_INPUT", "Trường 'address' bắt buộc và phải là chuỗi ký tự.", HTTPStatus.BAD_REQUEST)
            return

        raw_address = body["address"]
        clean_address = raw_address.strip()
        if not clean_address:
            self._send_error_json("EMPTY_ADDRESS", "Địa chỉ đầu vào không được để trống.", HTTPStatus.BAD_REQUEST)
            return

        if len(raw_address) > MAX_ADDRESS_CHARS:
            self._send_error_json(
                "ADDRESS_TOO_LONG",
                f"Địa chỉ vượt quá giới hạn tối đa {MAX_ADDRESS_CHARS} ký tự.",
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            )
            return

        try:
            res_dict, elapsed_ms, status = eng.normalize(raw_address)
            chan_doan = res_dict.pop("_chan_doan", None)
            response = {
                "input": raw_address,
                "result": res_dict,
                "elapsed_ms": elapsed_ms,
                "status": status,
                "thanh_phan": res_dict.get("thanh_phan", []),
                "ket_qua_hai_dong": res_dict.get("ket_qua_hai_dong"),
            }
            response["log_id"] = nhat_ky.ghi("chuan_hoa", {"nguon": "mot_dia_chi", "input": raw_address,
                                                             "status": status, "elapsed_ms": elapsed_ms,
                                                             "engine": eng.engine_name, "result": res_dict,
                                                             "chan_doan": chan_doan})
            self._send_json(response, HTTPStatus.OK)
        except Exception as e:
            nhat_ky.ghi_loi(raw_address, e)
            self._send_error_json("PROCESSING_ERROR", "Lỗi trong quá trình chuẩn hóa địa chỉ.", HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_batch(self) -> None:
        eng = NlpEngineAdapter.get_instance()
        if not eng.is_ready():
            self._send_error_json(
                "SERVICE_UNAVAILABLE",
                eng.error_message or "Hệ thống chuẩn hóa địa chỉ chưa sẵn sàng.",
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return

        body, err = self._read_body_json()
        if err == "PAYLOAD_TOO_LARGE":
            self._send_error_json("PAYLOAD_TOO_LARGE", "Dữ liệu yêu cầu vượt quá giới hạn 1MB.", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return
        if err == "INVALID_JSON" or body is None or not isinstance(body, dict):
            self._send_error_json("INVALID_JSON", "Định dạng JSON yêu cầu không hợp lệ.", HTTPStatus.BAD_REQUEST)
            return

        if "addresses" not in body or not isinstance(body["addresses"], list):
            self._send_error_json("INVALID_INPUT", "Trường 'addresses' bắt buộc và phải là mảng danh sách.", HTTPStatus.BAD_REQUEST)
            return

        addresses_list = body["addresses"]
        if len(addresses_list) == 0:
            self._send_error_json("EMPTY_BATCH", "Danh sách địa chỉ không được để trống.", HTTPStatus.BAD_REQUEST)
            return

        if len(addresses_list) > MAX_BATCH_SIZE:
            self._send_error_json(
                "BATCH_SIZE_EXCEEDED",
                f"Số lượng địa chỉ trong lô vượt quá giới hạn tối đa {MAX_BATCH_SIZE}.",
                HTTPStatus.BAD_REQUEST,
            )
            return

        t_batch_start = time.perf_counter()
        results_items: List[Dict[str, Any]] = []

        for idx, item in enumerate(addresses_list):
            if not isinstance(item, dict):
                results_items.append({
                    "id": str(idx + 1),
                    "input": "",
                    "status": "error",
                    "error": {"code": "INVALID_ITEM", "message": "Phần tử trong lô phải là đối tượng JSON."},
                })
                continue

            item_id = str(item.get("id") or f"item_{idx + 1}")
            addr_val = item.get("address")

            if not isinstance(addr_val, str):
                results_items.append({
                    "id": item_id,
                    "input": "",
                    "status": "error",
                    "error": {"code": "INVALID_ADDRESS", "message": "Trường 'address' phải là chuỗi ký tự."},
                })
                continue

            if not addr_val.strip():
                results_items.append({
                    "id": item_id,
                    "input": addr_val,
                    "status": "error",
                    "error": {"code": "EMPTY_ADDRESS", "message": "Địa chỉ đầu vào không được để trống."},
                })
                continue

            if len(addr_val) > MAX_ADDRESS_CHARS:
                results_items.append({
                    "id": item_id,
                    "input": addr_val,
                    "status": "error",
                    "error": {"code": "ADDRESS_TOO_LONG", "message": f"Địa chỉ vượt quá {MAX_ADDRESS_CHARS} ký tự."},
                })
                continue

            # Xử lý normalize hợp lệ
            try:
                res_dict, elapsed_ms, status = eng.normalize(addr_val)
                chan_doan = res_dict.pop("_chan_doan", None)
                results_items.append({
                    "id": item_id,
                    "input": addr_val,
                    "status": status,
                    "result": res_dict,
                    "elapsed_ms": elapsed_ms,
                    "thanh_phan": res_dict.get("thanh_phan", []),
                    "ket_qua_hai_dong": res_dict.get("ket_qua_hai_dong"),
                    "log_id": nhat_ky.ghi("chuan_hoa", {"nguon": "hang_loat", "id": item_id, "input": addr_val,
                                                        "status": status, "elapsed_ms": elapsed_ms,
                                                        "engine": eng.engine_name, "result": res_dict,
                                                        "chan_doan": chan_doan}),
                })
            except Exception as e:
                nhat_ky.ghi_loi(addr_val, e)
                results_items.append({
                    "id": item_id,
                    "input": addr_val,
                    "status": "error",
                    "error": {"code": "PROCESSING_ERROR", "message": "Lỗi nội bộ khi xử lý địa chỉ."},
                })

        batch_elapsed_ms = round((time.perf_counter() - t_batch_start) * 1000.0, 2)
        response_payload = {
            "items": results_items,
            "elapsed_ms": batch_elapsed_ms,
        }
        self._send_json(response_payload, HTTPStatus.OK)

    def _handle_feedback(self) -> None:
        body, err = self._read_body_json()
        if err or not isinstance(body, dict) or not isinstance(body.get("input"), str):
            self._send_error_json("INVALID_INPUT", "Cần trường 'input' (chuỗi) và tùy chọn 'log_id', 'ghi_chu'.", HTTPStatus.BAD_REQUEST)
            return
        ghi_chu = body.get("ghi_chu") if isinstance(body.get("ghi_chu"), str) else ""
        log_id = nhat_ky.ghi("bao_sai", {"input": body["input"], "ref_log_id": body.get("log_id"),
                                         "ghi_chu": ghi_chu[:1000]})
        self._send_json({"saved": log_id is not None, "log_id": log_id}, HTTPStatus.OK)

    def _serve_static_or_spa(self, req_path: str) -> None:
        """Phục vụ file static từ dist nếu tồn tại, SPA fallback về index.html."""
        if not DIST_DIR.exists() or not DIST_DIR.is_dir():
            # Nếu chưa build dist, trả trang thông tin API đơn giản
            info_html = (
                "<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'>"
                "<title>Address May Cry API</title></head><body>"
                "<h1>Address May Cry API Server</h1>"
                "<p>Máy chủ API đang hoạt động tại cổng 8080.</p>"
                "<ul>"
                "<li><a href='/api/v1/health'>/api/v1/health</a></li>"
                "</ul>"
                "<p>Frontend Vite dev server chạy tại: <code>http://localhost:5173</code></p>"
                "</body></html>"
            ).encode("utf-8")
            self._set_headers(HTTPStatus.OK, content_type="text/html; charset=utf-8")
            self.wfile.write(info_html)
            return

        # Xóa dấu '/' đầu
        rel_path = req_path.lstrip("/")
        if not rel_path:
            rel_path = "index.html"

        candidate_file = (DIST_DIR / rel_path).resolve()

        # Ngăn Path Traversal
        try:
            candidate_file.relative_to(DIST_DIR.resolve())
        except ValueError:
            self._send_error_json("FORBIDDEN", "Truy cập bị từ chối.", HTTPStatus.FORBIDDEN)
            return

        if candidate_file.is_file():
            self._send_static_file(candidate_file)
        else:
            # SPA Fallback về index.html
            index_file = DIST_DIR / "index.html"
            if index_file.is_file():
                self._send_static_file(index_file)
            else:
                self._send_error_json("NOT_FOUND", "Không tìm thấy tệp giao diện.", HTTPStatus.NOT_FOUND)

    def _send_static_file(self, filepath: Path) -> None:
        try:
            suffix = filepath.suffix.lower()
            if suffix == ".js":
                mime_type = "application/javascript"
            elif suffix == ".css":
                mime_type = "text/css"
            elif suffix == ".svg":
                mime_type = "image/svg+xml"
            elif suffix == ".json":
                mime_type = "application/json"
            elif suffix == ".html":
                mime_type = "text/html"
            else:
                mime_type, _ = mimetypes.guess_type(str(filepath))

            content_type = mime_type or "application/octet-stream"
            if content_type.startswith("text/") or content_type in ("application/javascript", "application/json"):
                content_type += "; charset=utf-8"

            data = filepath.read_bytes()
            cache_ctrl = "public, max-age=31536000, immutable" if "/assets/" in str(filepath).replace("\\", "/") else "no-cache"

            self._set_headers(
                status_code=HTTPStatus.OK,
                content_type=content_type,
                extra_headers={
                    "Content-Length": str(len(data)),
                    "Cache-Control": cache_ctrl,
                },
            )
            self.wfile.write(data)
        except Exception:
            self._send_error_json("INTERNAL_ERROR", "Lỗi đọc tệp tĩnh.", HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args: Any) -> None:
        """Ghi log ngắn gọn chuẩn HTTP, bảo vệ quyền riêng tư (không in raw address)."""
        sys.stderr.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {args[0]} - {args[1]}\n")


def create_server(host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """Tạo instance ThreadingHTTPServer."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, AddressMayCryApiHandler)
    return httpd


def run_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    # Nạp trước engine để sẵn sàng phục vụ
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Đang khởi tạo NLP Engine...")
    eng = NlpEngineAdapter.get_instance()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Engine status: {eng.status} ({eng.engine_name})")

    server = create_server(host, port)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Address May Cry API Server lắng nghe tại http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang dừng máy chủ...")
    finally:
        server.server_close()
        print("Máy chủ đã dừng.")


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(host, port)
