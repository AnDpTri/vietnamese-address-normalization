"""Bộ đánh giá chuẩn. Xem danh_gia/chuan/QUY_CHUAN.md.

Dùng (từ gốc repo, Python của .venv-neural):
  python -m danh_gia.chuan chay <ten> [--tap dev_that,dev_sinh,bo_kho,test400,vang] [--cnn ..] [--ranker ..] [--tu-dien ..]
  python -m danh_gia.chuan cham <ten>
  python -m danh_gia.chuan so_sanh <ten_A_dang_dung> <ten_B_de_xuat>
Kết quả ở rieng/danh_gia_chuan/<ten>/ (không lên git vì chứa đầu ra trên đáp án kín).
"""
import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from .cham import cham_mau, so_sanh_cap, tong_hop
from .du_lieu import GOC, TAT_CA_TAP, TRUONG, VAI_TRO, nap

THU_MUC = GOC / 'rieng' / 'danh_gia_chuan'
NHOM_BAO_CAO = ('that', 'sinh', 'do_thi', 'nong_thon', 'dia_chi_cu', 'xa_bi_chia', 'co_thon', 'co_duong',
                'khong_xac_dinh_xa', 'nhan_da_duyet_ai', 'nhan_can_duyet')
GIU_LAI = ('so_nha', 'ngo_ngach_hem', 'thon_xom', 'duong', 'xa_phuong', 'ma_xa', 'ma_tinh', 'canh_bao', 'xa_moi_ung_vien')


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16] if p and Path(p).exists() else None


def _danh_muc():
    sys.path.insert(0, str(GOC))
    from src.danh_muc import DanhMuc
    return DanhMuc()


def chay(a):
    sys.path.insert(0, str(GOC))
    from src import cau_hinh
    pipe = cau_hinh.tao_bo_chuan_hoa(cnn=a.cnn, ranker=a.ranker, tu_dien_duong=a.tu_dien)
    dm = pipe.danh_muc
    ra = THU_MUC / a.ten
    ra.mkdir(parents=True, exist_ok=True)
    try:
        commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=GOC, capture_output=True, text=True).stdout.strip()
        ban_nhap = bool(subprocess.run(['git', 'status', '--porcelain', 'src'], cwd=GOC, capture_output=True, text=True).stdout.strip())
    except OSError:
        commit, ban_nhap = None, None
    cnn, ranker, tu_dien = a.cnn or cau_hinh.CNN, a.ranker or cau_hinh.RANKER, a.tu_dien or cau_hinh.TU_DIEN_DUONG
    meta = {'ten': a.ten, 'luc': time.strftime('%Y-%m-%d %H:%M:%S'), 'commit': commit, 'src_co_sua_chua_commit': ban_nhap,
            'cnn': str(cnn), 'cnn_sha': _sha(cnn), 'ranker': str(ranker), 'ranker_sha': _sha(ranker),
            'tu_dien_duong': str(tu_dien), 'tu_dien_sha': _sha(tu_dien),
            'bao_ve_duong': cau_hinh.BAO_VE_DUONG, 'tien_to_mac_dinh': cau_hinh.TIEN_TO_MAC_DINH, 'tap': {}}
    for tap in a.tap.split(','):
        mau = nap(tap, dm)
        if not mau:
            print(f'{tap}: không có trên máy, bỏ qua'); continue
        for m in mau[:10]:
            pipe.chuan_hoa(m.dau_vao)  # làm nóng
        with open(ra / f'{tap}.jsonl', 'w', encoding='utf-8', newline='\n') as f:
            for m in mau:
                t0 = time.perf_counter()
                kq = asdict(pipe.chuan_hoa(m.dau_vao))
                ms = (time.perf_counter() - t0) * 1000
                f.write(json.dumps({'id': m.id, 'ms': round(ms, 2), 'out': {k: kq[k] for k in GIU_LAI}}, ensure_ascii=False) + '\n')
        meta['tap'][tap] = len(mau)
        print(f'{tap}: {len(mau)} câu', flush=True)
    (ra / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')


def _doc(ten, tap):
    p = THU_MUC / ten / f'{tap}.jsonl'
    return {d['id']: d for d in map(json.loads, open(p, encoding='utf-8'))} if p.exists() else None


def _cham_tap(ten, tap, dm):
    mau = nap(tap, dm)
    ra = _doc(ten, tap)
    if not mau or ra is None:
        return None, None, None
    mau = [m for m in mau if m.id in ra]
    ket = {m.id: cham_mau(m, ra[m.id]['out']) for m in mau}
    ms = sorted(ra[m.id]['ms'] for m in mau)
    return mau, ket, {'trung_vi_ms': statistics.median(ms), 'p95_ms': ms[int(.95 * (len(ms) - 1))]}


def _dong(ten_nhom, tk):
    if not tk or not tk['n']:
        return None
    ci = tk['du_6_ci']; sci = tk['xa_khang_dinh_sai_ci']
    f = lambda v: '—' if v is None else f'{v:.1f}'
    return (f"| {ten_nhom} | {tk['n']} | **{tk['du_6_pct']:.1f}** ({ci[0]:.1f}–{ci[1]:.1f}) | "
            + ' | '.join(f(tk[x]) for x in TRUONG)
            + f" | {tk['xa_khang_dinh_sai']} ({tk['xa_khang_dinh_sai_pct']:.1f}%, ≤{sci[1]:.1f}) | {f(tk['xa_chinh_xac_khi_khang_dinh'])} | {f(tk['xa_do_phu'])} "
            f"| {tk['dien_thua']} ({tk['dien_thua_duong']}) |")


TIEU_DE = ('| Nhóm | n | Đủ 6 trường % (KTC 95%) | Số nhà | Ngõ | Thôn | Đường | Mã xã | Mã tỉnh '
           '| Khẳng định sai mã xã | Chính xác khi khẳng định | Độ phủ mã xã | Điền thừa chi tiết (đường) |\n|' + '---|' * 13)


def cham(a):
    dm = _danh_muc()
    meta = json.loads((THU_MUC / a.ten / 'meta.json').read_text(encoding='utf-8'))
    md = [f"# Đánh giá chuẩn: {a.ten}", '',
          f"Commit `{meta['commit']}`{' (src có sửa chưa commit)' if meta.get('src_co_sua_chua_commit') else ''}; "
          f"CNN `{meta['cnn_sha']}`, ranker `{meta['ranker_sha']}`, từ điển đường `{Path(meta['tu_dien_duong']).name}` `{meta['tu_dien_sha']}`; "
          f"tiền tố mặc định: {meta['tien_to_mac_dinh']}. Chạy lúc {meta['luc']}.", '']
    js = {}
    for tap in TAT_CA_TAP:
        mau, ket, toc = _cham_tap(a.ten, tap, dm)
        if mau is None:
            continue
        md += [f"## {tap} (vai trò: {VAI_TRO[tap]}; tốc độ trung vị {toc['trung_vi_ms']:.0f} ms, p95 {toc['p95_ms']:.0f} ms)", '', TIEU_DE,
               _dong('**tất cả**', tong_hop(mau, ket))]
        js[tap] = {'tat_ca': tong_hop(mau, ket), 'toc_do': toc}
        nhom_co = sorted({g for m in mau for g in m.nhom if g.startswith('nhieu_')})
        for g in NHOM_BAO_CAO + tuple(nhom_co):
            con = [m for m in mau if g in m.nhom]
            if con and len(con) < len(mau):
                tk = tong_hop(con, ket); js[tap][g] = tk
                md.append(_dong(g, tk))
        tk = js[tap]['tat_ca']
        if 'chia_n' in tk:
            dong = f"Xã cũ bị chia ({tk['chia_n']} câu). "
            if tk['chia_giai_n']:
                dong += f"Vàng phân giải được xã mới ({tk['chia_giai_n']} câu): đúng mã {tk['chia_giai_dung']:.1f}%. "
            if tk['chia_trong_n']:
                dong += (f"Vàng phải để trống ({tk['chia_trong_n']} câu): để trống đúng {tk['chia_trong_dung']:.1f}%, "
                         f"gắn cờ `xa_bi_chia` {tk['chia_trong_gan_co']:.1f}%"
                         + (f", danh sách ứng viên phủ đủ {tk['chia_phu_ung_vien']:.1f}%" if tk.get('chia_phu_ung_vien') is not None else '') + '.')
            md += ['', dong]
        md.append('')
    md += ['KTC 95%: khoảng tin cậy Wilson. "≤x" là cận trên KTC của tỷ lệ khẳng định sai.',
           'Số chính để chọn cấu hình là dev_that. test400 có nhãn AI chưa người duyệt: chỉ tham khảo.']
    (THU_MUC / a.ten / 'bao_cao.md').write_text('\n'.join(md), encoding='utf-8')
    (THU_MUC / a.ten / 'bao_cao.json').write_text(json.dumps(js, ensure_ascii=False, indent=1), encoding='utf-8')
    print('\n'.join(md))


def so_sanh(a):
    dm = _danh_muc()
    md = [f"# So sánh: A = {a.a} (đang dùng), B = {a.b} (đề xuất)", '',
          '| Tập | Vai trò | n | Đủ 6 A → B | A đúng B sai | A sai B đúng | p | Kết luận | Khẳng định sai A → B | p | Kết luận '
          '| Điền thừa A → B | p | Kết luận |',
          '|' + '---|' * 14]
    ket_luan, chi_tiet = {}, []
    for tap in TAT_CA_TAP:
        ma, ka, _ = _cham_tap(a.a, tap, dm)
        mb, kb, _ = _cham_tap(a.b, tap, dm)
        if ma is None or mb is None:
            continue
        chung = [m for m in ma if m.id in kb]
        ss = so_sanh_cap(chung, ka, kb)
        ta, tb = tong_hop(chung, ka), tong_hop(chung, kb)
        d, s, t = ss['du_6'], ss['khong_khang_dinh_sai'], ss['khong_dien_thua']
        ket_luan[tap] = ss
        md.append(f"| {tap} | {VAI_TRO[tap]} | {len(chung)} | {ta['du_6_pct']:.1f} → {tb['du_6_pct']:.1f} | {d['a_dung_b_sai']} | {d['a_sai_b_dung']} "
                  f"| {d['p']:.3f} | {d['ket_luan']} | {ta['xa_khang_dinh_sai']} → {tb['xa_khang_dinh_sai']} | {s['p']:.3f} | {s['ket_luan']} "
                  f"| {ta['dien_thua']} → {tb['dien_thua']} | {t['p']:.3f} | {t['ket_luan']} |")
        ra_a, ra_b = _doc(a.a, tap), _doc(a.b, tap)
        for m in chung:
            if ka[m.id]['du_6'] != kb[m.id]['du_6'] or ka[m.id]['xa'] != kb[m.id]['xa'] or ka[m.id]['thua'] != kb[m.id]['thua']:
                oa, ob = ra_a[m.id]['out'], ra_b[m.id]['out']
                khac = [f for f in TRUONG if (oa.get(f) or '') != (ob.get(f) or '')]
                chi_tiet.append(f"| {tap} | {m.id} | {m.dau_vao[:70]} | {'đúng' if ka[m.id]['du_6'] else 'sai'} → {'đúng' if kb[m.id]['du_6'] else 'sai'} | "
                                + '; '.join(f"{f}: `{oa.get(f) or ''}` → `{ob.get(f) or ''}` (vàng `{m.vang[f]}`)" for f in khac) + ' |')
    # Luật chấp nhận (QUY_CHUAN.md mục 4): test400 và vang không tham gia quyết định.
    loai = [f"{tap}: {ten} kém hơn có ý nghĩa" for tap, ss in ket_luan.items() if VAI_TRO[tap] in ('chon', 'hoi_quy', 'do_ben')
            for ten, x in (('đủ 6 trường', ss['du_6']), ('khẳng định sai', ss['khong_khang_dinh_sai']),
                           ('điền thừa', ss['khong_dien_thua'])) if x['ket_luan'] == 'KÉM HƠN']
    ten_do = (('đủ 6 trường', 'du_6'), ('khẳng định sai', 'khong_khang_dinh_sai'), ('điền thừa', 'khong_dien_thua'))
    tot = {tap: [ten for ten, k in ten_do if ss[k]['ket_luan'] == 'TỐT HƠN'] for tap, ss in ket_luan.items()
           if VAI_TRO[tap] in ('chon', 'hoi_quy', 'do_ben')}
    if loai:
        phan_quyet = 'LOẠI B: ' + '; '.join(loai)
    elif tot.get('dev_that'):
        phan_quyet = 'NHẬN B (mạnh): dev_that tốt hơn có ý nghĩa về ' + ', '.join(tot['dev_that'])
    elif any(tot.values()):
        phan_quyet = ('NHẬN B (yếu): không tập nào kém hơn; tốt hơn có ý nghĩa chỉ ở tập phụ: '
                      + '; '.join(f"{tap} ({', '.join(v)})" for tap, v in tot.items() if v)
                      + '. Tập phụ có thể thiên lệch (bộ khó cùng nguồn agy với train): đọc các câu đổi kết quả trước khi nhận.')
    else:
        phan_quyet = ('TRUNG TÍNH: không tập nào khác biệt có ý nghĩa. Giữ A, trừ khi B có lý do khác ngoài số đo '
                      '(ghi rõ lý do khi nhận), và xem từng câu đổi kết quả bên dưới.')
    md += ['', f"**Phán quyết theo luật:** {phan_quyet}", '',
           f"## Các câu đổi kết quả ({len(chi_tiet)})", '', '| Tập | id | Đầu vào | Đủ 6 A → B | Trường khác nhau: A → B (vàng) |', '|---|---|---|---|---|'] + chi_tiet
    ra = THU_MUC / f"so_sanh_{a.a}__{a.b}.md"
    ra.write_text('\n'.join(md), encoding='utf-8')
    print('\n'.join(md[:4 + len(ket_luan) + 3]))
    print(f'... chi tiết: {ra}')


def main():
    ap = argparse.ArgumentParser(prog='python -m danh_gia.chuan')
    sp = ap.add_subparsers(dest='lenh', required=True)
    c = sp.add_parser('chay'); c.add_argument('ten'); c.add_argument('--tap', default=','.join(TAT_CA_TAP))
    c.add_argument('--cnn'); c.add_argument('--ranker'); c.add_argument('--tu-dien')
    c.set_defaults(ham=chay)
    c = sp.add_parser('cham'); c.add_argument('ten'); c.set_defaults(ham=cham)
    c = sp.add_parser('so_sanh'); c.add_argument('a'); c.add_argument('b'); c.set_defaults(ham=so_sanh)
    a = ap.parse_args()
    a.ham(a)


if __name__ == '__main__':
    main()
