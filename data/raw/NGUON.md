# BÁO CÁO NGUỒN VÀ ĐẶC TẢ DỮ LIỆU ĐƠN VỊ HÀNH CHÍNH VIỆT NAM

Tài liệu này tổng hợp thông tin xuất xứ, ngày truy cập, bản quyền, cấu trúc dữ liệu và các ghi chú đối soát của 3 bộ dữ liệu đơn vị hành chính phục vụ dự án chuẩn hóa địa chỉ tiếng Việt:

1. `moi_tinh_xa.csv` — Danh mục ĐVHC sau sáp nhập (mô hình 2 cấp, hiệu lực từ 01/07/2025).
2. `cu_tinh_huyen_xa.csv` — Danh mục ĐVHC trước sáp nhập (mô hình 3 cấp, 63 tỉnh/thành).
3. `doi_chieu_xa_cu_moi.csv` — Bảng đối chiếu chuyển đổi xã cũ sang xã mới.

Tất cả các tệp gốc tải về từ mạng được lưu trữ nguyên bản trong thư mục `D:\nlp_chuan_hoa_dia_chi\data\raw\goc\`.

---

## 1. Tệp `moi_tinh_xa.csv`

### 1.1. Thông tin chung
- **Đường dẫn lưu trữ:** `D:\nlp_chuan_hoa_dia_chi\data\raw\moi_tinh_xa.csv`
- **Số dòng:** 3.321 dòng dữ liệu (tổng cộng 3.322 dòng bao gồm header).
- **Định dạng:** CSV UTF-8, dấu phân cách phẩy (`,`), có tiêu đề cột.
- **Cột:** `ma_tinh,ten_tinh,loai_tinh,ma_xa,ten_xa,loai_xa`
- **Mốc hiệu lực:** 01/07/2025 (theo Quyết định số 19/2025/QĐ-TTg của Thủ tướng Chính phủ).

### 1.2. Thống kê & Phân bổ
- **Cấp tỉnh (34 đơn vị):**
  - **6 Thành phố trực thuộc trung ương:** Hà Nội (`01`), Hải Phòng (`31`), Huế (`46`), Đà Nẵng (`48`), Thành phố Hồ Chí Minh (`79`), Cần Thơ (`92`).
  - **28 Tỉnh:** Cao Bằng (`04`), Tuyên Quang (`08`), Điện Biên (`11`), Lai Châu (`12`), Sơn La (`14`), Lào Cai (`15`), Thái Nguyên (`19`), Lạng Sơn (`20`), Quảng Ninh (`22`), Bắc Ninh (`24`), Phú Thọ (`25`), Hưng Yên (`33`), Ninh Bình (`37`), Thanh Hóa (`38`), Nghệ An (`40`), Hà Tĩnh (`42`), Quảng Trị (`44`), Quảng Ngãi (`51`), Gia Lai (`52`), Khánh Hòa (`56`), Đắk Lắk (`66`), Lâm Đồng (`68`), Đồng Nai (`75`), Tây Ninh (`80`), Đồng Tháp (`82`), Vĩnh Long (`86`), An Giang (`91`), Cà Mau (`96`).
- **Cấp xã (3.321 đơn vị):**
  - `Xã`: 2.621 đơn vị.
  - `Phường`: 687 đơn vị.
  - `Đặc khu`: 13 đơn vị (Vân Đồn, Cô Tô, Cát Hải, Bạch Long Vĩ, Cồn Cỏ, Hoàng Sa, Lý Sơn, Trường Sa, Phú Quý, Côn Đảo, Phú Quốc, Thổ Châu, Kiên Hải).

### 1.3. Nguồn gốc & Bản quyền
- **Căn cứ pháp lý:**
  - Quyết định số 19/2025/QĐ-TTg ngày 30/06/2025 của Thủ tướng Chính phủ về việc ban hành Bảng danh mục và mã số các đơn vị hành chính Việt Nam.
  - Các Nghị quyết của Quốc hội và Ủy ban Thường vụ Quốc hội về việc sắp xếp các đơn vị hành chính cấp tỉnh và cấp xã năm 2025.
- **URL nguồn tra cứu & tài liệu:**
  - Cổng thông tin Danh mục hành chính - Tổng cục Thống kê (nay thuộc Cục Thống kê): [https://danhmuchanhchinh.nso.gov.vn/](https://danhmuchanhchinh.nso.gov.vn/)
  - Kho lưu trữ và bộ mã đối soát mở: [https://github.com/zindont/vietnam-address-kit](https://github.com/zindont/vietnam-address-kit) (file `data/source/conversion-table.xlsx` và `src/data/official/current-*.json`)
- **Ngày truy cập:** 25/10/2026.
- **Giấy phép:** Dữ liệu hành chính chính thức của Nhà nước; bộ dữ liệu mã nguồn mở phân phối kèm theo giấy phép MIT License (`data\raw\goc\LICENSE-vietnam-address-kit.txt`).

### 1.4. Điểm còn thiếu hoặc cần lưu ý
- **Biến động sau ngày 01/07/2025:** Đến cuối năm 2026, Quốc hội thông qua các Nghị quyết số `30/2026/QH16`, `36/2026/QH16`, `39/2026/QH16` và các Nghị quyết của UBTVQH nâng cấp 3 tỉnh lên thành phố trực thuộc trung ương (Quảng Ninh, Bắc Ninh, Đồng Nai) và điều chỉnh 23 xã lên phường. File `moi_tinh_xa.csv` này lưu trữ đúng chuẩn mốc **01/07/2025** theo đúng yêu cầu đề tài. Các sửa đổi năm 2026 đã được lưu trong tệp gốc `data\raw\goc\current-amendments-2026.json` để tiện tham khảo mở rộng.

---

## 2. Tệp `cu_tinh_huyen_xa.csv`

### 2.1. Thông tin chung
- **Đường dẫn lưu trữ:** `D:\nlp_chuan_hoa_dia_chi\data\raw\cu_tinh_huyen_xa.csv`
- **Số dòng:** 10.033 dòng dữ liệu (tổng cộng 10.034 dòng bao gồm header).
- **Định dạng:** CSV UTF-8, dấu phân cách phẩy (`,`), có tiêu đề cột.
- **Cột:** `ma_tinh,ten_tinh,ma_huyen,ten_huyen,ma_xa,ten_xa,loai_xa`
- **Mô hình hành chính:** Mô hình 3 cấp truyền thống trước ngày sáp nhập 01/07/2025.

### 2.2. Thống kê & Phân bổ
- **Cấp tỉnh (63 đơn vị):** Đủ 63 tỉnh/thành phố trực thuộc Trung ương của Việt Nam trước sáp nhập (mã từ `01` đến `96`).
- **Cấp huyện (698 đơn vị):** Gồm tất cả các quận, huyện, thị xã, thành phố thuộc tỉnh, thành phố trực thuộc thành phố trực thuộc trung ương (ví dụ: Thành phố Thủ Đức). Tên huyện trong cột `ten_huyen` được lưu kèm loại hình (ví dụ: `Quận Ba Đình`, `Huyện Sóc Sơn`, `Thị xã Sơn Tây`) để đảm bảo không mất thông tin phân loại do file không có cột `loai_huyen`.
- **Cấp xã (10.033 đơn vị):**
  - `Xã`: 7.686 đơn vị.
  - `Phường`: 1.731 đơn vị.
  - `Thị trấn`: 616 đơn vị.
  - Cột `ten_xa` lưu tên định danh của xã (ví dụ: `Trúc Bạch`, `Phúc Xá`); đối với các phường đánh số (như `Phường 1`, `Phường 14`) thì giữ nguyên tiền tố số do đây là tên chính thức. Cột `loai_xa` phân loại rõ `Phường`, `Xã`, hoặc `Thị trấn`.

### 2.3. Nguồn gốc & Bản quyền
- **Căn cứ pháp lý & kỹ thuật:**
  - Hệ thống danh mục mã số đơn vị hành chính Việt Nam do Tổng cục Thống kê ban hành và quản lý.
  - Bộ dữ liệu đối soát chuẩn hóa từ bảng chuyển đổi ĐVHC quốc gia (`data/source/conversion-table.xlsx`) và bảng đối chiếu `doi-chieu-2024-09-01.xls`.
- **URL nguồn:**
  - Tổng cục Thống kê: [https://danhmuchanhchinh.gso.gov.vn/](https://danhmuchanhchinh.gso.gov.vn/)
  - Repository: [https://github.com/zindont/vietnam-address-kit](https://github.com/zindont/vietnam-address-kit)
- **Ngày truy cập:** 25/10/2026.
- **Giấy phép:** Public Domain / MIT License.

### 2.4. Điểm còn thiếu hoặc cần lưu ý
- **5 Huyện đảo không có đơn vị cấp xã trực thuộc:** Trước sáp nhập năm 2025, Việt Nam có 5 huyện đảo đặc thù trực thuộc tỉnh/thành nhưng không chia thành các xã/thị trấn cấp dưới, gồm:
  1. Huyện Bạch Long Vĩ (mã `318`, TP Hải Phòng)
  2. Huyện Cồn Cỏ (mã `471`, tỉnh Quảng Trị)
  3. Huyện Hoàng Sa (mã `498`, TP Đà Nẵng)
  4. Huyện Lý Sơn (mã `536`, tỉnh Quảng Ngãi)
  5. Huyện Côn Đảo (mã `755`, tỉnh Bà Rịa - Vũng Tàu)
  Do bảng `cu_tinh_huyen_xa.csv` đặc tả danh mục ở cấp xã (`ma_xa, ten_xa, loai_xa`), 5 huyện này không có đơn vị cấp xã con nên không có dòng tương ứng trong file `cu_tinh_huyen_xa.csv`. Tuy nhiên, sự chuyển đổi của 5 huyện đảo này thành các Đặc khu mới được phản ánh trọn vẹn trong bảng `doi_chieu_xa_cu_moi.csv` và `moi_tinh_xa.csv`.

---

## 3. Tệp `doi_chieu_xa_cu_moi.csv`

### 3.1. Thông tin chung
- **Đường dẫn lưu trữ:** `D:\nlp_chuan_hoa_dia_chi\data\raw\doi_chieu_xa_cu_moi.csv`
- **Số dòng:** 10.571 dòng dữ liệu (tổng cộng 10.572 dòng bao gồm header).
- **Định dạng:** CSV UTF-8, dấu phân cách phẩy (`,`), có tiêu đề cột.
- **Cột:** `ma_xa_cu,ten_xa_cu,ten_huyen_cu,ten_tinh_cu,ma_xa_moi,ten_xa_moi,ten_tinh_moi,ghi_chu`

### 3.2. Cấu trúc & Quy tắc đối chiếu
- **Quan hệ đối chiếu:**
  - **Nhập nguyên vẹn / Đổi tên / Giữ nguyên (9.598 dòng):** Mỗi xã cũ được chuyển giao toàn bộ sang đúng một xã mới. Cột `ghi_chu` mang các giá trị nguyên bản từ văn bản của UBTVQH: `Nhập toàn bộ` (9.460 dòng), `Giữ nguyên` (127 dòng), `Đổi tên` (2 dòng), `Đổi loại hình` (2 dòng), v.v.
  - **Xã bị chia tách (970 dòng ứng với 440 xã cũ bị chia trong clean; raw có mã gán nhầm):**
    - Các số phân bổ ghi chú bên dưới mô tả raw (973 dòng), trước khi sửa mã trong clean.
    - Nếu một xã cũ bị chia tách sang nhiều xã mới (fan-out > 1), mỗi cặp đối chiếu được tách thành một dòng riêng biệt.
    - Cột `ghi_chu` được gán tiền tố chuẩn hóa `bi_chia`.
    - **827 dòng** mang giá trị `bi_chia`: Đây là các trường hợp nguồn chính thức ghi chung là "Nhập một phần" mà không có mô tả chi tiết thôn/xóm trong bảng tổng hợp.
    - **146 dòng** mang mô tả cụ thể về diện tích hoặc dân số được chép nguyên văn sau tiền tố `bi_chia: `, ví dụ:
      - `bi_chia: Nhập một phần diện tích, toàn bộ dân số` (58 dòng): Toàn bộ cư dân chuyển về một xã mới nhất định, xã kia chỉ tiếp nhận diện tích tự nhiên/đất trống.
      - `bi_chia: Nhập một phần diện tích` (81 dòng).
      - `bi_chia: Nhập một phần dân số` (2 dòng).
      - `bi_chia: Phần còn lại sau khi tách một phần vào xã Canh Vinh` (1 dòng).
      - `bi_chia: Đổi tên từ một phần Phường 15` (1 dòng).
      - `bi_chia: Đổi tên, đổi loại hình từ một phần thị trấn Lai Uyên` (1 dòng).
  - **Chuyển đổi trực tiếp cấp huyện lên đặc khu (6 dòng):** 5 huyện đảo (Bạch Long Vĩ, Cồn Cỏ, Hoàng Sa, Lý Sơn, Côn Đảo) và Khu vực bãi bồi ven biển Kim Sơn chuyển trực tiếp lên Đặc khu / Xã mới; trường hợp này `ma_xa_cu` để trống, `ten_huyen_cu` lưu tên huyện cũ tương ứng.

### 3.3. Nguồn gốc & Bản quyền
- **Nguồn chính thức:**
  - File bảng chuyển đổi ĐVHC mới - cũ toàn quốc: `BangChuyendoiĐVHCmoi_cu_final.xlsx` (Sheet `Tổng hợp_không merge `), văn bản tổng hợp của Bộ Nội vụ và Ủy ban Thường vụ Quốc hội đính kèm QĐ số 19/2025/QĐ-TTg.
  - Tệp gốc lưu tại: `D:\nlp_chuan_hoa_dia_chi\data\raw\goc\conversion-table.xlsx`.
- **URL nguồn tải:** [https://raw.githubusercontent.com/zindont/vietnam-address-kit/main/data/source/conversion-table.xlsx](https://raw.githubusercontent.com/zindont/vietnam-address-kit/main/data/source/conversion-table.xlsx)
- **Ngày truy cập:** 25/10/2026.
- **Giấy phép:** Public Domain / MIT License.

### 3.4. Điểm còn thiếu hoặc cần lưu ý cho mô hình chuẩn hóa địa chỉ
- Đối với 440 xã cũ bị chia (970 dòng trong bảng đối chiếu clean):
  - 58 trường hợp ghi nhận `Nhập một phần diện tích, toàn bộ dân số`: Theo phân tích nghiệp vụ dân cư (ADR-0002), các địa chỉ dân cư của xã cũ này thực tế thuộc về xã mới nhận "toàn bộ dân số".
  - Các trường hợp còn lại chỉ ghi `Nhập một phần` mà văn bản cấp Nghị quyết không số hóa ranh giới tới từng thôn/xóm trong bảng này. Khi chuẩn hóa địa chỉ gặp các xã này mà chuỗi đầu vào không có thông tin chi tiết thôn/xóm/tên đường, hệ thống cần gắn cờ cảnh báo `xa_bi_chia` và cung cấp danh sách xã mới tiềm năng theo đúng quy tắc mục 4 và 5 trong tài liệu đặc tả `bai_toan.md`.

---

## 4. Tóm tắt kiểm tra chất lượng (Data Integrity Checklist)

| Tên tệp | Số cột | Số dòng dữ liệu | Mã hóa | Kiểm tra toàn vẹn |
|---|:---:|:---:|:---:|:---:|
| `moi_tinh_xa.csv` | 6 | 3.321 | UTF-8 | Đủ 34 tỉnh, 3.321 xã/phường/đặc khu, 0 dòng trống, 0 mã trùng lặp |
| `cu_tinh_huyen_xa.csv` | 7 | 10.033 | UTF-8 | Đủ 63 tỉnh, 698 huyện, 10.033 xã/phường/thị trấn, 0 khóa ngoại mồ côi |
| `doi_chieu_xa_cu_moi.csv` | 8 | 10.571 | UTF-8 | 10.571 cặp quan hệ duy nhất, bao phủ toàn bộ 10.033 xã cũ và 3.321 xã mới |

### Hiệu chỉnh hai xã cũ trong data/clean

Danh mục raw giữ nguyên 10.033 xã; clean có 10.035 xã sau khi bổ sung Mỹ Hưng
`01651` (049, 04) và Phú Thịnh `02482` (075, 08) theo nguồn Cục Thống kê
`goc/doi-chieu-2024-09-01.xls`, Sheet1 dòng 894 và 1145. Bảng cộng đồng
`goc/conversion-table.xlsx` (sheet không merge, dòng 912 và 1260) gán nhầm
mã `01615` và `02485`; script sửa mã, giữ hai quan hệ nhập toàn bộ
`01651 → 01648` (NQ 1657, Điều 1 khoản 38) và `02482 → 02494`
(NQ 1684, Điều 1 khoản 28). Clean có 10.571 dòng đối chiếu, 440 xã đa đích
(970 dòng); Hồng Quang và Công Đa vẫn nhập toàn bộ vào Bế Văn Đàn và Trung Sơn.
Không thay đổi dữ liệu raw.
