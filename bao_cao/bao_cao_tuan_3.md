# Báo cáo tiến độ tuần 3

**Đề tài:** Xây dựng hệ thống chuẩn hóa địa chỉ tiếng Việt theo đơn vị hành chính mới sau sáp nhập 2025
**Môn:** Xử lý ngôn ngữ tự nhiên, lớp KHMT K22A
**Mã nguồn:** https://github.com/AnDpTri/nlp_chuan_hoa_dia_chi

---

## 1. Tóm tắt

| Hạng mục | Trạng thái |
|---|---|
| Đề tài, phạm vi, đặc tả | Xong |
| Dữ liệu hành chính (cũ, mới, đối chiếu) | Xong, còn 1 lỗi loại tỉnh |
| Tập test 400 địa chỉ thật | Có nhãn sơ bộ, chưa duyệt tay |
| Thiết kế hệ thống | Sơ bộ |
| Khung mã nguồn | Xong, chưa cài đặt |
| Dữ liệu huấn luyện | Chưa làm |
| Code hệ thống, chấm điểm | Chưa làm |

## 2. Đã làm

### 2.1. Đề tài và phạm vi
- Viết đặc tả: `bai_toan.md`.
- Quyết định:
  - Chuẩn hóa là mục tiêu chính. Phân loại có sẵn sau khi chuẩn hóa.
  - Chuyển cũ sang mới đến cấp xã. Huyện chỉ dùng để xác định, không xuất ra.
  - Số nhà, ngõ, thôn/xóm, đường không đổi theo luật, chỉ chuẩn hóa cách viết.
  - Thiếu thì để trống, không chắc thì gắn cờ.
  - Offline, không LLM, không API. Tốc độ quan trọng ngang độ chính xác.

### 2.2. Dữ liệu hành chính
Nguồn: danh mục Tổng cục Thống kê, bảng chuyển đổi theo QĐ 19/2025/QĐ-TTg, nghị quyết UBTVQH (qua bộ tổng hợp `vietnam-address-kit`). Chi tiết: `data/raw/NGUON.md`.

| Bộ dữ liệu | Số lượng |
|---|---|
| Danh mục mới (mốc 1/7/2025) | 34 tỉnh, 3.321 xã |
| Danh mục cũ | 63 tỉnh, 696 huyện, 10.033 xã |
| Đối chiếu xã cũ sang mới | 10.569 dòng, 440 xã cũ bị chia |

### 2.3. Làm sạch dữ liệu
Script: `data/clean/scripts/clean_and_validate.py`. Không sửa dữ liệu gốc, mọi sửa đổi ghi căn cứ trong `sua_doi.csv`.

Lỗi đã sửa:
- Tên tỉnh Quảng Trị ghi hai kiểu, đếm ra 64 tỉnh.
- TP Tân An (Long An) bị gán sang Tiền Giang.
- Tên mất dấu, sai loại đơn vị, hoa thường không thống nhất.
- Lỗi đặt dấu do chính script gây ra (Hoàng thành Hòang). Đã sửa, thêm kiểm tra.
- 2 dòng gán nhầm mã ở Cao Bằng, Tuyên Quang. Xác minh theo NQ 1657/NQ-UBTVQH15 và 1684/NQ-UBTVQH15: xóa 2 dòng thừa, Hồng Quang và Công Đa là nhập toàn bộ.

Kiểm tra đạt: không trùng mã, khóa ngoại hợp lệ, xã cũ nào cũng có đích, xã mới nào cũng có nguồn, mỗi tỉnh cũ vào đúng một tỉnh mới, bỏ dấu thì tên khớp bản gốc.

### 2.4. Tập test
Nguồn: OpenStreetMap, bản trích Geofabrik ngày 24/10/2026, giấy phép ODbL. Chỉ địa điểm công khai, không nhà dân. Chi tiết: `data/test/README.md`.

| Chỉ số | Giá trị |
|---|---|
| Tổng | 400 |
| Chuỗi nguyên văn (`addr:full`) | 150 |
| Ghép từ thẻ địa chỉ | 250 |
| Số tỉnh mới có mặt | 32/34 |
| Ghi theo địa giới cũ | 361 |
| Có viết tắt | 100 |
| Thuộc xã bị chia | 33 |
| Tự động khớp / cần duyệt | 168 / 232 |

Cách gán nhãn: Gemini (qua agy) tách phần chữ, code tra danh mục để gắn mã. Gemini không gắn mã. **Nhãn là sơ bộ, phải duyệt tay trước khi chấm điểm.**

### 2.5. Công trình liên quan
- Thư viện: `vietnamadminunits`, `vietnam-address-converter`, `vietnamese-address-parser`, parser của underthesea.
- API thương mại: TrackAsia, Vietmap.
- Nhận xét: đều dựa trên luật và tra từ điển, nhiều cái cần đầu vào sạch. Chưa thấy công trình học thuật dùng học máy.
- Dùng hai thư viện đầu làm mốc so sánh.

### 2.6. Thiết kế sơ bộ
- Pipeline: tiền xử lý → sinh ứng viên → ghép đường đi hợp lệ trên cây hành chính → tách số nhà/ngõ/thôn/đường → chuyển cũ sang mới → sinh đầu ra.
- Ý tưởng chính: giải cả địa chỉ cùng lúc, chọn tổ hợp thành phần tạo thành đường đi có thật trong cây. Ví dụ "cg" đi với "hn" thì là Cầu Giấy, Hà Nội.
- Cấu trúc dữ liệu: trie + hai cây hành chính (cũ, mới) có cạnh đối chiếu.
- Mô hình: logistic regression chấm điểm đường đi, CRF tách số nhà/ngõ/thôn/đường. Nâng lên LightGBM nếu cần.
- Python. Chạy được trước, đo, rồi tối ưu.
- Khung mã nguồn: `src/`, mỗi bước một module, đầu vào/đầu ra cố định.

## 3. Vấn đề

1. **Loại tỉnh lẫn mốc 2026:** `data/clean/moi_tinh.csv` ghi Quảng Ninh, Bắc Ninh, Đồng Nai là "Thành phố". Mốc 1/7/2025 phải là "Tỉnh". Cần sửa script.
2. **Tập test chưa duyệt:** 0/400 dòng có người duyệt.
3. **Tập test lệch:** 250 dòng ghép từ thẻ, không phải người gõ. Thiên về đô thị và cơ sở kinh doanh. Chỉ 10 dòng không dấu.
4. **Xã bị chia:** văn bản phần lớn chỉ ghi "nhập một phần", không rõ thôn/xóm nào về đâu. Nhiều khả năng chỉ gắn cờ được.

## 4. Kế hoạch tuần 4

1. Duyệt tay tập test, ưu tiên 232 dòng cần duyệt. Hai người duyệt chéo một phần.
2. Sửa loại tỉnh về mốc 1/7/2025.
3. Viết script chấm điểm.
4. Chạy hai thư viện mốc trên tập test.
5. Làm bản đơn giản chạy được từ đầu đến cuối (trie, cây, điểm đặt tay).
6. Dữ liệu huấn luyện từ ~27 nghìn địa chỉ OSM còn lại, loại các địa chỉ đã có trong tập test.
7. Chia việc trên Trello.
