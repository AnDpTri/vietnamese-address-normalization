/**
 * Tiện ích xuất dữ liệu CSV và JSON chuẩn cho Address May Cry (Phần B).
 * Tuân thủ nghiêm ngặt:
 * - CSV UTF-8 kèm BOM (\uFEFF) cho Excel đọc tiếng Việt đúng dấu.
 * - Chuẩn RFC 4180 (escape quotes "").
 * - Bảo vệ chống CSV Formula Injection: Nếu giá trị bắt đầu bằng =, +, -, @ thì thêm tiền tố ' trong CSV
 *   mà KHÔNG làm thay đổi số nhà hay mã hành chính trong dữ liệu JSON!
 * - Giữ nguyên toàn bộ các cột gốc từ file CSV nhập vào.
 * - Hàng chưa xử lý hoặc lỗi thì giữ nguyên trạng thái, không bịa kết quả chuẩn hóa.
 */

import type { BatchItem } from '../../shared/contracts';

export type BatchItemWithMeta = (BatchItem | (Omit<BatchItem, 'status'> & { status: 'pending' })) & {
  rowIndex: number;
  originalData?: Record<string, string>;
  selected?: boolean;
};

/**
 * Phòng vệ chống CSV Injection:
 * Ký tự bắt đầu bằng =, +, -, @ có thể kích hoạt mã thực thi trong Excel/Google Sheets.
 */
export function sanitizeForCsvFormula(val: string): string {
  if (!val || typeof val !== 'string') return '';
  const trimmed = val.trim();
  if (trimmed.length > 0 && (trimmed.startsWith('=') || trimmed.startsWith('+') || trimmed.startsWith('-') || trimmed.startsWith('@'))) {
    return `'${val}`;
  }
  return val;
}

/**
 * Thoát chuỗi theo chuẩn RFC 4180
 */
export function escapeCsvField(val: string | null | undefined): string {
  if (val === null || val === undefined) return '';
  const str = String(val);
  const sanitized = sanitizeForCsvFormula(str);

  // Nếu chứa dấu phẩy, dấu nháy kép, dấu xuống dòng, dấu chấm phẩy, hoặc bắt đầu bằng tiền tố nháy đơn bảo vệ
  if (
    sanitized.startsWith("'") ||
    sanitized.includes(',') ||
    sanitized.includes('"') ||
    sanitized.includes('\n') ||
    sanitized.includes('\r') ||
    sanitized.includes(';')
  ) {
    return `"${sanitized.replace(/"/g, '""')}"`;
  }
  return sanitized;
}

/**
 * Xuất danh sách Batch ra tệp CSV (UTF-8 kèm BOM)
 */
export function exportToCSV(
  items: BatchItemWithMeta[],
  originalHeaders: string[] = [],
  filename = 'address_may_cry_batch_export.csv'
): void {
  // 1. Xác định danh sách headers: Các cột gốc + Các cột chuẩn hóa mới
  const coreResultHeaders = [
    'dia_chi_chuan',
    'so_nha',
    'ngo_ngach_hem',
    'thon_xom',
    'duong',
    'xa_phuong',
    'ma_xa',
    'tinh',
    'ma_tinh',
    'chuoi_co_doi_chieu',
    'chuoi_thieu_du_lieu_doi_chieu',
    'trang_thai',
    'canh_bao',
    'elapsed_ms',
  ];

  // Lọc bỏ các cột gốc nội bộ như _row_index
  const cleanOriginalHeaders = originalHeaders.filter(h => !h.startsWith('_'));
  const allHeaders = [...cleanOriginalHeaders, ...coreResultHeaders];

  // 2. Xây dựng các dòng CSV
  const csvLines: string[] = [];

  // Dòng tiêu đề
  csvLines.push(allHeaders.map(h => escapeCsvField(h)).join(','));

  // Các dòng dữ liệu
  for (const item of items) {
    const rowValues: string[] = [];

    // Các cột gốc
    for (const h of cleanOriginalHeaders) {
      const origVal = item.originalData ? item.originalData[h] : '';
      rowValues.push(escapeCsvField(origVal || (h === 'dia_chi' || h === 'input' ? item.input : '')));
    }

    // Các cột kết quả chuẩn hóa
    const res = item.result;
    const haiDong = item.ket_qua_hai_dong || res?.ket_qua_hai_dong;
    if (res) {
      rowValues.push(escapeCsvField(res.dia_chi_chuan));
      rowValues.push(escapeCsvField(res.so_nha));
      rowValues.push(escapeCsvField(res.ngo_ngach_hem));
      rowValues.push(escapeCsvField(res.thon_xom));
      rowValues.push(escapeCsvField(res.duong));
      rowValues.push(escapeCsvField(res.xa_phuong));
      rowValues.push(escapeCsvField(res.ma_xa));
      rowValues.push(escapeCsvField(res.tinh));
      rowValues.push(escapeCsvField(res.ma_tinh));
      rowValues.push(escapeCsvField(haiDong?.co_doi_chieu?.chuoi || ''));
      rowValues.push(escapeCsvField(haiDong?.thieu_du_lieu_doi_chieu?.chuoi || ''));
      rowValues.push(escapeCsvField(item.status));
      rowValues.push(escapeCsvField(res.canh_bao ? res.canh_bao.join('; ') : ''));
      rowValues.push(escapeCsvField(item.elapsed_ms != null ? String(item.elapsed_ms) : ''));
    } else {
      // Hàng chưa xử lý hoặc lỗi: Không bịa kết quả!
      rowValues.push(''); // dia_chi_chuan
      rowValues.push(''); // so_nha
      rowValues.push(''); // ngo_ngach_hem
      rowValues.push(''); // thon_xom
      rowValues.push(''); // duong
      rowValues.push(''); // xa_phuong
      rowValues.push(''); // ma_xa
      rowValues.push(''); // tinh
      rowValues.push(''); // ma_tinh
      rowValues.push(''); // chuoi_co_doi_chieu
      rowValues.push(''); // chuoi_thieu_du_lieu_doi_chieu
      rowValues.push(escapeCsvField(item.status || 'chua_xu_ly'));
      rowValues.push(escapeCsvField(item.error ? `Lỗi: ${item.error.message}` : ''));
      rowValues.push(escapeCsvField(item.elapsed_ms != null ? String(item.elapsed_ms) : ''));
    }

    csvLines.push(rowValues.join(','));
  }

  // 3. Ghép UTF-8 BOM (\uFEFF) và tải xuống
  const csvContent = '\uFEFF' + csvLines.join('\r\n');
  downloadBlob(new Blob([csvContent], { type: 'text/csv;charset=utf-8;' }), filename);
}

/**
 * Xuất danh sách Batch ra tệp JSON
 */
export function exportToJSON(items: BatchItemWithMeta[], filename = 'address_may_cry_batch_export.json'): void {
  const exportPayload = {
    app: 'Address May Cry',
    target_date: '2025-07-01',
    exported_at: new Date().toISOString(),
    total_items: items.length,
    items: items.map(it => ({
      id: it.id,
      row_index: it.rowIndex,
      input: it.input,
      status: it.status,
      result: it.result || null,
      thanh_phan: it.thanh_phan || it.result?.thanh_phan || null,
      ket_qua_hai_dong: it.ket_qua_hai_dong || it.result?.ket_qua_hai_dong || null,
      elapsed_ms: it.elapsed_ms || null,
      error: it.error || null,
      original_columns: it.originalData || null,
    })),
  };

  const jsonContent = JSON.stringify(exportPayload, null, 2);
  downloadBlob(new Blob([jsonContent], { type: 'application/json;charset=utf-8;' }), filename);
}

/**
 * Hàm kích hoạt tải xuống tệp Blob trên trình duyệt an toàn
 */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
}
