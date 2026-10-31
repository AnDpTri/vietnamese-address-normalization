export type NhanThanhPhan =
  | 'so_nha'
  | 'ngo_ngach_hem'
  | 'thon_xom'
  | 'duong'
  | 'xa'
  | 'huyen'
  | 'tinh'
  | 'bo_qua';

export type DoiChieuTrangThai = 'co' | 'khong' | 'bo_qua';

export interface ThanhPhan {
  doan_goc: string;
  bat_dau: number;
  ket_thuc: number;
  nhan_la: NhanThanhPhan;
  chuan_hoa: string;
  doi_chieu: DoiChieuTrangThai;
  ly_do: string;
  ket_qua_moi: string;
}

export interface KetQuaHaiDongCoDoiChieu {
  xa_phuong: string;
  ma_xa: string;
  tinh: string;
  ma_tinh: string;
  chuoi: string;
}

export interface KetQuaHaiDongThieuDuLieu {
  so_nha: string;
  ngo_ngach_hem: string;
  thon_xom: string;
  duong: string;
  chuoi: string;
  ghi_chu: string;
}

export interface KetQuaHaiDong {
  co_doi_chieu: KetQuaHaiDongCoDoiChieu;
  thieu_du_lieu_doi_chieu: KetQuaHaiDongThieuDuLieu;
}

export interface AddressResult {
  so_nha: string;
  ngo_ngach_hem: string;
  thon_xom: string;
  duong: string;
  xa_phuong: string;
  ma_xa: string;
  tinh: string;
  ma_tinh: string;
  dia_chi_chuan: string;
  dia_chi_sau_tien_xu_ly?: string;
  canh_bao: string[];
  xa_moi_ung_vien: Record<string, string>[];
  dau_vet: Record<string, unknown>[];
  phan_chua_phan_loai: string;
  thong_ke: Record<string, unknown>;
  thanh_phan?: ThanhPhan[];
  ket_qua_hai_dong?: KetQuaHaiDong;
}

export interface ApiError {
  code: string;
  message: string;
}

export interface NormalizeResponse {
  input: string;
  result: AddressResult;
  elapsed_ms: number;
  status: 'processed' | 'needs_review';
  thanh_phan?: ThanhPhan[];
  ket_qua_hai_dong?: KetQuaHaiDong;
  log_id?: string | null;
}

export interface BatchInput {
  id: string;
  address: string;
}

export interface BatchItem {
  id: string;
  input: string;
  status: 'processed' | 'needs_review' | 'error';
  result?: AddressResult;
  elapsed_ms?: number;
  error?: ApiError;
  thanh_phan?: ThanhPhan[];
  ket_qua_hai_dong?: KetQuaHaiDong;
  log_id?: string | null;
}

export interface BatchResponse {
  items: BatchItem[];
  elapsed_ms: number;
}

export interface HealthResponse {
  status: 'ok' | 'loading' | 'error';
  engine: string;
  target_date: string;
  limits: { max_chars: number; max_batch: number };
  message?: string;
}
