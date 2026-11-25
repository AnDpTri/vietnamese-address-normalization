"""Nhật ký chuẩn hóa và báo sai.

AMC_LOG=render: ghi sự kiện JSON vào stdout; chỉ báo sai có địa chỉ và ghi chú.
AMC_LOG=1: ghi nhật ký phát triển đầy đủ vào api/logs/phien_YYYYMMDD.jsonl.
"""

import json
import os
import re
import threading
import time
import traceback
import uuid
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
_lock = threading.Lock()
_TRUONG_LOG_RENDER = {
    "chuan_hoa": ("nguon", "status", "elapsed_ms", "engine"),
    "loi_xu_ly": ("loai_loi",),
    "bao_sai": ("input", "ghi_chu", "ref_log_id"),
}


def bat() -> bool:
    return os.environ.get("AMC_LOG") == "1"


def ghi(loai: str, du_lieu: dict) -> str | None:
    """Ghi một sự kiện; trả về log_id (None nếu log tắt). Lỗi ghi log không được làm hỏng request."""
    tren_render = os.environ.get("AMC_LOG") == "render"
    if not tren_render and not bat():
        return None
    if tren_render:
        truong = _TRUONG_LOG_RENDER.get(loai, ())
        du_lieu = {k: du_lieu[k] for k in truong if k in du_lieu}
        ref_log_id = du_lieu.get("ref_log_id")
        if not isinstance(ref_log_id, str) or not re.fullmatch(r"[0-9a-f]{12}", ref_log_id):
            du_lieu.pop("ref_log_id", None)

    log_id = uuid.uuid4().hex[:12]
    dong = {"log_id": log_id, "loai": loai, "thoi_gian": time.strftime("%Y-%m-%dT%H:%M:%S"), **du_lieu}
    try:
        noi_dung = json.dumps(dong, ensure_ascii=False)
        with _lock:
            if tren_render:
                print(f"AMC_LOG {noi_dung}", flush=True)
            else:
                LOG_DIR.mkdir(exist_ok=True)
                tep = LOG_DIR / time.strftime("phien_%Y%m%d.jsonl")
                with open(tep, "a", encoding="utf-8", newline="\n") as f:
                    f.write(noi_dung + "\n")
    except (OSError, UnicodeError):
        return None
    return log_id


def ghi_loi(dau_vao: str, loi: Exception) -> str | None:
    if os.environ.get("AMC_LOG") == "render":
        return ghi("loi_xu_ly", {"loai_loi": type(loi).__name__})
    return ghi("loi_xu_ly", {"input": dau_vao, "loi": repr(loi), "traceback": traceback.format_exc()})
