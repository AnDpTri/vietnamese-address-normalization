# Chuẩn hóa địa chỉ tiếng Việt theo đơn vị hành chính mới

Đề tài môn Xử lý ngôn ngữ tự nhiên, lớp KHMT K22A.

Nhận địa chỉ nhập tự do (không dấu, viết tắt, sai chính tả, lộn thứ tự, ghi theo địa giới cũ) và trả về địa chỉ chuẩn theo đơn vị hành chính sau ngày 1/7/2025. Chạy offline trên CPU, không dùng LLM hay API.

- **[TONG_KET.md](TONG_KET.md)**: hệ thống hiện tại, số đo, nhật ký các hướng đã thử, lỗi đã biết. Đọc file này trước.
- [bai_toan.md](bai_toan.md): đặc tả bài toán.
- [bao_cao/](bao_cao/): báo cáo tiến độ tuần 3, tuần 4 và báo cáo cuối kỳ (Word, PDF).

## Hệ thống: hai phần

1. **Tiền xử lý** (`src/tien_xu_ly/`): chuỗi bẩn → địa chỉ sạch có cấu trúc (theo mốc cũ hoặc mới, tùy đầu vào). Char-CNN + CRF gán vai trò ký tự, trie sinh ứng viên hành chính, beam ghép đường đi hợp lệ trên cây hành chính, LightGBM ranker chọn giả thuyết, từ điển đường chuẩn tên đường.
2. **Chuyển đổi** (`src/chuyen_doi/`): địa chỉ cũ sạch → địa chỉ mới, chỉ tra bảng đối chiếu. Xã cũ bị chia: phân giải theo tên đường nếu có bằng chứng, không thì để trống và liệt kê ứng viên.

## Cấu trúc

```
src/            code chạy: tien_xu_ly/ (phần 1), chuyen_doi/ (phần 2), chuan_hoa.py (ghép hai phần), danh_muc.py, kieu_du_lieu.py, __main__.py (CLI)
mo_hinh/        char_v3_tc (đang dùng), char_v2_01 và crf_v1_01 (nguồn snapshot cho train)
data/
  clean/        danh mục hành chính cũ, mới, bảng đối chiếu (mốc 1/7/2025)
  ten_cu/       tên cũ/bí danh huyện, xã
  xa_chia_theo_duong/  bảng phân giải xã bị chia theo tên đường
  duong/        danh mục đường
  dev/          dev_goc, dev_kho; nhan_sua/ là nhãn đã sửa dùng để chấm
  train/        dữ liệu train (train.csv, bo_train/dat, tu_dien_train.json)
  test/         400 địa chỉ OSM, nhãn sơ bộ, chưa duyệt tay
danh_gia/       danh_gia/v3/ là bộ train/đo hiện hành; ngoài ra chỉ còn script mà v3 và test gọi (huan_luyen_char, du_lieu_char, chay_ban_thu, do_kiem_tra_test400...)
web/            Address May Cry (giao diện + API)
bao_cao/        báo cáo tuần và báo cáo cuối kỳ
tests/
rieng/          (không lên git) đáp án kín, bộ khó, thư mục train, mô hình lớn
luu_tru/        (không lên git) mọi thứ cũ, nguyên vẹn
```

Import dùng đường dẫn thật, ví dụ `from src.tien_xu_ly.char_cnn import BoTachCharCNN`. Chế độ không mô hình (`bo_tach=None`) vẫn chạy luật thuần.

Mọi nhánh cũ có tag `luu-tru/*` trên GitHub. Hook `danh_gia/v3/hooks/pre-commit` chặn commit file trong `rieng/` và `luu_tru/`; cài bằng `cp danh_gia/v3/hooks/pre-commit .git/hooks/`.

## Chạy

Môi trường: Python 3.12, `.venv-neural` (PyTorch, LightGBM, NumPy), xem `requirements-neural.txt`.

```powershell
$py = '.\.venv-neural\Scripts\python.exe'
$m = 'mo_hinh/thu_nghiem/char_v3_tc'
& $py -X utf8 -B -m src 'so 12 ngo 5 tran thai tong cau giay hn' --char-model $m/char_cnn.pt --ranker $m/ranker.txt --tu-dien-duong data/train/tu_dien_train.json --bao-ve-duong
```

Web: `web/address-may-cry/` (xem README trong đó). Đặt `AMC_LOG=1` để ghi log các bước trung gian.

## Đo

```powershell
# chạy dev + bộ khó (bộ khó cần rieng/bo_kho)
& $py -X utf8 -B danh_gia/v3/chay_mo_hinh.py $m/char_cnn.pt $m/ranker.txt rieng/train_v3/ket_<ten>
# chấm đầu cuối trên nhãn dev đã sửa
& $py -X utf8 -B danh_gia/v3/do_dau_cuoi_sua.py data/dev/nhan_sua rieng/train_v3/ket_<ten>/ket_qua.jsonl
# kiểm tra
& $py -X utf8 -B -m unittest discover -s tests -p 'test_*.py'
```

Đặt `CODE_ROOT` để đo code ở thư mục khác. Train lại: `bash danh_gia/v3/train_va_do.sh <ten_run>`.
