"""Bộ đo BẤT BIẾN (không cần nhãn): các biến đổi không mang thông tin thì không được làm đổi mã xã/tỉnh.
Và đo CHÍNH XÁC KHI KHẲNG ĐỊNH / ĐỘ PHỦ trên các tập có nhãn.
Dùng: CODE_ROOT=<mã> do_bat_bien.py <char_cnn.pt> <ranker.txt> <ten_lan_do> [so_cau_goc=1000]
Ghi danh_gia/ket_qua/bat_bien/<ten>.json"""
import csv, json, os, random, re, sys, time
from pathlib import Path

import duong_dan as dd  # gốc repo, CODE_ROOT vào sys.path
from src.cau_hinh import tao_bo_chuan_hoa  # noqa: E402  (cấu hình chung với web)

D = (dd.KET_QUA / 'bat_bien')
rng = random.Random(20261031)


def dt():
    return '09' + ''.join(rng.choice('0123456789') for _ in range(8))


# Mỗi biến đổi giữ nguyên thông tin địa chỉ.
BIEN_DOI = {
    'so_dien_thoai_cuoi': lambda s: f'{s} - {dt()}',
    'ghi_chu_cuoi': lambda s: f'{s} (gọi trước khi giao)',
    'them_viet_nam': lambda s: f'{s}, Việt Nam',
    'tien_to_dia_chi': lambda s: f'Địa chỉ: {s}',
    'bo_cach_sau_phay': lambda s: re.sub(r',\s+', ',', s),
    'phay_thanh_gach': lambda s: re.sub(r',\s*', ' - ', s),
    'viet_hoa_het': lambda s: s.upper(),
    'cach_doi': lambda s: re.sub(r'\s+', '  ', s),
    # Thêm chi tiết dưới xã ở đầu câu: thêm thông tin nhưng không được đổi xã/tỉnh.
    'them_xom_dau': lambda s: f'xóm 5 {s}',
}


def main(cnn, ranker, ten, n_goc):
    pipe = tao_bo_chuan_hoa(cnn=cnn, ranker=ranker)
    goc = []
    for f in ('dev_goc.csv', 'dev_kho.csv'):
        goc += [r['dau_vao'] for r in csv.DictReader(open(dd.DEV / f, encoding='utf-8-sig'))]
    goc += [r['dau_vao'] for r in csv.DictReader(open(dd.TEST, encoding='utf-8-sig'))]
    goc = sorted(set(goc))
    rng.shuffle(goc)
    goc = goc[:n_goc]
    t0 = time.time()
    dem = {k: {'tong': 0, 'doi_ma': 0, 'khang_dinh_khac': 0, 'mat_khang_dinh': 0, 'them_khang_dinh': 0} for k in BIEN_DOI}
    vi_du = {k: [] for k in BIEN_DOI}
    for s in goc:
        a = pipe.chuan_hoa(s)
        ka = (a.ma_xa, a.ma_tinh)
        for k, f in BIEN_DOI.items():
            s2 = f(s)
            b = pipe.chuan_hoa(s2)
            kb = (b.ma_xa, b.ma_tinh)
            d = dem[k]; d['tong'] += 1
            if ka != kb:
                d['doi_ma'] += 1
                if a.ma_xa and b.ma_xa and a.ma_xa != b.ma_xa:
                    d['khang_dinh_khac'] += 1
                elif a.ma_xa and not b.ma_xa:
                    d['mat_khang_dinh'] += 1
                elif b.ma_xa and not a.ma_xa:
                    d['them_khang_dinh'] += 1
                if len(vi_du[k]) < 15:
                    vi_du[k].append({'goc': s, 'bien_doi': s2, 'truoc': ka, 'sau': kb})
    tong = sum(d['tong'] for d in dem.values()); doi = sum(d['doi_ma'] for d in dem.values())
    kq = {'so_cau_goc': len(goc), 'tong_cap': tong, 'ty_le_doi_ma_pct': round(100 * doi / tong, 2),
          'ty_le_khang_dinh_khac_pct': round(100 * sum(d['khang_dinh_khac'] for d in dem.values()) / tong, 2),
          'theo_bien_doi': dem, 'vi_du': vi_du, 'giay': round(time.time() - t0)}
    D.mkdir(parents=True, exist_ok=True)
    (D / f'{ten}.json').write_text(json.dumps(kq, ensure_ascii=False, indent=2), encoding='utf-8')
    print(ten, '| cặp', tong, '| đổi mã', kq['ty_le_doi_ma_pct'], '% | khẳng định khác nhau', kq['ty_le_khang_dinh_khac_pct'], '%')
    for k, d in dem.items():
        print(f"   {k:20} đổi {d['doi_ma']:4} (khẳng định khác {d['khang_dinh_khac']}, mất {d['mat_khang_dinh']}, thêm {d['them_khang_dinh']})")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 1000)
