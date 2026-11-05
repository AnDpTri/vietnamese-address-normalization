"""Khởi chạy Address May Cry trên máy chủ (Docker / PaaS).

Nghe ở 0.0.0.0 và lấy cổng từ biến môi trường PORT (mặc định 8080),
vì các nền tảng đám mây tự cấp cổng qua biến này.

Trên Render gói miễn phí, máy chủ ngủ sau 15 phút không có truy cập từ ngoài.
Nếu có RENDER_EXTERNAL_URL (Render tự đặt), một luồng nền gọi /api/v1/health
qua địa chỉ công khai mỗi TU_PING_GIAY giây (mặc định 600) để máy chủ luôn thức.
Đặt TU_PING_GIAY=0 để tắt.
"""
import os
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from server import run_server  # noqa: E402


def _tu_ping(url: str, chu_ky: int) -> None:
    time.sleep(int(os.environ.get("TU_PING_CHO", "60")))  # chờ engine nạp xong
    while True:
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] tự ping {r.status}", flush=True)
        except Exception as e:  # mạng lỗi thì thử lại ở chu kỳ sau
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] tự ping lỗi: {e}", flush=True)
        time.sleep(chu_ky)


if __name__ == "__main__":
    url_ngoai = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    chu_ky = int(os.environ.get("TU_PING_GIAY", "600"))
    if url_ngoai and chu_ky > 0:
        threading.Thread(target=_tu_ping, args=(f"{url_ngoai}/api/v1/health", chu_ky), daemon=True).start()
    run_server(os.environ.get("HOST", "0.0.0.0"), int(os.environ.get("PORT", "8080")))
