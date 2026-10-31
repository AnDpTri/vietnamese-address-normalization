"""Sinh biến thể tổ hợp (máy móc, có seed) từ một địa chỉ gốc đã có đáp án.

Mỗi biến thể chồng 3-8 phép biến đổi lên các thành phần địa chỉ và ghi rõ phép đã dùng. Chỉ giữ câu
còn đủ ngữ cảnh: các tên còn đọc được (kể cả sai chính tả) phải chỉ ra đúng một xã cũ trong danh mục.

Dùng (từ gốc repo): py -3.12 data/bien_the/sinh_to_hop.py <goc.json> <ra.jsonl> [so_bien_the=60] [seed=20261031]
goc.json: {"id", "thanh_phan": [{"cap", "loai", "viet_tat": [...], "ten"}...], "dap_an": {...}}
"""
import json
import random
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.tien_xu_ly.tien_xu_ly import go_telex  # noqa: E402  người đọc hiểu được telex sót (Hoawngf = Hoằng)

SO_CHU = {'1': 'một', '2': 'hai', '3': 'ba', '4': 'bốn', '5': 'năm', '6': 'sáu', '7': 'bảy', '8': 'tám', '9': 'chín'}
# Phím kề trên bàn phím QWERTY, cho lỗi trượt phím.
KE = {'a': 'qsz', 'd': 'sfe', 'h': 'gjy', 'i': 'uok', 'k': 'jl', 'l': 'k', 'm': 'n', 'n': 'bm', 'o': 'ip',
      'g': 'fh', 'u': 'yi', 'y': 'tu', 't': 'ry', 'c': 'xv', 'x': 'zc', 'b': 'vn', 'p': 'o', 's': 'ad', 'r': 'et'}
TELEX = {'ă': 'aw', 'â': 'aa', 'đ': 'dd', 'ê': 'ee', 'ô': 'oo', 'ơ': 'ow', 'ư': 'uw'}
DAU_TELEX = {'́': 's', '̀': 'f', '̉': 'r', '̃': 'x', '̣': 'j'}
NHIEU = ['0912345678', 'Anh Tuấn', 'gần chợ', 'đối diện trường cấp 1', '(giao giờ hành chính)', 'Việt Nam',
         'sđt 0987.654.321', 'nhà bác Hùng']
TOI_THIEU_PHEP, TOI_DA_PHEP = 3, 8
NGAN_CACH = [', ', ',', ' ', ' - ', '\n', ' ; ', ', ', ', ']


def bo_dau(s):
    s = unicodedata.normalize('NFD', s.replace('đ', 'd').replace('Đ', 'D'))
    return unicodedata.normalize('NFC', ''.join(c for c in s if unicodedata.category(c) != 'Mn'))


def telex(word):
    """Gõ telex nhưng bộ gõ không bật: định -> ddinhj."""
    out, dau = '', ''
    for c in unicodedata.normalize('NFD', word):
        if c in DAU_TELEX:
            dau = DAU_TELEX[c]
        elif c == '̆':
            out += 'w'
        elif c == '̂':
            out += out[-1:] if out else ''
        elif c == '̛':
            out += 'w'
        else:
            out += 'dd' if c in 'đĐ' else c
    return out + dau


def truot_phim(word, rng):
    vt = [i for i, c in enumerate(word) if c.lower() in KE]
    if not vt:
        return word + word[-1]
    i = rng.choice(vt)
    return word[:i] + rng.choice(KE[word[i].lower()]) + word[i + 1:] if rng.random() < .6 else word[:i + 1] + rng.choice(KE[word[i].lower()]) + word[i + 1:]


THANH = '̣́̀̉̃'
LAN_AM = [('l', 'n'), ('n', 'l'), ('s', 'x'), ('x', 's'), ('tr', 'ch'), ('ch', 'tr'), ('d', 'gi'), ('gi', 'd'),
          ('y', 'i'), ('i', 'y')]


def mot_am_tiet(ten, rng, f):
    w = ten.split(); i = rng.randrange(len(w)); w[i] = f(w[i]); return ' '.join(w)


def sai_dau_thanh(am, rng):
    """Đổi, bỏ hoặc thêm dấu thanh của một âm tiết: Lộc -> Lốc, Mỹ -> My."""
    d = unicodedata.normalize('NFD', am)
    co = [c for c in d if c in THANH]
    goc = ''.join(c for c in d if c not in THANH)
    nguyen_am = [i for i, c in enumerate(goc) if c.lower() in 'aeiouy']
    if not nguyen_am:
        return am
    moi = rng.choice([t for t in THANH + ' ' if t not in co])
    i = nguyen_am[len(nguyen_am) // 2] + 1
    while i < len(goc) and unicodedata.combining(goc[i]):
        i += 1  # đặt dấu thanh sau dấu mũ/móc của nguyên âm (â, ơ), không chen vào giữa
    return unicodedata.normalize('NFC', goc[:i] + (moi if moi != ' ' else '') + goc[i:])


def lan_am(am, rng):
    """Lẫn âm địa phương ở đầu âm tiết hoặc i/y: Lộc -> Nộc, Mỹ -> Mĩ."""
    thap = am.casefold()
    for a, b in rng.sample(LAN_AM, len(LAN_AM)):
        if (a in 'iy' and a in thap) or thap.startswith(a):
            i = thap.index(a)
            moi = am[:i] + (b.upper() if am[i].isupper() else b) + am[i + len(a):]
            return moi
    return am


def dinh_am_tiet(ten, rng):
    w = ten.split()
    if len(w) < 2:
        return ten
    i = rng.randrange(len(w) - 1)
    return ' '.join(w[:i] + [w[i] + w[i + 1]] + w[i + 2:])


LOI_TEN_HAM = {
    'truot_phim': lambda t, rng: mot_am_tiet(t, rng, lambda a: truot_phim(a, rng)),
    'telex_sot': lambda t, rng: mot_am_tiet(t, rng, telex),
    'sai_dau_thanh': lambda t, rng: mot_am_tiet(t, rng, lambda a: sai_dau_thanh(a, rng)),
    'lan_am': lambda t, rng: mot_am_tiet(t, rng, lambda a: lan_am(a, rng)),
    'dinh_am_tiet': dinh_am_tiet,
}
LOI_TEN = sorted(LOI_TEN_HAM)


def chu_dau(ten):
    return ''.join(w[0] for w in ten.split()).lower()


def khoa(s):
    return bo_dau(s).casefold().replace(' ', '')


class DanhMucCu:
    """Đếm xã cũ khớp các tên còn lại (gồm tên cũ hơn trong ten_cu_alias) để gắn nhãn đủ/mơ hồ."""
    def __init__(self, goc_repo):
        import csv
        self.xa = []  # (ma_xa, khóa tên xã, ma_huyen, khóa huyện, ma_tinh, khóa tỉnh)
        for r in csv.DictReader(open(goc_repo / 'data/clean/cu_tinh_huyen_xa.csv', encoding='utf-8-sig')):
            self.xa.append((r['ma_xa'], khoa(r['ten_xa']), r['ma_huyen'], khoa(r['ten_huyen']), r['ma_tinh'], khoa(r['ten_tinh'])))
        self.alias = {'xa': {}, 'huyen': {}}
        for r in csv.DictReader(open(goc_repo / 'data/ten_cu/ten_cu_alias.csv', encoding='utf-8-sig')):
            if r['cap'] in self.alias:
                self.alias[r['cap']].setdefault(r['ma_cu'], set()).add(r['khoa_alias'])

    def so_xa_khop(self, ten):
        """ten: {cap: tên} của các cấp còn đọc được. Trả số xã cũ khớp."""
        if 'xa' not in ten:
            return 0
        kx, kh, kt = (khoa(ten[c]) if c in ten else None for c in ('xa', 'huyen', 'tinh'))
        ok = set()
        for ma, x, mh, h, mt, t in self.xa:
            if kx != x and kx not in self.alias['xa'].get(ma, ()):
                continue
            if kh and kh != h and kh not in self.alias['huyen'].get(mh, ()):
                continue
            if kt and kt != t:
                continue
            ok.add(ma)
        return len(ok)

    def tinh_cua(self, ten):
        """Mã tỉnh cũ của địa chỉ gốc (tên đầy đủ, đã chỉ ra đúng một xã)."""
        kx, kh, kt = (khoa(ten[c]) for c in ('xa', 'huyen', 'tinh'))
        return next(mt for ma, x, mh, h, mt, t in self.xa
                    if (kx == x or kx in self.alias['xa'].get(ma, ())) and kt == t)

    def loi_con_doc_duoc(self, cap, ten_dung, ten_loi, ma_tinh):
        """Tên gõ sai chỉ còn đọc được khi nó gần tên đúng hơn hẳn mọi tên khác cùng cấp trong tỉnh
        ('Hoằng Nộc' cách đều Hoằng Lộc và Hoằng Ngọc thì không còn chỉ ra xã nào)."""
        a, dung = re.sub(r'[^a-z0-9]', '', khoa(go_telex(ten_loi))), khoa(ten_dung)
        cot = {'xa': 1, 'huyen': 3, 'tinh': 5}[cap]
        khac = {r[cot] for r in self.xa if (cap == 'tinh' or r[4] == ma_tinh) and r[cot] != dung}
        d = khoang_cach(a, dung)
        return all(khoang_cach(a, k) > d for k in khac)


def khoang_cach(a, b):
    truoc = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        sau = [i]
        for j, cb in enumerate(b, 1):
            sau.append(min(truoc[j] + 1, sau[j - 1] + 1, truoc[j - 1] + (ca != cb)))
        truoc = sau
    return truoc[-1]


# Mỗi phép: (tên, phạm vi 'tp' cho từng thành phần hoặc 'cau' cho cả câu, làm mất thông tin xã?)
def sinh(goc, n, seed, dm):
    rng = random.Random(seed)
    tp_goc = goc['thanh_phan']
    ma_tinh = dm.tinh_cua({t['cap']: t['ten'] for t in tp_goc if t['cap'] in ('xa', 'huyen', 'tinh')})
    seen, out = set(), []
    thu = 0
    while len(out) < n and thu < n * 50:
        thu += 1
        phep = []
        tps, con_doc_duoc = [], {}
        for t in tp_goc:
            cap, loai, ten = t['cap'], t['loai'], t['ten']
            hanh_chinh = cap in ('xa', 'huyen', 'tinh')
            if hanh_chinh and rng.random() < (.06 if cap == 'xa' else .15):
                phep.append(f'bo_cap:{cap}'); continue
            p = []
            r = rng.random()
            if r < .3 and t.get('viet_tat'):
                loai = rng.choice(t['viet_tat']); p.append(f'viet_tat_loai:{cap}')
            elif r < .55 and loai:
                loai = ''; p.append(f'bo_loai:{cap}')
            doc_duoc = True
            if any(c.isdigit() for c in ten):
                # Tên có chữ số: không áp lỗi gõ (5 -> 55, 110A -> 110S là nơi khác), chỉ đổi số sang chữ.
                if ten.isdigit() and rng.random() < .2:
                    ten = SO_CHU.get(ten, ten); p.append('so_bang_chu')
                if t['ten'].isdigit() and not loai and hanh_chinh:
                    doc_duoc = False  # "5, 3, Hồ Chí Minh": mất chữ loại thì số không còn chỉ ra phường/quận
            elif hanh_chinh and rng.random() < .12:
                ten = chu_dau(ten); p.append(f'chu_dau:{cap}'); doc_duoc = False
            else:
                # Mỗi tên chịu 0-2 lỗi gõ chồng lên nhau; tên còn đọc được nếu vẫn gần tên đúng hơn hẳn tên khác.
                for _ in range(rng.choices((0, 1, 2), (.35, .45, .2))[0]):
                    ten_loi, ten = rng.choice(LOI_TEN), ten
                    ten = LOI_TEN_HAM[ten_loi](ten, rng)
                    p.append(f'{ten_loi}:{cap}')
                if hanh_chinh and ten != t['ten'] and not dm.loi_con_doc_duoc(cap, t['ten'], ten, ma_tinh):
                    doc_duoc = False
            phep += p
            if doc_duoc and hanh_chinh:
                con_doc_duoc[cap] = t['ten']
            tps.append((cap, (loai + ' ' + ten).strip() if loai and not loai.endswith('.') else (loai + ten if loai else ten)))
        # Đủ thông tin khi các tên còn đọc được chỉ ra đúng một xã cũ; chữ cái đầu tính như đã bỏ cấp đó.
        mat_xa = dm.so_xa_khop(con_doc_duoc) != 1
        if rng.random() < .3:
            tps.reverse(); phep.append('dao_nguoc')
        elif rng.random() < .15:
            rng.shuffle(tps); phep.append('xao_tron')
        sep = rng.choice(NGAN_CACH)
        if sep != ', ':
            phep.append('ngan_cach:' + repr(sep))
        s = sep.join(x for _, x in tps)
        r = rng.random()
        if r < .25:
            s = bo_dau(s); phep.append('bo_dau')
        elif r < .4:
            w = s.split(' '); idx = rng.sample(range(len(w)), max(1, len(w) // 3))
            s = ' '.join(bo_dau(x) if i in idx else x for i, x in enumerate(w)); phep.append('bo_dau_mot_phan')
        r = rng.random()
        if r < .15:
            s = s.upper(); phep.append('viet_hoa')
        elif r < .4:
            s = s.lower(); phep.append('viet_thuong')
        if rng.random() < .15:
            s2 = re.sub(r'(\d) (\w)', r'\1\2', s, count=1)
            if s2 != s:
                s = s2; phep.append('dinh_so_chu')
        if rng.random() < .15:
            nh = rng.choice(NHIEU)
            s = f'{nh} {s}' if rng.random() < .5 else f'{s} {nh}'; phep.append('nhieu')
        # Chỉ giữ câu còn đủ ngữ cảnh và không quá cực đoan.
        if mat_xa or not TOI_THIEU_PHEP <= len(phep) <= TOI_DA_PHEP or s in seen or s == goc.get('dia_chi'):
            continue
        seen.add(s)
        # Bỏ chữ loại của thôn ("5, Mỹ Hưng") thì không biết 5 là số nhà hay số xóm: không chấm trường thôn.
        out.append({'id': f"{goc['id']}_m{len(out) + 1:03d}", 'goc': goc['id'], 'dau_vao': s, 'phep': phep,
                    'so_phep': len(phep), 'muc_thong_tin': 'du', 'cham_thon': 'bo_loai:thon' not in phep,
                    'nguon': 'code'})
    return out


def main(goc_path, ra, n=60, seed=20261031):
    goc = json.loads(Path(goc_path).read_text(encoding='utf-8'))
    dm = DanhMucCu(Path(__file__).resolve().parents[2])
    if dm.so_xa_khop({t['cap']: t['ten'] for t in goc['thanh_phan'] if t['cap'] != 'thon'}) != 1:
        sys.exit('Địa chỉ gốc không chỉ ra đúng một xã cũ: kiểm lại tên trước khi sinh')
    rows = sinh(goc, int(n), int(seed), dm)
    Path(ra).parent.mkdir(parents=True, exist_ok=True)
    with open(ra, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'{len(rows)} biến thể -> {ra}')


if __name__ == '__main__':
    main(*sys.argv[1:])
