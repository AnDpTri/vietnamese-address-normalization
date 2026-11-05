"""Cấu hình pipeline dùng chung cho web, CLI và script đo.

Mọi nơi chạy mô hình "đang dùng" phải dựng pipeline qua tao_bo_chuan_hoa(), để số đo là số của
đúng hệ thống đang chạy trên web (cùng mô hình, cùng từ điển đường, cùng tùy chọn).
"""
import os
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]

# Mô hình đang dùng (Char-CNN + ranker LightGBM)
MO_HINH = GOC / 'mo_hinh' / 'thu_nghiem' / 'char_v3_tc'
CNN = MO_HINH / 'char_cnn.pt'
RANKER = MO_HINH / 'ranker.txt'

# Từ điển tên đường dùng chung cho web và số đo (AMC_TU_DIEN_DUONG để thử từ điển khác).
# Chọn tu_dien_train thay v5 ngày 05/11/2026 theo danh_gia/chuan (so_sanh td_v5 -> td_train: NHẬN yếu;
# bộ khó đủ 6 trường 4 kém / 15 tốt, p=0,019; điền thừa 38 -> 26): v5 bịa tên đường từ ghi chú
# ("gặp chị Hoa" -> Đường Hoa, "gọi trước 30 phút" -> Quốc lộ 30, "Hà Nội" -> Đường Hà Nội).
TU_DIEN_DUONG = Path(os.environ.get('AMC_TU_DIEN_DUONG', GOC / 'data' / 'train' / 'tu_dien_train.json'))

# Tùy chọn pipeline của sản phẩm
BAO_VE_DUONG = True
TIEN_TO_MAC_DINH = True  # tự thêm "Số", "Đường"... khi người dùng không ghi


def tao_bo_chuan_hoa(cnn=None, ranker=None, tu_dien_duong=None, tien_to_mac_dinh=None,
                     danh_muc=None, threads=1):
    """Dựng BoChuanHoa theo cấu hình sản phẩm. Tham số nào để None thì lấy giá trị mặc định ở trên.

    ranker=False: không dùng ranker (chỉ CNN). tu_dien_duong=False: không dùng từ điển đường.
    """
    from .chuan_hoa import BoChuanHoa
    from .danh_muc import DanhMuc
    from .tien_xu_ly.char_cnn import BoTachCharCNN
    from .tien_xu_ly.chuan_ten_duong import TuDienDuong
    from .tien_xu_ly.xep_hang import BoXepHang

    dm = danh_muc if danh_muc is not None else DanhMuc()
    bo_tach = BoTachCharCNN(Path(cnn or CNN), threads=threads)
    bo_xep_hang = None if ranker is False else BoXepHang(Path(ranker or RANKER), bo_tach.ma_bam, dm.ma_bam)
    tu_dien = None if tu_dien_duong is False else TuDienDuong(Path(tu_dien_duong or TU_DIEN_DUONG))
    return BoChuanHoa(danh_muc=dm, bo_tach=bo_tach, bo_xep_hang=bo_xep_hang, tu_dien_duong=tu_dien,
                      bao_ve_duong=BAO_VE_DUONG,
                      tien_to_mac_dinh=TIEN_TO_MAC_DINH if tien_to_mac_dinh is None else tien_to_mac_dinh)
