"""Ca hành vi độc lập với tập test cuối; chạy bằng unittest, không ghi dữ liệu."""

import unittest
import unicodedata
from src.chuan_hoa import BoChuanHoa
from src.tien_xu_ly.tim_kiem import Trie
from src.tien_xu_ly import token_co_vi_tri
from src.kieu_du_lieu import DonViNhan
from src.chuyen_doi import sang_cay_moi


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bo = BoChuanHoa()

    def test_cu_cung_ma_khac_thuc_the(self):
        r = self.bo.chuan_hoa("Số 12, phường Trúc Bạch, quận Ba Đình, Hà Nội")
        self.assertEqual((r.ma_xa, r.ma_tinh, r.so_nha), ("00004", "01", "Số 12"))
        self.assertEqual(r.xa_phuong, "Phường Ba Đình")

    def test_tron_moc(self):
        r = self.bo.chuan_hoa("Phường Ba Đình, quận Ba Đình, Hà Nội")
        self.assertEqual(r.ma_xa, "00004")
        self.assertTrue(any(x.get("moc") == "moi" and x["truong"] == "xa" for x in r.dau_vet))
        self.assertTrue(any(x.get("moc") == "cu" and x["truong"] == "huyen" for x in r.dau_vet))

    def test_dao_thu_tu(self):
        a = self.bo.chuan_hoa("Hà Nội, Quận Ba Đình, Phường Trúc Bạch, Số 12, Ngõ 5, Đường Lê Lợi")
        b = self.bo.chuan_hoa("Số 12, Ngõ 5, Đường Lê Lợi, Phường Trúc Bạch, Quận Ba Đình, Hà Nội")
        self.assertEqual(a.dia_chi_chuan, b.dia_chi_chuan)
        self.assertEqual(a.ngo_ngach_hem, "Ngõ 5")

    def test_nguon_khong_tuong_thich_du_cung_dich(self):
        dm = self.bo.danh_muc
        self.assertFalse(dm.tuong_thich(dm.lay("cu", "00004"), dm.lay("cu", "003")))
        r = self.bo.chuan_hoa("phường Trúc Bạch, quận Tây Hồ, Hà Nội")
        self.assertIn("mau_thuan_hanh_chinh", r.canh_bao)

    def test_xa_bi_chia_khong_chon_bua(self):
        dm = self.bo.danh_muc
        ma = next(k for k, v in sorted(dm.doi_chieu.items()) if len({x[0] for x in v}) > 1)
        old = dm.lay("cu", ma)
        huyen = dm.lay("cu", old.ma_cha)
        target, _, warnings = sang_cay_moi([DonViNhan("xa", ma, "cu")], {}, dm)
        self.assertEqual(target, "")
        self.assertIn("xa_bi_chia", warnings)
        # Có đủ cấp nguồn nhưng không có thông tin chi tiết để chọn đích.
        text = f"{dm.ten_day_du('cu', ma)}, {dm.ten_day_du('cu', huyen.ma)}, {dm.ten_day_du('cu', huyen.ma_cha)}"
        r = self.bo.chuan_hoa(text)
        self.assertEqual(r.ma_xa, "")
        self.assertGreater(len(r.xa_moi_ung_vien), 1)

    def test_ten_duong_khong_bi_nhan_la_tinh(self):
        r = self.bo.chuan_hoa("Đường Hà Nội")
        self.assertEqual(r.duong, "Đường Hà Nội")
        self.assertEqual(r.ma_tinh, "")
        self.assertEqual(r.ma_xa, "")

    def test_giu_so_nha_co_gach_cheo(self):
        r = self.bo.chuan_hoa("12/5, Đường Lê Lợi")
        self.assertEqual(r.so_nha, "Số 12/5")
        self.assertEqual(r.ngo_ngach_hem, "")
        self.assertIn("so_nha_can_duyet", r.canh_bao)

    def test_unicode_span_goc(self):
        text = unicodedata.normalize("NFD", "Số 18B, phường Trúc Bạch, quận Ba Đình, Hà Nội")
        r = self.bo.chuan_hoa(text)
        self.assertEqual(r.ma_xa, "00004")
        for s in r.dau_vet:
            self.assertEqual(s["doan_goc"], text[s["ky_tu_bat_dau"]:s["ky_tu_ket_thuc"]])
        self.assertEqual("".join(t.chu for t in token_co_vi_tri("DịchVọng")), "DịchVọng")

    def test_khong_dau_viet_tat(self):
        r = self.bo.chuan_hoa("18B, P.Truc Bach, Q.Ba Dinh, HN")
        self.assertEqual((r.ma_xa, r.ma_tinh), ("00004", "01"))

    def test_phuong_quan_dem_khong_giu_nguyen_so_nha(self):
        r = self.bo.chuan_hoa("Số 04, P.04, Q.08, TP.HCM")
        self.assertEqual((r.xa_phuong, r.tinh, r.so_nha), ("Phường Chánh Hưng", "Thành phố Hồ Chí Minh", "Số 04"))

    def test_dem_khong_khong_chot_phuong_bi_chia(self):
        r = self.bo.chuan_hoa("P.05, Q.08, TP.HCM")
        self.assertEqual(r.ma_xa, "")
        self.assertEqual({u["ten"] for u in r.xa_moi_ung_vien}, {"Phường Bình Đông", "Phường Chánh Hưng"})

    def test_thieu_tinh_suy_tu_nguon_du_nhat(self):
        r = self.bo.chuan_hoa("Phường Trúc Bạch, Quận Ba Đình")
        self.assertEqual(r.ma_tinh, "01")
        self.assertIn("thieu_tinh_dau_vao", r.canh_bao)

    def test_dau_vao_rong_va_kieu(self):
        r = self.bo.chuan_hoa("")
        self.assertEqual(r.dia_chi_chuan, "")
        self.assertIn("dau_vao_rong", r.canh_bao)
        with self.assertRaises(TypeError):
            self.bo.chuan_hoa(None)

    def test_levenshtein_trie(self):
        t = Trie()
        t.them("Trúc Bạch", "00004", "cu")
        self.assertEqual(t.tim("Trúc Bạhc"), [])
        self.assertEqual(t.tim("Truc Bach"), [("00004", "cu", 0)])
        self.assertIn(("00004", "cu", 1), t.tim("Truc Bachh", 1))

    def test_huyen_thanh_dac_khu(self):
        r = self.bo.chuan_hoa("Huyện Bạch Long Vĩ, Hải Phòng")
        self.assertEqual(r.ma_xa, "11948")
        self.assertEqual(r.xa_phuong, "Đặc khu Bạch Long Vĩ")

    def test_tinh_co_gach_noi(self):
        r = self.bo.chuan_hoa("Tỉnh Bà Rịa - Vũng Tàu")
        self.assertEqual(r.ma_tinh, "79")

    def test_ten_to_khong_thanh_tien_to_to(self):
        for name, prefix in [("Tô Vĩnh Diện", "Phố"), ("Tô Ngọc Vân", "Đường"), ("Tô Hiệu", "Đường")]:
            with self.subTest(name=name):
                r = self.bo.chuan_hoa(f"Số 3, {prefix} {name}, Phường Trúc Bạch, Quận Ba Đình, Hà Nội")
                self.assertEqual(r.duong, f"{prefix} {name}")
                self.assertEqual(r.thon_xom, "")
        r = self.bo.chuan_hoa("59 To Ngoc Van, Khu phố 4, Phường Trúc Bạch, Quận Ba Đình, HN")
        self.assertEqual(r.duong, "Đường To Ngoc Van")
        self.assertEqual(r.thon_xom, "Khu phố 4")

    def test_tinh_trong_ten_duong_khong_la_tinh(self):
        for prefix in ("Đường ", ""):
            r = self.bo.chuan_hoa(f"45 {prefix}XÔ VIẾT NGHỆ TĨNH, Phường Trúc Bạch, Quận Ba Đình, Hà Nội")
            self.assertEqual(r.duong, "Đường Xô Viết Nghệ Tĩnh")
            self.assertEqual(r.ma_tinh, "01")

    def test_thanh_pho_khong_bi_nhan_la_duong(self):
        r = self.bo.chuan_hoa("386, Tên Lửa, Phường An Lạc, Thành phố Hồ Chí Minh")
        self.assertEqual((r.ma_tinh, r.ma_xa), ("79", "27460"))
        self.assertEqual(r.duong, "Đường Tên Lửa")
        self.assertNotIn("thieu_tinh_dau_vao", r.canh_bao)
        r = self.bo.chuan_hoa("Thành phố Hồ Chí Minh")
        self.assertEqual(r.ma_tinh, "79")
        self.assertEqual(r.duong, "")

    def test_ten_duong_bat_dau_bang_tu_hanh_chinh(self):
        for name in ("Xã Đàn", "Thành Phố Mới", "Tổ Quốc"):
            r = self.bo.chuan_hoa(f"12, Đường {name}, Phường Trúc Bạch, Quận Ba Đình, Hà Nội")
            self.assertEqual(r.duong, "Đường " + name)
            self.assertEqual(r.ma_xa, "00004")

    def test_tien_to_chi_tiet_that_van_duoc_nhan(self):
        r = self.bo.chuan_hoa("Số 3, Tổ 58A, Ngõ 5, Phố Tô Vĩnh Diện, Phường Trúc Bạch, Quận Ba Đình, HN")
        self.assertEqual(r.thon_xom, "Tổ 58A")
        self.assertEqual(r.ngo_ngach_hem, "Ngõ 5")
        self.assertEqual(r.duong, "Phố Tô Vĩnh Diện")
        r = self.bo.chuan_hoa("12, Tỉnh lộ 10")
        self.assertEqual(r.duong, "Tỉnh lộ 10")
        self.assertEqual(r.ma_tinh, "")

    def test_giu_huyen_ro_khi_xa_mau_thuan(self):
        r = self.bo.chuan_hoa("185 Đường 3/2, phường 11, Quận 10, Hồ Chí Minh")
        self.assertEqual(r.ma_tinh, "79")
        self.assertEqual(r.ma_xa, "")
        self.assertIn("mau_thuan_hanh_chinh", r.canh_bao)
        self.assertTrue(any(x["truong"] == "huyen" and x["ma"] == "771" for x in r.dau_vet))
        self.assertEqual(r.xa_moi_ung_vien, [])

    def test_viet_tat_dinh_so_va_dau_vet(self):
        s = "90 Bành Văn Trân,P7,Q.Tân Bình,TPHCM"
        r = self.bo.chuan_hoa(s)
        self.assertEqual((r.ma_tinh, r.ma_xa), ("79", "26968"))
        self.assertEqual(r.duong, "Đường Bành Văn Trân")
        self.assertTrue(any(x["doan_goc"] == "P7" for x in r.dau_vet))

    def test_ngo_dinh_so_unicode_phan_ra(self):
        s = unicodedata.normalize("NFD", "12 ngõ5 Trần Thái Tông, P.DịchVọng, Q.CầuGiấy, HN")
        r = self.bo.chuan_hoa(s)
        self.assertEqual(r.ngo_ngach_hem, "Ngõ 5")
        self.assertEqual(r.duong, "Đường Trần Thái Tông")
        for x in r.dau_vet:
            self.assertEqual(x["doan_goc"], s[x["ky_tu_bat_dau"]:x["ky_tu_ket_thuc"]])

    def test_viet_tat_duong_va_loi_telex(self):
        for prefix in ("Đ.", "Đuong ", "dduowng "):
            r = self.bo.chuan_hoa(f"72 {prefix}ĐộiCấn, X.Nga Liên, H.Nga Sơn, Tỉnh Thanh Hóa")
            self.assertEqual(r.duong, "Đường Đội Cấn")
            self.assertEqual(r.ma_xa, "16138")

    def test_tu_doi_dien_khong_loai_nham_ten_duong(self):
        for name in ("Đội Cấn", "Điện Biên Phủ"):
            r = self.bo.chuan_hoa(f"12 {name}, Phường Trúc Bạch, Quận Ba Đình, Hà Nội")
            self.assertEqual(r.duong, "Đường " + name)

    def test_khong_bien_xa_chua_biet_thanh_so_nha(self):
        r = self.bo.chuan_hoa("P999, Thành phố Hồ Chí Minh")
        self.assertEqual(r.so_nha, "")
        self.assertEqual(r.ma_tinh, "79")
        self.assertEqual(r.ma_xa, "")

    def test_dau_vet_khong_chong_lan(self):
        s = "Số 12, Ngõ 5, Phố Tô Vĩnh Diện, Phường Trúc Bạch, Quận Ba Đình, Hà Nội"
        r = self.bo.chuan_hoa(s)
        used = set()
        for x in r.dau_vet:
            current = set(range(x["token_bat_dau"], x["token_ket_thuc"]))
            self.assertFalse(used & current)
            used.update(current)

    def test_ten_hanh_chinh_chua_tien_to_duong_thon(self):
        dm = self.bo.danh_muc
        for name in ("Bản Xèo", "Phố Mới", "Đường Lâm"):
            dv = next(x for x in dm.don_vi.values() if x.cay == "cu" and x.cap == "xa" and x.ten == name)
            district = dm.lay("cu", dv.ma_cha)
            s = f"{dm.ten_day_du('cu', dv.ma)}, {dm.ten_day_du('cu', district.ma)}, {dm.ten_day_du('cu', district.ma_cha)}"
            with self.subTest(name=name):
                r = self.bo.chuan_hoa(s)
                self.assertEqual(r.duong, "")
                self.assertEqual(r.thon_xom, "")
                self.assertTrue(any(x["truong"] == "xa" for x in r.dau_vet))

    def test_khac_loai_tinh_van_giu_ten_va_canh_bao(self):
        r = self.bo.chuan_hoa("Phường Từ Sơn, Thành phố Bắc Ninh, Bắc Ninh")
        self.assertEqual(r.ma_tinh, "24")
        self.assertEqual(r.xa_phuong, "Phường Từ Sơn")
        self.assertIn("loai_hanh_chinh_khac_danh_muc", r.canh_bao)

    def test_khac_loai_xa_duoc_kiem_tra_theo_ngu_canh(self):
        # Thị trấn Hòa Thành (huyện Hòa Thành) đã thành phường Long Hoa năm 2020 (NQ 865/NQ-UBTVQH14);
        # lớp tên cũ đưa về xã cũ 25630 -> Phường Long Hoa mới, không đoán theo tên sang Phường Hòa Thành (25645, khác loại).
        r = self.bo.chuan_hoa("Đường Đỗ Thị Tặng, Thị trấn Hòa Thành, Huyện Hòa Thành, Tây Ninh")
        self.assertEqual((r.ma_xa, r.ma_tinh), ("25630", "80"))
        self.assertEqual(r.duong, "Đường Đỗ Thị Tặng")
        for name in ("Bản Xèo", "Trúc Bạch"):
            r = self.bo.chuan_hoa("Tỉnh " + name)
            self.assertEqual(r.ma_xa, "")

    def test_xa_lo_trong_ten_duong_khong_thanh_xa_tinh(self):
        for street, expected in [("Đường Song Hành Xa lộ Hà Nội", "Đường Song Hành Xa Lộ Hà Nội"),
                                 ("Xa lộ Hà Nội", "Xa lộ Hà Nội"), ("Đại lộ Thăng Long", "Đại lộ Thăng Long")]:
            r = self.bo.chuan_hoa("844E, " + street)
            self.assertEqual(r.duong, expected)
            self.assertEqual(r.ma_xa, "")
            self.assertEqual(r.ma_tinh, "")
        from src.tien_xu_ly.quy_tac import CHI_TIET, khop_tien_to
        self.assertIsNone(khop_tien_to(["Xã", "Lộ", "25"], 0, CHI_TIET))


if __name__ == "__main__":
    unittest.main()
