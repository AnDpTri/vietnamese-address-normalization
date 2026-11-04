"""Khởi chạy Address May Cry trên máy chủ (Docker / PaaS).

Nghe ở 0.0.0.0 và lấy cổng từ biến môi trường PORT (mặc định 8080),
vì các nền tảng đám mây tự cấp cổng qua biến này.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from server import run_server  # noqa: E402

if __name__ == "__main__":
    run_server(os.environ.get("HOST", "0.0.0.0"), int(os.environ.get("PORT", "8080")))
