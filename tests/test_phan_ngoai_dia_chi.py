"""Che phần ngoài địa chỉ (nhãn, ", Việt Nam", ghi chú trong ngoặc) và gom khoảng trắng cho mạng nhận diện.

Các chuỗi viết tay, không lấy từ dev/test/vàng.
"""

import unittest
from unicodedata import normalize

from src.tien_xu_ly.phan_ngoai_dia_chi import che_phan_ngoai_dia_chi as che
from src.tien_xu_ly.tien_xu_ly import gom_khoang_trang


class PhanNgoaiDiaChiTests(unittest.TestCase):
    def test_cung_do_dai_va_giu_vi_tri(self):
        for s in ('Địa chỉ: 12 Lê Lợi, Hà Nội', '12 Lê Lợi, Hà Nội, Việt Nam',
                  'Số 5 Đường A, Quận 1 (gọi trước khi giao, sđt 0912345678)'):
            self.assertEqual(len(che(s)), len(s), s)
        self.assertEqual(che('Địa chỉ: 12 Lê Lợi, Hà Nội').strip(), '12 Lê Lợi, Hà Nội')
        self.assertEqual(che('12 Lê Lợi, Hà Nội, Việt Nam').strip(), '12 Lê Lợi, Hà Nội')
        self.assertEqual(che('Số 5 Đường A, Quận 1 (gọi trước khi giao, sđt 0912345678)').strip(), 'Số 5 Đường A, Quận 1')

    def test_ghi_chu_co_bang_chung_hanh_chinh_duoc_giu(self):
        s = 'Số 5 Đường A (Phường 7) '
        self.assertEqual(che(s), s)

    def test_nfd_giu_nguyen_cum_ky_tu_va_vi_tri_dia_chi(self):
        prefix = normalize('NFD', 'Địa chỉ: ')
        address = normalize('NFD', 'Phường Trúc Bạch, Quận Ba Đình, Hà Nội')
        suffix = normalize('NFD', ', Việt Nam (ghi chú giao hàng)')
        self.assertEqual(che(prefix + address + suffix), ' ' * len(prefix) + address + ' ' * len(suffix))

    def test_nfd_khong_che_ghi_chu_co_ten_hanh_chinh(self):
        address = normalize('NFD', 'Số 8 (Phường Trúc Bạch)')
        self.assertEqual(che(address), address)

    def test_khong_che_khi_con_lai_rong_hoac_la_ten_rieng(self):
        self.assertEqual(che('(abc)'), '(abc)')
        self.assertEqual(che('Số 5, Đường Việt Nam'), 'Số 5, Đường Việt Nam')

    def test_gom_khoang_trang_giu_offset(self):
        raw = '  Số  16   ngõ 12  '
        text, off = gom_khoang_trang(raw, [(i, i + 1) for i in range(len(raw))])
        self.assertEqual(text, 'Số 16 ngõ 12')
        self.assertEqual(len(text), len(off))
        self.assertEqual(raw[off[0][0]], 'S')
        self.assertEqual(raw[off[-1][0]], '2')


if __name__ == '__main__':
    unittest.main()
