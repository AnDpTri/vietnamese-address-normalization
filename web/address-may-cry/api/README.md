# Address May Cry — Real API Adapter & App Backend

Backend HTTP API thực tế cho sản phẩm **Address May Cry** — ứng dụng chuẩn hóa địa chỉ tiếng Việt mốc **01/07/2025**.  
Tuân thủ đầy đủ hợp đồng [`CONTRACT.md`](file:///D:/nlp_chuan_hoa_dia_chi/web/address-may-cry/CONTRACT.md) và TypeScript types tại [`src/shared/contracts.ts`](file:///D:/nlp_chuan_hoa_dia_chi/web/address-may-cry/src/shared/contracts.ts).

---

## 1. Kiến Trúc Kỹ Thuật

- **Giao thức & Cổng:** HTTP `127.0.0.1:8080`.
- **Framework:** Chuẩn thư viện Python (`http.server.ThreadingHTTPServer`), không phụ thuộc thêm thư viện ngoài, tối ưu bộ nhớ và CPU.
- **Engine NLP:**
  - Mô hình, từ điển đường và tùy chọn lấy từ `src/cau_hinh.py` (dùng chung với CLI và bộ đánh giá chuẩn `danh_gia/chuan`): hiện là `char_v3_tc` (CharCNN + ranker LightGBM) + `data/train/tu_dien_train.json` + danh mục `data/clean`, `bao_ve_duong=True`, `tien_to_mac_dinh=True`.
  - Chế độ: CPU 1 thread (`torch.set_num_threads(1)`). Đổi từ điển để thử: biến môi trường `AMC_TU_DIEN_DUONG`.
  - Quản lý đồng thời: Singleton model adapter, bảo vệ toàn bộ bước inference bằng `threading.Lock` để tránh xung đột trạng thái / race condition trên PyTorch.
- **Bảo mật & Quyền riêng tư:**
  - Không log raw địa chỉ ra console theo mặc định.
  - Ngăn chặn hoàn toàn Path Traversal khi serve file tĩnh từ `dist/`.
  - Không có endpoint thực thi shell, upload file, hay truy cập file tùy ý.
  - CORS header đầy đủ cho phép giao tiếp liền mạch với Vite dev server (`http://localhost:5173`).

---

## 2. Danh Sách Endpoints

### 2.1. `GET /api/v1/health`
Kiểm tra trạng thái sẵn sàng của hệ thống và giới hạn kỹ thuật.
- **Response 200 OK:**
  ```json
  {
    "status": "ok",
    "engine": "CNN v2 (char_v2_01) + Ranker v2 + Dict v5 (CPU 1 thread)",
    "target_date": "2025-07-01",
    "limits": {
      "max_chars": 2048,
      "max_batch": 100
    },
    "message": "Sẵn sàng chuẩn hóa địa chỉ Việt Nam theo mốc 01/07/2025."
  }
  ```

### 2.2. `POST /api/v1/normalize`
Chuẩn hóa một địa chỉ đơn lẻ.
- **Request Body (JSON):**
  ```json
  {
    "address": "Số 10 Đường Lê Lợi, Phường Bến Nghé, Quận 1, TP Hồ Chí Minh"
  }
  ```
- **Response 200 OK:**
  ```json
  {
    "input": "Số 10 Đường Lê Lợi, Phường Bến Nghé, Quận 1, TP Hồ Chí Minh",
    "result": {
      "so_nha": "Số 10",
      "duong": "Đường Lê Lợi",
      "ngo_ngach_hem": "",
      "thon_xom": "",
      "xa_phuong": "Phường Sài Gòn",
      "ma_xa": "26740",
      "tinh": "Thành phố Hồ Chí Minh",
      "ma_tinh": "79",
      "dia_chi_chuan": "Số 10, Đường Lê Lợi, Phường Sài Gòn, Thành phố Hồ Chí Minh",
      "canh_bao": [],
      "xa_moi_ung_vien": [],
      "dau_vet": [],
      "phan_chua_phan_loai": "",
      "thong_ke": {}
    },
    "elapsed_ms": 71.2,
    "status": "processed"
  }
  ```
  *(Trạng thái `status` là `needs_review` nếu có cảnh báo, nhiều ứng viên xã mới, hoặc có phần chưa phân loại).*

### 2.3. `POST /api/v1/batch`
Chuẩn hóa một lô địa chỉ (tối đa 100 địa chỉ/lần).
- **Request Body (JSON):**
  ```json
  {
    "addresses": [
      { "id": "1", "address": "Số 1 Đường Tràng Tiền, Hoàn Kiếm, Hà Nội" },
      { "id": "2", "address": "" },
      { "id": "3", "address": "456 Đường Nguyễn Trãi, Quận 5, TP Hồ Chí Minh" }
    ]
  }
  ```
- **Response 200 OK (Cô lập lỗi từng item, không làm hỏng cả batch):**
  ```json
  {
    "items": [
      {
        "id": "1",
        "input": "Số 1 Đường Tràng Tiền, Hoàn Kiếm, Hà Nội",
        "status": "processed",
        "result": { ... },
        "elapsed_ms": 65.4
      },
      {
        "id": "2",
        "input": "",
        "status": "error",
        "error": {
          "code": "EMPTY_ADDRESS",
          "message": "Địa chỉ đầu vào không được để trống."
        }
      },
      {
        "id": "3",
        "input": "456 Đường Nguyễn Trãi, Quận 5, TP Hồ Chí Minh",
        "status": "processed",
        "result": { ... },
        "elapsed_ms": 58.1
      }
    ],
    "elapsed_ms": 125.8
  }
  ```

---

## 3. Hướng Dẫn Vận Hành

### Khởi động Server ngầm (Background):
```powershell
& "D:\nlp_chuan_hoa_dia_chi\.venv-neural\Scripts\python.exe" web/address-may-cry/api/run.py
```

### Khởi động Server trực tiếp (Foreground):
```powershell
& "D:\nlp_chuan_hoa_dia_chi\.venv-neural\Scripts\python.exe" web/address-may-cry/api/run.py --foreground
```

### Dừng Server an toàn (theo PID):
```powershell
& "D:\nlp_chuan_hoa_dia_chi\.venv-neural\Scripts\python.exe" web/address-may-cry/api/stop.py
```

### Chạy bộ kiểm thử hợp đồng tự động:
```powershell
& "D:\nlp_chuan_hoa_dia_chi\.venv-neural\Scripts\python.exe" web/address-may-cry/api/tests/test_api_contract.py
```
