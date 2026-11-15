"""Hồi quy hai mã xã thiếu trong nguồn cộng đồng; địa chỉ viết tay."""

import unittest

from src.cau_hinh import tao_bo_chuan_hoa


class HaiXaCuBiThieuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bo = tao_bo_chuan_hoa()

    def kiem_tra(self, dia_chi, ma_cu, ma_moi, ten_moi, tinh, huyen):
        dm = self.bo.danh_muc
        cu = dm.lay('cu', ma_cu)
        self.assertEqual((cu.loai, cu.ma_cha), ('Xã', huyen))
        self.assertEqual(dm.lay('cu', huyen).ma_cha, tinh)
        self.assertEqual(dm.doi_chieu[ma_cu], [(ma_moi, 'Nhập toàn bộ')])
        r = self.bo.chuan_hoa(dia_chi)
        self.assertEqual((r.ma_xa, r.xa_phuong, r.ma_tinh), (ma_moi, ten_moi, tinh))
        self.assertNotIn('xa_bi_chia', r.canh_bao)

    def test_my_hung(self):
        self.kiem_tra('xã Mỹ Hưng, huyện Quảng Hòa, Cao Bằng',
                      '01651', '01648', 'Xã Phục Hòa', '04', '049')

    def test_phu_thinh(self):
        self.kiem_tra('xã Phú Thịnh, huyện Yên Sơn, Tuyên Quang',
                      '02482', '02494', 'Xã Thái Bình', '08', '075')

    def test_hong_quang(self):
        self.kiem_tra('xã Hồng Quang, huyện Quảng Hòa, Cao Bằng',
                      '01615', '01636', 'Xã Bế Văn Đàn', '04', '049')

    def test_cong_da(self):
        self.kiem_tra('xã Công Đa, huyện Yên Sơn, Tuyên Quang',
                      '02485', '02458', 'Xã Trung Sơn', '08', '075')


if __name__ == '__main__':
    unittest.main()
