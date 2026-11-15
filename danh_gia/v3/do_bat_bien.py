"""Bộ đo BẤT BIẾN (không cần nhãn): các biến đổi không mang thông tin thì không được làm đổi mã xã/tỉnh.
Bộ 9.000 cặp (1.000 câu gốc x 9 biến đổi) được CHỐT thành file cố định data/bat_bien/cap_bat_bien.csv (xem README ở đó),
script chỉ đọc file đó. Sinh lại file: thêm cờ --sinh-lai (seed 20261031, từ dev + test).
Dùng: do_bat_bien.py <char_cnn.pt|-> <ranker.txt|-> <ten_lan_do> [--sinh-lai]
  ('-' = cấu hình mặc định trong src/cau_hinh.py). Ghi rieng/danh_gia_chuan/bat_bien/<ten>.json
Số quyết định chỉ lấy trên các cặp nguồn dev (cột nguon = dev); cặp nguồn test chỉ báo cáo kèm, không dùng dò lỗi."""
import csv, json, random, re, sys, time
from pathlib import Path

import duong_dan as dd  # gốc repo, CODE_ROOT vào sys.path
from src.cau_hinh import tao_bo_chuan_hoa  # noqa: E402  (cấu hình chung với web)

D = dd.RIENG / 'danh_gia_chuan' / 'bat_bien'
FILE_CAP = dd.ROOT / 'data' / 'bat_bien' / 'cap_bat_bien.csv'
SEED = 20261031
N_GOC = 1000
rng = random.Random(SEED)


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


def sinh_bo(n_goc=N_GOC):
    """Sinh lại danh sách cặp (id, nguon, bien_doi, goc, bien_doi_dau_vao). Khớp bộ đã chốt khi seed và nguồn giữ nguyên."""
    global rng
    rng = random.Random(SEED)
    goc = {}
    for f in ('dev_goc.csv', 'dev_kho.csv'):
        for r in csv.DictReader(open(dd.DEV / f, encoding='utf-8-sig')):
            goc.setdefault(r['dau_vao'], 'dev')
    for r in csv.DictReader(open(dd.TEST, encoding='utf-8-sig')):
        goc.setdefault(r['dau_vao'], 'test')
    ds = sorted(goc)
    rng.shuffle(ds)
    cap = []
    for i, s in enumerate(ds[:n_goc]):
        for k, f in BIEN_DOI.items():
            cap.append({'id': f'bb{i:04d}_{k}', 'nguon': goc[s], 'bien_doi': k, 'goc': s, 'bien_doi_dau_vao': f(s)})
    return cap


def ghi_bo(cap):
    FILE_CAP.parent.mkdir(parents=True, exist_ok=True)
    with open(FILE_CAP, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, ['id', 'nguon', 'bien_doi', 'goc', 'bien_doi_dau_vao'])
        w.writeheader(); w.writerows(cap)


def doc_bo():
    return list(csv.DictReader(open(FILE_CAP, encoding='utf-8-sig')))


def _tong(dem, ks=None):
    d = {c: sum(x[c] for x in dem.values()) for c in ('tong', 'doi_ma', 'khang_dinh_khac', 'mat_khang_dinh', 'them_khang_dinh')}
    d['ty_le_doi_ma_pct'] = round(100 * d['doi_ma'] / d['tong'], 2) if d['tong'] else None
    d['ty_le_khang_dinh_khac_pct'] = round(100 * d['khang_dinh_khac'] / d['tong'], 2) if d['tong'] else None
    return d


def main(cnn, ranker, ten, sinh_lai=False):
    if sinh_lai or not FILE_CAP.exists():
        ghi_bo(sinh_bo())
    cap = doc_bo()
    pipe = tao_bo_chuan_hoa(cnn=None if cnn == '-' else cnn, ranker=None if ranker == '-' else ranker)
    t0 = time.time()
    moi = lambda: {k: {'tong': 0, 'doi_ma': 0, 'khang_dinh_khac': 0, 'mat_khang_dinh': 0, 'them_khang_dinh': 0} for k in BIEN_DOI}
    dem, dem_dev = moi(), moi()
    vi_du = {k: [] for k in BIEN_DOI}
    chi_tiet = []
    ket_goc = {}
    for r in cap:
        s, s2, k = r['goc'], r['bien_doi_dau_vao'], r['bien_doi']
        if s not in ket_goc:
            a = pipe.chuan_hoa(s)
            ket_goc[s] = (a.ma_xa, a.ma_tinh)
        ka = ket_goc[s]
        b = pipe.chuan_hoa(s2)
        kb = (b.ma_xa, b.ma_tinh)
        for d in ([dem[k], dem_dev[k]] if r['nguon'] == 'dev' else [dem[k]]):
            d['tong'] += 1
            if ka != kb:
                d['doi_ma'] += 1
                if ka[0] and kb[0] and ka[0] != kb[0]:
                    d['khang_dinh_khac'] += 1
                elif ka[0] and not kb[0]:
                    d['mat_khang_dinh'] += 1
                elif kb[0] and not ka[0]:
                    d['them_khang_dinh'] += 1
        if ka != kb:
            chi_tiet.append({'id': r['id'], 'nguon': r['nguon'], 'bien_doi': k, 'truoc': ka, 'sau': kb})
            if r['nguon'] == 'dev' and len(vi_du[k]) < 15:
                vi_du[k].append({'goc': s, 'bien_doi': s2, 'truoc': ka, 'sau': kb})
    kq = {'so_cau_goc': len({r['goc'] for r in cap}), 'tong_cap': len(cap), 'tong': _tong(dem), 'chi_dev': _tong(dem_dev),
          'theo_bien_doi': dem, 'theo_bien_doi_chi_dev': dem_dev, 'cap_doi_ma': chi_tiet, 'vi_du_dev': vi_du,
          'giay': round(time.time() - t0)}
    D.mkdir(parents=True, exist_ok=True)
    (D / f'{ten}.json').write_text(json.dumps(kq, ensure_ascii=False, indent=2), encoding='utf-8')
    for nhan, t in (('tất cả', kq['tong']), ('chỉ nguồn dev (số quyết định)', kq['chi_dev'])):
        print(f"{ten} | {nhan} | cặp {t['tong']} | đổi mã {t['ty_le_doi_ma_pct']} % | khẳng định khác nhau {t['ty_le_khang_dinh_khac_pct']} %")
    for k, d in dem.items():
        e = dem_dev[k]
        print(f"   {k:20} đổi {d['doi_ma']:4}/{d['tong']} (dev {e['doi_ma']:3}/{e['tong']}; khẳng định khác {d['khang_dinh_khac']}, mất {d['mat_khang_dinh']}, thêm {d['them_khang_dinh']})")


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0], args[1], args[2], '--sinh-lai' in sys.argv)
