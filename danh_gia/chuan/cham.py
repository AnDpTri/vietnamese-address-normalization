"""Chấm theo MỘT quy ước cho mọi tập, kèm khoảng tin cậy và so sánh cặp.

Quy ước so khớp trường chi tiết (số nhà, ngõ, thôn, đường):
- Bỏ dấu, thường hóa, bỏ dấu câu (giữ chữ, số, '/').
- Chữ loại đứng đầu (Số; Ngõ/Ngách/Hẻm/Kiệt; Thôn/Xóm/Ấp/Tổ dân phố...; Đường/Phố/Đại lộ) được tách ra:
  phần tên phải trùng; chữ loại chỉ bị bắt lỗi khi CẢ HAI bên có và khác nhóm (Đường = Phố = Đại lộ).
  Nhờ vậy nhãn có hay không ghi chữ loại (test400 không ghi "Số", "Đường") chấm như nhau,
  và pipeline luôn chạy đúng cấu hình sản phẩm.
- "Tháng Tám" = "Tháng 8" (tên đường kiểu Cách Mạng Tháng 8).
Mã xã, mã tỉnh: so đúng mã. Vàng để trống mã xã nghĩa là PHẢI để trống (xã bị chia, hoặc không đủ căn cứ).
"""
import math
import re
import unicodedata

from .du_lieu import TRUONG, TRUONG_CHI_TIET

_LOAI = {
    'so_nha': [('so',)],
    'ngo_ngach_hem': [('ngo',), ('ngach',), ('hem',), ('kiet',)],
    'thon_xom': [('to', 'dan', 'pho'), ('khu', 'dan', 'cu'), ('khu', 'pho'), ('thon',), ('xom',), ('ap',), ('ban',),
                 ('buon',), ('khom',), ('khoi',), ('tdp',), ('kp',), ('to',), ('khu',), ('lang',), ('doi',)],
    'duong': [('dai', 'lo'), ('duong',), ('pho',)],
}
_CUNG_NHOM = {('dai', 'lo'): 'duong', ('duong',): 'duong', ('pho',): 'duong',
              ('tdp',): ('to', 'dan', 'pho'), ('kp',): ('khu', 'pho')}
_SO_CHU = {'mot': '1', 'hai': '2', 'ba': '3', 'tu': '4', 'bon': '4', 'nam': '5', 'sau': '6', 'bay': '7',
           'tam': '8', 'chin': '9', 'muoi': '10'}


def _tu(s):
    s = unicodedata.normalize('NFD', (s or '').replace('đ', 'd').replace('Đ', 'D'))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').casefold()
    tu = re.findall(r'[a-z0-9/]+', s)
    return [_SO_CHU[t] if i and tu[i - 1] == 'thang' and t in _SO_CHU else t for i, t in enumerate(tu)]


def tach_loai(truong, s):
    tu = _tu(s)
    for loai in _LOAI.get(truong, ()):
        if tuple(tu[:len(loai)]) == loai and len(tu) > len(loai):
            return _CUNG_NHOM.get(loai, loai), tuple(tu[len(loai):])
    return None, tuple(tu)


def khop_chi_tiet(truong, du_doan, vang):
    la, ta = tach_loai(truong, du_doan)
    lb, tb = tach_loai(truong, vang)
    return ta == tb and (la is None or lb is None or la == lb)


def cham_mau(mau, ra):
    """Kết quả một mẫu: đúng từng trường, đúng đủ 6 trường, loại kết luận về mã xã."""
    ok = {}
    for f in TRUONG:
        if f in mau.bo_qua:
            continue
        if f in TRUONG_CHI_TIET:
            ok[f] = khop_chi_tiet(f, ra.get(f, ''), mau.vang[f])
        else:
            ok[f] = (ra.get(f) or '') == mau.vang[f]
    vx, rx = mau.vang['ma_xa'], ra.get('ma_xa') or ''
    if vx:
        xa = 'dung' if rx == vx else 'bo_trong' if not rx else 'khang_dinh_sai'
    else:
        xa = 'dung' if not rx else 'khang_dinh_sai'
    ung_vien_ra = {u.get('ma_xa') for u in (ra.get('xa_moi_ung_vien') or [])}
    # Điền thừa: mô hình điền trường chi tiết mà vàng để trống (ví dụ bịa tên đường từ "Hà Nội", "Lô 2").
    thua = [f for f in TRUONG_CHI_TIET if f in ok and not mau.vang[f].strip() and (ra.get(f) or '').strip()]
    return {'ok': ok, 'du_6': all(ok.values()), 'xa': xa, 'co_ma': bool(rx), 'thua': thua,
            'gan_co_chia': 'xa_bi_chia' in (ra.get('canh_bao') or []),
            'phu_ung_vien': bool(mau.ung_vien) and mau.ung_vien <= ung_vien_ra}


def wilson(k, n, z=1.96):
    """Khoảng tin cậy 95% Wilson cho tỷ lệ k/n, trả (thấp, cao) theo %."""
    if n == 0:
        return (0., 0.)
    p = k / n
    d = 1 + z * z / n
    tam = (p + z * z / (2 * n)) / d
    rong = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * max(0., tam - rong), 100 * min(1., tam + rong))


def mcnemar(b, c):
    """p hai phía (nhị thức chính xác) cho b câu A đúng-B sai và c câu A sai-B đúng."""
    n = b + c
    if n == 0:
        return 1.
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1., 2 * p)


def tong_hop(cac_mau, ket):
    """ket: id -> kết quả cham_mau. Trả thống kê của một nhóm mẫu."""
    n = len(cac_mau)
    if n == 0:
        return {'n': 0}
    kq = [ket[m.id] for m in cac_mau]
    du6 = sum(k['du_6'] for k in kq)
    tk = {'n': n, 'du_6': du6, 'du_6_pct': 100 * du6 / n, 'du_6_ci': wilson(du6, n)}
    for f in TRUONG:
        co = [k['ok'][f] for k in kq if f in k['ok']]
        tk[f] = 100 * sum(co) / len(co) if co else None
    co_ma = [(m, k) for m, k in zip(cac_mau, kq) if m.vang['ma_xa']]
    sai = sum(k['xa'] == 'khang_dinh_sai' for k in kq)
    khang_dinh = sum(k['co_ma'] for k in kq)  # số câu mô hình trả mã xã
    dung_khi_kd = sum(1 for k in kq if k['co_ma'] and k['xa'] == 'dung')
    tk.update({
        'xa_khang_dinh_sai': sai, 'xa_khang_dinh_sai_pct': 100 * sai / n, 'xa_khang_dinh_sai_ci': wilson(sai, n),
        'xa_chinh_xac_khi_khang_dinh': 100 * dung_khi_kd / khang_dinh if khang_dinh else None,
        'xa_do_phu': 100 * sum(1 for m, k in co_ma if k['xa'] != 'bo_trong') / len(co_ma) if co_ma else None,
        'xa_bo_trong_khi_co_ma': sum(1 for m, k in co_ma if k['xa'] == 'bo_trong'),
        'dien_thua': sum(bool(k['thua']) for k in kq),
        'dien_thua_duong': sum('duong' in k['thua'] for k in kq),
    })
    chia = [(m, k) for m, k in zip(cac_mau, kq) if 'xa_bi_chia' in m.nhom]
    if chia:
        # Xã cũ bị chia: vàng có mã (phân giải được, ví dụ theo tên đường) hoặc vàng để trống (phải để trống + gắn cờ).
        giai = [k for m, k in chia if m.vang['ma_xa']]
        trong = [(m, k) for m, k in chia if not m.vang['ma_xa']]
        tk['chia_n'] = len(chia)
        tk['chia_giai_n'] = len(giai)
        tk['chia_giai_dung'] = 100 * sum(k['xa'] == 'dung' for k in giai) / len(giai) if giai else None
        tk['chia_trong_n'] = len(trong)
        if trong:
            tk['chia_trong_dung'] = 100 * sum(k['xa'] == 'dung' for m, k in trong) / len(trong)
            tk['chia_trong_gan_co'] = 100 * sum(k['gan_co_chia'] for m, k in trong) / len(trong)
            co_uv = [k for m, k in trong if m.ung_vien]
            tk['chia_phu_ung_vien'] = 100 * sum(k['phu_ung_vien'] for k in co_uv) / len(co_uv) if co_uv else None
    return tk


def so_sanh_cap(cac_mau, ket_a, ket_b):
    """So hai phiên bản trên cùng mẫu: đủ 6 trường và khẳng định sai mã xã (McNemar)."""
    out = {}
    for ten, ham in (('du_6', lambda k: k['du_6']), ('khong_khang_dinh_sai', lambda k: k['xa'] != 'khang_dinh_sai'),
                     ('khong_dien_thua', lambda k: not k['thua'])):
        b = sum(1 for m in cac_mau if ham(ket_a[m.id]) and not ham(ket_b[m.id]))
        c = sum(1 for m in cac_mau if not ham(ket_a[m.id]) and ham(ket_b[m.id]))
        p = mcnemar(b, c)
        ket_luan = 'TỐT HƠN' if p < .05 and c > b else 'KÉM HƠN' if p < .05 and b > c else 'KHÔNG PHÂN BIỆT'
        out[ten] = {'a_dung_b_sai': b, 'a_sai_b_dung': c, 'p': p, 'ket_luan': ket_luan}
    return out
