"""Định dạng giá trị từ span; không chạy model, không tra mã hành chính."""
import re
from .quy_tac import CHI_TIET, SO_CO_DAU, khop_tien_to, bo_dau
from .tach_phan_con import viet_ten

def tien_to_hien_thi(tokens, field):
    """Chỉ giải tiền tố trong span đã nhận diện; không sửa tên riêng bên trong."""
    marker = khop_tien_to(tokens, 0, CHI_TIET) if tokens else None
    if marker and marker[1][0] == field:
        return marker
    # Các cách gõ Telex của đúng từ loại, gồm cách gõ ươ bằng uow/uwow.
    # Không fuzzy mọi từ đầu tên và không đổi dấu đã có.
    if field == 'duong' and tokens:
        raw = tokens[0].casefold()
        telex = {'dduowngf': 'Đường', 'duowngf': 'Đường',
                 'dduwowngf': 'Đường', 'duwowngf': 'Đường',
                 'dduongf': 'Đường', 'duongf': 'Đường', 'phoos': 'Phố'}
        if raw in telex:
            end = 2 if len(tokens) > 1 and tokens[1] == '.' else 1
            if end < len(tokens):
                return end, (field, telex[raw])
    return None


# Viết tắt chỉ đọc được khi đã biết span thuộc trường nào: "h"/"k"/"x" ở đầu câu
# có thể là Huyện/Xã, nên không đưa vào bảng tiền tố chung CHI_TIET.
def _sinh_viet_tat_trong_span():
    """Sinh từ CHI_TIET cho từng trường chi tiết: dạng viết liền (khupho), chữ đầu của cụm nhiều từ (kp, tdp)
    và một chữ cái đầu nếu chỉ một tiền tố của trường đó bắt đầu bằng chữ ấy (x -> Xóm; t thì vừa Thôn vừa Tổ nên bỏ)."""
    bang = {}
    for khoa, truong, chuan in CHI_TIET:
        if truong == 'duong':
            continue
        b = bang.setdefault(truong, {})
        tu = khoa.split()
        b.setdefault(''.join(tu), chuan)
        if len(tu) > 1:
            b.setdefault(''.join(w[0] for w in tu), chuan)
    for truong, b in bang.items():
        dau = {}
        for khoa, chuan in b.items():
            dau.setdefault(khoa[0], set()).add(chuan)
        for chu, chuans in dau.items():
            if len(chuans) == 1:
                b.setdefault(chu, next(iter(chuans)))
    bang['so_nha']['nha'] = 'Số'  # "Nhà 12": nhà đứng một mình trước số chính là số nhà
    return bang


VIET_TAT_TRONG_SPAN = _sinh_viet_tat_trong_span()


def tach_viet_tat(tokens, field):
    """sn384 / h.184 / kp14 / SN 58 -> (nhãn, phần thân); None nếu không phải viết tắt của field."""
    bang = VIET_TAT_TRONG_SPAN.get(field)
    if not bang or not tokens:
        return None
    m = re.fullmatch(r'([^\W\d_]+)(\d\S*)?', tokens[0])
    if not m or bo_dau(m.group(1)).casefold() not in bang:
        return None
    rest = tokens[1:]
    if not m.group(2) and rest and rest[0] == '.':
        rest = rest[1:]
    body = ([m.group(2)] if m.group(2) else []) + rest
    if not body or not body[0][0].isdigit():
        return None
    return bang[bo_dau(m.group(1)).casefold()], body


def ghep_so_nha(tokens):
    if not tokens:
        return ''
    norm_tokens = ['-' if t in ('–', '—') else t for t in tokens]
    no_space_chars = {'/', '\\', '-', '_', ';', '+'}
    parts = []
    for i, t in enumerate(norm_tokens):
        if i == 0:
            parts.append(t)
            continue
        prev = norm_tokens[i - 1]
        if t in no_space_chars or prev in no_space_chars:
            parts.append(t)
        elif prev.isdigit() and len(t) == 1 and t.isalpha():
            parts.append(t)
        elif len(prev) == 1 and prev.isalpha() and t.isdigit():
            parts.append(t)
        else:
            parts.append(' ' + t)
    res = ''.join(parts).strip()
    return re.sub(r'\s+([,.;:])', r'\1', res)


def dinh_dang_span(tokens, field, tien_to_mac_dinh=True, tien_to_so_nha=None, tien_to_duong=None):
    if tien_to_so_nha is None:
        tien_to_so_nha = tien_to_mac_dinh
    if tien_to_duong is None:
        tien_to_duong = tien_to_mac_dinh
    marker = tien_to_hien_thi(tokens, field)
    viet_tat = None if marker else tach_viet_tat(tokens, field)
    if marker and marker[1][0] == field:
        end, (_, label) = marker
        body = tokens[end:]
    elif viet_tat:
        label, body = viet_tat
        marker = (0, (field, label))
    else:
        body = tokens
        if field == 'so_nha':
            label = 'Số' if tien_to_so_nha else ''
        elif field == 'duong':
            label = 'Đường' if tien_to_duong else ''
        else:
            label = ''
    if not body:
        return '', False
    if field == 'duong' and label in ('Đường', ''):
        inner = khop_tien_to(body, 0, CHI_TIET)
        # d. QL 5A là loại tuyến cụ thể. Không xóa chữ Phố/Đường trong tên riêng.
        if inner and inner[1][0] == 'duong' and inner[1][1] in ('Quốc lộ', 'Tỉnh lộ', 'ĐT', 'HL', 'ĐH'):
            end = inner[0]
            if end < len(body) and re.fullmatch(r'\d+[A-Za-z]{0,2}', body[end]):
                label, body = inner[1][1], body[end:]
        elif len(body) == 1:
            # QL3, TL298 viết dính: cùng nghĩa với 'QL 3', 'TL 298' ở nhánh trên.
            dinh_lien = re.fullmatch(r'(QL|TL)(\d+[A-Za-z]{0,2})', body[0], re.I)
            if dinh_lien:
                label = 'Quốc lộ' if dinh_lien.group(1).upper() == 'QL' else 'Tỉnh lộ'
                body = [dinh_lien.group(2)]
    if field == 'so_nha':
        # Không loại token 5–6 chữ số: đây có thể chính là số nhà hợp lệ.
        # Phân biệt mã bưu chính phải dựa vào ngữ cảnh, không dựa độ dài.
        clean_tokens = list(body)
        while clean_tokens and clean_tokens[0] in {',', ';', '.'}:
            clean_tokens.pop(0)
        while clean_tokens and clean_tokens[-1] in {',', ';', '.'}:
            clean_tokens.pop()
        value = ghep_so_nha(clean_tokens)
        # Cờ này chỉ điều khiển việc *tự thêm* tiền tố khi input không có.
        # Nếu input đã ghi rõ "Số", phải bảo toàn kiểu hiển thị đó.
        if not tien_to_so_nha and not marker:
            return value, False
    else:
        if field == 'thon_xom' and label and len(body) == 1 and body[0].casefold() in SO_CO_DAU:
            # Xóm năm -> Xóm 5. Chỉ khi viết đủ dấu: "Xóm Nam" (không dấu) có thể là tên riêng (xóm phía nam).
            body = [SO_CO_DAU[body[0].casefold()]]
        value = viet_ten(body)
        if field == 'duong' and label in ('Quốc lộ', 'Tỉnh lộ', 'ĐT', 'HL', 'ĐH'):
            value = ' '.join(t.upper() if re.fullmatch(r'\d+[A-Za-z]{1,2}', t) else t for t in value.split())
    return ' '.join(x for x in (label, value) if x), field == 'duong' and not marker
