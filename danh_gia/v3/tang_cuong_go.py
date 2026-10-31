"""Tăng cường kiểu gõ thật lên các dòng train (goi_[0-9]*.jsonl), nhãn ký tự được dời theo.

Mỗi dòng ra chồng 2-4 phép: bỏ dấu phẩy/gạch ngăn cách (câu viết liền, lỗi tên thôn nuốt cả câu), bỏ dấu (toàn câu
hoặc một số từ), viết thường/HOA, dính số vào chữ sau ("xóm 5mỹ"), telex sót trong tên hành chính, viết tắt chữ loại
(Xã -> x., Huyện -> h.). Không dùng dev, bộ khó hay bộ biến thể.
Dùng: tang_cuong_go.py <so_dong_ra>  -> ghi bo_train/dat/goi_go.jsonl"""
import duong_dan as dd  # gốc repo, CODE_ROOT vào sys.path
import json, random, re, sys, unicodedata

DAT = dd.BO_TRAIN_DAT
R = random.Random(20261101)
DAU_TELEX = {'́': 's', '̀': 'f', '̉': 'r', '̃': 'x', '̣': 'j'}
VIET_TAT = {'xã': ['x.', 'x', 'X.'], 'phường': ['p.', 'P.', 'p'], 'thị trấn': ['tt', 'TT.'], 'huyện': ['h.', 'H.', 'h'],
            'quận': ['q.', 'Q.', 'q'], 'thị xã': ['tx', 'TX.'], 'tỉnh': ['t.', 'T.', 'tinh'], 'thành phố': ['tp', 'TP.', 'Tp']}
HANH_CHINH = {'xa', 'huyen', 'tinh'}


def bo_dau_ky_tu(c):
    if c in 'đĐ':
        return 'd' if c == 'đ' else 'D'
    return unicodedata.normalize('NFD', c)[0]


def telex(w):
    out, dau = '', ''
    for c in unicodedata.normalize('NFD', w):
        if c in DAU_TELEX:
            dau = DAU_TELEX[c]
        elif c in '̛̆':
            out += 'w'
        elif c == '̂':
            out += out[-1:]
        else:
            out += 'dd' if c in 'đĐ' else c
    return out + dau


class Cau:
    """Chuỗi ký tự kèm vị trí gốc từng ký tự (None với ký tự chèn) để dời nhãn."""
    def __init__(self, text, spans):
        self.c = [(ch, i) for i, ch in enumerate(text)]
        self.spans = spans

    def text(self):
        return ''.join(ch for ch, _ in self.c)

    def span_moi(self):
        out = []
        for f, a, b in self.spans:
            vt = [k for k, (_, i) in enumerate(self.c) if i is not None and a <= i < b]
            if not vt:
                return None
            out.append([f, vt[0], vt[-1] + 1])
        return out

    def trong_span(self, k):
        i = self.c[k][1]
        return i is not None and any(a <= i < b for _, a, b in self.spans)

    def thay(self, k0, k1, moi):
        """Thay ký tự [k0, k1) bằng chuỗi moi; ký tự mới mang vị trí gốc của ký tự cũ tương ứng (thừa lấy ký tự cuối)."""
        cu = self.c[k0:k1]
        self.c[k0:k1] = [(ch, cu[min(j, len(cu) - 1)][1]) for j, ch in enumerate(moi)]


def bo_ngan_cach(x):
    t = x.text()
    for m in reversed(list(re.finditer(r'\s*[,;]\s*|\s+-\s+', t))):
        if not any(x.trong_span(k) for k in range(m.start(), m.end()) if t[k] in ',;-'):
            x.thay(m.start(), m.end(), ' ')


def bo_dau(x, mot_phan):
    t = x.text()
    tu = [m.span() for m in re.finditer(r'\w+', t)]
    chon = set(R.sample(range(len(tu)), max(1, len(tu) // 3))) if mot_phan else set(range(len(tu)))
    for j in chon:
        a, b = tu[j]
        x.thay(a, b, ''.join(bo_dau_ky_tu(ch) for ch in t[a:b]))


def dinh_so(x):
    t = x.text()
    ms = [m for m in re.finditer(r'(?<=\d) (?=[^\W\d_])', t)]
    if ms:
        m = R.choice(ms)
        x.thay(m.start(), m.end(), '')


def telex_hanh_chinh(x):
    t = x.text()
    tu = [m for m in re.finditer(r'\w+', t) if not t[m.start():m.end()].isascii()
          and any(f in HANH_CHINH and a <= x.c[m.start()][1] < b for f, a, b in x.spans if x.c[m.start()][1] is not None)]
    if tu:
        m = R.choice(tu)
        x.thay(m.start(), m.end(), telex(t[m.start():m.end()]))


def viet_tat_loai(x):
    t = x.text()
    for f, a, b in x.spans:
        if f not in HANH_CHINH:
            continue
        vt = [k for k, (_, i) in enumerate(x.c) if i == a]
        if not vt:
            continue
        k = vt[0]
        for loai, vtat in VIET_TAT.items():
            if t[k:k + len(loai) + 1].casefold() == loai + ' ' and R.random() < .6:
                vt = R.choice(vtat)  # chỉ viết liền khi có dấu chấm (x.Lương); "xLương" không ai viết
                x.thay(k, k + len(loai) + 1, vt + (R.choice(['', ' ']) if vt.endswith('.') else ' '))
                t = x.text()
                break


def tang_cuong(row):
    x = Cau(row['text'], row['spans'])
    phep = []
    if R.random() < .6:
        bo_ngan_cach(x); phep.append('bo_ngan_cach')
    if R.random() < .4:
        viet_tat_loai(x); phep.append('viet_tat_loai')
    if R.random() < .25:
        telex_hanh_chinh(x); phep.append('telex')
    r = R.random()
    if r < .25:
        bo_dau(x, False); phep.append('bo_dau')
    elif r < .4:
        bo_dau(x, True); phep.append('bo_dau_mot_phan')
    if R.random() < .2:
        dinh_so(x); phep.append('dinh_so')
    t = x.text()
    r = R.random()
    if r < .25:
        x.c = [(ch.lower(), i) for ch, i in x.c]; phep.append('viet_thuong')
    elif r < .35:
        x.c = [(ch.upper(), i) for ch, i in x.c]; phep.append('viet_hoa')
    # Gộp khoảng trắng thừa do các phép trên để lại.
    k = 1
    while k < len(x.c):
        if x.c[k][0] == ' ' and x.c[k - 1][0] == ' ':
            del x.c[k]
        else:
            k += 1
    spans = x.span_moi()
    text = x.text()
    if len(phep) < 2 or spans is None or text == row['text']:
        return None
    return {'id': row['id'] + '_go', 'text': text, 'spans': spans, 'loai_nhieu': row['loai_nhieu'],
            'nhieu_them': 'tang_cuong_go:' + ','.join(phep)}


def main(so_dong):
    rows = [json.loads(l) for p in sorted(DAT.glob('goi_[0-9]*.jsonl')) for l in open(p, encoding='utf-8')]
    R.shuffle(rows)
    out = []
    for r in rows:
        x = tang_cuong(r)
        if x:
            s = sorted(x['spans'], key=lambda z: z[1])  # tự kiểm: span không chồng, nằm trong câu, không rỗng
            assert all(0 <= a < b <= len(x['text']) for _, a, b in s)
            assert all(s[i][2] <= s[i + 1][1] for i in range(len(s) - 1))
            out.append(x)
        if len(out) >= int(so_dong):
            break
    with open(DAT / 'goi_go.jsonl', 'w', encoding='utf-8', newline='\n') as f:
        for x in out:
            f.write(json.dumps(x, ensure_ascii=False) + '\n')
    print(len(out), 'dong tang cuong kieu go')
    for x in out[:15]:
        print('  ', x['text'], '|', [(f, x['text'][a:b]) for f, a, b in x['spans']])


if __name__ == '__main__':
    main(sys.argv[1])
