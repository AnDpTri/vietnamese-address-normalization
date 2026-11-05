"""Kiểm thử bộ chấm chuẩn (danh_gia/chuan): quy ước so khớp, phân loại mã xã, thống kê."""
import unittest

from danh_gia.chuan.cham import cham_mau, khop_chi_tiet, mcnemar, so_sanh_cap, tong_hop, wilson
from danh_gia.chuan.du_lieu import Mau


def mau(**vang):
    v = {f: '' for f in ('so_nha', 'ngo_ngach_hem', 'thon_xom', 'duong', 'ma_xa', 'ma_tinh')}
    v.update(vang)
    return Mau('x', 't', '', v)


class QuyUocKhop(unittest.TestCase):
    def test_chu_loai_thieu_mot_ben_khong_bi_bat_loi(self):
        self.assertTrue(khop_chi_tiet('so_nha', 'Số 181', '181'))
        self.assertTrue(khop_chi_tiet('duong', 'Tây Thạnh', 'Đường Tây Thạnh'))

    def test_duong_bang_pho_va_thang_tam(self):
        self.assertTrue(khop_chi_tiet('duong', 'Phố Lê Lai', 'Đường Lê Lai'))
        self.assertTrue(khop_chi_tiet('duong', 'Đường Cách Mạng Tháng Tám', 'Đường Cách Mạng Tháng 8'))

    def test_chu_loai_khac_nhom_la_sai(self):
        self.assertFalse(khop_chi_tiet('ngo_ngach_hem', 'Ngách 5', 'Ngõ 5'))
        self.assertFalse(khop_chi_tiet('thon_xom', 'Thôn 4', 'Xóm 4'))
        self.assertTrue(khop_chi_tiet('thon_xom', 'TDP 5', 'Tổ dân phố 5'))

    def test_ten_cat_cut_va_bia_la_sai(self):
        self.assertFalse(khop_chi_tiet('duong', 'Đường Song', 'Đường Song Hành'))
        self.assertFalse(khop_chi_tiet('duong', 'Đường Hà Nội', ''))


class PhanLoaiMaXa(unittest.TestCase):
    def test_vang_co_ma(self):
        m = mau(ma_xa='00070', ma_tinh='01')
        self.assertEqual(cham_mau(m, {'ma_xa': '00070', 'ma_tinh': '01'})['xa'], 'dung')
        self.assertEqual(cham_mau(m, {'ma_xa': '', 'ma_tinh': '01'})['xa'], 'bo_trong')
        self.assertEqual(cham_mau(m, {'ma_xa': '00004', 'ma_tinh': '01'})['xa'], 'khang_dinh_sai')

    def test_vang_phai_de_trong(self):
        m = mau(ma_tinh='01')
        self.assertEqual(cham_mau(m, {'ma_xa': '', 'ma_tinh': '01'})['xa'], 'dung')
        self.assertEqual(cham_mau(m, {'ma_xa': '00070', 'ma_tinh': '01'})['xa'], 'khang_dinh_sai')

    def test_dien_thua(self):
        m = mau(ma_xa='1', ma_tinh='2')
        self.assertEqual(cham_mau(m, {'duong': 'Đường Hoa', 'ma_xa': '1', 'ma_tinh': '2'})['thua'], ['duong'])


class ThongKe(unittest.TestCase):
    def test_wilson(self):
        thap, cao = wilson(348, 400)
        self.assertAlmostEqual(thap, 83.35, places=1)
        self.assertAlmostEqual(cao, 89.95, places=1)
        self.assertEqual(wilson(0, 0), (0., 0.))

    def test_mcnemar(self):
        self.assertEqual(mcnemar(0, 0), 1.)
        self.assertAlmostEqual(mcnemar(4, 15), 0.0192, places=3)
        self.assertAlmostEqual(mcnemar(4, 0), 0.125, places=3)

    def test_so_sanh_va_tong_hop(self):
        ms = [Mau(str(i), 't', '', {'so_nha': '', 'ngo_ngach_hem': '', 'thon_xom': '', 'duong': '', 'ma_xa': '1', 'ma_tinh': '2'})
              for i in range(20)]
        a = {m.id: cham_mau(m, {'ma_xa': '1', 'ma_tinh': '2'}) for m in ms}
        b = {m.id: cham_mau(m, {'ma_xa': '9' if int(m.id) < 10 else '1', 'ma_tinh': '2'}) for m in ms}
        ss = so_sanh_cap(ms, a, b)
        self.assertEqual(ss['du_6']['ket_luan'], 'KÉM HƠN')
        self.assertEqual(ss['khong_khang_dinh_sai']['a_dung_b_sai'], 10)
        self.assertEqual(tong_hop(ms, b)['xa_khang_dinh_sai'], 10)


if __name__ == '__main__':
    unittest.main()
