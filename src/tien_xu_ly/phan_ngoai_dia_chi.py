"""Phần đầu/đuôi chuỗi không phải địa chỉ: nhãn "Địa chỉ:", ", Việt Nam", ghi chú trong ngoặc (kể cả số điện thoại trong ngoặc).

Các phần này không mang thông tin về nơi chốn nhưng làm mạng nhận diện ký tự thấy ngữ cảnh khác (cùng một địa chỉ
thêm ghi chú cuối câu có thể đổi cả mã xã). Hàm ở đây thay chúng bằng khoảng trắng CÙNG ĐỘ DÀI, nên mọi vị trí
ký tự của phần còn lại giữ nguyên và dấu vết vẫn trỏ vào chuỗi gốc.

Thận trọng: ghi chú trong ngoặc chỉ bị che khi nội dung không có bằng chứng hành chính (tiền tố xã/phường/huyện,
hay tên đơn vị khớp đúng); không có gì để lại ở phần đầu thì không che gì.
"""

import re
import unicodedata

from .quy_tac import cac_tien_to
from .tien_xu_ly import token_co_vi_tri

_NHAN_DAU = re.compile(r"^\s*(?:địa\s*chỉ|dia\s*chi|đ/c|address|addr)\s*[:：]\s*", re.I)
_QUOC_GIA_CUOI = re.compile(r"(?:[,;]|\s[-–—])\s*(?:việt\s*nam|viet\s*nam|vietnam|vn)\s*\.?\s*$", re.I)
_DIEN_THOAI_CUOI = re.compile(
    r"(?:[\s,;:\-–—(]+|^)(?:(?:sđt|sdt|đt|dt|tel|hotline|lh|liên\s*hệ|phone|zalo|gọi|goi)\s*[:.]?\s*)?"
    r"(?:\+?84|0)(?:[\s.\-]?\d){8,10}\s*\)?\s*[.,;]?\s*$", re.I)
_GHI_CHU_NGOAC_CUOI = re.compile(r"\s*[(\[][^()\[\]]*[)\]]\s*\.?\s*$")


def _co_bang_chung_hanh_chinh(noi_dung, trie):
    """Nội dung trong ngoặc có tiền tố hành chính kèm tên, hay tên tỉnh, hay tên huyện/xã dài từ hai chữ khớp đúng."""
    from .tim_kiem import sinh_ung_vien
    tokens = [t.chu for t in token_co_vi_tri(noi_dung)]
    if any(kind == 'hanh_chinh' and end < len(tokens) and tokens[end][0].isalnum()
           for end, kind, _ in cac_tien_to(tokens).values()):
        return True
    if trie is None:
        return False
    return any(u.kieu_khop in ('chinh_xac', 'khong_dau')
               and (u.cap == 'tinh' or u.ket_thuc - u.bat_dau >= 2)
               for u in sinh_ung_vien(tokens, trie, bao_ve_chi_tiet=False))


def che_phan_ngoai_dia_chi(chuoi, trie=None):
    """Trả chuỗi cùng độ dài, phần ngoài địa chỉ ở đầu/đuôi thay bằng khoảng trắng."""
    if not chuoi or not unicodedata.is_normalized('NFC', chuoi):
        return chuoi
    out = chuoi

    def che(a, b):
        nonlocal out
        if any(c.isalnum() for c in out[:a]):  # còn phần đầu để xử lý
            out = out[:a] + ' ' * (b - a) + out[b:]
            return True
        return False

    m = _NHAN_DAU.match(out)
    if m and any(c.isalnum() for c in out[m.end():]):
        out = ' ' * m.end() + out[m.end():]
    for _ in range(4):  # đuôi lồng nhau: "... (ghi chú) - 09xx", "..., Việt Nam (ghi chú)"
        cuoi = out.rstrip()
        m = _GHI_CHU_NGOAC_CUOI.search(cuoi)
        if m and not _co_bang_chung_hanh_chinh(cuoi[m.start():m.end()].strip(' ()[].'), trie) and che(m.start(), len(out)):
            continue
        m = _QUOC_GIA_CUOI.search(cuoi)
        if m and che(m.start(), len(out)):
            continue
        break
    return out
