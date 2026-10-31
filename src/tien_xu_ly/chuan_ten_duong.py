"""Tra tên đường từ train; không phải danh mục đường đã xác minh.

Chỉ bổ sung dấu/mở rộng dạng viết tắt có một kết quả trong tỉnh đã chọn.
Không sửa dấu đã nhập và không dùng nhãn dev/test. Đoán gần đúng (chuan_hoa_gan_dung) chỉ dùng cho đoạn
mô hình đã gán là đường, có ngưỡng chặt và luôn kèm cảnh báo là tên đoán.
"""

import hashlib
import itertools
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from .quy_tac import CHI_TIET, SO_CO_DAU, khop_tien_to
from .tien_xu_ly import bo_dau, go_telex, token_co_vi_tri


def tach_ten(value):
    tokens = [t.chu for t in token_co_vi_tri(value)]
    if not tokens:
        return None
    marker = khop_tien_to(tokens, 0, CHI_TIET)
    if marker and marker[1][0] == 'duong':
        end, (_, kind) = marker
        body = tokens[end:]
        co_tien_to = True
    else:
        kind = 'Đường'
        body = tokens
        co_tien_to = False
    if not body or any(not t.isalnum() for t in body):
        return None
    return kind, body, co_tien_to


def khoa(words):
    return ''.join(bo_dau(w) for w in words)


SO_CHU = {
    'mot': ('mot', 'm', '1'),
    'hai': ('hai', 'h', '2'),
    'ba': ('ba', 'b', '3'),
    'bon': ('bon', 'b', '4'),
    'tu': ('tu', 't', '4'),
    'nam': ('nam', 'n', '5'),
    'sau': ('sau', 's', '6'),
    'bay': ('bay', 'b', '7'),
    'tam': ('tam', 't', '8'),
    'chin': ('chin', 'c', '9'),
    'muoi': ('muoi', 'm', '10'),
}


_AM_TIET = re.compile(
    r'(ngh|ng|nh|ch|gh|gi|kh|ph|qu|th|tr|[bcdghklmnprstvx])?'
    r'(uye|uya|uyu|ieu|yeu|oai|oay|oao|oeo|uay|uoi|uou|ai|ao|au|ay|eo|eu|ia|ie|iu|oa|oe|oi|oo|ua|ue|ui|uo|uu|uy|ye'
    r'|[aeiouy])'
    r'(ch|ng|nh|[cmnpt])?')


def am_tiet_hop_le(w):
    """Âm tiết viết được theo chính tả tiếng Việt (xét dạng không dấu): Linh có, Linnh/Quys/Tabg không."""
    w = bo_dau(w).casefold()
    return w.isdigit() or bool(_AM_TIET.fullmatch(w))


def khoang_cach(a, b):
    truoc = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        sau = [i]
        for j, cb in enumerate(b, 1):
            sau.append(min(truoc[j] + 1, sau[j - 1] + 1, truoc[j - 1] + (ca != cb)))
        truoc = sau
    return truoc[-1]


def khoa_so(words):
    """Khóa coi số viết bằng chữ và bằng chữ số là một: Tháng Tám = Tháng 8. Giữ dấu (Tám khác Tâm)."""
    words = [unicodedata.normalize('NFC', w).casefold() for w in words]
    return tuple(SO_CO_DAU.get(w, w) for w in words)


def gop_cung_ten(out):
    """Các mục chỉ khác nhau ở cách viết số (Cách Mạng Tháng 8 / Tháng Tám) là một đường: giữ dạng viết bằng chữ."""
    nhom = {}
    for item in out:
        kind, words, _ = tach_ten(item['gia_tri'])
        k = (kind, khoa_so(words))
        cu = nhom.get(k)
        if cu is None or (any(c.isdigit() for c in cu['gia_tri']) and not any(c.isdigit() for c in item['gia_tri'])):
            nhom[k] = item
    return list(nhom.values())


def cac_dang(words):
    """Dạng đầy đủ và tổ hợp nguyên từ/chữ đầu, không sinh biến thể địa chỉ."""
    folded = [bo_dau(w) for w in words]
    out = {''.join(folded)}
    if 2 <= len(words) <= 7 and all(w.isalnum() for w in folded):
        choices = []
        for w in folded:
            if w in SO_CHU:
                choices.append(SO_CHU[w])
            elif w.isdigit():
                choices.append((w,))
            else:
                choices.append((w, w[0]))
        for parts in itertools.product(*choices):
            key = ''.join(parts)
            if len(key) >= 3:
                out.add(key)
    return out


def tuong_thich_dau(actual, canonical):
    actual = unicodedata.normalize('NFC', ''.join(actual)).casefold()
    canonical = unicodedata.normalize('NFC', ''.join(canonical)).casefold()
    if bo_dau(actual) != bo_dau(canonical):
        # Chỉ mở rộng viết tắt hoàn toàn không dấu.
        return actual == bo_dau(actual)
    return len(actual) == len(canonical) and all(a == b or a == bo_dau(b) for a, b in zip(actual, canonical))


def _khong_dau(words):
    text = ' '.join(words)
    return bo_dau(text) == text.casefold() and any(c.isalpha() for c in text)


def muc_bi_loi(entry, dang_theo_khoa):
    """Mục từ điển hỏng do nhãn train nhiễu: chữ bị chẻ/hoa lẫn ('Nguyễ N Khuyế N') hoặc tên KHÔNG DẤU
    trong khi cùng khóa đã có dạng có dấu (nó làm mọi tỉnh khác từ chối vì 'nhiều dạng')."""
    parsed = tach_ten(entry['canonical'])
    if not parsed:
        return False
    words = parsed[1]
    if any(len(w) == 1 and w.isalpha() and w.isupper() and i > 0 and words[i - 1][-1].islower() for i, w in enumerate(words)):
        return True
    if any(any(c.isupper() for c in w[1:]) and any(c.islower() for c in w) for w in words):
        return True
    if _khong_dau(words):
        return any(not _khong_dau(other) for other in dang_theo_khoa[khoa(words)])
    return False


class TuDienDuong:
    def __init__(self, path):
        path = Path(path)
        self.ma_bam = hashlib.sha256(path.read_bytes()).hexdigest()
        payload = json.loads(path.read_text(encoding='utf-8'))
        if payload.get('format') != 1 or payload.get('source_scope') != 'train_only':
            raise ValueError('Từ điển đường phải có schema train_only phiên bản 1')
        self.index = defaultdict(dict)
        self.index_bare = defaultdict(dict)
        self.index_qg = defaultdict(dict)
        self.index_bare_qg = defaultdict(dict)
        self._ten_theo_tinh = None  # tỉnh -> khóa tên đầy đủ -> mục, dựng khi cần đoán gần đúng
        dang_theo_khoa = defaultdict(list)
        for item in payload['entries']:
            parsed = tach_ten(item['canonical'])
            if parsed:
                dang_theo_khoa[khoa(parsed[1])].append(parsed[1])
        self.so_muc_bi_loi = 0
        for item in payload['entries']:
            if muc_bi_loi(item, dang_theo_khoa):
                self.so_muc_bi_loi += 1
                continue
            parsed = tach_ten(item['canonical'])
            if not parsed or not item['province']:
                raise ValueError('Tên/tỉnh từ điển không hợp lệ')
            kind, words, _ = parsed
            for key in cac_dang(words):
                self.index[item['province'], kind, key][item['canonical'].casefold()] = item
                self.index_bare[item['province'], key][item['canonical'].casefold()] = item
                self.index_qg[kind, key][item['canonical'].casefold()] = item
                self.index_bare_qg[key][item['canonical'].casefold()] = item

    def ung_vien(self, value, ma_tinh):
        """Trả cả va chạm và xung đột dấu; không chọn tên thay caller. Không thấy thì thử lại sau khi gỡ phím telex
        còn sót (Traanf Quý Kiên -> Tran Quý Kiên): đó là đọc lại đúng chữ đã gõ, không phải đoán gần đúng."""
        out = self._ung_vien(value, ma_tinh)
        if not out:
            telex = go_telex(value)
            if telex != value:
                out = self._ung_vien(telex, ma_tinh)
        return out

    def _ung_vien(self, value, ma_tinh):
        parsed = tach_ten(value)
        if not parsed or not ma_tinh:
            return []
        kind, words, co_tien_to = parsed
        choices = list(self.index.get((ma_tinh, kind, khoa(words)), {}).values())
        if not choices and (kind == 'Đường' or not co_tien_to):
            choices = list(self.index_bare.get((ma_tinh, khoa(words)), {}).values())
        nguon = 'tu_dien_train_chua_xac_minh'
        if not choices:
            choices = self._toan_quoc_duy_nhat(kind, words, co_tien_to)
            nguon = 'tu_dien_train_toan_quoc_chua_xac_minh'
        out = []
        for item in sorted(choices, key=lambda x: x['canonical']):
            item_parsed = tach_ten(item['canonical'])
            if not item_parsed:
                continue
            canonical_kind, canonical_words, _ = item_parsed
            if nguon != 'tu_dien_train_chua_xac_minh' and co_tien_to:
                canonical_kind = kind  # nhánh toàn quốc chỉ bổ sung dấu, giữ tiền tố người dùng đã gõ
            out.append({'gia_tri': canonical_kind + ' ' + ' '.join(canonical_words),
                        'canonical_kind': canonical_kind,
                        'tuong_thich_dau': tuong_thich_dau(words, canonical_words),
                        'nguon': nguon, 'ma_tinh': ma_tinh,
                        'train_ids': list(item['train_ids']), 'tu_dien_sha256': self.ma_bam,
                        'xac_minh_doc_lap': False})
        return gop_cung_ten(out)

    def _toan_quoc_duy_nhat(self, kind, words, co_tien_to):
        """Tỉnh không có tên này trong train: chỉ nhận khi toàn từ điển có đúng MỘT dạng có dấu cho khóa."""
        key = khoa(words)
        choices = list(self.index_qg.get((kind, key), {}).values())
        if not choices and (kind == 'Đường' or not co_tien_to):
            choices = list(self.index_bare_qg.get(key, {}).values())
        choices = [c for c in choices if khoa(tach_ten(c['canonical'])[1]) == key]  # không mở rộng viết tắt ngoài tỉnh
        names = {tuple(tach_ten(c['canonical'])[1]) for c in choices}
        return choices if len(names) == 1 else []

    def chuan_hoa_gan_dung(self, value, ma_tinh, tien_to_mac_dinh=True, tien_to_duong=None):
        """Đoán tên đường gõ sai (Trần Quys Kiên, Đỗ Thị Tặbg) trong các đường của tỉnh: lệch tối đa 1 ký tự với tên
        6-9 chữ, 2 với tên từ 10 chữ (sau khi gỡ telex), và tên gần nhất phải hơn hẳn tên kế tiếp. Chỉ gọi cho đoạn
        mô hình đã gán là đường; bằng chứng ghi nguồn 'tu_dien_train_gan_dung' để cảnh báo là tên đoán."""
        if tien_to_duong is None:
            tien_to_duong = tien_to_mac_dinh
        parsed = tach_ten(go_telex(value))
        if not parsed or not ma_tinh:
            return value, None
        kind, words, co_tien_to = parsed
        k = ''.join(c for c in khoa(words) if c.isalnum())
        # Tên toàn âm tiết hợp lệ (Lê Thái Tổ, Đông Tác) nhiều khả năng là đường có thật mà từ điển chưa có:
        # không "sửa" thành tên gần giống. Chỉ đoán khi có âm tiết không thể có trong tiếng Việt (Linnh, Tặbg).
        if len(k) < 6 or all(am_tiet_hop_le(w) for w in words):
            return value, None
        if self._ten_theo_tinh is None:
            self._ten_theo_tinh = defaultdict(dict)
            for (tinh, _, _), muc in self.index.items():
                for item in muc.values():
                    p = tach_ten(item['canonical'])
                    if p:
                        self._ten_theo_tinh[tinh][khoa(p[1])] = (p[0], p[1], item)
        so = [c for c in k if c.isdigit()]
        ds = sorted((khoang_cach(k, kk), kk) for kk in self._ten_theo_tinh.get(ma_tinh, {})
                    if [c for c in kk if c.isdigit()] == so)  # Trang Liệt 1 không thành Trang Liệt 3
        if not ds:
            return value, None
        toi_da = 2 if len(k) >= 10 else 1
        d, kk = ds[0]
        if d == 0 or d > toi_da or (len(ds) > 1 and ds[1][0] <= d + 1):
            return value, None
        c_kind, c_words, item = self._ten_theo_tinh[ma_tinh][kk]
        if co_tien_to:
            c_kind = kind  # giữ loại người dùng đã ghi (Phố Bà Triêuj -> Phố Bà Triệu)
        new = (c_kind + ' ' if co_tien_to or tien_to_duong else '') + ' '.join(c_words)
        return new, {'nguon': 'tu_dien_train_gan_dung', 'ma_tinh': ma_tinh, 'khoang_cach': d,
                     'gia_tri_truoc': value, 'gia_tri_sau': new,
                     'train_ids': item['train_ids'], 'tu_dien_sha256': self.ma_bam}

    def chuan_hoa(self, value, ma_tinh, tien_to_mac_dinh=True, tien_to_duong=None):
        if tien_to_duong is None:
            tien_to_duong = tien_to_mac_dinh
        parsed = tach_ten(value)
        if not parsed or not ma_tinh:
            return value, None
        kind, words, co_tien_to = parsed
        choices = self.ung_vien(value, ma_tinh)
        # Không chọn bằng tần suất khi cùng khóa có nhiều tên, kể cả khác dấu.
        if len(choices) != 1:
            return value, None
        item = choices[0]
        if not item['tuong_thich_dau']:
            return value, None
        new = item['gia_tri']
        c_kind = item.get('canonical_kind', kind)
        if not co_tien_to and not tien_to_duong:
            if new.startswith(c_kind + ' '):
                new = new[len(c_kind) + 1:]
        if new.casefold() == value.casefold():
            return new, None  # chỉ khác hoa/thường: lấy cách viết của từ điển, không tính là sửa tên
        return new, {'nguon': item['nguon'], 'ma_tinh': ma_tinh,
                     'gia_tri_truoc': value, 'gia_tri_sau': new,
                     'train_ids': item['train_ids'], 'tu_dien_sha256': self.ma_bam}


def tao_tu_dien(train_path, output):
    train_path, output = Path(train_path), Path(output)
    entries = {}
    rejected = defaultdict(int)
    rows = 0
    for line in train_path.read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        if row.get('split') not in ('train_goc', 'train_bo_sung'):
            raise ValueError('Không chấp nhận hàng ngoài train')
        rows += 1
        ref = row['ref']
        value = ref.get('duong', '')
        parsed = tach_ten(value)
        if not row.get('canonical_usable') or not parsed or not ref.get('ma_tinh'):
            rejected['thieu_ten_tinh_hoac_nhan_khong_dung_duoc'] += 1
            continue
        _, words, _ = parsed
        aliases = cac_dang(words)
        observed = []
        for field, a, b in row['detail_spans_raw']:
            if field != 'duong':
                continue
            raw = row['text'][a:b]
            raw_parsed = tach_ten(raw)
            raw_words = raw_parsed[1] if raw_parsed else [t.chu for t in token_co_vi_tri(raw)]
            if raw_words and khoa(raw_words) in aliases and tuong_thich_dau(raw_words, words):
                observed.append(raw)
        if not observed:
            rejected['ten_khong_can_chinh_voi_span_train'] += 1
            continue
        key = ref['ma_tinh'], value.casefold()
        item = entries.setdefault(key, {'province': ref['ma_tinh'], 'canonical': value,
                                        'train_ids': [], 'observed_forms': []})
        item['train_ids'].append(row['id'])
        item['observed_forms'] = sorted(set(item['observed_forms'] + observed))
    payload = {'format': 1, 'source_scope': 'train_only', 'label_quality': 'nhan_train_chua_phai_danh_muc_duong_chung_thuc',
               'source_sha256': hashlib.sha256(train_path.read_bytes()).hexdigest(),
               'source_rows': rows, 'rejected': dict(rejected),
               'entries': sorted(entries.values(), key=lambda r: (r['province'], r['canonical']))}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload
