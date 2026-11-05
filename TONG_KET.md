# Tổng kết dự án (31/10/2026)

Một trang thay cho hơn 30 báo cáo rời của các ngày 26–31/10. Bản gốc của từng báo cáo vẫn còn trong tag `luu-tru/*` và thư mục `luu_tru/`.

## 1. Hệ thống hiện tại

Bài toán chỉ có **hai phần**, đo riêng từng phần:

| Phần | Làm gì | Thành phần |
|---|---|---|
| **1. Tiền xử lý** (`src/tien_xu_ly/`) | Chuỗi bẩn → địa chỉ sạch có cấu trúc, theo mốc cũ hoặc mới tùy đầu vào | Char-CNN + CRF gán vai trò từng ký tự (7 vai trò); trie sinh ứng viên hành chính (khớp đúng, không dấu, viết tắt chữ đầu, sai chính tả); beam ghép đường đi hợp lệ trên cây hành chính cũ và mới; LightGBM LambdaRank chọn giả thuyết; tra tên cũ; từ điển đường |
| **2. Chuyển đổi** (`src/chuyen_doi/`) | Địa chỉ cũ sạch → địa chỉ mới | Chỉ tra bảng đối chiếu. Xã cũ bị chia: phân giải theo tên đường nếu bảng có bằng chứng, không thì để trống và liệt kê ứng viên |

**Mô hình đang dùng:** `mo_hinh/thu_nghiem/char_v3_tc` (CNN 1,4 MB + ranker), train trên dữ liệu thật ×2 + 9.992 địa chỉ bẩn do agy sinh (kiểm bằng máy) + 4.000 dòng tăng cường số nhà.

**Mã nguồn (dọn 31/10, không đổi kết quả: 3.100/3.100 câu giống hệt):** `src/` giảm từ 4.075 còn 3.060 dòng. Bỏ 17 file lối vào tương thích `src/*.py` và thư mục alias `src/lien_ket_v1` (import thẳng `src.tien_xu_ly.<module>`); gỡ đường thử nghiệm đã bỏ (ViDeBERTa, liên kết v1, hợp đồng và tùy chọn `--videberta-model`, `--hop-dong`) sang `luu_tru/tu_repo_20261031/`; 19 script đo cũ trong `danh_gia/` cũng ở đó. Bốn bước sửa sau ranker trong `BoLamSach` là bốn hàm có tên. Test: 156.

**Nguyên tắc đã chốt:**
- Không khẳng định khi không đủ bằng chứng: để trống và gắn cảnh báo, không chọn bừa.
- Số nhà, ngõ, thôn, đường không có dữ liệu đối chiếu: chỉ chuẩn hóa hình thức, chấm theo "tách đúng, giữ đúng chữ người gõ".
- Đầu ra không có cấp huyện.
- Mọi bản chạy thử phải bật log đủ các bước trung gian (`AMC_LOG=1`, `BoChuanHoa.chuan_hoa_chan_doan`). Sửa theo nguyên nhân gốc, không vá khớp từng câu.

## 2. Số đo hiện tại

**Từ 05/11/2026 số chính thức lấy theo [quy chuẩn đánh giá](danh_gia/chuan/QUY_CHUAN.md)** (một quy ước chấm, tách thật/sinh, khoảng tin cậy 95%). Cấu hình web = cấu hình đo (`src/cau_hinh.py`, từ điển `tu_dien_train`):

| Tập | Đủ 6 trường | Khẳng định sai mã xã |
|---|---|---|
| dev_osm_that: 400 địa chỉ OSM thật (số chính) | **86,8%** (83,1–89,7) | 12 (3,0%) |
| dev_sinh: 1.200 địa chỉ sinh từ danh mục | 97,2% | 0 |
| bộ khó (1.500) | 86,9% | 14 (0,9%) |
| test400 (nhãn AI chưa duyệt, tham khảo) | 69,8% (quy ước chấm mới) | 37 (9,2%) |

Con số 94,2% dưới đây gộp 736 địa chỉ sinh (đúng 98,1%) với 400 địa chỉ thật (87,0%), không còn dùng làm số chính. Tập vàng 300 địa chỉ ngoài OSM đang chờ người duyệt (`rieng/vang/`).

Số cũ (đo 31/10, bộ chấm cũ):

Đo lại ngày 31/10 trên code đã dọn (`char_v3_tc`, từ điển `tu_dien_train.json`). Kết quả giống hệt từng câu (3.100/3.100) với lượt đo ngay trước khi dọn.

**Đầu cuối** (sau chuyển đổi, 6 trường: số nhà, ngõ, thôn, đường, mã xã, mã tỉnh; so bỏ dấu; nhãn dev đã sửa):

| Tập | Đúng cả 6 trường | Số nhà | Ngõ | Thôn | Đường | Mã xã | Mã tỉnh |
|---|---|---|---|---|---|---|---|
| dev_goc (1.136) | **1.070 — 94,2%** | 98,9 | 99,8 | 99,6 | 98,4 | 96,9 | 100 |
| dev_kho (464) | **445 — 95,9%** | 99,8 | 100 | 100 | 96,3 | 99,6 | 100 |

**Riêng tiền xử lý** (đơn vị chọn trước chuyển đổi + 4 trường chi tiết, đúng cả câu):

| Tập | Đúng cả câu | Yếu nhất |
|---|---|---|
| Dev (1.600) | 85,8% | thôn/xóm 78,6%, đường 92,3% |
| Bộ khó (1.500, `rieng/bo_kho`) | 83,1% | gõ sai 55,1% (đường 45%), không dấu: thôn 48% |
| Bộ khó, nhóm sạch | 98,5% | |

**Tập test 400** (nhãn AI chưa duyệt, đo 31/10 trước khi dọn): 249/400 = 62,25% đúng 6 trường thô, mã xã 89,5%.

**Tốc độ** (CPU laptop, 1 luồng, 300 câu dev, đã nạp mô hình): trung bình 74,9 ms/câu, trung vị 72,8 ms, P95 138,9 ms.

**Đọc số cho đúng:**
- Nhãn dev ban đầu do máy gán, sai nhiều; `data/dev/nhan_sua` là bản đã sửa (agy dò 5 gói + sửa tay). Dev đã được dùng để chọn cấu hình, nên không phải phép đo độc lập.
- Bộ khó và dữ liệu train cùng do agy viết (khác seed, khác tên đường): mức tăng trên bộ khó có thể bị thổi phồng.
- Tập test 400 có nhãn AI chưa người duyệt và **đã bị mở nhiều lần**, không còn là tập giữ kín.

## 3. Nhật ký các hướng đã thử

| Hướng | Kết quả | Quyết định |
|---|---|---|
| Luật v1→v3 (trie + beam + điểm đặt tay) | Dev gốc (nhãn cũ) 73,9% → 76,6% sáu trường | Thay bằng mô hình; giữ trie, beam |
| CRF v1 (python-crfsuite, CPU) | 78,8% / 59,1% (dev gốc / dev khó, nhãn cũ) | Giữ làm nền cho lớp CRF trên CNN, không dùng riêng |
| Char-CNN + CRF + LightGBM ranker v1 | 78,6% / 60,3% | **Nền của hệ thống hiện tại** |
| + tra tên đường từ train + bảo vệ ranh giới đường | 82,8% / 63,8%, không câu nào tụt | Giữ |
| ViDeBERTa-xsmall (Colab T4, 70M tham số) | 77,4% / 60,8%; chậm khoảng 7 lần trên CPU | Bỏ |
| ViDeBERTa train lại trên dữ liệu v3 (GPU máy) | Kém CNN 1–2 điểm mọi phép đo; 117 ms so với 54 ms/câu | Bỏ |
| Nhánh lai ViDeBERTa (khôi phục ranh giới đường) | Bỏ khi refactor (`3386239`) | Bỏ |
| PhoBERT-base-v2 (gói Colab, kiểm tokenizer) | Dừng ở khâu chuẩn bị, chưa có kết quả hơn | Bỏ |
| Liên kết thực thể neural (bi-encoder ViDeBERTa đóng băng) | Thử trên Colab, không đưa vào | Bỏ |
| Train v3: 10.000 địa chỉ bẩn agy sinh + tăng cường số nhà | Bộ khó (riêng tiền xử lý) 57,2% → 82,7%; dev giữ nguyên | **Giữ (v3_tc)** |
| Train thêm 15.000 địa chỉ OSM nhãn từ thẻ | Test 248 → 227; OSM gộp số nhà vào tên đường | Bỏ |
| Tách hai module (tiền xử lý / chuyển đổi) | 0/3.130 câu đổi hành vi | Giữ |
| Tên cũ huyện, xã (từ vietnamadminunits, MIT) | Tra được đơn vị đã nhập/đổi tên trước danh mục cũ | Giữ |
| Không chọn bừa giữa các cách hiểu ngang bằng chứng | Dev không đổi; test: khẳng định sai mã xã 34 → 33 | Giữ |
| Cảnh báo `don_vi_ghi_khong_khop` | Báo nhầm trên dev 49 → 2 câu | Giữ |
| Phân giải xã bị chia theo tên đường (OSM + GIS) | Bảng 197 dòng, 66 xã; 280/280 điểm giữ lại đúng | Giữ |
| Ranh giới thôn/xóm (agy A–E, 31/10) | Review đánh FAIL (3 lỗi HIGH) | Dở, ở nhánh `wip/thon-xom-dang-do-20261031` |
| Từ điển đường v2–v5 (agy tổng hợp văn bản đô thị) | Web dùng v5 (2.381 mục); số đo dùng `tu_dien_train` (1.018 mục) | **Chưa thống nhất** (xem mục 4) |

## 4. Lỗi đã biết và việc còn dở

1. ~~Hai từ điển đường~~ (xong 05/11/2026): web và mọi script đo dùng chung `src/cau_hinh.py`; chọn `tu_dien_train` vì v5 bịa tên đường từ ghi chú (xem QUY_CHUAN.md mục 6).
2. **Ranh giới thôn/xóm** khi không có dấu phẩy (`xóm 5 xã mỹ hưng huyện…`): bản sửa dở, có kế hoạch sửa trong `luu_tru/tu_repo_20261031` (báo cáo điều phối 31/10).
3. **Viết tắt bỏ nguyên âm** (`hnoi`, `p.trc bch`): không tra được, đang để trống.
4. **Tập test 400** chưa duyệt tay, đã bị mở nhiều lần. Cần một tập giữ kín mới có người duyệt.
5. Điểm yếu trên bộ phủ rộng (8.934 câu, đáp án ở `rieng/bo_phu_rong`): nhóm xã mới (khoảng 86% xã đúng), tên cũ, chỉ ghi tên xã.

## 5. Bài học về quy trình

- **Agy từng gian lận test** (thêm `tests/__init__.py` biến 5 test lỗi thành test rỗng). Luôn tự chạy cổng kiểm và đọc diff.
- **Nhãn máy không phải gold.** Mọi tỷ lệ "khớp nhãn" phải ghi rõ là khớp nhãn nào.
- **Không tuyên bố cải thiện khi dev chưa tăng.** Bộ khó cùng nguồn với train dễ thổi phồng.
- **Không để worktree và nhánh tràn lan:** đến 31/10 có 24 worktree, khoảng 30 nhánh, dữ liệu đo nằm ngoài git và script đo nạp nhầm code cũ. Từ nay chỉ có `main`; thử nghiệm làm trên nhánh ngắn, xong trong ngày thì merge hoặc xóa.

## 6. Lưu trữ

- Tag `luu-tru/<nhánh>` trên GitHub cho mọi nhánh cũ (40 tag), kể cả các nhánh `wip/*-20261031` chứa việc dở.
- `luu_tru/` (không lên git): các worktree cũ (vẫn dùng được), `nlp_rf_gate`, `nlp_demo`, `PhoBERT_CPU_Check_20261030`, bản chép tay refactor, và `tu_repo_20261031/` chứa báo cáo, colab, mô hình cũ, kết quả đo cũ đã gỡ khỏi repo.
- `rieng/` (không lên git): đáp án kín (bộ khó, bộ phủ rộng), thư mục train v3, dữ liệu OSM, ViDeBERTa, venv GPU, dữ liệu tham chiếu số nhà và GIS.
