# BÁO CÁO TIẾN ĐỘ: DỮ LIỆU ĐỐI CHIẾU ĐỊA CHỈ CŨ → MỚI DƯỚI CẤP XÃ/PHƯỜNG

**Ngày chốt số liệu:** 31/10/2026  
**Dự án:** \`D:\nlp_chuan_hoa_dia_chi\`  
**Phạm vi:** Thu thập bằng chứng địa chỉ cũ → địa chỉ mới ở cấp số nhà, ngõ, đường, tòa nhà, phòng hoặc địa điểm cụ thể sau sắp xếp hành chính.  
**Trạng thái tổng thể:** **CHƯA ĐỦ – CHƯA THỂ NGHIỆM THU TOÀN QUỐC.**

---

## 1. Kết luận điều hành

Bộ dữ liệu đối chiếu hiện tại là một **tập hạt giống (seed/reference set)**, chưa phải cơ sở dữ liệu địa chỉ cũ–mới toàn quốc.

Số liệu được chốt trực tiếp từ CSV hiện có là **20 cặp địa chỉ**, không phải 18 như snapshot đã được nhắc ở trao đổi trước. Trong đó:

- 19/20 cặp có số nhà hoặc chi tiết đường phố/địa điểm cụ thể.
- 1/20 chỉ có tên cụm công nghiệp, không có số nhà.
- Chỉ có dữ liệu ở 4/34 đơn vị hành chính cấp tỉnh sau sắp xếp.
- 30/34 đơn vị cấp tỉnh chưa có bất kỳ cặp nào trong CSV hiện tại.
- Chưa có mẫu số quốc gia về tổng số địa chỉ cũ cần chuyển đổi, vì vậy **không thể tính chính xác còn thiếu bao nhiêu cặp số nhà**.
- Tất cả 20 dòng vẫn mang trạng thái \`human_review_required_before_gold\` và \`reference_only_not_training\`.

**Kết luận:** Không được coi bộ này là đầy đủ, không dùng làm Gold Dataset và không suy rộng một cặp địa chỉ doanh nghiệp thành quy tắc cho toàn bộ phường/xã cũ.

## 2. Độ bao phủ theo tỉnh/thành

Nghị quyết 202/2025/QH15 là căn cứ sắp xếp đơn vị hành chính cấp tỉnh; sau sắp xếp cả nước có 34 đơn vị hành chính cấp tỉnh (28 tỉnh và 6 thành phố). Tham chiếu: [Nghị quyết 202/2025/QH15 trên Cổng văn bản Chính phủ](https://vanban.chinhphu.vn/?classid=1&docid=213930&orggroupid=1&pageid=27160) và [thông tin của Quốc hội về 34 đơn vị cấp tỉnh](https://quochoi.vn/gioithieu/gioithieuveqh/Pages/hoat-dong-qh.aspx?ItemID=97746).

| Tỉnh/thành mới | Số cặp hiện có | Trạng thái |
|---|---:|---|
| Thành phố Hà Nội | 9 | Có mẫu, chưa đủ độ phủ |
| Thành phố Hồ Chí Minh | 8 | Có mẫu, chưa đủ độ phủ |
| Thành phố Hải Phòng | 2 | Có mẫu, chưa đủ độ phủ |
| Thành phố Đà Nẵng | 1 | Có mẫu, chưa đủ độ phủ |
| 30 đơn vị cấp tỉnh còn lại | 0 | Chưa có cặp trong CSV |
| **Tổng** | **20** | **4/34 tỉnh/thành có mẫu** |

Tỷ lệ bao phủ theo tiêu chí “có ít nhất một cặp địa chỉ” là 4/34, tương đương khoảng 11,8%. Đây **không phải** tỷ lệ bao phủ số nhà hoặc tỷ lệ hoàn thành chuyển đổi địa chỉ: bốn địa phương có mẫu vẫn chỉ có một số ít địa chỉ đơn lẻ.

## 3. Quy mô và cấu trúc dữ liệu hiện có

Tệp dữ liệu chính: \`rieng/doi_chieu_dia_chi_cu_moi/cap_nha_duong_dia_chi_cu_moi.csv\`.

| Chỉ tiêu | Số lượng |
|---|---:|
| Tổng cặp địa chỉ cũ → mới | 20 |
| Có số nhà/chi tiết đường phố hoặc địa điểm | 19 |
| Không có số nhà | 1 |
| Có mã xã/phường mới | 20/20 |
| Chi tiết địa chỉ được giữ nguyên sau chuẩn hóa | 19/20 |
| Có ánh xạ xã/phường cũ → mới duy nhất theo crosswalk | 12 |
| Nguồn nêu đích cụ thể và đích khớp một ứng viên trong crosswalk | 6 |
| Trường hợp phường cũ bị chia, phải rà soát theo địa chỉ cụ thể | 2 |
| Cặp không có dòng đối chiếu cũ tương ứng trong crosswalk hiện tại | 1 |

Hai trường hợp phường cũ bị chia cần xử lý thận trọng:

1. Phường 6, quận Bình Thạnh → Phường Bình Lợi Trung: văn bản doanh nghiệp nêu đích cụ thể, nhưng lịch sử địa giới qua Nghị quyết 1278/NQ-UBTVQH15 và 1685/NQ-UBTVQH15 khiến crosswalk hiện tại không có một dòng ánh xạ đơn giản tương ứng. Chỉ giữ đây là bằng chứng cho địa chỉ cụ thể trong hồ sơ; không suy rộng cho toàn Phường 6 cũ.
2. Phường 5, quận 8 → Phường Chánh Hưng: crosswalk thể hiện địa bàn cũ bị chia giữa các đơn vị mới; nguồn doanh nghiệp nêu một địa chỉ cụ thể. Cần kiểm tra tài liệu gốc và căn cứ địa giới trước khi nâng cấp nhãn.

Mã xã/phường mới đã tra được cho 20/20 dòng. Điều này chỉ xác nhận trường mã đích tồn tại trong danh mục hiện dùng; **không chứng minh độc lập rằng số nhà nằm chính xác trong ranh giới đó**.

## 4. Cơ cấu nguồn bằng chứng

| Loại nguồn | Số dòng |
|---|---:|
| Công văn doanh nghiệp tự khai trên cổng Bộ Y tế | 14 |
| Bản ghi công bố trên hệ thống dịch vụ công Bộ Y tế | 3 |
| Quyết định/văn bản chính thức của cơ quan nhà nước | 2 |
| Công văn doanh nghiệp được Sở Y tế đăng tải | 1 |
| **Tổng** | **20** |

Phần lớn dữ liệu đến từ công văn doanh nghiệp tự xác nhận địa chỉ trước và sau sắp xếp. Đây là bằng chứng hữu ích cho **chính địa điểm của đơn vị đó**, nhưng không tương đương danh mục địa chỉ số nhà do cơ quan địa chính hoặc cơ quan quản lý địa chỉ chứng nhận.

Các trường nguồn đang được giữ trong CSV gồm: \`source\`, \`source_type\`, \`source_url\`, \`source_note\`, \`document_date\`, \`crosswalk_status\`, \`review_status\` và \`data_use\`.

## 5. QA và điều kiện sử dụng

- 20/20 dòng có mã xã/phường mới.
- 19/20 dòng có chi tiết số nhà/đường/địa điểm.
- 12 dòng được crosswalk đánh dấu ánh xạ duy nhất.
- 6 dòng có đích do nguồn khai báo khớp một ứng viên của crosswalk; một số vẫn nằm trong vùng có địa giới bị chia.
- 2 dòng cần rà soát lịch sử địa giới cấp phường.
- 20/20 dòng vẫn được đánh dấu \`human_review_required_before_gold\`.
- 20/20 dòng vẫn được đánh dấu \`reference_only_not_training\`.

Không được tự động chuyển các dòng sang Gold chỉ dựa trên việc mã xã/phường mới tồn tại hoặc tên phường khớp. Quy trình duyệt tối thiểu cho mỗi dòng phải mở văn bản gốc, kiểm tra nguyên văn địa chỉ cũ/mới, ngày văn bản, tư cách nguồn, chữ ký/xác nhận nếu có, căn cứ sắp xếp và tính nhất quán của số nhà/đường.

## 6. Tài liệu nguồn đã thu thập nhưng chưa đồng nghĩa với dữ liệu đã trích xuất

Thư mục nguồn hiện có **29 tệp PDF**, ngoài ra còn có HTML, XLSX, JSON và script khảo sát. Các manifest tải nguồn ghi nhận tổng cộng 54 lượt mục tải/kiểm tra, trong đó 35 lượt thành công và 19 lượt lỗi; có mục trùng giữa các manifest, vì vậy không được coi đây là 54 tài liệu độc lập.

Các PDF và tài liệu ứng viên cần tiếp tục được đọc, trích xuất và kiểm tra xem có chứa cặp địa chỉ cũ–mới hay không. Chúng **chưa được tự động tính vào 20 dòng CSV**. Tài liệu tải thành công cũng chưa mặc nhiên tạo thành một cặp hợp lệ.

## 7. Đầu mối dữ liệu quy mô lớn: Vietnam Post

Hồ sơ khảo sát nằm tại \`rieng/doi_chieu_dia_chi_cu_moi/vnpost_tool_access_status.json\`.

Kết quả ghi nhận:

- Công cụ VNPost được giới thiệu hỗ trợ tra cứu địa chỉ cũ → mới và mới → cũ.
- VNPost công bố giải pháp có hỗ trợ xử lý Excel và tích hợp API; tuy nhiên mẫu Excel, giới hạn, endpoint và schema API chưa được xác minh độc lập.
- Cổng tra cứu trả về 403 Forbidden từ môi trường khảo sát.
- Chưa tìm thấy tệp tải công khai chứa bảng chuyển đổi địa chỉ toàn quốc.
- Thông tin công khai mô tả cơ sở dữ liệu VNPost có quy mô khoảng 23 triệu địa chỉ; đây là đầu mối cần xin quyền khai thác chính thức, không phải dữ liệu mà dự án đang sở hữu.

**Hướng xử lý:** liên hệ VNPost qua cổng [developer.vnpost.vn](https://developer.vnpost.vn/) để xin quyền API/Excel hoặc thỏa thuận chia sẻ dữ liệu. Không scrape, vượt chặn hoặc phân phối lại dữ liệu không được cấp quyền.

## 8. Phân biệt với bộ 4.398 địa chỉ tham khảo

Bộ địa chỉ tham khảo trong \`data/tham_chieu_so_nha_toan_quoc/\` chứa các địa chỉ độc lập (ví dụ địa chỉ cơ sở, doanh nghiệp, tổ chức). Nó không đồng nghĩa với cặp đối chiếu cũ → mới.

Vì vậy:
- Không cộng 4.398 địa chỉ tham khảo vào 20 cặp đối chiếu.
- Không báo cáo 4.418 là số cặp đã chuyển đổi.
- Chỉ một bản ghi có đủ địa chỉ cũ, địa chỉ mới và bằng chứng nguồn mới được tính vào tập cặp đối chiếu.

## 9. Vấn đề kỹ thuật cần xử lý

Qua kiểm tra đường dẫn thực tế, script \`build_exact_address_pairs.py\` đang lấy \`ROOT = D.parent\`, khiến script tìm \`rieng/clean/\`. Thư mục này không tồn tại; dữ liệu danh mục thực tế nằm ở \`data/clean/\` trong thư mục gốc dự án.

Do đó, script tái tạo hiện cần được sửa đường dẫn gốc trước khi có thể chạy lại ổn định. CSV và JSON đang có vẫn tồn tại, nhưng không nên tuyên bố quy trình tái tạo đã được kiểm chứng cho đến khi sửa và chạy lại script thành công.

## 10. Kế hoạch hoàn thiện

1. **Sửa script tái tạo:** trỏ đúng tới \`data/clean/moi_tinh_xa.csv\` và \`data/clean/doi_chieu_xa_cu_moi.csv\`; chạy lại, so sánh CSV/JSON đầu ra và kiểm tra diff.
2. **Khai thác tài liệu đang có:** đọc toàn bộ PDF/HTML/XLSX ứng viên; chỉ thêm dòng khi nguồn ghi rõ cặp cũ–mới hoặc có bằng chứng địa điểm cụ thể đủ mạnh.
3. **Lập ma trận 34 tỉnh/thành:** mỗi tỉnh có số nguồn đã tìm, số tài liệu đã đọc, số cặp trích xuất, số cặp qua QA và trạng thái thiếu dữ liệu.
4. **Ưu tiên 30 tỉnh/thành chưa có cặp:** mở rộng nguồn cơ quan nhà nước, hồ sơ công bố doanh nghiệp, quyết định đổi tên đường/đánh số nhà và dữ liệu bưu chính được cấp quyền.
5. **Xin dữ liệu VNPost:** ưu tiên API/Excel được cấp phép thay vì thu thập thủ công từng địa chỉ.
6. **Xử lý địa giới bị chia:** đối chiếu nghị quyết cấp xã và chuỗi lịch sử trước/sau 01/01/2025, 01/07/2025; không ánh xạ theo tên phường đơn thuần.
7. **Đặt chuẩn Gold:** chỉ nâng cấp sau khi kiểm tra tài liệu gốc và xác nhận độc lập; giữ các dòng còn tranh chấp ở trạng thái review.

## 11. Tiêu chí nghiệm thu

Chỉ xem là hoàn thành khi:

- Có ma trận bao phủ đủ 34/34 tỉnh/thành và báo cáo rõ tỉnh nào còn thiếu.
- Có nguồn đối chiếu hợp lệ cho từng cặp địa chỉ.
- Có địa chỉ chi tiết dưới cấp xã/phường, ưu tiên số nhà, ngõ, đường, thôn/xóm, tổ dân phố và địa điểm.
- Có quy tắc xử lý địa giới bị chia, không suy diễn sai từ crosswalk cấp xã.
- Có thống kê số cặp đã trích xuất, số cặp đã xác minh, số cặp bị loại và số địa chỉ còn thiếu dựa trên một mẫu số/nguồn tổng thể xác định.
- Các bản ghi Gold có bằng chứng và lịch sử duyệt có thể truy vết.

**Hiện trạng nghiệm thu:** Chưa đạt. Đã có bộ tham chiếu ban đầu 20 cặp; chưa có cơ sở để kết luận dữ liệu địa chỉ chi tiết toàn quốc đã đầy đủ hoặc xác định chính xác tổng số cặp còn thiếu.

---

## 12. Vị trí dữ liệu và tài liệu

Thư mục dữ liệu đối chiếu:

\`D:\nlp_chuan_hoa_dia_chi\rieng\doi_chieu_dia_chi_cu_moi\`

Các tệp chính:

- \`cap_nha_duong_dia_chi_cu_moi.csv\` — 20 cặp địa chỉ hiện được ghi nhận.
- \`bao_cao_cap_nha_duong_dia_chi_cu_moi.json\` — số liệu QA và SHA-256.
- \`README.md\` — mô tả bộ dữ liệu và đầu mối VNPost.
- \`vnpost_tool_access_status.json\` — trạng thái khảo sát VNPost.
- \`download_*_manifest*.json\` — nhật ký tải nguồn.
- \`*.pdf\`, \`*.html\`, \`*.xlsx\` — tài liệu nguồn/ứng viên.
- \`build_exact_address_pairs.py\` — script tạo bộ CSV/JSON; cần sửa đường dẫn đầu vào trước khi chạy lại.

Báo cáo này được lưu tại \`docs/BAO_CAO_TIEN_DO_DOI_CHIEU_DIA_CHI_CU_MOI_20261031.md\`.
