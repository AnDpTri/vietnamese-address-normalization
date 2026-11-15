"""Ranker không bỏ rơi chữ người dùng gõ: đơn vị khớp đúng trên đoạn dài hơn thắng đơn vị ngắn bỏ chữ.

Các chuỗi viết tay, không lấy từ dev/test/vàng.
"""

import unittest

from src.cau_hinh import tao_bo_chuan_hoa


class DonViDayDuHonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bo = tao_bo_chuan_hoa()

    def test_ten_phuong_dai_hon_khong_bi_cat_chu_cuoi(self):
        for text in ('12 ngo 5 tran thai tong p dich vong hau q cau giay hn',
                     'số 3 đường Xuân Thủy p dich vong hau cau giay ha noi'):
            with self.subTest(text=text):
                sach = self.bo.bo_lam_sach.lam_sach(text)
                self.assertIn('Dịch Vọng Hậu', sach.xa)
                self.assertNotIn('phan_chua_phan_loai', sach.canh_bao)
                self.assertEqual(sach.ma_tinh, '01')

    def test_ten_ngan_van_dung_khi_khong_co_chu_them(self):
        sach = self.bo.bo_lam_sach.lam_sach('12 ngõ 5 Trần Thái Tông, phường Dịch Vọng, quận Cầu Giấy, Hà Nội')
        self.assertTrue(sach.xa.endswith('Dịch Vọng'), sach.xa)


if __name__ == '__main__':
    unittest.main()
