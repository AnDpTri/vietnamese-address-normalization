# Quy chuẩn đánh giá

Mọi số đo báo cáo, mọi quyết định đổi mô hình, từ điển, luật hay cấu hình **chỉ dùng bộ này**. Các script đo cũ trong `danh_gia/` và `danh_gia/v3/` vẫn chạy được nhưng không còn là căn cứ quyết định.

```bash
PY=.venv-neural/Scripts/python.exe
$PY -X utf8 -B -m danh_gia.chuan chay <ten> [--cnn ..] [--ranker ..] [--tu-dien ..] [--tap dev_that,dev_sinh,bo_kho,test400,vang]
$PY -X utf8 -B -m danh_gia.chuan cham <ten>                  # báo cáo theo tập và theo nhóm
$PY -X utf8 -B -m danh_gia.chuan so_sanh <ten_dang_dung> <ten_de_xuat>   # so cặp + phán quyết + từng câu đổi
```

Kết quả ở `rieng/danh_gia_chuan/` (không lên git vì chứa đầu ra trên đáp án kín). Pipeline luôn dựng qua `src/cau_hinh.tao_bo_chuan_hoa()`, tức đúng cấu hình đang chạy trên web; `meta.json` ghi commit và mã băm của CNN, ranker, từ điển.

## 1. Tập dữ liệu và vai trò

| Tập | Nội dung | Vai trò | Dùng để quyết định? |
|---|---|---|---|
| `dev_that` | 400 địa chỉ OSM thật trong dev, nhãn máy rồi sửa | **chọn**: số chính | Có |
| `dev_sinh` | 1.200 địa chỉ sinh từ danh mục | hồi quy | Chỉ để loại (không được kém đi) |
| `bo_kho` | 1.500 biến thể bẩn (gõ sai, không dấu, viết tắt, ghi chú giao hàng...) | độ bền | Để loại; tốt hơn chỉ cho "nhận yếu" |
| `test400` | 400 địa chỉ OSM thật, nhãn AI **chưa người duyệt**, đã bị mở nhiều lần | tham khảo | Không |
| `vang` | 300 địa chỉ thật **ngoài OSM** (cổng dữ liệu mở, Bộ Y tế, Sở Y tế), 25 tỉnh, 130 có thôn/bản; chỉ dòng người đã duyệt | xác nhận | Không dùng hằng ngày; chạy khi chốt phiên bản |

Không bao giờ gộp các tập thành một con số. Số đặt ở đầu báo cáo là `dev_that`, kèm khoảng tin cậy.

## 2. Quy ước chấm (một quy ước cho mọi tập)

- Trường chi tiết (số nhà, ngõ, thôn, đường): bỏ dấu, thường hóa, bỏ dấu câu. Chữ loại đầu (Số; Ngõ/Ngách/Hẻm/Kiệt; Thôn/Xóm/Ấp/Bản/Tổ dân phố...; Đường/Phố/Đại lộ) tách riêng: **tên phải trùng**, chữ loại chỉ bị bắt lỗi khi cả hai bên có và khác nhóm (Đường = Phố = Đại lộ; TDP = Tổ dân phố). "Tháng Tám" = "Tháng 8".
- Mã xã, mã tỉnh: đúng mã. Vàng để trống mã xã nghĩa là **phải để trống** (xã cũ bị chia không phân giải được, hoặc không đủ căn cứ).
- Pipeline chạy đúng cấu hình sản phẩm cho mọi tập (không còn đổi `tien_to_mac_dinh` theo tập); khác biệt quy ước ghi nhãn được bộ chấm xử lý.

## 3. Chỉ số (báo theo từng tập và từng nhóm)

| Chỉ số | Ý nghĩa |
|---|---|
| Đủ 6 trường % (KTC 95% Wilson) | Số nhà, ngõ, thôn, đường, mã xã, mã tỉnh đều đúng |
| Từng trường % | |
| **Khẳng định sai mã xã** (số, %, cận trên KTC) | Trả mã xã khác vàng, hoặc trả mã khi phải để trống. Chỉ số an toàn số 1 |
| Chính xác khi khẳng định / độ phủ mã xã | Trong các câu có trả mã, bao nhiêu đúng; trong các câu vàng có mã, bao nhiêu có trả |
| **Điền thừa chi tiết** (số câu, trong đó đường) | Điền số nhà/ngõ/thôn/đường khi vàng để trống, ví dụ bịa "Đường Hoa" từ "gặp chị Hoa" |
| Xã cũ bị chia | Vàng phân giải được: đúng mã %. Vàng phải để trống: để trống đúng %, gắn cờ `xa_bi_chia` %, danh sách ứng viên phủ đủ đáp án % |
| Tốc độ | Trung vị, p95 ms/câu (một luồng CPU) |

Nhóm: `that`/`sinh`, `do_thi`/`nong_thon` (theo loại xã vàng), `dia_chi_cu` (chuyển đổi cũ→mới), `xa_bi_chia`, `co_thon`, `co_duong`, `khong_xac_dinh_xa`, `nhieu_*` (bộ khó), `nhan_*` (test400).

## 4. So sánh và luật chấp nhận

So cặp trên cùng câu bằng McNemar chính xác (đếm câu A đúng B sai và A sai B đúng) cho ba phép đo: đủ 6 trường, không khẳng định sai, không điền thừa. Kết luận mỗi ô: TỐT HƠN / KÉM HƠN (p < 0,05) hoặc KHÔNG PHÂN BIỆT.

Phán quyết (tự in ra; `test400` và `vang` không tham gia):

1. **LOẠI**: kém hơn có ý nghĩa ở bất kỳ phép đo nào trên `dev_that`, `dev_sinh` hoặc `bo_kho`.
2. **NHẬN (mạnh)**: không bị loại và `dev_that` tốt hơn có ý nghĩa.
3. **NHẬN (yếu)**: không bị loại, chỉ tốt hơn có ý nghĩa ở `dev_sinh`/`bo_kho`. Phải đọc các câu đổi kết quả và ghi lý do trong commit.
4. **TRUNG TÍNH**: không có khác biệt có ý nghĩa. Giữ bản đang dùng, trừ khi có lý do ngoài số đo (ghi rõ).

Mỗi lần nhận một thay đổi: ghi phán quyết, các số chính và lý do vào commit; chạy `vang` khi chốt phiên bản để báo cáo.

## 5. Giới hạn đã biết (đọc số cho đúng)

- **Độ nhạy thấp**: với 400 câu, KTC 95% rộng khoảng ±3 điểm; chênh dưới khoảng 2 điểm thường không phân biệt được. 300 câu vàng còn rộng hơn (±5 điểm ở mức 70%). Muốn thấy cải tiến nhỏ phải tăng cỡ tập.
- `dev_that` đã được dùng để chọn cấu hình nhiều lần: không còn là phép đo độc lập.
- `bo_kho` cùng nguồn agy với dữ liệu train: thiên về những gì train đã có.
- `test400`: nhãn AI chưa duyệt; 75 câu `khong_xac_dinh_xa` là nơi nhãn để trống vì thận trọng, nên "khẳng định sai" ở nhóm đó có thể là đúng thật.
- Quy ước chấm là một lựa chọn: coi Đường = Phố và bỏ qua chữ loại thiếu có thể che lỗi chữ loại.
- Tập vàng thiên về địa chỉ tổ chức (doanh nghiệp, cơ sở y tế) và các tỉnh có cổng dữ liệu mở (Sơn La, Lạng Sơn, Đắk Lắk...), không đại diện địa chỉ hộ dân.

## 6. Số nền hiện tại (05/11/2026, `char_v3_tc` + `tu_dien_train`)

| Tập | Đủ 6 trường | Khẳng định sai mã xã | Điền thừa |
|---|---|---|---|
| dev_that (400) | **86,8%** (83,1–89,7) | 12 (3,0%) | 11 |
| dev_sinh (1.200) | 97,2% (96,2–98,0) | 0 | 7 |
| bo_kho (1.500) | 86,9% (85,1–88,5) | 14 (0,9%) | 26 |
| test400 (tham khảo) | 69,8% (65,1–74,0) | 37 (9,2%) | 30 |
| vang | chưa có dòng nào được duyệt | | |

Quyết định đầu tiên theo quy chuẩn: từ điển đường mặc định đổi từ `tu_dien_duong_v5.json` sang `tu_dien_train.json` (so_sanh td_v5 → td_train: NHẬN yếu; bộ khó đủ 6 trường 4 kém / 15 tốt, p = 0,019; điền thừa 38 → 26, p < 0,001; v5 bịa tên đường từ ghi chú như "gặp chị Hoa" → Đường Hoa).
