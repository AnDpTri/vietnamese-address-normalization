"""Module adapter bọc pipeline chuẩn hóa địa chỉ NLP (Address May Cry).
Khởi tạo model 1 lần (Singleton), chạy CPU 1 thread, bảo vệ thread-safe với Lock.
Hoàn toàn tuân thủ hợp đồng CONTRACT.md và src/shared/contracts.ts.
Engine: CNN v3_tc + Ranker v3_tc (hai module).
"""

import os
import sys
import time
import re
import csv
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

# Xác định root mã NLP theo biến môi trường AMC_CODE_ROOT (mặc định gốc repo)
AMC_CODE_ROOT = os.environ.get("AMC_CODE_ROOT", str(Path(__file__).resolve().parents[3]))
CODE_ROOT_PATH = Path(AMC_CODE_ROOT).resolve()
if str(CODE_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT_PATH))

# Đặt số thread torch trước khi nạp
import torch
torch.set_num_threads(1)

from src.danh_muc import DanhMuc
from src.tien_xu_ly.char_cnn import BoTachCharCNN
from src.tien_xu_ly.xep_hang import BoXepHang
from src.tien_xu_ly.chuan_ten_duong import TuDienDuong
from src.chuan_hoa import BoChuanHoa
from src.kieu_du_lieu import KetQua

PURE_SEPARATORS = set(" \t\r\n,;-–—|~#()[]{}")
PHONE_RE = re.compile(r"(?:sđt|sdt|đt|dt|tel|phone|hotline|zalo|điện thoại)?[:.\s]*0\d{8,10}\b", re.IGNORECASE)


class NlpEngineAdapter:
    """Adapter bọc BoChuanHoa singleton và thread-safe cho HTTP API."""

    _instance: Optional["NlpEngineAdapter"] = None
    _init_lock = threading.Lock()

    def __init__(self):
        self._lock = threading.Lock()
        self.status = "loading"
        self.error_message: Optional[str] = None
        self.engine_name = "CNN v3_tc + Ranker v3_tc (hai module)"
        self.target_date = "2025-07-01"
        self._pipe: Optional[BoChuanHoa] = None
        self._dm: Optional[DanhMuc] = None
        self._cnn: Optional[BoTachCharCNN] = None
        self._ranker: Optional[BoXepHang] = None
        self._tdd: Optional[TuDienDuong] = None

        # Bảng tra cứu đối chiếu hành chính
        self._doi_chieu_xa: Dict[str, List[Dict[str, str]]] = {}
        self._moi_xa: Dict[str, Dict[str, str]] = {}
        self._moi_tinh: Dict[str, str] = {}
        self._cu_xa: Dict[str, Dict[str, str]] = {}
        self._cu_huyen: Dict[str, Dict[str, str]] = {}
        self._cu_tinh: Dict[str, str] = {}

        self._load_reference_data()
        self._load_models()

    def _load_reference_data(self) -> None:
        """Nạp các bảng đối chiếu từ data/clean của CODE_ROOT."""
        try:
            clean_dir = CODE_ROOT_PATH / "data" / "clean"
            dc_path = clean_dir / "doi_chieu_xa_cu_moi.csv"
            moi_path = clean_dir / "moi_tinh_xa.csv"
            cu_path = clean_dir / "cu_tinh_huyen_xa.csv"

            if dc_path.exists():
                with open(dc_path, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        self._doi_chieu_xa.setdefault(row["ma_xa_cu"], []).append(row)

            if moi_path.exists():
                with open(moi_path, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        self._moi_xa[row["ma_xa"]] = row
                        self._moi_tinh[row["ma_tinh"]] = row["ten_tinh"]

            # Chữ loại của huyện/tỉnh cũ và tỉnh mới (Quận, Thành phố...) để hiển thị địa chỉ sau tiền xử lý.
            self._loai_huyen, self._loai_tinh_cu, self._loai_tinh_moi = {}, {}, {}
            for ten_tep, kho, cot_ma, cot_loai in (("cu_huyen.csv", self._loai_huyen, "ma_huyen", "loai_huyen"),
                                                   ("cu_tinh.csv", self._loai_tinh_cu, "ma_tinh", "loai_tinh"),
                                                   ("moi_tinh.csv", self._loai_tinh_moi, "ma_tinh", "loai_tinh")):
                duong_dan = cu_path.parent / ten_tep
                if duong_dan.exists():
                    with open(duong_dan, encoding="utf-8-sig") as f:
                        for row in csv.DictReader(f):
                            kho[row[cot_ma]] = row[cot_loai]

            if cu_path.exists():
                with open(cu_path, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        self._cu_xa[row["ma_xa"]] = row
                        self._cu_huyen[row["ma_huyen"]] = row
                        self._cu_tinh[row["ma_tinh"]] = row["ten_tinh"]
        except Exception as e:
            # Ghi nhận nhưng không chặn nếu file thiếu
            print(f"Cảnh báo nạp reference data: {e}", file=sys.stderr)

    def _load_models(self) -> None:
        try:
            cnn_path = CODE_ROOT_PATH / "mo_hinh" / "thu_nghiem" / "char_v3_tc" / "char_cnn.pt"
            ranker_path = CODE_ROOT_PATH / "mo_hinh" / "thu_nghiem" / "char_v3_tc" / "ranker.txt"
            dict_path = CODE_ROOT_PATH / "danh_gia" / "ket_qua" / "tu_dien_duong_v5.json"

            if not cnn_path.exists():
                raise FileNotFoundError(f"Không tìm thấy checkpoint CharCNN: {cnn_path}")
            if not ranker_path.exists():
                raise FileNotFoundError(f"Không tìm thấy checkpoint Ranker: {ranker_path}")
            if not dict_path.exists():
                raise FileNotFoundError(f"Không tìm thấy từ điển đường v5: {dict_path}")

            # Danh mục mặc định của DanhMuc()
            self._dm = DanhMuc()
            self._cnn = BoTachCharCNN(cnn_path, threads=1)
            self._ranker = BoXepHang(ranker_path, self._cnn.ma_bam, self._dm.ma_bam)
            self._tdd = TuDienDuong(dict_path)

            self._pipe = BoChuanHoa(
                self._dm,
                bo_tach=self._cnn,
                bo_xep_hang=self._ranker,
                tu_dien_duong=self._tdd,
                bao_ve_duong=True,
                tien_to_mac_dinh=True,
            )

            # Warm-up 1 câu ngắn để khởi tạo bộ nhớ torch
            with self._lock:
                _ = self._pipe.chuan_hoa("Hà Nội")

            self.status = "ok"
            self.error_message = None
        except Exception as e:
            self.status = "error"
            self.error_message = f"Lỗi khởi tạo NLP Engine: {type(e).__name__}: {e}"
            self._pipe = None

    @classmethod
    def get_instance(cls) -> "NlpEngineAdapter":
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def is_ready(self) -> bool:
        return self.status == "ok" and self._pipe is not None

    def build_thanh_phan(self, raw_address: str, res_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Dựng danh sách thanh_phan phủ toàn bộ chuỗi nhập theo đúng thứ tự."""
        dau_vet = res_dict.get("dau_vet") or []
        canh_bao = set(res_dict.get("canh_bao") or [])
        xa_moi_ung_vien = res_dict.get("xa_moi_ung_vien") or []

        spans: List[Dict[str, Any]] = []
        for dv in dau_vet:
            start = dv.get("ky_tu_bat_dau")
            end = dv.get("ky_tu_ket_thuc")
            doan_goc = dv.get("doan_goc", "")
            if start is None or end is None or start >= end:
                continue

            # Kiểm tra đúng vị trí trong input
            if raw_address[start:end] != doan_goc:
                pos = raw_address.find(doan_goc)
                if pos != -1:
                    start = pos
                    end = pos + len(doan_goc)
                else:
                    continue

            truong = dv.get("truong", "")
            ma = dv.get("ma", "")
            moc = dv.get("moc", "cu")
            gia_tri = dv.get("gia_tri", "")

            # Đơn vị hành chính nhận ra trong câu nhưng không tra được (tiền xử lý ghi ma rỗng + lý do)
            if truong in ("xa", "huyen", "tinh") and not ma:
                nhan_la = truong
                chuan_hoa = doan_goc
                doi_chieu = "khong"
                ly_do = ("Có đơn vị cùng tên nhưng không cùng địa bàn với các phần còn lại của địa chỉ"
                         if dv.get("kieu_khop") == "khong_khop_dia_ban"
                         else "Không có trong danh mục hành chính (có thể là tên trước khi sáp nhập)")
                ket_qua_moi = ""
            # Kiểm tra nếu duong nhưng thực chất là SĐT
            elif truong == "duong" and PHONE_RE.search(doan_goc):
                nhan_la = "bo_qua"
                chuan_hoa = ""
                doi_chieu = "bo_qua"
                ly_do = "Không thuộc địa chỉ (số điện thoại/ghi chú)"
                ket_qua_moi = ""
            elif truong in ("so_nha", "ngo_ngach_hem", "thon_xom", "duong"):
                nhan_la = truong
                chuan_hoa = gia_tri or doan_goc
                doi_chieu = "khong"
                labels = {
                    "so_nha": "số nhà",
                    "ngo_ngach_hem": "ngõ ngách",
                    "thon_xom": "thôn xóm",
                    "duong": "tên đường",
                }
                ly_do = f"Không có dữ liệu chuẩn để đối chiếu {labels.get(truong, truong)}, chỉ chuẩn hóa cách viết"
                ket_qua_moi = chuan_hoa
            elif truong == "huyen":
                nhan_la = "huyen"
                h_info = self._cu_huyen.get(ma)
                if h_info:
                    ten_h = h_info.get("ten_huyen", "")
                    prefix = "Quận" if "quận" in doan_goc.lower() else ("Huyện" if "huyện" in doan_goc.lower() else ("Thị xã" if "thị xã" in doan_goc.lower() or "tx" in doan_goc.lower() else ""))
                    chuan_hoa = f"{prefix} {ten_h}".strip() if prefix else ten_h
                else:
                    chuan_hoa = doan_goc.title()
                doi_chieu = "co"
                ly_do = "Theo cải cách hành chính 01/07/2025, không còn cấp huyện"
                ket_qua_moi = "Không còn cấp huyện"
            elif truong == "tinh":
                nhan_la = "tinh"
                chuan_hoa = res_dict.get("tinh") or self._moi_tinh.get(ma) or self._cu_tinh.get(ma) or doan_goc
                doi_chieu = "co"
                ly_do = "Đã là đơn vị mới" if moc == "moi" else "Đơn vị hành chính cấp tỉnh/thành phố"
                ket_qua_moi = res_dict.get("tinh") or chuan_hoa
            elif truong == "xa":
                nhan_la = "xa"
                if moc == "moi":
                    chuan_hoa = res_dict.get("xa_phuong") or doan_goc
                    doi_chieu = "co"
                    ly_do = "Đã là đơn vị mới"
                    ket_qua_moi = chuan_hoa
                else:
                    x_info = self._cu_xa.get(ma)
                    if x_info:
                        chuan_hoa = f"{x_info['loai_xa']} {x_info['ten_xa']}".strip()
                    else:
                        chuan_hoa = doan_goc.title()

                    if "xa_bi_chia" in canh_bao or len(xa_moi_ung_vien) > 1:
                        doi_chieu = "co"
                        n_cand = len(xa_moi_ung_vien) if len(xa_moi_ung_vien) > 1 else len(self._doi_chieu_xa.get(ma, []))
                        ly_do = f"Xã cũ bị chia về {n_cand if n_cand > 1 else 2} xã mới, chưa đủ thông tin để chọn"
                        ket_qua_moi = ""
                    else:
                        records = self._doi_chieu_xa.get(ma, [])
                        if records:
                            rec = records[0]
                            ten_cu = rec.get("ten_xa_cu") or chuan_hoa
                            ten_moi = rec.get("ten_xa_moi") or res_dict.get("xa_phuong", "")
                            ghi_chu = rec.get("ghi_chu", "")
                            doi_chieu = "co"
                            ket_qua_moi = res_dict.get("xa_phuong") or ten_moi
                            if ghi_chu == "Nhập toàn bộ":
                                ly_do = f"{ten_cu} (cũ) đã nhập toàn bộ vào {ket_qua_moi}"
                            elif ghi_chu == "Giữ nguyên":
                                ly_do = f"{ten_cu} giữ nguyên địa giới thành {ket_qua_moi}"
                            else:
                                ly_do = f"{ten_cu} chuyển đổi thành {ket_qua_moi}"
                        else:
                            if res_dict.get("xa_phuong"):
                                doi_chieu = "co"
                                ket_qua_moi = res_dict["xa_phuong"]
                                ly_do = f"Chuyển đổi sang {ket_qua_moi}"
                            else:
                                doi_chieu = "khong"
                                ket_qua_moi = ""
                                ly_do = "Không tìm thấy thông tin đối chiếu cho xã/phường này"
            else:
                nhan_la = "bo_qua"
                chuan_hoa = ""
                doi_chieu = "bo_qua"
                ly_do = "Không thuộc địa chỉ (số điện thoại/ghi chú)"
                ket_qua_moi = ""

            spans.append({
                "bat_dau": start,
                "ket_thuc": end,
                "doan_goc": raw_address[start:end],
                "nhan_la": nhan_la,
                "chuan_hoa": chuan_hoa,
                "doi_chieu": doi_chieu,
                "ly_do": ly_do,
                "ket_qua_moi": ket_qua_moi,
            })

        # Sắp xếp các span nhận diện theo bat_dau
        spans.sort(key=lambda s: (s["bat_dau"], s["ket_thuc"]))

        # Phủ toàn bộ chuỗi: chèn các khoảng trống không thuộc span nào thành bo_qua
        final_spans: List[Dict[str, Any]] = []
        current_idx = 0

        for s in spans:
            if s["bat_dau"] > current_idx:
                gap_start = current_idx
                gap_end = s["bat_dau"]
                # Bỏ qua khoảng trắng và dấu phân cách thuần ở hai đầu gap
                while gap_start < gap_end and raw_address[gap_start] in PURE_SEPARATORS:
                    gap_start += 1
                while gap_end > gap_start and raw_address[gap_end - 1] in PURE_SEPARATORS:
                    gap_end -= 1
                if gap_start < gap_end:
                    gap_text = raw_address[gap_start:gap_end]
                    final_spans.append({
                        "bat_dau": gap_start,
                        "ket_thuc": gap_end,
                        "doan_goc": gap_text,
                        "nhan_la": "bo_qua",
                        "chuan_hoa": "",
                        "doi_chieu": "bo_qua",
                        "ly_do": "Không thuộc địa chỉ (số điện thoại/ghi chú)",
                        "ket_qua_moi": "",
                    })

            # Tránh chồng lấn nếu span sau nằm đè span trước
            if final_spans and s["bat_dau"] < final_spans[-1]["ket_thuc"]:
                continue

            final_spans.append(s)
            current_idx = max(current_idx, s["ket_thuc"])

        # Kiểm tra phần cuối chuỗi sau span cuối
        if current_idx < len(raw_address):
            gap_start = current_idx
            gap_end = len(raw_address)
            while gap_start < gap_end and raw_address[gap_start] in PURE_SEPARATORS:
                gap_start += 1
            while gap_end > gap_start and raw_address[gap_end - 1] in PURE_SEPARATORS:
                gap_end -= 1
            if gap_start < gap_end:
                gap_text = raw_address[gap_start:gap_end]
                final_spans.append({
                    "bat_dau": gap_start,
                    "ket_thuc": gap_end,
                    "doan_goc": gap_text,
                    "nhan_la": "bo_qua",
                    "chuan_hoa": "",
                    "doi_chieu": "bo_qua",
                    "ly_do": "Không thuộc địa chỉ (số điện thoại/ghi chú)",
                    "ket_qua_moi": "",
                })

        final_spans.sort(key=lambda s: s["bat_dau"])
        return final_spans

    def build_ket_qua_hai_dong(self, res_dict: Dict[str, Any], thanh_phan: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Tạo đối tượng ket_qua_hai_dong: co_doi_chieu và thieu_du_lieu_doi_chieu."""
        xa_phuong = (res_dict.get("xa_phuong") or "").strip()
        ma_xa = (res_dict.get("ma_xa") or "").strip()
        tinh = (res_dict.get("tinh") or "").strip()
        ma_tinh = (res_dict.get("ma_tinh") or "").strip()

        # Dòng 1: Có đối chiếu (xã/phường, tỉnh mới)
        co_parts = [p for p in [xa_phuong, tinh] if p]
        co_chuoi = ", ".join(co_parts)

        # Lấy các thành phần chi tiết từ thanh_phan (đã loại bỏ SĐT/ghi chú giả dạng đường)
        so_nha = (res_dict.get("so_nha") or "").strip()
        ngo_ngach_hem = (res_dict.get("ngo_ngach_hem") or "").strip()
        thon_xom = (res_dict.get("thon_xom") or "").strip()
        duong = (res_dict.get("duong") or "").strip()

        if thanh_phan is not None:
            duong_tp = [tp["chuan_hoa"] for tp in thanh_phan if tp["nhan_la"] == "duong"]
            if duong_tp:
                duong = duong_tp[0]
            elif any(tp["nhan_la"] == "bo_qua" and PHONE_RE.search(tp["doan_goc"]) for tp in thanh_phan):
                # Nếu chuỗi duong trong res_dict thực chất là SĐT, không đưa vào thieu_du_lieu
                if PHONE_RE.search(duong):
                    duong = ""

        thieu_parts = [p for p in [so_nha, ngo_ngach_hem, thon_xom, duong] if p]
        thieu_chuoi = ", ".join(thieu_parts)

        return {
            "co_doi_chieu": {
                "xa_phuong": xa_phuong,
                "ma_xa": ma_xa,
                "tinh": tinh,
                "ma_tinh": ma_tinh,
                "chuoi": co_chuoi,
            },
            "thieu_du_lieu_doi_chieu": {
                "so_nha": so_nha,
                "ngo_ngach_hem": ngo_ngach_hem,
                "thon_xom": thon_xom,
                "duong": duong,
                "chuoi": thieu_chuoi,
                "ghi_chu": "Chỉ chuẩn hóa cách viết, không có dữ liệu để kiểm đúng sai",
            },
        }

    THU_TU_TIEN_XU_LY = ("so_nha", "ngo_ngach_hem", "thon_xom", "duong", "xa", "huyen", "tinh")

    def _ten_hanh_chinh(self, cap: str, ma: str, moc: str) -> str:
        """Tên đầy đủ (kèm chữ loại) của đơn vị theo đúng mốc: cũ (trước 01/07/2025) hoặc mới."""
        if cap == "xa":
            r = (self._cu_xa if moc == "cu" else self._moi_xa).get(ma)
            return f"{r['loai_xa']} {r['ten_xa']}" if r else ""
        if cap == "huyen":
            r = self._cu_huyen.get(ma)
            return f"{self._loai_huyen.get(ma, '')} {r['ten_huyen']}".strip() if r else ""
        if cap == "tinh":
            ten, loai = (self._cu_tinh.get(ma), self._loai_tinh_cu.get(ma)) if moc == "cu" else                         (self._moi_tinh.get(ma), self._loai_tinh_moi.get(ma))
            return f"{loai or ''} {ten}".strip() if ten else ""
        return ""

    def dia_chi_sau_tien_xu_ly(self, res_dict: Dict[str, Any]) -> str:
        """Địa chỉ đã làm sạch, CHƯA chuyển đổi: chi tiết (số nhà, ngõ, thôn, đường) như kết quả; xã/huyện/tỉnh theo
        đúng mốc người dùng viết (cũ hoặc mới), xếp từ nhỏ đến lớn, bỏ phần không thuộc địa chỉ."""
        phan = {f: res_dict.get(f) for f in ("so_nha", "ngo_ngach_hem", "thon_xom", "duong") if res_dict.get(f)}
        for dv in res_dict.get("dau_vet") or []:
            cap, ma = dv.get("truong"), dv.get("ma")
            if cap in ("xa", "huyen", "tinh") and ma and cap not in phan:
                ten = self._ten_hanh_chinh(cap, ma, dv.get("moc") or "cu")
                if ten:
                    phan[cap] = ten
        return ", ".join(phan[t] for t in self.THU_TU_TIEN_XU_LY if t in phan)

    def normalize(self, address: str) -> Tuple[Dict[str, Any], float, str]:
        """Chuẩn hóa một địa chỉ đơn.

        Returns:
            Tuple[Dict[str, Any], float, str]:
                - result: dict tương thích AddressResult (kèm thanh_phan và ket_qua_hai_dong)
                - elapsed_ms: thời gian đo thực tế (ms)
                - status: 'processed' hoặc 'needs_review'
        """
        if not self.is_ready():
            raise RuntimeError("Engine chưa sẵn sàng hoặc đã gặp lỗi khởi tạo.")

        t0 = time.perf_counter()
        chan_doan = None
        with self._lock:
            # Khi bật nhật ký phát triển (AMC_LOG=1), lấy kèm các bước trung gian; kết quả giống hệt chuan_hoa.
            if os.environ.get("AMC_LOG") == "1":
                res, chan_doan = self._pipe.chuan_hoa_chan_doan(address)
            else:
                res = self._pipe.chuan_hoa(address)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        res_dict = asdict(res)
        if chan_doan is not None:
            res_dict["_chan_doan"] = chan_doan  # server tách ra ghi log, không gửi cho client

        # Xây dựng thanh_phan và ket_qua_hai_dong
        thanh_phan = self.build_thanh_phan(address, res_dict)
        ket_qua_hai_dong = self.build_ket_qua_hai_dong(res_dict, thanh_phan)

        res_dict["thanh_phan"] = thanh_phan
        res_dict["ket_qua_hai_dong"] = ket_qua_hai_dong
        res_dict["dia_chi_sau_tien_xu_ly"] = self.dia_chi_sau_tien_xu_ly(res_dict)

        # Đánh giá status: 'needs_review' khi có cảnh báo, nhiều xã mới ứng viên (mơ hồ),
        # hoặc có phần chưa phân loại đáng kể, hoặc thiếu mã hành chính.
        canh_bao = res_dict.get("canh_bao") or []
        xa_moi_ung_vien = res_dict.get("xa_moi_ung_vien") or []
        phan_chua_phan_loai = (res_dict.get("phan_chua_phan_loai") or "").strip()
        ma_tinh = (res_dict.get("ma_tinh") or "").strip()
        ma_xa = (res_dict.get("ma_xa") or "").strip()

        needs_review = (
            len(canh_bao) > 0
            or len(xa_moi_ung_vien) > 1
            or bool(phan_chua_phan_loai)
            or not ma_tinh
            or not ma_xa
        )

        status = "needs_review" if needs_review else "processed"
        return res_dict, round(elapsed_ms, 2), status
