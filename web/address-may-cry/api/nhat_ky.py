"""Nhật ký chuẩn hóa và báo sai.

AMC_LOG=render: ghi tệp JSONL trên máy chủ và gửi bản sao vào Render Logs.
Chỉ sự kiện báo sai có địa chỉ và ghi chú. AMC_LOG_DIR có thể trỏ tới ổ đĩa gắn ngoài.
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


def _ghi_tep_jsonl(thu_muc: Path, ngay: str, noi_dung: str) -> None:
    thu_muc.mkdir(parents=True, exist_ok=True, mode=0o700)
    tep = thu_muc / f"phien_{ngay}.jsonl"
    mo_tep = os.open(tep, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    with os.fdopen(mo_tep, "a", encoding="utf-8", newline="\n") as f:
        f.write(noi_dung + "\n")


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
    luc = time.localtime()
    dong = {"log_id": log_id, "loai": loai, "thoi_gian": time.strftime("%Y-%m-%dT%H:%M:%S", luc), **du_lieu}
    thu_muc = Path(os.environ.get("AMC_LOG_DIR") or LOG_DIR)
    da_luu = False
    with _lock:
        try:
            _ghi_tep_jsonl(thu_muc, time.strftime("%Y%m%d", luc), json.dumps(dong, ensure_ascii=False))
            da_luu = True
        except (OSError, UnicodeError):
            pass
        if tren_render:
            try:
                ban_sao = json.dumps({**dong, "luu_tep": da_luu}, ensure_ascii=False)
                print(f"AMC_LOG {ban_sao}", flush=True)
                da_luu = True
            except (OSError, UnicodeError):
                pass
    return log_id if da_luu else None


def ghi_loi(dau_vao: str, loi: Exception) -> str | None:
    if os.environ.get("AMC_LOG") == "render":
        return ghi("loi_xu_ly", {"loai_loi": type(loi).__name__})
    return ghi("loi_xu_ly", {"input": dau_vao, "loi": repr(loi), "traceback": traceback.format_exc()})
