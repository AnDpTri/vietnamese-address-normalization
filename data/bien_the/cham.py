"""Chấm hệ thống trên bộ biến thể: mọi biến thể của một địa chỉ gốc phải ra cùng đáp án với địa chỉ gốc.

Dùng (từ gốc repo, môi trường .venv-neural):
  python data/bien_the/cham.py <thu_muc> g01 g02 ... [--ra ket_qua.json] [--in-sai]
Với mỗi gN đọc <thu_muc>/gN.json và mọi <thu_muc>/gN_*.jsonl (code, agy). In theo địa chỉ và nguồn: đúng xã+tỉnh,
khẳng định sai (ra mã xã khác đáp án), và đúng từng trường chi tiết có trong đáp án (so không dấu, bỏ khoảng trắng).
Trường thôn chỉ chấm ở câu còn chữ loại của thôn (cham_thon).
"""
import argparse
import json
import os
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, os.environ.get('CODE_ROOT', str(GOC)))
M = GOC / 'mo_hinh' / 'thu_nghiem' / 'char_v3_tc'
CHI_TIET = ('so_nha', 'ngo_ngach_hem', 'thon_xom', 'duong')


def fold(s):
    s = unicodedata.normalize('NFD', (s or '').replace('đ', 'd').replace('Đ', 'D'))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').casefold().replace(' ', '')


def tao_pipe(tu_dien, m=M):
    from src.danh_muc import DanhMuc
    from src.tien_xu_ly.char_cnn import BoTachCharCNN
    from src.tien_xu_ly.xep_hang import BoXepHang
    from src.tien_xu_ly.chuan_ten_duong import TuDienDuong
    from src.chuan_hoa import BoChuanHoa
    dm = DanhMuc(); ext = BoTachCharCNN(m / 'char_cnn.pt', threads=1)
    return BoChuanHoa(danh_muc=dm, bo_tach=ext, bo_xep_hang=BoXepHang(m / 'ranker.txt', ext.ma_bam, dm.ma_bam),
                      tu_dien_duong=TuDienDuong(tu_dien), bao_ve_duong=True, tien_to_mac_dinh=True)


def cham_mot(pipe, goc, rows):
    da = goc['dap_an']
    fs = [f for f in CHI_TIET if f in da]
    nhom = defaultdict(lambda: defaultdict(int))
    sai = []
    for r in rows:
        kq = pipe.chuan_hoa(r['dau_vao'])
        d = {'xa': kq.ma_xa == da['ma_xa'] and kq.ma_tinh == da['ma_tinh'],
             'sai': bool(kq.ma_xa) and kq.ma_xa != da['ma_xa']}
        for f in fs:
            if f != 'thon_xom' or r.get('cham_thon', True):
                d[f] = fold(getattr(kq, f)) == fold(da[f])
        for k in ('tat_ca', r['nguon']):
            g = nhom[k]; g['n'] += 1
            for f, v in d.items():
                g[f] += v; g['n_' + f] += 1
        if not d['xa'] or not all(d.get(f, True) for f in fs):
            sai.append({'id': r['id'], 'nguon': r['nguon'], 'dau_vao': r['dau_vao'], 'ra': kq.dia_chi_chuan,
                        'ma_xa': kq.ma_xa, 'canh_bao': kq.canh_bao,
                        'truong_sai': [f for f in ['xa'] + fs if d.get(f) is False]})
    return {k: dict(v) for k, v in nhom.items()}, sai, fs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('thu_muc')
    ap.add_argument('goc', nargs='+')
    ap.add_argument('--tu-dien', default=str(GOC / 'danh_gia' / 'ket_qua' / 'tu_dien_duong_v5.json'))
    ap.add_argument('--ra')
    ap.add_argument('--mo-hinh', type=Path, default=M, help='thư mục có char_cnn.pt và ranker.txt')
    ap.add_argument('--in-sai', action='store_true')
    a = ap.parse_args()
    pipe = tao_pipe(a.tu_dien, a.mo_hinh)
    d = Path(a.thu_muc)
    tong, ket = defaultdict(int), {}
    for gid in a.goc:
        goc = json.loads((d / f'{gid}.json').read_text(encoding='utf-8'))
        rows = [json.loads(l) for p in sorted(d.glob(f'{gid}_*.jsonl')) if 'bi_loai' not in p.name
                for l in open(p, encoding='utf-8')]
        nhom, sai, fs = cham_mot(pipe, goc, rows)
        ket[gid] = {'nhom': nhom, 'sai': sai}
        g = nhom['tat_ca']
        ct = ' '.join(f"{f}={g[f] / max(g['n_' + f], 1):.0%}" for f in fs)
        print(f"{gid} {g['n']:4} câu | xã {g['xa'] / g['n']:6.1%} | sai {g['sai']:3} | {ct} | {goc['dia_chi']}")
        for k in ('code', 'agy'):
            if k in nhom:
                print(f"      {k:4} {nhom[k]['n']:4} câu | xã {nhom[k]['xa'] / nhom[k]['n']:6.1%} | sai {nhom[k]['sai']:3}")
        for k in ('n', 'xa', 'sai'):
            tong[k] += g[k]
        if a.in_sai:
            for s in sai:
                print(f"   [{s['nguon']}] {s['dau_vao']!r} -> {s['ra']!r} {s['ma_xa'] or '-'} sai={s['truong_sai']}")
    print(f"TỔNG {tong['n']} câu | xã {tong['xa'] / max(tong['n'], 1):.1%} | khẳng định sai {tong['sai']}")
    if a.ra:
        Path(a.ra).write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
