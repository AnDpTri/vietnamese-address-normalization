"""Khôi phục tên đường bằng từ điển và span chi tiết."""

from .quy_tac import CHI_TIET, khop_tien_to
from .tien_xu_ly import bo_dau


def thu_ung_vien_duong(tu_dien_duong, cand: str, ma_tinh: str, tien_to_mac_dinh: bool = True, tien_to_duong: bool | None = None):
    cand_matches = tu_dien_duong.ung_vien(cand, ma_tinh)
    if len(cand_matches) == 1 and cand_matches[0]['tuong_thich_dau']:
        cand_new, cand_ev = tu_dien_duong.chuan_hoa(
            cand, ma_tinh,
            tien_to_mac_dinh=tien_to_mac_dinh,
            tien_to_duong=tien_to_duong
        )
        return cand_new, (cand_ev or cand_matches[0])
    return None, None


def loc_tien_to_phong_tang(detail):
    if detail.get('duong') and detail['duong'].casefold().replace('đường ', '').replace('phố ', '').startswith(('phòng ', 'tầng ', 'căn hộ ', 'tòa nhà ', 'kios ', 'gian hàng ')):
        detail = dict(detail)
        detail['duong'] = ''
    return detail


def mo_rong_duong_tu_unknown(curr_duong, current_new_duong, duong_spans, tokens, unknown, ma_tinh,
                             tu_dien_duong, tien_to_mac_dinh=True, tien_to_duong=None, cam=frozenset()):
    """Nới span đường sang token chưa phân loại liền kề; không lấy token trong `cam` (đơn vị hành chính khả thi).
    Trả thêm khoảng token mới của đường (None nếu không nới)."""
    new_duong = current_new_duong
    name_evidence = None
    pham_vi = None
    end_idx = duong_spans[-1]['ket_thuc']
    cand = curr_duong
    while end_idx < len(tokens) and end_idx in unknown and end_idx not in cam and tokens[end_idx] not in {',', ';', '.', '-'}:
        cand = cand + ' ' + tokens[end_idx]
        cand_new, cand_ev = thu_ung_vien_duong(
            tu_dien_duong, cand, ma_tinh,
            tien_to_mac_dinh=tien_to_mac_dinh,
            tien_to_duong=tien_to_duong
        )
        if cand_new is not None:
            new_duong = cand_new
            name_evidence = cand_ev
            unknown = [u for u in unknown if u not in range(duong_spans[-1]['ket_thuc'], end_idx + 1)]
            pham_vi = (duong_spans[0]['bat_dau'], end_idx + 1)
            break
        end_idx += 1
    if not name_evidence:
        start_idx = duong_spans[0]['bat_dau']
        cand = curr_duong
        while (start_idx - 1 >= 0 and (start_idx - 1) in unknown and (start_idx - 1) not in cam
               and tokens[start_idx - 1] not in {',', ';', '.', '-'}):
            cand = tokens[start_idx - 1] + ' ' + cand
            cand_new, cand_ev = thu_ung_vien_duong(
                tu_dien_duong, cand, ma_tinh,
                tien_to_mac_dinh=tien_to_mac_dinh,
                tien_to_duong=tien_to_duong
            )
            if cand_new is not None:
                new_duong = cand_new
                name_evidence = cand_ev
                unknown = [u for u in unknown if u not in range(start_idx - 1, duong_spans[0]['bat_dau'])]
                pham_vi = (start_idx - 1, duong_spans[-1]['ket_thuc'])
                break
            start_idx -= 1
    return new_duong, name_evidence, unknown, pham_vi


def khoi_phuc_tu_so_nha(duong_spans, spans, tokens, detail, ma_tinh, tu_dien_duong,
                        tien_to_mac_dinh=True, tien_to_duong=None, tien_to_so_nha=None):
    so_nha_spans = [s for s in spans if s.get('truong') == 'so_nha']
    if not (duong_spans and so_nha_spans):
        return None, None
    d_start = duong_spans[0]['bat_dau']
    d_end = duong_spans[-1]['ket_thuc']
    sns = so_nha_spans[-1]
    if sns['ket_thuc'] == d_start and tokens[d_start - 1].isdigit():
        cand = ' '.join(tokens[d_start - 1 : d_end])
        cand_new, cand_ev = thu_ung_vien_duong(
            tu_dien_duong, cand, ma_tinh,
            tien_to_mac_dinh=tien_to_mac_dinh,
            tien_to_duong=tien_to_duong
        )
        if cand_new is not None:
            sns['ket_thuc'] -= 1
            if sns['ket_thuc'] <= sns['bat_dau']:
                detail['so_nha'] = ''
            else:
                from .crf_chi_tiet import dinh_dang_span
                detail['so_nha'], _ = dinh_dang_span(
                    tokens[sns['bat_dau']:sns['ket_thuc']], 'so_nha',
                    tien_to_mac_dinh=tien_to_mac_dinh,
                    tien_to_so_nha=tien_to_so_nha
                )
            return cand_new, cand_ev
    return None, None


def dung_lai_tu_span_cnn(duong_spans, tokens, ma_tinh, tu_dien_duong, tien_to_mac_dinh=True, tien_to_duong=None):
    if not (ma_tinh and duong_spans):
        return None, None
    cand = ' '.join(tokens[duong_spans[0]['bat_dau']:duong_spans[-1]['ket_thuc']])
    return thu_ung_vien_duong(tu_dien_duong, cand, ma_tinh, tien_to_mac_dinh=tien_to_mac_dinh, tien_to_duong=tien_to_duong)


def khoi_phuc_tu_spans(curr_duong, new_duong, duong_spans, spans, tokens, unknown, detail, ma_tinh,
                       tu_dien_duong, tien_to_mac_dinh=True, tien_to_duong=None, tien_to_so_nha=None, cam=frozenset()):
    new_duong, name_evidence, unknown, pham_vi = mo_rong_duong_tu_unknown(
        curr_duong, new_duong, duong_spans, tokens, unknown, ma_tinh, tu_dien_duong,
        tien_to_mac_dinh, tien_to_duong, cam
    )
    verified = bool(name_evidence)
    if not verified and curr_duong and ma_tinh:
        ung = tu_dien_duong.ung_vien(curr_duong, ma_tinh)
        if len(ung) == 1 and ung[0]['tuong_thich_dau']:
            verified = True
    if not verified and ma_tinh:
        cand_new, cand_ev = khoi_phuc_tu_so_nha(
            duong_spans, spans, tokens, detail, ma_tinh, tu_dien_duong,
            tien_to_mac_dinh, tien_to_duong, tien_to_so_nha
        )
        if cand_new is not None:
            new_duong = cand_new
            name_evidence = cand_ev
            verified = True
    if not verified and ma_tinh:
        cand_new, cand_ev = dung_lai_tu_span_cnn(
            duong_spans, tokens, ma_tinh, tu_dien_duong,
            tien_to_mac_dinh, tien_to_duong
        )
        if cand_new is not None:
            new_duong = cand_new
            name_evidence = cand_ev
            verified = True
    return new_duong, name_evidence, unknown, pham_vi


def quet_token_chua_phan_loai(tokens, unknown, ma_tinh, tu_dien_duong, tien_to_mac_dinh=True, tien_to_duong=None,
                              cam=frozenset()):
    """Tìm tên đường trong các nhóm token chưa phân loại; token trong `cam` không được dùng.
    Trả thêm khoảng token của tên đường tìm được."""
    u_sorted = sorted(u for u in unknown if u not in cam)
    if not (ma_tinh and u_sorted):
        return None, None, unknown, None
    groups = []
    curr_g = [u_sorted[0]]
    for idx in u_sorted[1:]:
        if idx == curr_g[-1] + 1 and tokens[idx] not in {',', ';', '.', '-'}:  # token cấm đã bị loại nên tự cắt nhóm
            curr_g.append(idx)
        else:
            groups.append(curr_g)
            curr_g = [idx]
    groups.append(curr_g)

    # Giữ nguyên ngữ nghĩa bản gốc: KHÔNG dừng sau nhóm đầu tiên. Nhóm sau khớp thì ghi đè
    # kết quả và loại thêm token khỏi unknown; sau mỗi nhóm, vòng start dừng khi đã có tên.
    new_duong, name_evidence, pham_vi = None, None, None
    for g in groups:
        for start in range(len(g)):
            for end in range(start + 1, min(start + 7, len(g) + 1)):
                sub_phrase = ' '.join(tokens[g[k]] for k in range(start, end))
                cand_new, cand_ev = thu_ung_vien_duong(
                    tu_dien_duong, sub_phrase, ma_tinh,
                    tien_to_mac_dinh=tien_to_mac_dinh,
                    tien_to_duong=tien_to_duong
                )
                if cand_new is not None:
                    new_duong = cand_new
                    name_evidence = cand_ev
                    unknown = [u for u in unknown if u not in g[start:end]]
                    pham_vi = (g[start], g[end - 1] + 1)
                    break
            if new_duong:
                break
    return new_duong, name_evidence, unknown, pham_vi


TIEN_TO_DUONG_RUT_GON = {'d', 'duong', 'pho', 'p'}


def bo_duong_viet_tat_chua_giai(detail, spans, tokens, chuoi):
    """Tên đường chỉ là một chữ viết tắt VIẾT HOA (2-4 chữ cái) mà từ điển không giải được: để trống thay vì bịa tên.

    Chỉ áp dụng khi chuỗi nhập có chữ thường (nếu cả chuỗi viết hoa thì chữ hoa không còn là dấu hiệu viết tắt).
    """
    if not detail.get('duong') or not any(c.islower() for c in chuoi):
        return detail, spans, False
    for s in spans:
        if s.get('truong') != 'duong':
            continue
        words = [t for t in tokens[s['bat_dau']:s['ket_thuc']] if any(c.isalnum() for c in t)]
        body = [w for w in words if bo_dau(w.casefold().rstrip('.')) not in TIEN_TO_DUONG_RUT_GON]
        if len(body) == 1 and body[0].isalpha() and body[0].isupper() and 2 <= len(body[0]) <= 4:
            detail = dict(detail)
            detail['duong'] = ''
            return detail, [x for x in spans if x is not s], True
    return detail, spans, False


def thon_khong_tien_to_la_duong(detail, spans, tokens, ma_tinh, tu_dien_duong, tien_to_mac_dinh, tien_to_duong):
    """Đoạn gán thôn/xóm mà câu không ghi chữ loại (thôn, xóm, tổ...) và từ điển khớp đúng một tên đường
    của tỉnh: là tên đường (ví dụ '110A CMT8, ...'). Có chữ loại thì giữ là thôn."""
    thon = [s for s in spans if s.get('truong') == 'thon_xom']
    if len(thon) != 1:
        return detail, spans, '', None
    s = thon[0]
    phan = tokens[s['bat_dau']:s['ket_thuc']]
    if khop_tien_to(phan, 0, CHI_TIET):
        return detail, spans, '', None
    new, ev = thu_ung_vien_duong(tu_dien_duong, ' '.join(phan), ma_tinh,
                                 tien_to_mac_dinh=tien_to_mac_dinh, tien_to_duong=tien_to_duong)
    if new is None:
        return detail, spans, '', None
    detail = dict(detail, thon_xom='')
    spans = [x for x in spans if x is not s] + [{**s, 'truong': 'duong', 'gia_tri': new}]
    return detail, spans, new, ev


def phuc_hoi_ten_duong(detail, spans, unknown, tokens, ma_tinh, tu_dien_duong,
                       tien_to_mac_dinh=True, tien_to_duong=None, tien_to_so_nha=None, cam=frozenset()):
    """Khôi phục tên đường bằng từ điển. `cam`: token là đơn vị hành chính khả thi, không bao giờ thành tên đường.
    Token lấy thêm được ghi vào span 'duong' (dấu vết khớp kết quả) và phần chưa phân loại được tính lại."""
    name_evidence = None
    unknown_goc = list(unknown)
    detail = loc_tien_to_phong_tang(detail)
    if tu_dien_duong is None:
        return detail, spans, unknown, name_evidence

    detail = dict(detail)
    curr_duong = detail['duong']
    new_duong, name_evidence = tu_dien_duong.chuan_hoa(
        curr_duong, ma_tinh,
        tien_to_mac_dinh=tien_to_mac_dinh,
        tien_to_duong=tien_to_duong
    )
    if not name_evidence and curr_duong and ma_tinh:
        duong_spans = [s for s in spans if s.get('truong') == 'duong']
        if duong_spans:
            new_duong, name_evidence, unknown, pham_vi = khoi_phuc_tu_spans(
                curr_duong, new_duong, duong_spans, spans, tokens, unknown, detail,
                ma_tinh, tu_dien_duong, tien_to_mac_dinh, tien_to_duong, tien_to_so_nha, cam
            )
            if pham_vi:
                spans = [x for x in spans if x.get('truong') != 'duong']
                spans.append({'truong': 'duong', 'bat_dau': pham_vi[0], 'ket_thuc': pham_vi[1], 'gia_tri': new_duong})
        if not name_evidence and duong_spans:
            # Cuối cùng mới đoán gần đúng, và chỉ trên đoạn mô hình đã gán là đường.
            doan, ev = tu_dien_duong.chuan_hoa_gan_dung(
                curr_duong, ma_tinh, tien_to_mac_dinh=tien_to_mac_dinh, tien_to_duong=tien_to_duong)
            if ev:
                new_duong, name_evidence = doan, ev

    if not new_duong and ma_tinh and detail.get('thon_xom'):
        detail, spans, new_duong, name_evidence = thon_khong_tien_to_la_duong(
            detail, spans, tokens, ma_tinh, tu_dien_duong, tien_to_mac_dinh, tien_to_duong)

    if not new_duong and ma_tinh and unknown:
        cand_new, cand_ev, unknown, pham_vi = quet_token_chua_phan_loai(
            tokens, unknown, ma_tinh, tu_dien_duong,
            tien_to_mac_dinh=tien_to_mac_dinh,
            tien_to_duong=tien_to_duong,
            cam=cam
        )
        if cand_new is not None:
            new_duong = cand_new
            name_evidence = cand_ev
            spans = spans + [{'truong': 'duong', 'bat_dau': pham_vi[0], 'ket_thuc': pham_vi[1], 'gia_tri': cand_new}]

    detail['duong'] = new_duong
    if unknown != unknown_goc:
        detail['phan_chua_phan_loai'] = ' '.join(tokens[i] for i in unknown)
    return detail, spans, unknown, name_evidence
