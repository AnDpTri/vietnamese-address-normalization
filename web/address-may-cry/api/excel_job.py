"""Chuẩn hóa một cột địa chỉ trong file Excel (.xlsx), chạy nền để không vượt thời gian chờ của tunnel.

Luồng: xem(file) -> danh sách sheet, tiêu đề, vài dòng mẫu; chay(file_id, sheet, cot) -> job_id;
tien_do(job_id) -> số dòng đã xong; tai(job_id) -> chính file cũ với cột địa chỉ được thay bằng địa chỉ chuẩn
(các cột khác giữ nguyên). Ô chưa chắc (thiếu xã/phường mới) tô vàng, kèm ghi chú chứa địa chỉ gốc và cảnh báo.
File và kết quả chỉ giữ trong bộ nhớ, tự xóa sau GIU_GIAY.
"""

import datetime
import io
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_DONG = 5000
GIU_GIAY = 3600
SO_DONG_MAU = 5

MAU_THIEU_XA = PatternFill('solid', fgColor='FFF4CE')

_tep: Dict[str, Dict[str, Any]] = {}
_viec: Dict[str, Dict[str, Any]] = {}
_khoa = threading.Lock()


def _don_dep() -> None:
    het = time.time() - GIU_GIAY
    with _khoa:
        for kho in (_tep, _viec):
            for k in [k for k, v in kho.items() if v['luc'] < het]:
                del kho[k]


def _chuoi(v: Any) -> str:
    if isinstance(v, datetime.datetime):  # ngày trong bảng xem trước: 17/02/1989, không phải 1989-02-17 00:00:00
        return v.strftime('%d/%m/%Y' if v.time() == datetime.time() else '%d/%m/%Y %H:%M')
    if isinstance(v, datetime.date):
        return v.strftime('%d/%m/%Y')
    return '' if v is None else str(v).strip()


def xem(du_lieu: bytes, ten_tep: str) -> Dict[str, Any]:
    """Đọc file, trả các sheet với tiêu đề (dòng 1), số dòng dữ liệu và vài dòng mẫu. Lỗi -> ValueError."""
    _don_dep()
    if len(du_lieu) > MAX_FILE_BYTES:
        raise ValueError(f'File vượt quá {MAX_FILE_BYTES // (1024 * 1024)} MB.')
    try:
        wb = load_workbook(io.BytesIO(du_lieu), read_only=True, data_only=True)
    except Exception:
        raise ValueError('Không đọc được file. Chỉ hỗ trợ Excel .xlsx (file .xls cũ hãy lưu lại thành .xlsx).')
    sheets = []
    for ws in wb.worksheets:
        dong = [[_chuoi(c) for c in r] for r in ws.iter_rows(values_only=True)]
        dong = [r for r in dong if any(r)]
        if not dong:
            continue
        rong = max(len(r) for r in dong)
        tieu_de = [(dong[0] + [''] * rong)[i] or f'Cột {get_column_letter(i + 1)}' for i in range(rong)]
        sheets.append({'ten': ws.title, 'tieu_de': tieu_de, 'so_dong': len(dong) - 1,
                       'mau': [(r + [''] * rong)[:rong] for r in dong[1:1 + SO_DONG_MAU]],
                       'cot_goi_y': _goi_y_cot(tieu_de, dong[1:1 + 50])})
    wb.close()
    if not sheets:
        raise ValueError('File không có dữ liệu.')
    file_id = uuid.uuid4().hex
    with _khoa:
        _tep[file_id] = {'du_lieu': du_lieu, 'ten': ten_tep, 'luc': time.time()}
    return {'file_id': file_id, 'ten_tep': ten_tep, 'sheets': sheets, 'max_dong': MAX_DONG}


def _goi_y_cot(tieu_de: List[str], mau: List[List[str]]) -> int:
    """Cột có tên gợi ý địa chỉ; không có thì cột có chuỗi trung bình dài nhất."""
    for i, t in enumerate(tieu_de):
        if any(k in t.casefold() for k in ('địa chỉ', 'dia chi', 'address', 'đ/c', 'dc')):
            return i
    do_dai = [sum(len(r[i]) if i < len(r) else 0 for r in mau) for i in range(len(tieu_de))]
    return max(range(len(tieu_de)), key=lambda i: do_dai[i]) if tieu_de else 0


def chay(file_id: str, sheet: str, cot: int, chuan_hoa: Callable[[str], Dict[str, Any]],
         ghi_log: Optional[Callable[[str, Dict[str, Any]], None]] = None) -> str:
    """Bắt đầu chuẩn hóa cột `cot` (đánh số từ 0) của `sheet`, chạy nền. Trả job_id."""
    _don_dep()
    with _khoa:
        tep = _tep.get(file_id)
    if tep is None:
        raise ValueError('File đã hết hạn hoặc chưa tải lên. Hãy tải lại file.')
    wb = load_workbook(io.BytesIO(tep['du_lieu']), data_only=True)
    if sheet not in wb.sheetnames:
        raise ValueError('Không có sheet này trong file.')
    ws = wb[sheet]
    so_dong = ws.max_row - 1
    if so_dong > MAX_DONG:
        raise ValueError(f'Sheet có {so_dong} dòng, vượt giới hạn {MAX_DONG} dòng mỗi lần.')
    if not 0 <= cot < ws.max_column:
        raise ValueError('Cột không hợp lệ.')
    job_id = uuid.uuid4().hex
    viec = {'luc': time.time(), 'tong': so_dong, 'xong': 0, 'trang_thai': 'dang_chay', 'loi': None,
            'thieu_xa': 0, 'ket_qua': None, 'ten_ra': _ten_ra(tep['ten'])}
    with _khoa:
        _viec[job_id] = viec
    threading.Thread(target=_xu_ly, args=(wb, ws, cot, viec, chuan_hoa, ghi_log), daemon=True).start()
    return job_id


def _ten_ra(ten: str) -> str:
    goc = ten.rsplit('.', 1)[0] if '.' in ten else ten
    return f'{goc or "dia_chi"}_chuan_hoa.xlsx'


def _xu_ly(wb: Workbook, ws, cot: int, viec: Dict[str, Any], chuan_hoa, ghi_log) -> None:
    try:
        for r in range(2, ws.max_row + 1):
            o = ws.cell(row=r, column=cot + 1)
            dau_vao = _chuoi(o.value)
            if dau_vao:
                try:
                    kq = chuan_hoa(dau_vao)
                except Exception:
                    kq = {'canh_bao': ['loi_xu_ly']}
                if kq.get('dia_chi_chuan'):
                    o.value = kq['dia_chi_chuan']
                if not kq.get('ma_xa'):
                    # Chưa chắc: tô vàng, ghi chú địa chỉ gốc và cảnh báo để người dùng kiểm lại.
                    viec['thieu_xa'] += 1
                    o.fill = MAU_THIEU_XA
                    o.comment = Comment(f"Gốc: {dau_vao}\nCảnh báo: {', '.join(kq.get('canh_bao') or [])}",
                                        'Address May Cry', width=320, height=110)
                if ghi_log:
                    ghi_log(dau_vao, kq)
            viec['xong'] += 1
        ra = io.BytesIO()
        wb.save(ra)
        viec['ket_qua'] = ra.getvalue()
        viec['trang_thai'] = 'xong'
    except Exception as e:  # báo lỗi cho giao diện, không làm sập máy chủ
        viec['trang_thai'] = 'loi'
        viec['loi'] = f'Lỗi khi xử lý file: {type(e).__name__}'


def tien_do(job_id: str) -> Optional[Dict[str, Any]]:
    with _khoa:
        v = _viec.get(job_id)
    if v is None:
        return None
    return {k: v[k] for k in ('tong', 'xong', 'trang_thai', 'loi', 'thieu_xa', 'ten_ra')}


def tai(job_id: str) -> Optional[Dict[str, Any]]:
    with _khoa:
        v = _viec.get(job_id)
    if v is None or v['trang_thai'] != 'xong':
        return None
    return {'du_lieu': v['ket_qua'], 'ten': v['ten_ra']}
