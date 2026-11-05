"""Nạp mọi tập đánh giá về một khuôn chung (Mau) để chấm bằng một quy ước duy nhất.

Danh mục tập (mã, tên, mô tả, vai trò): BO_DU_LIEU bên dưới; in ra bằng `python -m danh_gia.chuan ds`.
Xem danh_gia/chuan/QUY_CHUAN.md.
"""
import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]
TRUONG_CHI_TIET = ('so_nha', 'ngo_ngach_hem', 'thon_xom', 'duong')
TRUONG = TRUONG_CHI_TIET + ('ma_xa', 'ma_tinh')

# Danh mục bộ dữ liệu. Mã tự mô tả: <loại>_<nguồn>_<cách gán nhãn>.
# vai_tro: chon (số chính, chọn cấu hình) | hoi_quy | do_ben (chỉ để loại) | tham_khao | xac_nhan (không tham gia luật).
BO_DU_LIEU = {
    'dev_osm_that': {
        'ten': 'Dev: địa chỉ OSM thật',
        'vai_tro': 'chon',
        'nguon': 'data/dev/nhan_sua/dev_goc.csv, các dòng loai_nhan = nhan_may',
        'mo_ta': ('Địa chỉ thật lấy từ OpenStreetMap (thẻ addr:full hoặc ghép các thẻ addr:*) của cơ sở công khai. '
                  'Nhãn do máy gán từ thẻ, sau đó sửa (agy dò 5 gói + sửa tay). Chủ yếu đô thị; rất ít thôn. '
                  'SỐ CHÍNH để chọn cấu hình; đã dùng nhiều lần nên không còn là phép đo độc lập.'),
    },
    'dev_sinh_danh_muc': {
        'ten': 'Dev: địa chỉ sinh từ danh mục hành chính',
        'vai_tro': 'hoi_quy',
        'nguon': 'data/dev/nhan_sua/dev_goc.csv (loai_nhan = tong_hop) + data/dev/nhan_sua/dev_kho.csv',
        'mo_ta': ('Địa chỉ do máy ghép theo khuôn từ danh mục xã cũ/mới (ví dụ "Số 72, Đường Đội Cấn, Xã Nga Liên, '
                  'Huyện Nga Sơn, Tỉnh Thanh Hóa"): sạch, đúng thứ tự, tên đường ghép bừa. Cùng cách sinh với một phần train. '
                  'Chỉ dùng kiểm hồi quy: không được kém đi; không phải số chính.'),
    },
    'kho_bien_the_ban': {
        'ten': 'Bộ khó: biến thể bẩn của địa chỉ',
        'vai_tro': 'do_ben',
        'nguon': 'rieng/bo_kho (ra/ra_*.csv + dap_an_giu_kin.json, đáp án giữ kín, không lên git)',
        'mo_ta': ('Địa chỉ do agy viết rồi làm bẩn theo 8 kiểu: sạch, không dấu, gõ sai, viết tắt, đảo thứ tự hành chính, '
                  'đính dấu phẩy, chi tiết khó, chữ tạp nhầm (ghi chú giao hàng, số điện thoại). Đáp án là mã xã/tỉnh '
                  'kỳ vọng (nhiều ứng viên = phải để trống). Đo độ bền với chữ bẩn; cùng nguồn agy với train nên dễ thiên lệch.'),
    },
    'test_osm_nhan_ai': {
        'ten': 'Test: địa chỉ OSM thật, nhãn AI chưa người duyệt',
        'vai_tro': 'tham_khao',
        'nguon': 'data/test/dia_chi_test.csv',
        'mo_ta': ('Địa chỉ thật của cơ sở công khai trên OSM (150 addr:full nguyên văn, 250 ghép thẻ), 32 tỉnh. '
                  'Nhãn agy tách + tra mã độc lập; AI tự duyệt 292 dòng, 108 dòng bảo lưu; 0 dòng người duyệt. '
                  'Đã bị mở nhiều lần khi phát triển: chỉ tham khảo, không dùng để quyết định.'),
    },
    'vang_ngoai_osm_ai': {
        'ten': 'Vàng: địa chỉ thật ngoài OSM, AI duyệt',
        'vai_tro': 'xac_nhan',
        'nguon': 'rieng/vang/vang.csv (không lên git), dòng trang_thai = da_duyet_ai hoặc da_duyet',
        'mo_ta': ('300 địa chỉ thật không lấy từ OSM: cổng dữ liệu mở Sơn La, Tây Ninh, Thanh Hóa, Hà Tĩnh; Sở Y tế Đắk Lắk; '
                  'Bộ Y tế; văn phòng công chứng, thừa phát lại. 25 tỉnh, nhiều thôn/bản/tổ/khối. Nhãn: agy tách -> tra mã '
                  'độc lập -> lượt agy duyệt thứ hai -> kiểm bằng mã; 247 dòng được nhận. Vàng AI, không phải vàng người. '
                  'Chỉ chạy khi chốt phiên bản.'),
    },
}
# Mã cũ (trước 05/11/2026) vẫn nhận được để đọc kết quả đã lưu.
MA_CU = {'dev_that': 'dev_osm_that', 'dev_sinh': 'dev_sinh_danh_muc', 'bo_kho': 'kho_bien_the_ban',
         'test400': 'test_osm_nhan_ai', 'vang': 'vang_ngoai_osm_ai'}
VAI_TRO = {k: v['vai_tro'] for k, v in BO_DU_LIEU.items()}
TAT_CA_TAP = tuple(BO_DU_LIEU)
TAP_CHINH = 'dev_osm_that'


def ma_tap(tap):
    return MA_CU.get(tap, tap)


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
    tap = ma_tap(tap)
    nhan_sua = GOC / 'data' / 'dev' / 'nhan_sua'
    if tap == 'dev_osm_that':
        return _tu_csv_nhan(nhan_sua / 'dev_goc.csv', tap, lambda r: r['loai_nhan'] == 'nhan_may', dm, ['that'])
    if tap == 'dev_sinh_danh_muc':
        return (_tu_csv_nhan(nhan_sua / 'dev_goc.csv', tap, lambda r: r['loai_nhan'] != 'nhan_may', dm, ['sinh'])
                + _tu_csv_nhan(nhan_sua / 'dev_kho.csv', tap, lambda r: True, dm, ['sinh']))
    if tap == 'test_osm_nhan_ai':
        out = _tu_csv_nhan(GOC / 'data' / 'test' / 'dia_chi_test.csv', tap, lambda r: True, dm, ['that'])
        trang_thai = {r['id']: r['trang_thai_nhan'] for r in csv.DictReader(
            open(GOC / 'data' / 'test' / 'dia_chi_test.csv', encoding='utf-8-sig'))}
        for m in out:
            m.nhom.add('nhan_' + trang_thai[m.id])
        return out
    if tap == 'vang_ngoai_osm_ai':
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
    if tap == 'kho_bien_the_ban':
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
