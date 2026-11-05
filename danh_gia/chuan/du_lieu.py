"""Nạp mọi tập đánh giá về một khuôn chung (Mau) để chấm bằng một quy ước duy nhất.

Các tập và vai trò (xem danh_gia/chuan/QUY_CHUAN.md):
  dev_that  400 địa chỉ OSM thật trong dev (nhãn máy + sửa)      -> CHỌN CẤU HÌNH, số chính
  dev_sinh  1.200 địa chỉ sinh từ danh mục (dev_goc + dev_kho)    -> kiểm hồi quy, không là số chính
  bo_kho    1.500 biến thể bẩn (rieng/bo_kho, đáp án giữ kín)      -> kiểm độ bền, không là số chính
  test400   400 địa chỉ OSM thật, nhãn AI CHƯA người duyệt         -> tham khảo, không dùng để chọn
  vang      300 địa chỉ thật ngoài OSM, người duyệt (rieng/vang)   -> xác nhận khi chốt phiên bản
"""
import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]
TRUONG_CHI_TIET = ('so_nha', 'ngo_ngach_hem', 'thon_xom', 'duong')
TRUONG = TRUONG_CHI_TIET + ('ma_xa', 'ma_tinh')

# Vai trò của từng tập trong luật chấp nhận
VAI_TRO = {'dev_that': 'chon', 'dev_sinh': 'hoi_quy', 'bo_kho': 'do_ben', 'test400': 'tham_khao', 'vang': 'xac_nhan'}
TAT_CA_TAP = tuple(VAI_TRO)


@dataclass
class Mau:
    id: str
    tap: str
    dau_vao: str
    vang: dict                      # 6 trường; ma_xa '' nghĩa là phải để trống
    nhom: set = field(default_factory=set)
    bo_qua: set = field(default_factory=set)
    ung_vien: set = field(default_factory=set)  # mã xã mới có thể (khi xã cũ bị chia)


def _ung_vien_tu_ghi_chu(ghi_chu):
    m = re.search(r'xa_moi_ung_vien=(\[.*?\])', ghi_chu or '')
    if not m:
        return set()
    try:
        return {x['ma_xa'] for x in json.loads(m[1])}
    except (ValueError, KeyError, TypeError):
        return set()


def _nhom_chung(m, ma_xa_cu, canh_bao, dm):
    if ma_xa_cu:
        m.nhom.add('dia_chi_cu')
    if 'xa_bi_chia' in canh_bao or len(m.ung_vien) > 1:
        m.nhom.add('xa_bi_chia')
    if m.vang['thon_xom']:
        m.nhom.add('co_thon')
    if m.vang['duong']:
        m.nhom.add('co_duong')
    if not m.vang['ma_xa'] and 'xa_bi_chia' not in m.nhom:
        m.nhom.add('khong_xac_dinh_xa')
    if m.vang['ma_xa'] and dm is not None and ('moi', m.vang['ma_xa']) in dm.don_vi:
        m.nhom.add('nong_thon' if dm.lay('moi', m.vang['ma_xa']).loai == 'Xã' else 'do_thi')


def _tu_csv_nhan(duong_dan, tap, loc, dm, nhom_them=()):
    out = []
    for r in csv.DictReader(open(duong_dan, encoding='utf-8-sig')):
        if not loc(r):
            continue
        m = Mau(r['id'], tap, r['dau_vao'], {f: (r.get(f) or '').strip() for f in TRUONG},
                bo_qua=set((r.get('bo_qua') or '').split()), ung_vien=_ung_vien_tu_ghi_chu(r.get('ghi_chu')))
        m.nhom.update(nhom_them)
        _nhom_chung(m, (r.get('ma_xa_cu') or '').strip(), r.get('canh_bao') or '', dm)
        out.append(m)
    return out


def nap(tap, dm=None):
    """Trả về list[Mau] của một tập; tập không có trên máy thì trả []."""
    nhan_sua = GOC / 'data' / 'dev' / 'nhan_sua'
    if tap == 'dev_that':
        return _tu_csv_nhan(nhan_sua / 'dev_goc.csv', tap, lambda r: r['loai_nhan'] == 'nhan_may', dm, ['that'])
    if tap == 'dev_sinh':
        return (_tu_csv_nhan(nhan_sua / 'dev_goc.csv', tap, lambda r: r['loai_nhan'] != 'nhan_may', dm, ['sinh'])
                + _tu_csv_nhan(nhan_sua / 'dev_kho.csv', tap, lambda r: True, dm, ['sinh']))
    if tap == 'test400':
        out = _tu_csv_nhan(GOC / 'data' / 'test' / 'dia_chi_test.csv', tap, lambda r: True, dm, ['that'])
        trang_thai = {r['id']: r['trang_thai_nhan'] for r in csv.DictReader(
            open(GOC / 'data' / 'test' / 'dia_chi_test.csv', encoding='utf-8-sig'))}
        for m in out:
            m.nhom.add('nhan_' + trang_thai[m.id])
        return out
    if tap == 'vang':
        # Tập vàng giữ kín, không lên git: rieng/vang/vang.csv (chỉ dòng trang_thai=da_duyet được chấm).
        p = GOC / 'rieng' / 'vang' / 'vang.csv'
        if not p.exists():
            return []
        # Nhận dòng người duyệt (da_duyet) và AI duyệt độc lập + kiểm mã (da_duyet_ai, xem rieng/vang/ai_duyet.py).
        out = _tu_csv_nhan(p, tap, lambda r: (r.get('trang_thai') or '') in ('da_duyet', 'da_duyet_ai'), dm, ['that'])
        dong = {r['id']: r for r in csv.DictReader(open(p, encoding='utf-8-sig'))}
        for m in out:
            m.nhom.update((dong[m.id].get('nhom') or '').split())
            m.nhom.add('duyet_ai' if dong[m.id]['trang_thai'] == 'da_duyet_ai' else 'duyet_nguoi')
        return out
    if tap == 'bo_kho':
        thu_muc = GOC / 'rieng' / 'bo_kho'
        if not (thu_muc / 'dap_an_giu_kin.json').exists():
            return []
        dap_an = {g['id']: g for g in json.load(open(thu_muc / 'dap_an_giu_kin.json', encoding='utf-8'))}
        out = []
        for p in sorted((thu_muc / 'ra').glob('ra_*.csv')):
            for r in csv.DictReader(open(p, encoding='utf-8')):
                g = dap_an[r['id']]
                xa, tinh = g['ma_xa_moi_ky_vong'], g['ma_tinh_moi_ky_vong']
                vang = {f: g.get(f, '') for f in TRUONG_CHI_TIET}
                vang['ma_xa'] = xa[0] if len(xa) == 1 else ''
                vang['ma_tinh'] = tinh[0] if len(tinh) == 1 else ''
                m = Mau(r['id'], tap, r['dia_chi'], vang, ung_vien=set(xa) if len(xa) > 1 else set())
                m.nhom.update(['sinh', 'nhieu_' + g['loai_nhieu']])
                _nhom_chung(m, g['ma_xa_cu'] if g['era'] == 'cu' else '', '', dm)
                out.append(m)
        return out
    raise ValueError(f'Tập không biết: {tap}')
