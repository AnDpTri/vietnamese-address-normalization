# char_v3_tc — mô hình tiền xử lý đang dùng (thay char_v2_01 từ 31/10/2026)

- CNN ký tự + ranker LightGBM, ranker gắn với CNN này (extractor_sha256 655db4a1…).
- Dữ liệu train: dữ liệu thật của char_v2_01 x2 + 9.992 địa chỉ bẩn do agy sinh (nhãn từng ký tự, kiểm bằng máy) + 4.000 dòng tăng cường dạng số nhà thật (dải số, nhiều số, mã lô, căn hộ, Km...). Không dùng dev.
- Nơi train và nhật ký: D:\nlp_rf_gate\train_v3 (v3_tc, NHAT_KY.md, BAO_CAO_SANG.md).

| | char_v2_01 | char_v3_tc |
|---|---|---|
| Dev 1.600, riêng tiền xử lý | 85,8% | 85,7% |
| Bộ khó 1.500, riêng tiền xử lý | 61,2% | 82,7% |
| dev_goc đầu cuối 6 trường | 87,4% (993) | 87,4% (993) |
| dev_kho đầu cuối 6 trường | 89,9% (417) | 90,9% (422) |

Lưu ý: bộ khó và dữ liệu train đều do agy viết, mức tăng trên bộ khó có thể bị thổi phồng. Dev đã dùng để chọn cấu hình.
Quay lại bản cũ: đổi đường dẫn về mo_hinh/thu_nghiem/char_v2_01 (vẫn giữ nguyên).

Hiệu chỉnh danh mục hai xã cũ: bổ sung Mỹ Hưng `01651` → Phục Hòa `01648`
và Phú Thịnh `02482` → Thái Bình `02494`. Chỉ cập nhật trường `catalogue_sha256`
trong `ranker.json` cho khớp danh mục tái sinh; không train lại, không sửa
`ranker.txt` hay `char_cnn.pt`. Đặc trưng ranker không dùng mã địa phương.
Các ranker ở `char_v2_01` vẫn giữ băm cũ và không nạp được với danh mục mới.

Đã đo `sau_2_xa` so với `kiem_lai` (main `9ab0704`): `dev_osm_that` 400 câu,
`dev_sinh_danh_muc` 1.200 câu, `kho_bien_the_ban` 1.500 câu; cả 3.100 câu
giữ nguyên mọi trường đầu ra, không câu nào kém đi. Phép đo dùng wrapper tạm
chuyển đầu ra khỏi `rieng/` và giới hạn so sánh đúng ba tập trên; không chạy test/vàng.
