"""Bước 1: chuẩn hóa chuỗi đầu vào và tách token.

Giữ lại vị trí của từng token trong chuỗi gốc để truy vết.
"""

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    chu: str
    bat_dau: int
    ket_thuc: int


HAU_TO_SO_NHA = {"bis", "ter"}  # 252Bis, 14Ter: hậu tố số nhà, không phải chữ dính liền


def token_co_vi_tri(chuoi: str) -> list[Token]:
    """Khoảng ký tự luôn trỏ vào chuỗi gốc, kể cả Unicode phân rã."""
    out = []
    # Dấu nháy chỉ nối khi nằm giữa các phần tên: D'Ran, M’Đrắk.
    # Ngoặc nháy bao quanh tên vẫn là dấu câu, offset luôn ở chuỗi gốc.
    for m in re.finditer(r"[\w\u0300-\u036f]+(?:[/\u0027\u2019\u02bc][\w\u0300-\u036f]+)*|[^\w\s]", chuoi):
        raw = m.group()
        # DịchVọng -> Dịch, Vọng; không tách 18B hay chữ viết tắt HN.
        cuts = [0]
        for i in range(1, len(raw)):
            prev = i-1
            while prev >= 0 and unicodedata.combining(raw[prev]):
                prev -= 1
            if prev >= 0 and raw[prev].islower() and raw[i].isupper() and "/" not in raw:
                cuts.append(i)
            # 5mỹ -> 5, mỹ (gõ thiếu cách): số liền trước một chữ từ hai ký tự có chữ thường.
            # Không tách số nhà 18B, 843M, 252Bis hay mã viết hoa 12AB.
            if prev >= 0 and raw[prev].isdigit() and raw[i].isalpha() and "/" not in raw:
                chu = re.match(r"[^\W\d_]+", unicodedata.normalize("NFC", raw[i:])).group()
                if len(chu) >= 2 and any(c.islower() for c in chu) and chu.casefold() not in HAU_TO_SO_NHA:
                    cuts.append(i)
        # P7, Q10, ngõ5: tách tiền tố và số, giữ nguyên offset và số nhà 18B.
        glued = re.fullmatch(r"(p|q|h|x|f|phg|phường|phuong|quận|quan|xã|xa|xóm|xom|thôn|thon|ấp|ap|tổ|to|kp|tt|tx"
                             r"|ngõ|ngách|hẻm|kiệt|ngo|ngach|hem|kiet|ng)(\d+[A-Za-z]?(?:/\d+[A-Za-z]?)*)",
                             unicodedata.normalize("NFC", raw), re.I)
        if glued:
            cuts.append(re.search(r"\d", raw).start())
        cuts = sorted(set(cuts + [len(raw)]))
        for a, b in zip(cuts, cuts[1:]):
            out.append(Token(unicodedata.normalize("NFC", raw[a:b]), m.start()+a, m.start()+b))
    return out


def chuan_hoa_chuoi(chuoi: str) -> str:
    """Unicode NFC, viết thường, gom khoảng trắng, tách dấu câu."""
    return " ".join(tach_token(chuoi)).casefold()


def bo_dau(chuoi: str) -> str:
    """Bỏ dấu tiếng Việt, đổi đ thành d."""
    return "".join(c for c in unicodedata.normalize("NFD", chuoi.casefold().replace("đ", "d")) if unicodedata.category(c) != "Mn")


def go_telex(text):
    """Gỡ phím telex còn sót khi bộ gõ không bật: Huwng -> Hung, ddinhj -> dinh, loojc -> loc.

    Âm tiết tiếng Việt không chứa w, dd, aa/ee/oo (trừ -oong) và không có s/f/r/x/j đứng sau nguyên âm (dấu thanh
    telex đứng cuối hoặc trước phụ âm cuối: loojc), nên chỉ gỡ ở từ toàn chữ không dấu dài từ 3 ký tự (không đụng
    tx, tp, ql); trả về chuỗi gốc nếu không có gì để gỡ."""
    out = []
    for w in text.split():
        t = w.casefold()
        if len(t) >= 3 and t.isascii() and t.isalpha():
            t = t.replace('dd', 'd').replace('w', '').replace('aa', 'a').replace('ee', 'e')
            t = t.replace('oong', '\0').replace('oo', 'o').replace('\0', 'oong')
            t = re.sub(r'(?<=[aeiouy])[sfrxj]|[sfrxj]$', '', t)
        out.append(t if t != w.casefold() else w)
    return ' '.join(out)


def tach_token(chuoi: str) -> list[str]:
    return [t.chu for t in token_co_vi_tri(chuoi)]


def nfc_offsets(raw):
    """Mỗi ký tự NFC trỏ tới cả cụm ký tự nguồn, gồm dấu phân rã."""
    chars, offsets = [], []
    i = 0
    while i < len(raw):
        j = i + 1
        while j < len(raw) and unicodedata.combining(raw[j]):
            j += 1
        cluster = unicodedata.normalize('NFC', raw[i:j])
        chars.extend(cluster)
        offsets.extend([(i, j)] * len(cluster))
        i = j
    return ''.join(chars), offsets

