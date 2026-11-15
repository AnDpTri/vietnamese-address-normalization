"""CRF bốn vai trò chi tiết + O; không gọi API, không tự phục hồi tên riêng."""

import hashlib
import math
import re
from pathlib import Path

from .tien_xu_ly import bo_dau
from .quy_tac import (
    CHI_TIET,
    CHU_CAI_LOAI_TRU_SO_NHA,
    DAU_NGAT_CHI_TIET,
    DAU_NGAT_SO_NHA,
    DAU_NGAT_TOA_NHA,
    DO_DAI_MA_BUU_CHINH,
    GIA_TRI_THON_XOM_LOAI_BO,
    HAU_TO_DUONG_TIENG_ANH,
    TIEN_TO_PHO_HANH_CHINH,
    TIEN_TO_THANH_PHO,
    TIEN_TO_THON_XOM,
    TU_KHOA_CMT8,
    TU_KHOA_TOA_NHA_BAT_DAU,
    TU_KHOA_TOA_NHA_DAU,
    TU_KHOA_TOA_NHA_LIEN_TRUOC_1,
    TU_KHOA_TOA_NHA_LIEN_TRUOC_2,
    TU_KHOA_TOA_NHA_LIEN_TRUOC_3,
    cac_tien_to,
    khop_tien_to,
)
from .tach_phan_con import FIELDS, viet_ten
from .dinh_dang import tien_to_hien_thi, dinh_dang_span


def dac_trung(tokens):
    """Đặc trưng quan sát toàn chuỗi, không dùng nhãn/mã/mốc tham chiếu."""
    markers = cac_tien_to(tokens)
    mark = {}
    for i, (end, kind, attrs) in markers.items():
        for j in range(i, end):
            mark[j] = kind + ':' + (attrs[0] if kind == 'chi_tiet' else 'admin')
    shapes = []
    for t in tokens:
        shape = ''.join('d' if c.isdigit() else 'X' if c.isupper() else 'x' if c.isalpha() else c for c in t)
        shapes.append(re.sub(r'(.)\1+', r'\1', shape))
    seq = []
    for i, t in enumerate(tokens):
        low, plain = t.casefold(), bo_dau(t)
        f = {'bias': 1., 'w': low, 'plain': plain, 'shape': shapes[i],
             'upper': t.isupper(), 'title': t.istitle(), 'digit': t.isdigit(),
             'has_digit': any(c.isdigit() for c in t), 'alpha': t.isalpha(),
             'punct': not any(c.isalnum() for c in t), 'accent': low != plain,
             'slash': '/' in t, 'mark': mark.get(i, ''), 'bos': i == 0, 'eos': i == len(tokens)-1}
        for size in (2, 3, 4):
            f['pre'+str(size)] = plain[:size]
            f['suf'+str(size)] = plain[-size:]
        for delta in (-2, -1, 1, 2):
            j = i+delta
            if 0 <= j < len(tokens):
                p = str(delta)+':'
                f[p+'w'] = tokens[j].casefold()
                f[p+'plain'] = bo_dau(tokens[j])
                f[p+'shape'] = shapes[j]
                f[p+'mark'] = mark.get(j, '')
                f[p+'digit'] = tokens[j].isdigit()
        seq.append(f)
    return seq


def bio_spans(labels):
    """I mồ côi mở span mới, đồng thời đếm lỗi BIO gốc để không che lỗi đo."""
    spans, invalid = [], 0
    field, start = None, 0
    for i, tag in enumerate([*labels, 'O']):
        role = tag[2:] if tag[:2] in {'B-', 'I-'} and tag[2:] in FIELDS else None
        continuation = role is not None and tag.startswith('I-') and role == field
        if tag.startswith('I-') and not continuation:
            invalid += 1
        if field is not None and not continuation:
            spans.append((field, start, i))
        if not continuation:
            field, start = role, i
    return spans, invalid


def tao_nhan(n, spans):
    tags = ['O'] * n
    for field, a, b in spans:
        if field not in FIELDS or not 0 <= a < b <= n:
            raise ValueError('Span sai phạm vi/nhãn')
        for i in range(a, b):
            if tags[i] != 'O':
                raise ValueError('Span chồng lấn')
            tags[i] = ('B-' if i == a else 'I-')+field
    return tags


def la_toa_nha_chung_cu(tokens, a, b):
    first = bo_dau(tokens[a].rstrip('.').casefold())
    if first in TU_KHOA_TOA_NHA_DAU:
        return True
    span_bd = bo_dau(' '.join(tokens[a:b]).casefold())
    for kw in TU_KHOA_TOA_NHA_BAT_DAU:
        if span_bd.startswith(kw):
            return True
    p = a - 1
    while p >= 0 and tokens[p] in DAU_NGAT_TOA_NHA:
        p -= 1
    if p >= 0:
        prev_1 = bo_dau(tokens[p].rstrip('.').casefold())
        if prev_1 in TU_KHOA_TOA_NHA_LIEN_TRUOC_1:
            return True
        if p >= 1:
            prev_2 = bo_dau(' '.join(tokens[p-1:p+1]).casefold())
            if prev_2 in TU_KHOA_TOA_NHA_LIEN_TRUOC_2:
                return True
        if p >= 2:
            prev_3 = bo_dau(' '.join(tokens[p-2:p+1]).casefold())
            if prev_3 in TU_KHOA_TOA_NHA_LIEN_TRUOC_3:
                return True
    return False


def la_duong_thanh_pho(tokens, a):
    if a > 0:
        prev_tok = bo_dau(tokens[a-1].casefold())
        curr_tok = bo_dau(tokens[a].casefold())
        return prev_tok in TIEN_TO_THANH_PHO and curr_tok == 'pho'
    return False


def chinh_bien_so_nha(tokens, a, b):
    if b - a > 1 and bo_dau(tokens[b-1].rstrip('.').casefold()) in TU_KHOA_CMT8:
        b -= 1
    if b - a > 1 and b < len(tokens) and bo_dau(tokens[b].rstrip('.').casefold()) in HAU_TO_DUONG_TIENG_ANH:
        b -= 1
    if (b < len(tokens) 
        and len(tokens[b]) == 1 
        and tokens[b].isalpha() 
        and tokens[b].lower() not in CHU_CAI_LOAI_TRU_SO_NHA
        and tokens[b-1][-1].isdigit()
        and (b + 1 == len(tokens) or (b + 1 < len(tokens) and tokens[b+1] in DAU_NGAT_SO_NHA))):
        b += 1
    return b


def loc_va_chinh_bien_span(tokens, f, a, b):
    """Lọc span không hợp lệ và căn chỉnh biên cho trường số nhà."""
    if f == 'duong':
        if la_duong_thanh_pho(tokens, a) or la_toa_nha_chung_cu(tokens, a, b):
            return False, b
    elif f == 'so_nha':
        b = chinh_bien_so_nha(tokens, a, b)
    return True, b


def loc_so_nha_ma_buu_chinh(tokens, f, value, end_idx):
    if f == 'so_nha':
        num_val = value.casefold().replace('số', '').strip()
        if num_val.isdigit() and len(num_val) in DO_DAI_MA_BUU_CHINH and (
            end_idx >= len(tokens) - 2 or all(not any(c.isalnum() for c in tokens[k]) for k in range(end_idx, len(tokens)))
        ):
            return ''
    return value


class NguCanhCRF:
    def __init__(self, tokens, labels, p_o):
        self.tokens, self.labels, self.p_o = tokens, labels, p_o
        self.loi_bio = bio_spans(labels)[1]

    def diem_hanh_chinh(self, occupied):
        return sum(math.log(max(self.p_o[i], 1e-8)) for i in occupied)

    def _bat_dau_ranh_gioi(self, j, prefixes):
        """Token j mở một cấp hành chính có tên theo sau (xã Tam Hiệp, p. Yersin): hết phần chi tiết không dấu phẩy.
        Hai chữ cấp liền nhau (xã phường...) chỉ tính chữ sau cùng, như ranh giới trong tach_co_dau_vet."""
        marker = prefixes.get(j)
        if not marker or marker[1] != 'hanh_chinh':
            return False
        end = marker[0]
        return end < len(self.tokens) and self.tokens[end][0].isalnum() and end not in prefixes

    def tach(self, occupied, tien_to_mac_dinh=True, tien_to_so_nha=None, tien_to_duong=None):
        if tien_to_so_nha is None:
            tien_to_so_nha = tien_to_mac_dinh
        if tien_to_duong is None:
            tien_to_duong = tien_to_mac_dinh
        tags = ['O' if i in occupied else tag for i, tag in enumerate(self.labels)]
        spans, _ = bio_spans(tags)
        prefixes = cac_tien_to(self.tokens)
        values = {f: [] for f in FIELDS}
        output_spans, used = [], set(occupied)
        inferred = False
        for f, a, b in spans:
            # Dấu câu ngoài đoạn không thành tên; phần giữa đoạn vẫn giữ.
            while a < b and not any(c.isalnum() for c in self.tokens[a]):
                a += 1
            while b > a and not any(c.isalnum() for c in self.tokens[b-1]):
                b -= 1
            if a >= b or any(k in used for k in range(a, b)):
                continue
            # Lọc đường thành phố, chung cư và căn chỉnh biên số nhà (lần 1)
            hop_le, b = loc_va_chinh_bien_span(self.tokens, f, a, b)
            if not hop_le:
                continue
            marker = khop_tien_to(self.tokens, a, CHI_TIET)
            if marker:
                proper_field = marker[1][0]
                if proper_field in FIELDS:
                    f = proper_field
                    if proper_field == 'thon_xom' and marker[1][1] in TIEN_TO_THON_XOM:
                        end_idx = marker[0]
                        # Dừng ở token đã là đơn vị hành chính: không dấu phẩy thì "xóm 5 xã mỹ hưng ..." không nuốt xã.
                        # Cũng dừng ở chữ cấp hành chính có tên theo sau (xã, p., huyện...) dù giả thuyết đã chọn không dùng
                        # nó: "bản Pom Coọng xã Chiềng Ve" không nuốt xã, "xóm 11 p. Yersin x. Thành Lộc" không nuốt "p. Yersin".
                        while (end_idx < len(self.tokens) and end_idx not in used
                               and self.tokens[end_idx] not in DAU_NGAT_CHI_TIET):
                            if khop_tien_to(self.tokens, end_idx, CHI_TIET):
                                break
                            if end_idx >= b and self._bat_dau_ranh_gioi(end_idx, prefixes):
                                break
                            end_idx += 1
                        if end_idx > b:
                            b = end_idx
            # Áp dụng lại khối luật sau khi tiền tố có thể đổi f hoặc b (lần 2)
            hop_le, b = loc_va_chinh_bien_span(self.tokens, f, a, b)
            if not hop_le:
                continue
            value, guessed = dinh_dang_span(self.tokens[a:b], f, tien_to_mac_dinh=tien_to_mac_dinh,
                                           tien_to_so_nha=tien_to_so_nha, tien_to_duong=tien_to_duong)
            if f == 'thon_xom' and value.casefold() in GIA_TRI_THON_XOM_LOAI_BO:
                value = ''
            value = loc_so_nha_ma_buu_chinh(self.tokens, f, value, b)
            if value and a < b:
                values[f].append(value)
                output_spans.append({'truong': f, 'bat_dau': a, 'ket_thuc': b, 'gia_tri': value})
                used.update(range(a, b))
                inferred |= guessed
        # Rà soát phần chưa phân loại (unknown) có tiền tố chi tiết rõ ràng
        unknown_candidates = [i for i, t in enumerate(self.tokens) if i not in used and any(c.isalnum() for c in t)]
        for i in unknown_candidates:
            if i in used:
                continue
            if la_duong_thanh_pho(self.tokens, i):
                continue
            if i > 0 and bo_dau(self.tokens[i-1].casefold()) in TIEN_TO_PHO_HANH_CHINH and bo_dau(self.tokens[i].casefold()) == 'pho':
                continue
            marker = khop_tien_to(self.tokens, i, CHI_TIET)
            if marker:
                end, (f, label) = marker
                if f == 'duong' and la_duong_thanh_pho(self.tokens, i):
                    continue
                j = end
                while j < len(self.tokens) and j not in used and self.tokens[j] not in DAU_NGAT_CHI_TIET:
                    if j > end and self._bat_dau_ranh_gioi(j, prefixes):
                        break
                    j += 1
                if j > i:
                    val, g = dinh_dang_span(self.tokens[i:j], f, tien_to_mac_dinh=tien_to_mac_dinh,
                                            tien_to_so_nha=tien_to_so_nha, tien_to_duong=tien_to_duong)
                    val = loc_so_nha_ma_buu_chinh(self.tokens, f, val, j)
                    if val:
                        values[f].append(val)
                        output_spans.append({'truong': f, 'bat_dau': i, 'ket_thuc': j, 'gia_tri': val})
                        used.update(range(i, j))
                        inferred |= g
        unknown = [i for i, t in enumerate(self.tokens) if i not in used and any(c.isalnum() for c in t)]
        detail = {f: ', '.join(dict.fromkeys(values[f])) for f in FIELDS}
        detail['phan_chua_phan_loai'] = ' '.join(self.tokens[i] for i in unknown)
        return detail, output_spans, unknown, inferred


class BoTachCRF:
    def __init__(self, model_path, bao_ve_chi_tiet=False):
        try:
            import pycrfsuite
        except ImportError as e:
            raise ImportError('Cần cài requirements-crf.txt bằng Python của .venv-crf') from e
        p = Path(model_path)
        self.ma_bam = hashlib.sha256(p.read_bytes()).hexdigest()
        self.tagger = pycrfsuite.Tagger()
        self.tagger.open(str(p))
        self.bao_ve_chi_tiet = bao_ve_chi_tiet

    def chuan_bi(self, tokens):
        if not tokens:
            return NguCanhCRF([], [], [])
        labels = self.tagger.tag(dac_trung(tokens))
        p_o = [self.tagger.marginal('O', i) for i in range(len(tokens))]
        return NguCanhCRF(tokens, labels, p_o)
