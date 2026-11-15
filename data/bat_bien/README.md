# Bộ cặp bất biến (không có nhãn)

`cap_bat_bien.csv`: 9.000 cặp = 1.000 câu gốc x 9 biến đổi không mang thông tin (số điện thoại cuối, ghi chú cuối, thêm ", Việt Nam", tiền tố "Địa chỉ:", bỏ cách sau phẩy, phẩy thành gạch, viết hoa hết, nhân đôi dấu cách, thêm "xóm 5" đầu câu).

- **Nguồn:** `dau_vao` của `data/dev/dev_goc.csv`, `data/dev/dev_kho.csv` (cột `nguon` = dev, 7.218 cặp) và `data/test/dia_chi_test.csv` (cột `nguon` = test, 1.782 cặp). Chỉ lấy chữ đầu vào, không lấy nhãn.
- **Cách sinh:** các câu gốc duy nhất, sắp xếp, xáo bằng `random.Random(20261031)`, lấy 1.000 câu đầu; biến đổi định nghĩa trong `danh_gia/v3/do_bat_bien.py` (`BIEN_DOI`). Sinh lại: `python danh_gia/v3/do_bat_bien.py - - <ten> --sinh-lai`.
- **Cách đo:** pipeline chạy câu gốc và câu biến đổi; cặp "đổi mã" khi (mã xã, mã tỉnh) khác nhau. Kết quả ghi ở `rieng/danh_gia_chuan/bat_bien/<ten>.json`. Số dùng để quyết định chỉ lấy trên các cặp nguồn dev; cặp nguồn test chỉ báo kèm, không dùng để dò lỗi.
- **Không được dùng để train** (chứa chữ của dev và test).
