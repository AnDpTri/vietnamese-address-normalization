"""Ranh giới thôn/xóm khi không có dấu phẩy: phần chi tiết dừng ở chữ cấp hành chính có tên theo sau.

Các chuỗi viết tay, không lấy từ dev/test/vàng.
"""

import unittest

from src.cau_hinh import tao_bo_chuan_hoa
from src.tien_xu_ly import tach_token


class RanhGioiThonXomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bo = tao_bo_chuan_hoa()

    def test_thon_khong_nuot_xa_khi_xa_khong_vao_gia_thuyet(self):
        # Không có đơn vị xã khớp để giả thuyết dùng: chữ "xã Tam Hiệp" vẫn không được thành tên thôn.
        r = self.bo.chuan_hoa('thôn 5 ql1a xã Tam Hiệp huyện Phú Xuyên Hà Nội')
        self.assertNotIn('xã', r.thon_xom.casefold())
        self.assertNotIn('tam hiệp', r.thon_xom.casefold())

    def test_thon_dung_truoc_p_cham_ten(self):
        r = self.bo.chuan_hoa('xóm 11 p. Yersin x. Thành Lộc h. Hậu Lộc t. Thanh Hóa')
        self.assertEqual(r.thon_xom, 'Xóm 11')

    def test_ql_dinh_lien_so_tach_khoi_thon(self):
        self.assertEqual(tach_token('QL14'), ['QL', '14'])
        self.assertEqual(tach_token('tl298'), ['tl', '298'])
        self.assertEqual(tach_token('QL1A'), ['QL', '1A'])
        self.assertEqual(tach_token('QL1234567'), ['QL1234567'])  # không đụng chuỗi số dài
        r = self.bo.chuan_hoa('bản 1 QL14 xã Hoằng Thịnh huyện Hoằng Hóa')
        self.assertEqual(r.thon_xom, 'Bản 1')
        self.assertEqual(r.duong, 'Quốc lộ 14')

    def test_ten_thon_nhieu_chu_khong_bi_cat(self):
        r = self.bo.chuan_hoa("thôn Tân Thành 2 xã Ea Tul huyện Cư M'gar Đắk Lắk")
        self.assertEqual(r.thon_xom, 'Thôn Tân Thành 2')


if __name__ == '__main__':
    unittest.main()
