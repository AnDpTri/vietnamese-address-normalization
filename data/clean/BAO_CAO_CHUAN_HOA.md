# BÁO CÁO LÀM SẠCH VÀ KIỂM CHỨNG BỘ DỮ LIỆU ĐƠN VỊ HÀNH CHÍNH VIỆT NAM

**Dự án:** NLP Chuẩn hóa địa chỉ tiếng Việt theo đơn vị hành chính sau sáp nhập 2025  
**Địa điểm lưu trữ bộ dữ liệu sạch:** `D:\nlp_chuan_hoa_dia_chi\data\clean\`  
**Thời điểm thực hiện kiểm chứng:** Tháng 10/2026  
**Mốc dữ liệu chuẩn hóa chính:** Hiệu lực ngày **01/07/2025** (Quyết định số 19/2025/QĐ-TTg)

---

## 1. MỤC TIÊU VÀ PHẠM VI XỬ LÝ

Bài toán chuẩn hóa địa chỉ tự do tiếng Việt yêu cầu một cơ sở dữ liệu hành chính chuẩn xác, toàn vẹn về mặt tham chiếu quan hệ, bảo toàn đầy đủ các quan hệ phân rã địa giới và phân định rạch ròi các mốc thời gian hành chính.

Báo cáo này mô tả chi tiết quá trình kiểm chứng độc lập, làm sạch và chuẩn hóa bộ dữ liệu hành chính từ nguồn `data\raw\` chuyển giao sang `data\clean\`, tuân thủ các nguyên tắc:
1. **Bảo toàn nguyên trạng `data\raw`**: Không chỉnh sửa bất kỳ tệp tin nào trong thư mục raw và thư mục con `data\raw\goc\`.
2. **Không tự suy đoán/đoán mò**: Mọi sửa đổi phải có căn cứ pháp lý và đối soát chéo từ văn bản chính thức của Nhà nước; các mâu thuẫn chưa thể đính chính chính thức được bảo lưu nguyên vẹn và ghi nhận vào bảng theo dõi (`issues.csv`, `can_xem_lai.csv`).
3. **Bảo toàn 100% quan hệ chuyển đổi**: Bảo toàn tất cả 440 mã xã cũ có nhiều đích chuyển đổi (fan-out > 1) và toàn bộ ghi chú gốc của văn bản; không tự ý chọn một đích duy nhất.
4. **Phân tách nghiêm ngặt mốc hiệu lực**: Bộ dữ liệu chính chốt đúng mốc hiệu lực **01/07/2025**; toàn bộ các nghị quyết và điều chỉnh phát sinh trong năm 2026 được tách riêng sang tệp `thay_doi_2026.csv`.
5. **Khả năng tái lập (Idempotent)**: Toàn bộ kết quả được tạo ra tự động bằng mã nguồn Python chuẩn (`clean_and_validate.py`) lưu tại `data\clean\scripts\`, không phụ thuộc internet và không cài thêm thư viện bên ngoài.

---

## 2. NGUỒN DỮ LIỆU, MỐC THỜI GIAN VÀ BẢN QUYỀN

### 2.1. Nguồn dữ liệu tham chiếu
- **Cổng thông tin Danh mục đơn vị hành chính Việt Nam (Tổng cục Thống kê / Cục Thống kê):**  
  URL: [https://danhmuchanhchinh.nso.gov.vn/](https://danhmuchanhchinh.nso.gov.vn/) (trước đây là `danhmuchanhchinh.gso.gov.vn`).
- **Kho lưu trữ bộ mã chuyển đổi mã nguồn mở cộng đồng:**  
  URL: [https://github.com/zindont/vietnam-address-kit](https://github.com/zindont/vietnam-address-kit)  
  Tệp đối chiếu gốc: `data/source/conversion-table.xlsx` (bản tổng hợp không merge của Bộ Nội vụ/UBTVQH), `doi-chieu-2024-09-01.xls`, `src/data/official/current-*.json`, `legacy-*.json`.
- **Hệ thống văn bản quy phạm pháp luật:**
  - Quyết định số 19/2025/QĐ-TTg ngày 30/06/2025 của Thủ tướng Chính phủ về Danh mục và mã số các đơn vị hành chính Việt Nam.
  - Quyết định số 124/2004/QĐ-TTg ngày 08/07/2004 của Thủ tướng Chính phủ về ban hành bảng danh mục và mã số các đơn vị hành chính Việt Nam.
  - Nghị quyết của Quốc hội khóa XV về sáp nhập đơn vị hành chính cấp tỉnh năm 2025 (sáp nhập còn 34 tỉnh/thành).
  - Nghị quyết số 897/NQ-UBTVQH14 (sắp xếp ĐVHC cấp huyện, cấp xã tỉnh Cao Bằng năm 2020).
  - Nghị quyết số 816/NQ-UBTVQH14 (sắp xếp ĐVHC cấp huyện, cấp xã tỉnh Tuyên Quang năm 2019).
  - Nghị quyết số 175/2024/QH15 thành lập Thành phố Huế trực thuộc Trung ương.
  - Các Nghị quyết năm 2026: 30/2026/QH16 (Đồng Nai), 36/2026/QH16 (Quảng Ninh), 39/2026/QH16 (Bắc Ninh), 388/NQ-UBTVQH16, 237/NQ-UBTVQH16.

### 2.2. Phân định mốc thời gian
- **Mốc 1 (Trước 01/07/2025):** Mô hình 3 cấp (Tỉnh - Huyện - Xã). Toàn quốc gồm **63 tỉnh/thành phố**, **696 quận/huyện/thị xã/thành phố thuộc tỉnh** (trong đó 691 huyện có xã trực thuộc và 5 huyện đảo đặc thù không chia cấp xã), **10.035 xã/phường/thị trấn**.
- **Mốc 2 (Hiệu lực từ 01/07/2025):** Mô hình 2 cấp (Tỉnh - Xã). Toàn quốc sắp xếp còn **34 tỉnh/thành phố** (6 Thành phố trực thuộc TW và 28 Tỉnh) và **3.321 đơn vị cấp xã** (2.621 xã, 687 phường, 13 đặc khu).
- **Mốc 3 (Các biến động phát sinh trong năm 2026):** Điều chỉnh nâng cấp 3 tỉnh lên thành phố trực thuộc Trung ương và nâng cấp 22 xã/thị trấn thành phường. Toàn bộ mốc này được tách biệt độc lập trong `thay_doi_2026.csv`.

### 2.3. Bản quyền & Giấy phép sử dụng
- **Văn bản và dữ liệu nhà nước:** Căn cứ Điều 19 Luật Sở hữu trí tuệ Việt Nam, văn bản quy phạm pháp luật, văn bản hành chính của cơ quan nhà nước không thuộc đối tượng bảo hộ quyền tác giả.
- **Bộ mã nguồn và dữ liệu đối soát cộng đồng (`vietnam-address-kit`):** Được cấp phép theo giấy phép **MIT License** (ghi nhận tại tệp `data\raw\goc\LICENSE-vietnam-address-kit.txt`).
- **Tuyên bố minh bạch:** Báo cáo **không** khẳng định bộ dữ liệu là "Public Domain" một cách tuyệt đối, vì dữ liệu có sự cấu trúc hóa và biên tập của các tác giả cộng đồng theo giấy phép MIT. Người sử dụng cần tuân thủ điều khoản ghi nhận bản quyền MIT của tệp mã nguồn mở gốc.

---

## 3. QUY ƯỚC THIẾT KẾ DỮ LIỆU & CHUẨN HÓA

Nhằm phục vụ tối ưu cho thuật toán tách từ và chuẩn hóa NLP:
1. **Chuẩn hóa mã định danh (Codes):**
   - Giữ nguyên chuỗi định danh có chữ số `0` ở đầu (zero-padded string).
   - Cấp tỉnh: chuỗi 2 chữ số (`01`, `04`, `80`, `91`...).
   - Cấp huyện: chuỗi 3 chữ số (`001`, `018`, `794`, `900`...).
   - Cấp xã: chuỗi 5 chữ số (`00004`, `00556`, `27691`...).
2. **Quy ước tên và loại hình (Separation of Name and Type):**
   - **Tên lưu trong cột `ten_*` hoàn toàn KHÔNG kèm tiền tố loại hình**. Tên đầy đủ được tái tạo bằng công thức đồng nhất:  
     $$\text{Tên đầy đủ} = \text{loại} + \text{" "} + \text{tên}$$
   - **Đơn vị đánh số:** Tuân thủ triệt để quy ước trên để không làm mất tính tổng quát.
     - Phường đánh số: `loai_xa = "Phường"`, `ten_xa = "1"` $\rightarrow$ Tên đầy đủ: `Phường 1`.
     - Quận đánh số: `loai_huyen = "Quận"`, `ten_huyen = "1"` $\rightarrow$ Tên đầy đủ: `Quận 1`.
     - Các đơn vị khác: `loai_xa = "Xã"`, `ten_xa = "Cổ Bi"` $\rightarrow$ `Xã Cổ Bi`.
3. **Chuẩn hóa chính tả & Unicode:**
   - Sử dụng định dạng **Unicode NFC** trên 100% trường chuỗi.
   - Chuẩn hóa vị trí dấu thanh theo quy chuẩn mới của Bộ Giáo dục và Đào tạo:
     - Áp dụng cho các vần `oa`, `oe`, `uy` khi vần đó đứng **CUỐI** âm tiết (không có phụ âm cuối hay nguyên âm nào theo sau): dấu đặt trên nguyên âm thứ nhất `o`, `u` (`hoà` $\rightarrow$ `hòa`, `khoẻ` $\rightarrow$ `khỏe`, `thuỵ` $\rightarrow$ `thụy`, `hoá` $\rightarrow$ `hóa`, `hoè` $\rightarrow$ `hòe`, `xoá` $\rightarrow$ `xóa`...).
     - Nếu sau vần có phụ âm cuối (`n, ng, nh, c, ch, m, p, t`) hoặc bán âm cuối (`i`): dấu luôn nằm trên nguyên âm âm chính và **KHÔNG** được đổi (`Hoàng`, `Hoàn`, `Khoát`, `Thuyết`, `Toàn`, `Hoài`, `Khoái` giữ nguyên 100%).
     - Không đổi vần `uy` khi đi sau `qu` (`Quý`, `Quỳ`, `Quỹ` giữ nguyên).
     - Xử lý chuẩn hóa theo từng âm tiết độc lập (tách theo khoảng trắng và dấu gạch ngang), bảo toàn nguyên vẹn mọi ký tự khác.
   - Chuẩn hóa viết hoa các danh từ chỉ loại hình: `Thành phố`, `Thị xã`, `Thị trấn`, `Quận`, `Huyện`, `Đặc khu`, `Phường`, `Xã`.
4. **Quan hệ liên kết bảng chuyển đổi (`doi_chieu_xa_cu_moi.csv`):**
   - Bắt buộc lưu trữ đầy đủ các cột mã: `ma_xa_cu`, `ma_huyen_cu`, `ma_tinh_cu`, `ma_xa_moi`, `ma_tinh_moi`.
   - Mọi liên kết thực hiện bằng khóa mã, người dùng không cần ghép chuỗi hoặc nối theo tên.

---

## 4. BẢNG THỐNG KÊ SỐ LƯỢNG THỰC TẾ

| Tên bảng trong `data\clean\` | Số dòng dữ liệu | Số cột | Ý nghĩa danh mục | Khóa chính |
|---|:---:|:---:|---|---|
| `moi_tinh.csv` | 34 | 3 | Danh mục 34 tỉnh/thành phố mới (mốc 01/07/2025) | `ma_tinh` |
| `cu_tinh.csv` | 63 | 3 | Danh mục 63 tỉnh/thành phố cũ (trước 01/07/2025) | `ma_tinh` |
| `cu_huyen.csv` | 696 | 4 | Danh mục 696 huyện cũ (gồm 5 huyện đảo không có xã) | `ma_huyen` |
| `moi_tinh_xa.csv` | 3.321 | 6 | Danh mục 3.321 xã/phường/đặc khu mới (mốc 01/07/2025) | `ma_xa` |
| `cu_tinh_huyen_xa.csv` | 10.035 | 7 | Danh mục 10.035 xã/phường/thị trấn cũ trước sáp nhập | `ma_xa` |
| `doi_chieu_xa_cu_moi.csv` | 10.571 | 11 | Bảng đối chiếu chuyển đổi cũ sang mới | Cặp `(ma_xa_cu, ma_xa_moi)` |
| `thay_doi_2026.csv` | 25 | 6 | Các biến động ĐVHC phát sinh trong năm 2026 | `ma` |
| `sua_doi.csv` | 27 | 7 | Nhật ký đối soát ghi nhận các dòng sửa đổi cụ thể | - |
| `issues.csv` | 2 | 7 | Danh sách các trường hợp ngoại lệ hợp lệ | - |
| `can_xem_lai.csv` | 0 | 11 | Danh sách bản ghi cần xem lại (đã xử lý xong toàn bộ) | - |

---

## 5. CHI TIẾT CÁC SỬA ĐỔI, LÝ DO VÀ BẰNG CHỨNG ĐỐI SOÁT

Toàn bộ 27 sửa đổi cụ thể được ghi nhận chi tiết tại `data\clean\sua_doi.csv`. Dưới đây là các nhóm vấn đề trọng yếu đã được xác minh và xử lý triệt để:

### 5.1. Xử lý mã huyện trùng lặp 794 (Tân An) và 900 (Hà Tiên) trong `legacy-districts.json`
- **Hiện tượng nguồn:** `legacy-districts.json` có 698 bản ghi nhưng chỉ có 696 mã duy nhất:
  - Mã `794`: xuất hiện 2 lần với `provinceCode: 80` (Long An) và `provinceCode: 82` (Tiền Giang).
  - Mã `900`: xuất hiện 2 lần với `provinceCode: 91` (Kiên Giang) và `provinceCode: 89` (An Giang).
- **Xác minh pháp lý trước 01/07/2025:**
  - Căn cứ Quyết định 124/2004/QĐ-TTg: Thành phố Tân An là tỉnh lỵ của tỉnh Long An (mã tỉnh `80`). Tỉnh Tiền Giang (mã tỉnh `82`) có thành phố tỉnh lỵ là TP Mỹ Tho (mã huyện `815`), không có đơn vị nào tên Tân An.
  - Căn cứ Nghị quyết số 573/NQ-UBTVQH14: Thành phố Hà Tiên trực thuộc tỉnh Kiên Giang (mã tỉnh `91`). Tỉnh An Giang (mã tỉnh `89`) gồm TP Long Xuyên (`883`), TP Châu Đốc (`884`), TX Tân Châu (`886`), không có Thành phố Hà Tiên.
- **Xử lý:**
  - Loại bỏ bản ghi `794` gán nhầm tỉnh `82` và bản ghi `900` gán nhầm tỉnh `89`.
  - Trong `cu_tinh_huyen_xa.csv`:
    - Phường 4 Tân An (mã xã `27691`) trong raw bị gán nhầm `ma_tinh: 82, ten_tinh: Tiền Giang` $\rightarrow$ sửa thành `ma_tinh: 80, ten_tinh: Long An`.
    - Xã Tiên Hải Hà Tiên (mã xã `30781`) trong raw bị gán nhầm `ma_tinh: 89, ten_tinh: An Giang` $\rightarrow$ sửa thành `ma_tinh: 91, ten_tinh: Kiên Giang`.
  - Kết quả: Bảng `cu_huyen.csv` có đúng **696 mã huyện duy nhất**, không còn trùng lặp mã.

### 5.2. Bảo toàn 5 huyện đảo không có cấp xã trực thuộc và bãi bồi Kim Sơn
- **Hiện trạng:** Trước 01/07/2025, Việt Nam có 5 huyện đảo đặc thù không phân chia đơn vị hành chính cấp xã con gồm:
  1. Huyện Bạch Long Vĩ (mã `318`, TP Hải Phòng, mã tỉnh `31`).
  2. Huyện Cồn Cỏ (mã `471`, Tỉnh Quảng Trị, mã tỉnh `45`).
  3. Huyện Hoàng Sa (mã `498`, TP Đà Nẵng, mã tỉnh `48`).
  4. Huyện Lý Sơn (mã `536`, Tỉnh Quảng Ngãi, mã tỉnh `51`).
  5. Huyện Côn Đảo (mã `755`, Tỉnh Bà Rịa - Vũng Tàu, mã tỉnh `77`).
- **Xử lý:**
  - Bảo toàn độc lập 5 huyện này trong `cu_huyen.csv`. Không tự ý tạo xã giả để nhồi vào `cu_tinh_huyen_xa.csv`.
  - Trong `doi_chieu_xa_cu_moi.csv`: 5 huyện đảo và khu vực Bãi bồi ven biển Kim Sơn (`ma_huyen_cu: 376`, `ma_tinh_cu: 37`) được bảo toàn với `ma_xa_cu` để trống, nhưng điền đầy đủ `ma_huyen_cu`, `ma_tinh_cu`, `ma_xa_moi`, `ma_tinh_moi`.
  - Sửa lỗi huyện Cồn Cỏ: Trong file nguồn `legacy-districts.json` và mapping, Cồn Cỏ bị gán nhầm mã tỉnh cũ là `44` (Quảng Bình cũ / Quảng Trị mới). Căn cứ Nghị định 44/2004/NĐ-CP, Cồn Cỏ thuộc tỉnh Quảng Trị cũ (mã `45`). Đã hiệu chỉnh `ma_tinh_cu = 45`.

### 5.3. Sửa lỗi mã xã Đặng Xá (00553 $\rightarrow$ 00556) và gắn cờ `bi_chia`
- **Hiện tượng:** Dòng chuyển đổi từ Xã Đặng Xá (Gia Lâm, Hà Nội) sang Xã Thuận An (mã mới `00562`) trong `doi_chieu_xa_cu_moi.csv` ghi `ten_xa_cu: Xã Đặng Xá` nhưng lại mang `ma_xa_cu: 00553`.
- **Căn cứ đối soát:** Trong danh mục xã cũ, `00553` là mã của Xã Cổ Bi; `00556` là mã của Xã Đặng Xá. Trong tệp gốc `conversion-table.xlsx`, dòng chuyển đổi sang Xã Phù Đổng (00541) ghi đúng mã `00556`, dòng sang Thuận An bị lỗi typo gán nhầm mã 00553 của Cổ Bi ở dòng liền kề.
- **Xử lý:**
  - Sửa `ma_xa_cu` dòng này thành `00556`.
  - Xã Đặng Xá (00556) có 2 đích chuyển đổi: sang Xã Phù Đổng (00541) và sang Xã Thuận An (00562). Dòng sang Phù Đổng ban đầu chỉ ghi `Nhập một phần diện tích` $\rightarrow$ đã chuẩn hóa thêm tiền tố `bi_chia: Nhập một phần diện tích` theo đúng quy ước phân loại fan-out > 1, đồng thời bảo toàn trọn vẹn mô tả nguồn.

### 5.4. Chuẩn hóa loại hình xã Xuân Quang 3, Xuân Phước và Thị trấn Ngan Dừa
- **Mã 22108 (Xuân Quang 3) & 22111 (Xuân Phước):** Thuộc huyện miền núi Đồng Xuân, tỉnh Phú Yên. Trong `cu_tinh_huyen_xa.csv` bị ghi nhầm `loai_xa: Phường` $\rightarrow$ Đã sửa thành `loai_xa: Xã` (huyện Đồng Xuân chỉ có xã và thị trấn La Hai, không có phường).
- **Mã 31843 (Ngan Dừa):** Thị trấn huyện lỵ của huyện Hồng Dân, Bạc Liêu. Trong raw bị ghi `ten_xa: Thi trấn Ngan Dừa, loai_xa: Phường` $\rightarrow$ Đã sửa lỗi chính tả thiếu dấu nặng, tách loại khỏi tên: `ten_xa: Ngan Dừa, loai_xa: Thị trấn`.
- **Mã 24496 (Ea Kly):** Trong `doi_chieu_xa_cu_moi.csv`, tên xã mới bị mất dấu ngã ("Xa Ea Kly") $\rightarrow$ Đã sửa thành `Xã Ea Kly`.

### 5.5. Sửa lỗi đặt dấu thanh kiểu mới và đồng bộ đối chiếu tên xã cũ
- **Lỗi nhận diện và phân tích nguyên nhân:**  
  Trong bước chuẩn hóa dấu thanh kiểu mới trước đây, script sử dụng phép thay thế chuỗi con toàn cục một cách máy móc (`'hoà': 'hòa'`, `'khoá': 'khóa'`). Do âm tiết `Hoàng`, `Hoàn` chứa chuỗi con `Hoà`, `Khoát` chứa `Khoá`, `Hoài` chứa `Hoà`... dẫn tới làm hỏng toàn bộ các âm tiết có phụ âm cuối và bán âm cuối (`Hoàng` thành `Hòang`, `Hoàn Kiếm` thành `Hòan Kiếm`, `Hoàng Mai` thành `Hòang Mai`, `Khoát` thành `Khóat`, `Hoài Đức` thành `Hòai Đức`...).  
  Tổng cộng có đúng **340 ô** dữ liệu bị lỗi đặt sai dấu thanh trên 4 bảng clean:
  - `cu_huyen.csv`: 5 ô (`Hòan Kiếm`, `Hòang Mai`, `Hòang Su Phì`...).
  - `cu_tinh_huyen_xa.csv`: 128 ô.
  - `doi_chieu_xa_cu_moi.csv`: 188 ô.
  - `moi_tinh_xa.csv`: 19 ô.
- **Biện pháp kỹ thuật khắc phục:**
  1. Tái cấu trúc hoàn toàn hàm chuẩn hóa `normalize_tone()` và `normalize_syllable()`:
     - Tách văn bản thành các âm tiết độc lập (theo khoảng trắng và dấu gạch ngang).
     - Chỉ chuyển dấu sang nguyên âm thứ nhất khi âm tiết **kết thúc** bằng vần `oa`, `oe`, `uy` (`hoà` $\rightarrow$ `hòa`, `khoẻ` $\rightarrow$ `khỏe`, `thuỵ` $\rightarrow$ `thụy`, `hoá` $\rightarrow$ `hóa`, `hoè` $\rightarrow$ `hòe`, `xoá` $\rightarrow$ `xóa`).
     - Tuyệt đối giữ nguyên dấu trên nguyên âm âm chính khi có phụ âm cuối (`n, ng, nh, c, ch, m, p, t`) hoặc bán âm cuối (`i`): `Hoàng`, `Hoàn`, `Khoát`, `Thuyết`, `Toàn`, `Hoài`, `Khoái` giữ nguyên 100%.
     - Bảo toàn vần `uy` đi sau phụ âm đầu `qu` (`Quý`, `Quỳ`, `Quỹ` giữ nguyên).
  2. Sửa lỗi cắt nhầm tên xã `Xa Dung` (huyện Điện Biên Đông, tỉnh Điện Biên; mã cũ `03373`, mã mới `03208`):
     - Hàm `parse_ward_name_type()` trước đây có dòng cắt bỏ `Xa ` do nhầm tưởng là tiền tố loại hình, làm tên xã `Xa Dung` bị biến dạng thành `Dung`.
     - Đã loại bỏ logic sai này, khôi phục tên xã `Xa Dung` nguyên vẹn trên cả `cu_tinh_huyen_xa.csv`, `moi_tinh_xa.csv` và `doi_chieu_xa_cu_moi.csv`.
  3. Chuẩn hóa `ten_xa_cu` trong `doi_chieu_xa_cu_moi.csv` qua `normalize_tone()`:
     - Giúp chuyển đổi đồng bộ `Thuỷ` thành `Thủy` (`Liêm Thủy`, `Sơn Thủy`, `Thắng Thủy`, `Khánh Thủy`, `Ninh Thủy`) và `Thị Trấn Yên Minh` thành `Thị trấn Yên Minh`.
- **Kết quả xử lý triệt để ~92 dòng không khớp tên xã cũ trong `doi_chieu_xa_cu_moi.csv`:**
  - **85 dòng** do lỗi dấu thanh sai lệch giữa raw và clean (`Hoàng`/`Hòang`, `Khoái`/`Khóai`) $\rightarrow$ đã tự động khớp 100% sau khi sửa hàm chuẩn hóa dấu.
  - **5 dòng** do lệch kiểu dấu `Thuỷ`/`Thủy` $\rightarrow$ đã khớp 100% sau khi áp dụng chuẩn hóa dấu thanh cho `ten_xa_cu`.
  - **1 dòng** tên xã `Xa Dung` $\rightarrow$ đã khớp 100% sau khi sửa logic bóc tách loại hình xã.
  - **2 dòng** gán nhầm mã trong nguồn cộng đồng: Mỹ Hưng mang nhầm mã Hồng Quang, Phú Thịnh mang nhầm mã Công Đa. Sửa thành `01651` và `02482` theo `data/raw/goc/doi-chieu-2024-09-01.xls` (Sheet1 dòng 894, 1145), bổ sung hai xã vào danh mục cũ và giữ hai quan hệ nhập toàn bộ.

### 5.6. Xác minh và xử lý triệt để 2 dòng nghi vấn mâu thuẫn mã/tên (mã 01615 Cao Bằng và mã 02485 Tuyên Quang)
- **Mã 01615 (Xã Hồng Quang / Xã Mỹ Hưng, Huyện Quảng Hòa, Tỉnh Cao Bằng):**
  - **Căn cứ pháp lý:** Nghị quyết số 1657/NQ-UBTVQH15 ngày 16/06/2025 của Ủy ban Thường vụ Quốc hội về việc sắp xếp các đơn vị hành chính cấp xã của tỉnh Cao Bằng năm 2025:
    - Khoản 39 Điều 1: "Sắp xếp toàn bộ diện tích tự nhiên, quy mô dân số của các xã Hồng Quang, Cách Linh và Bế Văn Đàn thành xã mới có tên gọi là xã Bế Văn Đàn."
    - Khoản 38 Điều 1: "Sắp xếp toàn bộ diện tích tự nhiên và quy mô dân số của thị trấn Tà Lùng, thị trấn Hòa Thuận, xã Mỹ Hưng và xã Đại Sơn thành xã mới có tên gọi là xã Phục Hòa."
  - **Kết luận:** Mỹ Hưng có mã `01651` theo nguồn Cục Thống kê (Sheet1 dòng 894), bị thiếu trong danh mục cộng đồng và bị gán nhầm mã `01615` của Hồng Quang trong bảng chuyển đổi. Giữ quan hệ `01651 → 01648`; Hồng Quang vẫn `01615 → 01636`.
  - **Xử lý:** Bổ sung Mỹ Hưng `01651` vào danh mục xã cũ, sửa mã dòng đối chiếu sang Phục Hòa và ghi `Nhập toàn bộ`; Hồng Quang sang Bế Văn Đàn vẫn `Nhập toàn bộ`. Không xóa quan hệ.
- **Mã 02485 (Xã Công Đa / Xã Phú Thịnh, Huyện Yên Sơn, Tỉnh Tuyên Quang):**
  - **Căn cứ pháp lý:** Nghị quyết số 1684/NQ-UBTVQH15 ngày 16/06/2025 của Ủy ban Thường vụ Quốc hội về việc sắp xếp các đơn vị hành chính cấp xã của tỉnh Tuyên Quang năm 2025:
    - Khoản 27 Điều 1: "Sắp xếp toàn bộ diện tích tự nhiên, quy mô dân số của các xã Đạo Viện, Công Đa và Trung Sơn thành xã mới có tên gọi là xã Trung Sơn."
    - Khoản 28 Điều 1: "Sắp xếp toàn bộ diện tích tự nhiên, quy mô dân số của xã Phú Thịnh, xã Tiến Bộ và một phần diện tích tự nhiên, quy mô dân số của xã Thái Bình thành xã mới có tên gọi là xã Thái Bình."
  - **Kết luận:** Phú Thịnh có mã `02482` theo nguồn Cục Thống kê (Sheet1 dòng 1145, ghi "Đóng mã do sáp nhập vào xã Thái Bình"), bị thiếu trong danh mục cộng đồng và bị gán nhầm mã `02485` của Công Đa. Giữ quan hệ `02482 → 02494`; Công Đa vẫn `02485 → 02458`.
  - **Xử lý:** Bổ sung Phú Thịnh `02482` vào danh mục xã cũ, sửa mã dòng đối chiếu sang Thái Bình và ghi `Nhập toàn bộ`; Công Đa sang Trung Sơn vẫn `Nhập toàn bộ`. Không xóa quan hệ.

### 5.7. Hiệu chỉnh loại hình cấp tỉnh về đúng mốc 01/07/2025 (Quảng Ninh 22, Bắc Ninh 24, Đồng Nai 75)
- **Hiện tượng và nguyên nhân:**
  Trong file nguồn cộng đồng `current-provinces.json`, tác giả repo `vietnam-address-kit` đã cập nhật trước các Nghị quyết năm 2026 của Quốc hội khóa XVI nâng cấp 3 tỉnh Quảng Ninh, Bắc Ninh, Đồng Nai lên thành phố trực thuộc Trung ương, gán trường `"type": "city"`. Logic trước đây của script khi sinh `moi_tinh.csv` căn cứ vào `type == 'city'` nên gán nhầm loại hình 3 tỉnh này thành `Thành phố`, gây lệch mốc mục tiêu **01/07/2025** và mâu thuẫn với `moi_tinh_xa.csv` (ghi `Tỉnh`) và `doi_chieu_xa_cu_moi.csv` (ghi `Tỉnh`).
- **Căn cứ xác minh mốc 01/07/2025:**
  1. **Quyết định số 19/2025/QĐ-TTg ngày 30/06/2025** của Thủ tướng Chính phủ: Tại thời điểm 01/07/2025, toàn quốc sắp xếp còn 34 tỉnh/thành, trong đó chỉ có đúng **6 Thành phố trực thuộc Trung ương** (Hà Nội, Hải Phòng, Huế, Đà Nẵng, TP.HCM, Cần Thơ); 28 đơn vị còn lại là **Tỉnh** (bao gồm Quảng Ninh mã `22`, Bắc Ninh mã `24`, Đồng Nai mã `75`).
  2. **Bảng chuyển đổi quốc gia gốc:** `data/raw/goc/conversion-table.xlsx`, sheet `Tổng hợp_không merge `, cột A:
     - Ô A2537: `Tỉnh Quảng Ninh (22)`
     - Ô A2722: `Tỉnh Bắc Ninh (24)`
     - Ô A8114: `Tỉnh Đồng Nai (75)`
  3. **Tệp dữ liệu gốc:** `data/raw/moi_tinh_xa.csv` ghi rõ `loai_tinh: Tỉnh` cho cả 3 mã này.
  4. Các Nghị quyết nâng cấp 3 tỉnh lên Thành phố trực thuộc TW (`30/2026/QH16`, `36/2026/QH16`, `39/2026/QH16`) có hiệu lực trong năm 2026 và đã được tách riêng vào `thay_doi_2026.csv`.
- **Biện pháp xử lý và kiểm soát tự động:**
  - Sửa logic sinh `moi_tinh.csv` trong `clean_and_validate.py`: Khóa cứng danh sách 6 thành phố trực thuộc Trung ương tại mốc 01/07/2025 (`01`, `31`, `46`, `48`, `79`, `92`); toàn bộ 28 đơn vị còn lại nhận `loai_tinh = 'Tỉnh'`.
  - Ghi nhận 3 bản ghi sửa đổi vào `sua_doi.csv` (tổng hiện tại 27 bản ghi, gồm 2 bản ghi bổ sung xã cũ).
  - Bổ sung 2 kiểm tra tự động nghiêm ngặt trong `validate_all()`:
    + `moiTinhConsistency`: Kiểm tra 100% khớp `loai_tinh` và `ten_tinh` giữa `moi_tinh.csv` và `moi_tinh_xa.csv`.
    + `asOf2025CentralCities`: Kiểm tra đúng 6 Thành phố trực thuộc TW; nếu có bất kỳ tỉnh nào khác (đặc biệt 22, 24, 75) mang loại `Thành phố` thì validation lập tức nhận kết quả FAIL.

---

## 6. BẢO TOÀN DỮ LIỆU & THỐNG KÊ XÃ ĐA ĐÍCH (FAN-OUT > 1)

Một yêu cầu cốt lõi của bài toán là bảo toàn toàn bộ các xã bị phân rã sang nhiều đơn vị hành chính mới để mô hình NLP có đủ căn cứ gán cờ `xa_bi_chia`:

- **Tổng số mã xã cũ bị chia tách (fan-out > 1):** **440 mã xã**. Sửa mã Mỹ Hưng và Phú Thịnh thay vì xóa dòng; cả hai xã này, Hồng Quang `01615` và Công Đa `02485` đều chỉ có một đích, với quan hệ `Nhập toàn bộ`.
- **Tổng số dòng chuyển đổi của các xã đa đích:** **970 dòng**.
- **Phân bổ chi tiết các ghi chú và cờ phân loại:**
  1. `bi_chia`: 823 dòng.
  2. `bi_chia: Nhập một phần diện tích`: 82 dòng.
  3. `bi_chia: Nhập một phần diện tích, toàn bộ dân số`: 58 dòng.
  4. `bi_chia: Nhập một phần dân số`: 2 dòng.
  5. `bi_chia: Nhập toàn bộ diện tích`: 1 dòng (xã Kỳ Lợi, Hà Tĩnh).
  6. `bi_chia: Nhâp một phần diện tích`: 1 dòng.
  7. `bi_chia: Phần còn lại sau khi tách một phần vào xã Canh Vinh`: 1 dòng.
  8. `bi_chia: Đổi tên từ một phần Phường 15`: 1 dòng.
  9. `bi_chia: Đổi tên, đổi loại hình từ một phần thị trấn Lai Uyên`: 1 dòng.

> [!NOTE]
> Nhóm 58 dòng `bi_chia: Nhập một phần diện tích, toàn bộ dân số` mang ý nghĩa nghiệp vụ cực kỳ quan trọng: toàn bộ cư dân thực tế được chuyển về xã mới nhận dân cư; xã còn lại chỉ tiếp nhận đất đai/diện tích tự nhiên không có dân cư.

---

## 7. KẾT QUẢ XÁC MINH VÀ XỬ LÝ DỨT ĐIỂM CÁC BẢN GHI NGHI VẤN

Báo cáo giữ nguyên tắc **không đoán mò, chỉ sửa đổi khi tìm được văn bản chính thức làm căn cứ**. Hai trường hợp nghi vấn trước đây tại `data\clean\issues.csv` và `data\clean\can_xem_lai.csv` đã được xác minh toàn diện và xử lý triệt để:

### 7.1. Xác minh Mã 01615 (Xã Hồng Quang / Xã Mỹ Hưng - Huyện Quảng Hòa, Tỉnh Cao Bằng)
- **Văn bản pháp lý xác minh:** Nghị quyết số 1657/NQ-UBTVQH15 ngày 16/06/2025 của Ủy ban Thường vụ Quốc hội về việc sắp xếp các đơn vị hành chính cấp xã của tỉnh Cao Bằng năm 2025 (`https://thuvienphapluat.vn`).
  - **Khoản 39 Điều 1:** Sắp xếp toàn bộ diện tích tự nhiên, quy mô dân số của các xã Hồng Quang, Cách Linh và Bế Văn Đàn thành xã mới có tên gọi là xã Bế Văn Đàn.
  - **Khoản 38 Điều 1:** Sắp xếp toàn bộ diện tích tự nhiên và quy mô dân số của thị trấn Tà Lùng, thị trấn Hòa Thuận, xã Mỹ Hưng và xã Đại Sơn thành xã mới có tên gọi là xã Phục Hòa.
- **Kết luận:** Mỹ Hưng có mã `01651` theo nguồn Cục Thống kê (Sheet1 dòng 894), bị thiếu trong danh mục cộng đồng và bị gán nhầm mã `01615` của Hồng Quang trong bảng chuyển đổi. Giữ quan hệ `01651 → 01648`; Hồng Quang vẫn `01615 → 01636`.
- **Xử lý:** Bổ sung Mỹ Hưng `01651` vào danh mục xã cũ, sửa mã dòng đối chiếu sang Phục Hòa và ghi `Nhập toàn bộ`; Hồng Quang sang Bế Văn Đàn vẫn `Nhập toàn bộ`. Không xóa quan hệ.

### 7.2. Xác minh Mã 02485 (Xã Công Đa / Xã Phú Thịnh - Huyện Yên Sơn, Tỉnh Tuyên Quang)
- **Văn bản pháp lý xác minh:** Nghị quyết số 1684/NQ-UBTVQH15 ngày 16/06/2025 của Ủy ban Thường vụ Quốc hội về việc sắp xếp các đơn vị hành chính cấp xã của tỉnh Tuyên Quang năm 2025 (`https://thuvienphapluat.vn`).
  - **Khoản 27 Điều 1:** Sắp xếp toàn bộ diện tích tự nhiên, quy mô dân số của các xã Đạo Viện, Công Đa và Trung Sơn thành xã mới có tên gọi là xã Trung Sơn.
  - **Khoản 28 Điều 1:** Sắp xếp toàn bộ diện tích tự nhiên, quy mô dân số của xã Phú Thịnh, xã Tiến Bộ và một phần diện tích tự nhiên, quy mô dân số của xã Thái Bình thành xã mới có tên gọi là xã Thái Bình.
- **Kết luận:** Phú Thịnh có mã `02482` theo nguồn Cục Thống kê (Sheet1 dòng 1145, ghi "Đóng mã do sáp nhập vào xã Thái Bình"), bị thiếu trong danh mục cộng đồng và bị gán nhầm mã `02485` của Công Đa. Giữ quan hệ `02482 → 02494`; Công Đa vẫn `02485 → 02458`.
- **Xử lý:** Bổ sung Phú Thịnh `02482` vào danh mục xã cũ, sửa mã dòng đối chiếu sang Thái Bình và ghi `Nhập toàn bộ`; Công Đa sang Trung Sơn vẫn `Nhập toàn bộ`. Không xóa quan hệ.

### 7.3. Tình trạng hiện tại của `can_xem_lai.csv` và `issues.csv`
- `can_xem_lai.csv`: **0 bản ghi** (tất cả các dòng mâu thuẫn mã/tên đã được giải quyết dứt điểm có căn cứ pháp lý rõ ràng).
- `issues.csv`: **2 bản ghi**, chỉ lưu 2 trường hợp ngoại lệ địa lý hợp lệ đã được xác minh (Khu vực bãi bồi ven biển Kim Sơn và 5 Huyện đảo không có cấp xã trực thuộc).

---

## 8. KẾT QUẢ KIỂM CHỨNG TỰ ĐỘNG (VALIDATION REPORT)

Trích xuất kết quả tự động từ tệp `data\clean\validation.json`:

```json
{
  "status": "PASS",
  "asOfDate": "2025-07-01",
  "statistics": {
    "moi_tinh_count": 34,
    "cu_tinh_count": 63,
    "cu_huyen_count": 696,
    "moi_tinh_xa_count": 3321,
    "cu_tinh_huyen_xa_count": 10035,
    "doi_chieu_count": 10571,
    "thay_doi_2026_count": 25,
    "sua_doi_count": 27
  },
  "primaryKeyDuplicates": {
    "moi_tinh": { "duplicate_count": 0, "duplicate_keys": [] },
    "cu_tinh": { "duplicate_count": 0, "duplicate_keys": [] },
    "cu_huyen": { "duplicate_count": 0, "duplicate_keys": [] },
    "moi_tinh_xa": { "duplicate_count": 0, "duplicate_keys": [] },
    "cu_tinh_huyen_xa": { "duplicate_count": 0, "duplicate_keys": [] }
  },
  "foreignKeyIntegrity": {
    "cu_tinh_huyen_xa_to_cu_tinh": [],
    "cu_tinh_huyen_xa_to_cu_huyen": [],
    "moi_tinh_xa_to_moi_tinh": [],
    "doi_chieu_to_cu_xa": [],
    "doi_chieu_to_cu_huyen": [],
    "doi_chieu_to_cu_tinh": [],
    "doi_chieu_to_moi_xa": [],
    "doi_chieu_to_moi_tinh": []
  },
  "missingRequiredFields": {
    "moi_tinh": 0,
    "cu_tinh": 0,
    "cu_huyen": 0,
    "moi_tinh_xa": 0,
    "cu_tinh_huyen_xa": 0,
    "doi_chieu": 0
  },
  "duplicateConversionPairs": 0,
  "coverage": {
    "old_wards_total": 10035,
    "old_wards_covered_in_doi_chieu": 10035,
    "old_wards_coverage_rate": "100.00%",
    "new_wards_total": 3321,
    "new_wards_covered_in_doi_chieu": 3321,
    "new_wards_coverage_rate": "100.00%"
  },
  "multiDestinationWards": {
    "total_multi_dest_wards": 440,
    "total_multi_dest_rows": 970,
    "notes_breakdown": {
      "bi_chia": 823,
      "bi_chia: Nhập một phần diện tích": 82,
      "bi_chia: Nhập một phần diện tích, toàn bộ dân số": 58,
      "bi_chia: Nhâp một phần diện tích": 1,
      "bi_chia: Nhập một phần dân số": 2,
      "bi_chia: Nhập toàn bộ diện tích": 1,
      "bi_chia: Phần còn lại sau khi tách một phần vào xã Canh Vinh": 1,
      "bi_chia: Đổi tên từ một phần Phường 15": 1,
      "bi_chia: Đổi tên, đổi loại hình từ một phần thị trấn Lai Uyên": 1
    }
  },
  "unresolvedIssues": [],
  "reviewFiles": [
    "data/clean/issues.csv",
    "data/clean/can_xem_lai.csv",
    "data/clean/sua_doi.csv"
  ],
  "invalidTonePlacement": {
    "error_count": 0,
    "invalid_cells": []
  },
  "rawComparison": {
    "unexplained_discrepancy_count": 0,
    "discrepancies": []
  },
  "doiChieuNameConsistency": {
    "unexplained_mismatch_count": 0,
    "mismatches": [],
    "can_xem_lai_documented_count": 0
  },
  "toneNormalizationFix": {
    "description": "Chuẩn hóa dấu thanh kiểu mới theo âm tiết cho vần oa, oe, uy đứng cuối; bảo toàn âm tiết có phụ âm cuối",
    "cells_repaired_count": 340,
    "cells_repaired_breakdown": {
      "moi_tinh_xa.csv": 19,
      "cu_huyen.csv": 5,
      "cu_tinh_huyen_xa.csv": 128,
      "doi_chieu_xa_cu_moi.csv": 188
    },
    "status": "RESOLVED"
  }
}
```

### 8.1. Chi tiết kết quả các kiểm tra bổ sung mới
1. **Kiểm tra dấu thanh sai vị trí (`invalidTonePlacement`):**
   - Tiêu chí: Quét toàn bộ ô dữ liệu chuỗi trong tất cả các tệp CSV; không còn bất kỳ âm tiết nào có `o` hoặc `u` mang dấu thanh rồi đi liền sau là `a, e, y` và phụ âm cuối (`n, ng, nh, c, ch, m, p, t`) hoặc bán âm cuối (`i`) như `Hòang`, `Hòan`, `Thúyết`, `Khóat`, `Khóai`.
   - Kết quả: **0 lỗi** (`error_count = 0`). Toàn bộ 340 ô bị lỗi trước đây đã được khắc phục hoàn toàn.
2. **Kiểm tra so sánh toàn diện với dữ liệu gốc `data\raw` (`rawComparison`):**
   - Tiêu chí: Sau khi loại bỏ toàn bộ dấu thanh, dấu mũ, dấu móc và chuyển về chữ thường, mọi tên đơn vị hành chính trong `data\clean` phải trùng khớp 100% với tên gốc tương ứng cùng mã trong `data\raw`. Bất kỳ sự khác biệt nào ngoài danh sách các mã đã phê duyệt trong `sua_doi.csv` đều bị coi là lỗi.
   - Kết quả: **0 sai lệch ngoài kiểm soát** (`unexplained_discrepancy_count = 0`). Đảm bảo dữ liệu sạch chỉ điều chỉnh vị trí dấu thanh theo quy chuẩn mới, bảo toàn 100% nội dung chữ cái gốc.
3. **Kiểm tra khớp tên xã trong `doi_chieu_xa_cu_moi.csv` (`doiChieuNameConsistency`):**
   - Tiêu chí: Tên xã cũ và xã mới trong bảng đối chiếu (sau khi bóc tách tiền tố loại hình `Xã`, `Phường`, `Thị trấn`, `Đặc khu`) phải khớp đúng tuyệt đối với tên trong danh mục xã cũ (`cu_tinh_huyen_xa.csv`) và danh mục xã mới (`moi_tinh_xa.csv`) theo mã.
   - Kết quả: **0 sai lệch ngoài kiểm soát** (`unexplained_mismatch_count = 0`). Toàn bộ mâu thuẫn mã/tên đã được giải quyết triệt để (`can_xem_lai_documented_count = 0`). Khớp chính xác 100% tên đơn vị hành chính giữa các danh mục.
4. **Kiểm tra nhất quán tỉnh giữa `moi_tinh.csv` và `moi_tinh_xa.csv` (`moiTinhConsistency`):**
   - Tiêu chí: Mọi `ma_tinh` phải khớp 100% cả về `loai_tinh` và `ten_tinh` giữa bảng tỉnh mới và bảng xã mới.
   - Kết quả: **0 sai lệch** (`discrepancy_count = 0`).
5. **Kiểm tra chuẩn hóa mốc hiệu lực 01/07/2025 (`asOf2025CentralCities`):**
   - Tiêu chí: Đúng 6 Thành phố trực thuộc Trung ương (`01`, `31`, `46`, `48`, `79`, `92`); toàn bộ 28 đơn vị cấp tỉnh còn lại phải có `loai_tinh == 'Tỉnh'`. Không được lẫn bất kỳ mốc nâng cấp nào của năm 2026 vào danh mục chính.
   - Kết quả: **PASS**, đủ 6 thành phố, 0 tỉnh sai loại hình (`discrepancy_count = 0`).

---

## 9. HƯỚNG DẪN TÁI TẠO BỘ DỮ LIỆU SẠCH (REPRODUCIBILITY)

Để tái tạo toàn bộ kết quả từ thư mục `data\raw` và chạy kiểm tra tự động, thực hiện lệnh:

```bash
# Sử dụng Python 3.12 (hoặc Python 3.11 bất kỳ có sẵn trên máy)
py -3.12 D:\nlp_chuan_hoa_dia_chi\data\clean\scripts\clean_and_validate.py
```

Lệnh trên sẽ:
1. Đọc dữ liệu từ `data\raw` (chế độ chỉ đọc, không sửa đổi).
2. Xử lý chuẩn hóa theo đúng các quy tắc pháp lý và kỹ thuật đã nêu.
3. Sinh lại toàn bộ các tệp CSV và JSON trong `data\clean\`.
4. Thực hiện validation toàn diện và in thông báo kiểm tra ra console.
