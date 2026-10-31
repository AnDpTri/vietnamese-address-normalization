"""Module Tiền xử lý: biến chuỗi bẩn thành DiaChiSach có cấu trúc.

Bao gồm tách token, nhận diện (CRF, CNN, Trie), sinh và xếp hạng giả thuyết,
định dạng chi tiết và khôi phục tên đường. KHÔNG chuyển đổi mã hành chính mới.
"""

from dataclasses import replace

from ..danh_muc import DanhMuc
from ..kieu_du_lieu import DiaChiSach, DonViNhan, NoiBoTienXuLy
from .tim_kiem import dung_trie, sinh_ung_vien, bo_sung_tu_luoi_goc
from .tien_xu_ly import token_co_vi_tri, bo_dau, go_telex
from .giai_ma import tim_duong_di
from .tach_phan_con import tach_co_dau_vet, FIELDS
from .quy_tac import cac_tien_to, CHI_TIET, khop_tien_to
from .phuc_hoi_duong import phuc_hoi_ten_duong, bo_duong_viet_tat_chua_giai


def _tao_dau_vet(records, chuoi, a, b, **extra):
    return {"token_bat_dau": a, "token_ket_thuc": b, "ky_tu_bat_dau": records[a].bat_dau,
            "ky_tu_ket_thuc": records[b-1].ket_thuc,
            "doan_goc": chuoi[records[a].bat_dau:records[b-1].ket_thuc], **extra}


def _don_vi_nhan(duong_di):
    """Rút giả thuyết beam về danh sách đơn vị sạch (cấp, mã, mốc), giữ thứ tự."""
    return [DonViNhan(cap=u.cap, ma=u.ma, cay=u.cay) for u in duong_di.ung_vien]


def _token_crf_hanh_chinh(crf_context, records=None):
    """Chỉ số token nằm trong đoạn CRF gán xã/huyện/tỉnh. `records` mặc định lấy từ crf_context."""
    char_spans = getattr(crf_context, 'char_spans', None) or ()
    if records is None:
        records = getattr(crf_context, 'records', None) or ()
    return {i for i, t in enumerate(records)
            for r, a, b in char_spans if r in ('xa', 'huyen', 'tinh') and a <= t.bat_dau and t.ket_thuc <= b}


def token_hanh_chinh_kha_thi(records, candidates, crf_context, ma_tinh, dm):
    """Token mà CRF gán là đơn vị hành chính VÀ có ứng viên hành chính khả thi phủ nó
    (cùng tỉnh mới đã chọn; chưa chọn tỉnh thì cần khớp chính xác). Các token này không được dùng làm tên đường.
    Ví dụ 'Hà Nội' gán tỉnh, khớp đúng tỉnh 01 -> cấm; 'Hoàng Văn Thụ' gán xã nhưng không có xã đó trong tỉnh -> không cấm."""
    char_spans = getattr(crf_context, 'char_spans', None)
    if not char_spans:
        return frozenset()
    crf_hc = _token_crf_hanh_chinh(crf_context, records)
    cam = set()
    for u in candidates:
        # Khớp gần đúng (sai chính tả) là bằng chứng yếu: 'Trần' ~ 'Trà An' không đủ để cấm đoạn làm tên đường.
        if u.kieu_khop == 'sai_chinh_ta' or not crf_hc.intersection(range(u.bat_dau, u.ket_thuc)):
            continue
        kha_thi = ma_tinh in dm.dich_tinh(u.cay, u.ma) if ma_tinh else u.kieu_khop == 'chinh_xac'
        if kha_thi:
            cam.update(i for i in range(u.bat_dau, u.ket_thuc) if i in crf_hc)
    return frozenset(cam)


def dau_vet_hanh_chinh_khong_khop(records, chuoi, crf_context, candidates, unknown):
    """Đoạn CRF gán là xã/huyện/tỉnh mà vẫn nằm trong phần chưa phân loại: ghi dấu vết với ma rỗng và lý do,
    để đầu ra không coi nó là chữ thừa. 'khong_co_trong_danh_muc' khi không có ứng viên nào trên đoạn,
    'khong_khop_dia_ban' khi có đơn vị cùng tên nhưng không hợp với các đơn vị còn lại."""
    out = []
    con_lai = set(unknown)
    for r, a, b in getattr(crf_context, 'char_spans', None) or ():
        if r not in ('xa', 'huyen', 'tinh'):
            continue
        idx = [i for i, t in enumerate(records) if a <= t.bat_dau and t.ket_thuc <= b and i in con_lai]
        if not idx:
            continue
        lo, hi = idx[0], idx[-1] + 1
        co_ung_vien = any(u.bat_dau < hi and lo < u.ket_thuc for u in candidates)
        out.append(_tao_dau_vet(records, chuoi, lo, hi, truong=r, ma='', moc='',
                                kieu_khop='khong_khop_dia_ban' if co_ung_vien else 'khong_co_trong_danh_muc'))
    return out


def don_vi_ghi_khong_khop(best, candidates, crf_context, dm, chi_tiet=frozenset()):
    """Đoạn CRF gán hành chính mà giả thuyết đã chọn bỏ qua, có ứng viên khớp đúng tên, nhưng KHÔNG ứng viên nào
    hợp (cha-con, cùng địa bàn) với các đơn vị đã chọn: người dùng ghi một đơn vị không khớp, ví dụ xã không thuộc
    huyện đã ghi. Kết quả vẫn giữ theo các đơn vị còn lại, kèm cảnh báo. Trả danh sách khoảng token bị mâu thuẫn.
    Chỉ xét đoạn có tiền tố hành chính (người dùng chủ ý ghi là đơn vị) và không nằm trong chi tiết đã tách
    (đường/thôn): mảnh vụn CRF ('Thành', 'Thừa') hay tên đường bị CRF tưởng là xã ('Lê Lai') không phải lỗi người nhập."""
    crf_hc = _token_crf_hanh_chinh(crf_context)
    dung = {i for u in best.ung_vien for i in range(u.bat_dau, u.ket_thuc)}
    chon = [dm.lay(u.cay, u.ma) for u in best.ung_vien]
    if not chon:
        return []
    theo_doan = {}
    for u in candidates:
        doan = set(range(u.bat_dau, u.ket_thuc))
        if u.kieu_khop == 'sai_chinh_ta' or not u.co_tien_to or doan & dung or doan & chi_tiet or not doan <= crf_hc:
            continue
        hop = all(dm.tuong_thich(dm.lay(u.cay, u.ma), c) for c in chon)
        theo_doan.setdefault((u.bat_dau, u.ket_thuc), []).append(hop)
    return [k for k, ds in sorted(theo_doan.items()) if not any(ds)]


def gia_thuyet_tuong_duong(best, ranked, crf_context):
    """Các giả thuyết có bằng chứng NGANG giả thuyết đã chọn: cùng tập chữ ký đơn vị (cấp, kiểu khớp, có tiền tố,
    tên cũ, CRF có gán hành chính hay không), chỉ khác mã hoặc khác đoạn. Ranker không có căn cứ trong câu để
    phân xử giữa chúng (vd 21 'Phường 5' trùng tên; 'An Bình' và 'Vũ Thư' mâu thuẫn, mỗi cách bỏ một đơn vị khớp đúng),
    nên chúng được coi là cách hiểu gần bằng; bước chuyển đổi tự để trống nếu chúng ra kết quả khác nhau."""
    crf_hc = _token_crf_hanh_chinh(crf_context)
    # Thiếu dấu không phải bằng chứng yếu hơn: 'Vu Thư' và 'Vũ Thư' cùng là khớp đúng tên.
    muc = {'chinh_xac': 'dung_ten', 'khong_dau': 'dung_ten'}

    # Độ dài đoạn khớp là bằng chứng: 'Cát Tiên' (bỏ chữ '2') giải thích ít hơn 'Cát Tiên 2'.
    # Mốc cũng là bằng chứng: giả thuyết cùng một mốc ăn khớp với các tên còn lại trong câu hơn giả thuyết lẫn mốc
    # ('tinh long an ... xa dong thanh': Đông Thạnh cũ, không phải Đông Thành mới).
    # Vị trí là bằng chứng: đơn vị đứng cuối câu ('20, Yên Bái, Đà Nẵng': Đà Nẵng là tỉnh, Yên Bái là đường).
    records = getattr(crf_context, 'records', None) or ()
    cuoi = max((i for i, t in enumerate(records) if any(c.isalnum() for c in t.chu)), default=-1) + 1

    def chu_ky(path):
        return (path.cay, sorted((u.cap, u.cay, muc.get(u.kieu_khop, u.kieu_khop), u.co_tien_to, u.ten_cu,
                                  u.ket_thuc - u.bat_dau, set(range(u.bat_dau, u.ket_thuc)) <= crf_hc,
                                  u.ket_thuc == cuoi) for u in path.ung_vien))
    goc = chu_ky(best)
    if not goc[1]:
        return []
    return [x for x in ranked if x[1] is not best and chu_ky(x[1]) == goc]


def gia_thuyet_mo_rong_nhat_quan(chon, ranked, dm, crf_context):
    """Giả thuyết gồm mọi đơn vị của giả thuyết đã chọn cộng thêm đơn vị khớp không sai chính tả, không qua tên cũ,
    nằm trên đoạn CRF gán là hành chính, và đổi ra đúng cùng tập xã mới / tỉnh mới. Chọn nó không đổi mã kết quả,
    chỉ giải thích thêm phần của câu mà ranker bỏ qua vì cả hai cách đều cho cùng đáp án lúc train
    (ví dụ bỏ 'Hà Nội' trước số điện thoại)."""
    from .xep_hang import tap_dich
    char_spans = getattr(crf_context, 'char_spans', None)
    records = getattr(crf_context, 'records', None)
    if not char_spans or not records:
        return None
    crf_hc = _token_crf_hanh_chinh(crf_context)
    def khoa(p):
        return {(u.bat_dau, u.ket_thuc, u.ma, u.cay) for u in p.ung_vien}
    goc = khoa(chon[1])
    dich = tap_dich(chon[1], dm)
    if not dich[1]:
        return None
    for item in ranked:
        k = khoa(item[1])
        if not (k > goc):
            continue
        them = [u for u in item[1].ung_vien if (u.bat_dau, u.ket_thuc, u.ma, u.cay) not in goc]
        if any(u.kieu_khop == 'sai_chinh_ta' or u.ten_cu or not set(range(u.bat_dau, u.ket_thuc)) <= crf_hc
               for u in them):
            continue
        if tap_dich(item[1], dm) == dich:
            return item
    return None


def _tinh_cua_duong_di(duong_di, dm):
    provinces = None
    for u in duong_di.ung_vien:
        ps = set(dm.dich_tinh(u.cay, u.ma))
        provinces = ps if provinces is None else provinces & ps
    return set() if provinces is None else provinces


SO_BANG_CHU = {'mot': '1', 'hai': '2', 'ba': '3', 'bon': '4', 'tu': '4', 'nam': '5', 'lam': '5', 'sau': '6',
               'bay': '7', 'tam': '8', 'chin': '9', 'muoi': '10'}
LOAI_DUNG_TRUOC_SO = {'phuong', 'p', 'phg', 'f', 'quan', 'q', 'xom', 'x', 'thon', 'ap', 'to', 'khu', 'kp', 'ban'}


def doc_lai_token(tokens):
    """Cách đọc khác của từng token, giữ nguyên vị trí: gỡ telex; số bằng chữ đứng ngay sau chữ loại thành chữ số."""
    out = [go_telex(t) for t in tokens]
    for i in range(1, len(tokens)):
        j = i - 1
        while j > 0 and tokens[j] == '.':  # Q.ba: bỏ qua dấu chấm viết tắt
            j -= 1
        truoc = bo_dau(tokens[j].casefold())
        if truoc in LOAI_DUNG_TRUOC_SO and bo_dau(tokens[i].casefold()) in SO_BANG_CHU:
            out[i] = SO_BANG_CHU[bo_dau(tokens[i].casefold())]
    return out


BAC = {'xa': 1, 'huyen': 2, 'tinh': 3}  # chi tiết (số nhà, ngõ, đường, thôn) là bậc 0


def dung_thu_bac(item):
    """Địa chỉ viết theo một chiều: nhỏ đến lớn hoặc lớn đến nhỏ. Xét các đơn vị hành chính và chi tiết theo vị trí."""
    _, path, _, spans, _, _ = item
    moc = sorted([(u.bat_dau, BAC[u.cap]) for u in path.ung_vien] + [(s['bat_dau'], 0) for s in spans])
    bac = [b for _, b in moc]
    bac = [b for i, b in enumerate(bac) if i == 0 or b != bac[i - 1]]
    return all(x < y for x, y in zip(bac, bac[1:])) or all(x > y for x, y in zip(bac, bac[1:]))


def _bo_gia_thuyet_dao_thu_bac(ranked):
    """Bỏ giả thuyết đảo thứ bậc (xóm, huyện, rồi xã) khi có giả thuyết đúng thứ bậc với ít nhất ngần ấy đơn vị hành
    chính và không để sót thêm phần nào; câu viết xáo trộn thật (không cách hiểu nào đúng thứ bậc) không bị đụng tới."""
    dung = [x for x in ranked if dung_thu_bac(x)]
    if not dung or dung[0] is ranked[0]:
        return ranked
    def bi_troi(x):
        if any(x is y for y in dung):
            return False
        return any(len(y[1].ung_vien) >= len(x[1].ung_vien) and set(y[4]) <= set(x[4]) for y in dung)
    giu = [x for x in ranked if not bi_troi(x)]
    return giu or ranked


# Bốn bước sửa sau ranker. Mỗi bước nhận danh sách `close` (các giả thuyết gần điểm nhất, phần tử đầu là
# giả thuyết được chọn) và trả `close` mới; giả thuyết được chọn luôn là close[0].

def _uu_tien_ten_hien_hanh(close):
    """Bước 1. Tên hiện hành thắng tên cũ khi điểm gần bằng: tên cũ chỉ dùng khi không còn cách hiểu nào
    bằng tên hiện hành. Chỉ so các cách hiểu giải thích được ngang nhau: cách hiểu tên cũ để lại ít phần chưa
    phân loại hơn mọi cách hiểu tên hiện hành thì được giữ (không đánh đổi phần câu đã giải thích lấy tên mới)."""
    hien_hanh = [x for x in close if not any(u.ten_cu for u in x[1].ung_vien)]
    if not hien_hanh or len(hien_hanh) == len(close):
        return close
    it_sot_nhat = min(len(x[4]) for x in hien_hanh)
    return [x for x in close if any(x is h for h in hien_hanh) or len(x[4]) < it_sot_nhat]


def _thay_bang_mo_rong_nhat_quan(close, ranked, dm, crf_context):
    """Bước 2. Ranker bỏ qua đơn vị mà bỏ hay giữ đều ra cùng đáp án lúc train; nếu có giả thuyết giải thích
    thêm đúng phần đó mà không đổi mã kết quả thì dùng nó làm giả thuyết được chọn."""
    mo_rong = gia_thuyet_mo_rong_nhat_quan(close[0], ranked, dm, crf_context)
    return close if mo_rong is None else [mo_rong] + close[1:]


def _bo_cach_hieu_giai_thich_it_hon(close, ranked):
    """Cách hiểu gần điểm để lại chưa phân loại nhiều hơn hẳn giả thuyết được chọn, và không giả thuyết nào
    chứa nó mà giải thích được ngang giả thuyết được chọn, thì nó không khớp được với phần còn lại của câu:
    không tính nó khi xét câu còn mơ hồ."""
    goc = set(close[0][4])
    def khoa(p):
        return {(u.bat_dau, u.ket_thuc, u.ma, u.cay) for u in p.ung_vien}
    def mo_rong_duoc(x):
        k = khoa(x[1])
        return any(khoa(y[1]) >= k and set(y[4]) <= goc for y in ranked)
    return [close[0]] + [x for x in close[1:] if not set(x[4]) > goc or mo_rong_duoc(x)]


def _them_gia_thuyet_tuong_duong(close, ranked, crf_context):
    """Bước 3. Thêm các giả thuyết bằng chứng ngang giả thuyết được chọn để bước chuyển đổi và chọn tỉnh
    biết câu còn cách hiểu khác (không chọn bừa giữa chúng)."""
    them = gia_thuyet_tuong_duong(close[0][1], ranked, crf_context)
    return close + [x for x in them if all(x is not c for c in close)]


def _chon_tinh(close, dm):
    """Bước 4. Mã tỉnh chỉ được chọn khi mọi giả thuyết trong `close` cùng chỉ về đúng một tỉnh mới."""
    tinh = set().union(*[_tinh_cua_duong_di(x[1], dm) for x in close])
    return next(iter(tinh)) if len(tinh) == 1 else ""


class BoLamSach:
    PHIEN_BAN = "baseline_luat_v3"

    def __init__(self, danh_muc: DanhMuc | None = None, beam: int = 40, bo_tach=None, bo_xep_hang=None,
                 tu_dien_duong=None, bao_ve_duong=False, tien_to_mac_dinh: bool = True,
                 tien_to_so_nha: bool | None = None, tien_to_duong: bool | None = None):
        if bo_xep_hang is not None and not hasattr(bo_tach, 'chuan_bi_chuoi'):
            raise ValueError('Ranker thử nghiệm cần bộ nhận diện có đầu ra ký tự')
        self.danh_muc = danh_muc or DanhMuc()
        if beam < 1:
            raise ValueError("beam phải >= 1")
        self.beam = beam
        self.bo_tach = bo_tach
        self.bo_xep_hang = bo_xep_hang
        self.tu_dien_duong = tu_dien_duong
        self.bao_ve_duong = bao_ve_duong
        self.tien_to_mac_dinh = tien_to_mac_dinh
        self.tien_to_so_nha = tien_to_mac_dinh if tien_to_so_nha is None else tien_to_so_nha
        self.tien_to_duong = tien_to_mac_dinh if tien_to_duong is None else tien_to_duong
        if bo_tach is not None:
            self.PHIEN_BAN = getattr(bo_tach, 'phien_ban', 'thu_nghiem_crf_v1_' + ('bao_ve' if bo_tach.bao_ve_chi_tiet else 'mo'))
        if bo_xep_hang is not None:
            self.PHIEN_BAN += '_lambdarank'
        if bao_ve_duong:
            self.PHIEN_BAN += '_bao_ve_duong'
        if tu_dien_duong is not None:
            self.PHIEN_BAN += '_ten_train'
        self.trie = dung_trie(self.danh_muc)
        self.tra_cuu_neural = None
        if hasattr(bo_tach, 'chuan_bi_chuoi'):
            from .tra_cuu_neural import TraCuuNeural
            self.tra_cuu_neural = TraCuuNeural(self.danh_muc)

    def _sinh_ung_vien_va_mo_rong(self, records, lexical_records, tokens, crf_context):
        dm = self.danh_muc
        bao_ve = self.bo_tach is None or self.bo_tach.bao_ve_chi_tiet
        candidates = sinh_ung_vien(tokens, self.trie, bao_ve_chi_tiet=bao_ve)
        # Đọc lại từng token (vị trí giữ nguyên) rồi tra thêm, kể cả khi mô hình không đánh dấu đoạn đó là hành chính:
        # gỡ phím telex còn sót ("tinh nam ddinh" -> Nam Định) và số viết bằng chữ ngay sau chữ loại ("phường năm",
        # "quận ba" -> Phường 5, Quận 3). Ứng viên thêm được tính là khớp không dấu.
        tokens_telex = doc_lai_token(tokens)
        if tokens_telex != tokens:
            # Trùng chỗ với ứng viên gần đúng (sai chính tả) thì ứng viên gỡ telex thay vào: nó đọc đúng chữ đã gõ.
            co = {(u.bat_dau, u.ket_thuc, u.cay, u.ma): u for u in candidates}
            for u in sinh_ung_vien(tokens_telex, self.trie, bao_ve_chi_tiet=bao_ve):
                k = (u.bat_dau, u.ket_thuc, u.cay, u.ma)
                if u.kieu_khop == 'sai_chinh_ta' or (k in co and co[k].kieu_khop != 'sai_chinh_ta'):
                    continue
                co[k] = replace(u, kieu_khop='khong_dau') if u.kieu_khop == 'chinh_xac' else u
            candidates = sorted(co.values(), key=lambda u: (u.bat_dau, u.ket_thuc, u.cay, u.ma))
        if self.tra_cuu_neural is not None:
            candidates, lexical_added = bo_sung_tu_luoi_goc(lexical_records, records, self.trie, candidates,
                                                          bao_ve_chi_tiet=self.bo_tach.bao_ve_chi_tiet)
            candidates = self.tra_cuu_neural.mo_rong(crf_context, tokens, self.trie, candidates)
            if lexical_added:
                crf_context.lookup_stats['lexical_added'] = lexical_added
        if crf_context is None and self.bo_tach is not None:
            crf_context = self.bo_tach.chuan_bi(tokens)
        if self.bao_ve_duong and crf_context is not None:
            from .crf_chi_tiet import bio_spans
            protected = []
            for field, a, b in bio_spans(crf_context.labels)[0]:
                marker = khop_tien_to(tokens[a:b], 0, CHI_TIET)
                if field == 'duong' and marker and marker[1][0] == 'duong':
                    protected.append((a + marker[0], b))
            candidates = [u for u in candidates if u.co_tien_to or not any(
                a <= u.bat_dau and u.ket_thuc <= b for a, b in protected)]
        return candidates, crf_context

    def tao_gia_thuyet(self, chuoi):
        if not isinstance(chuoi, str):
            raise TypeError("Địa chỉ phải là chuỗi")
        records = token_co_vi_tri(chuoi)
        lexical_records = records
        crf_context = self.bo_tach.chuan_bi_chuoi(chuoi) if hasattr(self.bo_tach, 'chuan_bi_chuoi') else None
        if crf_context is not None:
            records = crf_context.records
        tokens = [t.chu for t in records]
        candidates, crf_context = self._sinh_ung_vien_va_mo_rong(records, lexical_records, tokens, crf_context)
        admin_spans = {(u.bat_dau, u.ket_thuc) for u in candidates if u.co_tien_to and u.kieu_khop != "sai_chinh_ta"}
        prefixes = {i: p for i, p in cac_tien_to(tokens).items() if not any(a < i < b for a, b in admin_spans)}
        paths = tim_duong_di(candidates, len(tokens), self.danh_muc, self.beam)
        ranked = []
        for path in paths:
            occupied = {i for u in path.ung_vien for i in range(u.bat_dau, u.ket_thuc)}
            detail, spans, unknown, inferred = (
                crf_context.tach(occupied, tien_to_mac_dinh=self.tien_to_mac_dinh,
                                 tien_to_so_nha=self.tien_to_so_nha, tien_to_duong=self.tien_to_duong)
                if crf_context is not None
                else tach_co_dau_vet(tokens, occupied, prefixes, tien_to_mac_dinh=self.tien_to_mac_dinh,
                                     tien_to_so_nha=self.tien_to_so_nha, tien_to_duong=self.tien_to_duong))
            score = path.diem - .12*len(unknown) + .05*sum(s["ket_thuc"]-s["bat_dau"] for s in spans)
            if crf_context is not None:
                score += crf_context.diem_hanh_chinh(occupied)
                if hasattr(crf_context, 'diem_ung_vien'):
                    score += sum(crf_context.diem_ung_vien(u) for u in path.ung_vien)
            ranked.append((score, path, detail, spans, unknown, inferred))
        return records, candidates, crf_context, ranked

    def _chon_gia_thuyet_va_tinh(self, tokens, candidates, crf_context, ranked):
        if self.bo_xep_hang is not None:
            from .xep_hang import dac_trung_gia_thuyet
            features = [dac_trung_gia_thuyet(x, tokens, candidates, self.danh_muc, crf_context) for x in ranked]
            scores = self.bo_xep_hang.cham_diem(features)
            ranked = [(float(s), *item[1:]) for s, item in zip(scores, ranked)]
        ranked.sort(key=lambda x: -x[0])
        ranked = _bo_gia_thuyet_dao_thu_bac(ranked)
        score, best, detail, spans, unknown, inferred = ranked[0]
        margin = self.bo_xep_hang.nguong_gan if self.bo_xep_hang is not None else .65
        close = [x for x in ranked if score - x[0] <= margin]
        close = _uu_tien_ten_hien_hanh(close)
        close = _thay_bang_mo_rong_nhat_quan(close, ranked, self.danh_muc, crf_context)
        score, best, detail, spans, unknown, inferred = close[0]
        close = _bo_cach_hieu_giai_thich_it_hon(close, ranked)
        close = _them_gia_thuyet_tuong_duong(close, ranked, crf_context)
        ma_tinh = _chon_tinh(close, self.danh_muc)
        return score, best, detail, spans, unknown, inferred, close, ranked, ma_tinh

    def _xu_ly_duong_va_canh_bao(self, detail, spans, unknown, tokens, ma_tinh, chuoi, cam=frozenset()):
        detail, spans, unknown, name_evidence = phuc_hoi_ten_duong(
            detail, spans, unknown, tokens, ma_tinh, self.tu_dien_duong,
            tien_to_mac_dinh=self.tien_to_mac_dinh,
            tien_to_duong=self.tien_to_duong,
            tien_to_so_nha=self.tien_to_so_nha,
            cam=cam
        )
        road_warnings = []
        if name_evidence:
            road_warnings.append('ten_duong_tham_chieu_train_chua_xac_minh')
            if name_evidence.get('nguon') == 'tu_dien_train_gan_dung':
                road_warnings.append('ten_duong_doan_gan_dung')
        else:
            detail, spans, bo_viet_tat = bo_duong_viet_tat_chua_giai(detail, spans, tokens, chuoi)
            if bo_viet_tat:
                road_warnings.append('ten_duong_viet_tat_chua_giai')
        for f in ("duong", "thon_xom"):
            name = detail[f].split(" ", 1)[-1] if detail[f] else ""
            if any(c.isalpha() for c in name) and bo_dau(name) == name.casefold():
                road_warnings.append("ten_chi_tiet_chua_xac_minh_dau")
        return detail, spans, unknown, name_evidence, road_warnings

    def _thu_thap_canh_bao_giua(self, best, candidates, unknown, crf_context, inferred, detail):
        warnings = []
        occupied = {i for u in best.ung_vien for i in range(u.bat_dau, u.ket_thuc)}
        if any(u.co_tien_to and u.kieu_khop != "sai_chinh_ta" and not occupied.intersection(range(u.bat_dau, u.ket_thuc)) for u in candidates):
            warnings.append("mau_thuan_hanh_chinh")
        if any(u.kieu_khop == "sai_chinh_ta" for u in best.ung_vien):
            warnings.append("khop_gan_dung")
        if any(u.kieu_khop == "khac_dau" for u in best.ung_vien):
            warnings.append("dau_ten_khac_danh_muc")
        if any(u.kieu_khop == "khac_loai" for u in best.ung_vien):
            warnings.append("loai_hanh_chinh_khac_danh_muc")
        if unknown:
            warnings.append("phan_chua_phan_loai")
        if any(getattr(crf_context, 'lookup_stats', {}).get(k) for k in ('truncated_spans', 'truncated_lookups')):
            warnings.append('ung_vien_tra_cuu_bi_gioi_han')
        if inferred:
            warnings.append("loai_duong_suy_tu_crf" if crf_context is not None else "duong_suy_tu_vi_tri")
        if any(c in detail["so_nha"] for c in "/-–—;"):
            warnings.append("so_nha_can_duyet")
        return warnings

    def _tao_dau_vet_va_thong_ke(self, records, chuoi, best, spans, crf_context, name_evidence, tokens, candidates, ranked, close, score):
        dau_vet = []
        for u in sorted(best.ung_vien, key=lambda u: u.bat_dau):
            dau_vet.append(_tao_dau_vet(records, chuoi, u.bat_dau, u.ket_thuc,
                                        truong=u.cap, ma=u.ma, moc=u.cay,
                                        kieu_khop=u.kieu_khop, diem=u.diem))
        for s in spans:
            dau_vet.append(_tao_dau_vet(records, chuoi, s["bat_dau"], s["ket_thuc"],
                                        truong=s["truong"], gia_tri=s["gia_tri"],
                                        kieu_khop="crf" if crf_context is not None else "luat"))
            if s['truong'] == 'duong' and name_evidence:
                dau_vet[-1]['chuan_hoa_ten'] = name_evidence
        thong_ke = {"so_token": len(tokens), "so_ung_vien": len(candidates), "so_gia_thuyet": len(ranked),
                    "so_cach_hieu_gan_nhat": len(close), "diem": round(score, 4),
                    "moc_dich": "2025-07-01", "mo_hinh": "crf_va_diem_ghep_tay" if crf_context is not None else "luat_va_diem_tay"}
        if crf_context is not None:
            thong_ke['crf_model_sha256'] = self.bo_tach.ma_bam
            thong_ke['crf_bio_loi_truoc_sua'] = crf_context.loi_bio
        if hasattr(self.bo_tach, 'phien_ban'):
            thong_ke['mo_hinh'] = getattr(self.bo_tach, 'ten_mo_hinh', 'char_cnn_crf') + '_va_diem_tay'
            thong_ke['diem_nhan_dien'] = 'log_softmax_emission_khong_phai_marginal_CRF'
            thong_ke['tra_cuu_neural'] = crf_context.lookup_stats
            if hasattr(crf_context, 'segmentation_fallback'):
                thong_ke['tach_tu_fallback_raw'] = crf_context.segmentation_fallback
        if self.bo_xep_hang is not None:
            thong_ke['mo_hinh'] = getattr(self.bo_tach, 'ten_mo_hinh', 'char_cnn_crf') + '_va_lambdarank'
            thong_ke['ranker_sha256'] = self.bo_xep_hang.ma_bam
            thong_ke['diem_khong_phai_xac_suat'] = True
        thong_ke["phien_ban"] = self.PHIEN_BAN
        if self.tu_dien_duong is not None:
            thong_ke['tu_dien_duong_sha256'] = self.tu_dien_duong.ma_bam
            thong_ke['ten_duong_da_doi'] = bool(name_evidence)
        return dau_vet, thong_ke

    def lam_sach(self, chuoi: str) -> DiaChiSach:
        return self.lam_sach_chi_tiet(chuoi)[0]

    def lam_sach_chi_tiet(self, chuoi: str) -> tuple[DiaChiSach, NoiBoTienXuLy]:
        records, candidates, crf_context, ranked = self.tao_gia_thuyet(chuoi)
        tokens = [t.chu for t in records]
        score, best, detail, spans, unknown, inferred, close, ranked, ma_tinh = self._chon_gia_thuyet_va_tinh(
            tokens, candidates, crf_context, ranked
        )
        mid_warnings = self._thu_thap_canh_bao_giua(best, candidates, unknown, crf_context, inferred, detail)
        detail_truoc_duong = dict(detail)
        cam = token_hanh_chinh_kha_thi(records, candidates, crf_context, ma_tinh, self.danh_muc)
        detail, spans, unknown, name_evidence, road_warnings = self._xu_ly_duong_va_canh_bao(
            detail, spans, unknown, tokens, ma_tinh, chuoi, cam
        )
        if not unknown:  # bước khôi phục đường đã xếp hết phần chưa phân loại
            mid_warnings = [w for w in mid_warnings if w != "phan_chua_phan_loai"]
        chi_tiet = {i for s in spans for i in range(s['bat_dau'], s['ket_thuc'])}
        if don_vi_ghi_khong_khop(best, candidates, crf_context, self.danh_muc, chi_tiet):
            mid_warnings.append("don_vi_ghi_khong_khop")
        post_warnings = (["dau_vao_rong"] if not chuoi.strip() else []) + road_warnings
        dau_vet, thong_ke = self._tao_dau_vet_va_thong_ke(
            records, chuoi, best, spans, crf_context, name_evidence, tokens, candidates, ranked, close, score
        )
        dau_vet += dau_vet_hanh_chinh_khong_khop(records, chuoi, crf_context, candidates, unknown)
        don_vi_xa = next((u for u in best.ung_vien if u.cap == "xa"), None)
        don_vi_huyen = next((u for u in best.ung_vien if u.cap == "huyen"), None)
        don_vi_tinh = next((u for u in best.ung_vien if u.cap == "tinh"), None)
        dm = self.danh_muc
        sach = DiaChiSach(
            so_nha=detail["so_nha"],
            ngo_ngach_hem=detail["ngo_ngach_hem"],
            thon_xom=detail["thon_xom"],
            duong=detail["duong"],
            phan_chua_phan_loai=detail["phan_chua_phan_loai"],
            don_vi=_don_vi_nhan(best),
            cach_hieu_gan=[_don_vi_nhan(x[1]) for x in close],
            ma_xa=don_vi_xa.ma if don_vi_xa else "",
            ma_huyen=don_vi_huyen.ma if don_vi_huyen else "",
            ma_tinh=don_vi_tinh.ma if don_vi_tinh else "",
            xa=dm.ten_day_du(don_vi_xa.cay, don_vi_xa.ma) if don_vi_xa else "",
            huyen=dm.ten_day_du(don_vi_huyen.cay, don_vi_huyen.ma) if don_vi_huyen else "",
            tinh=dm.ten_day_du(don_vi_tinh.cay, don_vi_tinh.ma) if don_vi_tinh else "",
            cay=best.cay,
            canh_bao_giua=mid_warnings,
            canh_bao_sau=post_warnings,
            canh_bao=mid_warnings + post_warnings,
            dau_vet=dau_vet,
            thong_ke=thong_ke,
            chuoi=chuoi,
        )
        noi_bo = NoiBoTienXuLy(records=records, candidates=candidates, crf_context=crf_context, ranked=ranked,
                               close=close, score=score, spans=spans, name_evidence=name_evidence,
                               chi_tiet_truoc_duong=detail_truoc_duong)
        return sach, noi_bo
