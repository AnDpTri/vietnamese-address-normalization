import React, { useState, useRef, useMemo, useEffect } from 'react';
import type { BatchInput, BatchItem } from '../../shared/contracts';
import { normalizeBatch } from '../../shared/api';
import { parseCSV, parsePastedLines, CSV_LIMITS } from './csvParser';
import { exportToCSV, exportToJSON, type BatchItemWithMeta } from './exportUtils';
import { SAMPLE_ADDRESSES, getSampleCsvContent } from './sampleData';
import { ResultDetails } from '../../components/ResultDetails';
import { describeWarning } from '../../lib/warnings';
import { StatusBadge } from '../../components/StatusBadge';
import styles from './batch.module.css';

export interface BatchWorkspaceProps {
  onInspect?: (item: BatchItem) => void;
}

const CHUNK_SIZE = 20;


export default function BatchWorkspace({ onInspect }: BatchWorkspaceProps) {
  // Chế độ nhập liệu: 'paste' (dán) | 'csv' (tệp CSV)
  const [inputMode, setInputMode] = useState<'paste' | 'csv'>('paste');

  // Trạng thái nhập liệu Dán
  const [pastedText, setPastedText] = useState<string>('');

  // Trạng thái nhập liệu CSV
  const [csvFileName, setCsvFileName] = useState<string>('');
  const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
  const [csvRawRows, setCsvRawRows] = useState<Record<string, string>[]>([]);
  const [selectedAddressCol, setSelectedAddressCol] = useState<string>('');
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Danh sách dòng xử lý
  const [batchItems, setBatchItems] = useState<BatchItemWithMeta[]>([]);

  // Trạng thái thực thi
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [processedCount, setProcessedCount] = useState<number>(0);
  const [totalElapsedMs, setTotalElapsedMs] = useState<number>(0);
  const [activeSessionId, setActiveSessionId] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Controller hủy request
  const abortControllerRef = useRef<AbortController | null>(null);

  // Bộ lọc & Tìm kiếm
  const [statusFilter, setStatusFilter] = useState<'all' | 'needs_review' | 'processed' | 'error'>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Phân trang
  const [pageSize, setPageSize] = useState<number>(25);
  const [currentPage, setCurrentPage] = useState<number>(1);

  // Ngăn xem chi tiết (Drawer Inspector)
  const [inspectingItem, setInspectingItem] = useState<BatchItemWithMeta | null>(null);

  const closeDrawerRef = useRef<HTMLButtonElement | null>(null);
  const inspectingId = inspectingItem?.id;
  useEffect(() => {
    if (!inspectingId) return;
    const opener = document.activeElement as HTMLElement | null;
    closeDrawerRef.current?.focus();
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setInspectingItem(null); };
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      opener?.focus?.();
    };
  }, [inspectingId]);
  // Đồng bộ item đang xem chi tiết khi danh sách cập nhật
  useEffect(() => {
    if (inspectingItem) {
      const updated = batchItems.find(it => it.id === inspectingItem.id);
      if (updated) setInspectingItem(updated);
    }
  }, [batchItems, inspectingItem]);

  // Hủy tiến trình khi unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // --- CÁC HÀM XỬ LÝ NHẬP LIỆU ---

  // Xử lý nạp dữ liệu mẫu
  const handleLoadSample = (sample: string) => {
    setPastedText(prev => (prev ? `${prev.trim()}\n${sample}` : sample));
    setErrorMessage(null);
  };

  const handleLoadAllSamples = () => {
    const all = SAMPLE_ADDRESSES.map(s => s.address).join('\n');
    setPastedText(all);
    setErrorMessage(null);
  };

  // Tải về file CSV mẫu
  const handleDownloadSampleCsv = () => {
    const content = getSampleCsvContent();
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mau_dia_chi_chuan.csv';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
  };

  // Xử lý chọn tệp CSV
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) await processUploadedFile(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const processUploadedFile = async (file: File) => {
    setErrorMessage(null);
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setErrorMessage('Hiện tại hệ thống chỉ hỗ trợ tệp định dạng .csv (UTF-8). Vui lòng chuyển đổi tệp bảng tính sang CSV.');
      return;
    }
    if (file.size > CSV_LIMITS.MAX_FILE_BYTES) {
      setErrorMessage(`Dung lượng tệp ${(file.size / (1024 * 1024)).toFixed(1)}MB vượt quá giới hạn tối đa 5MB. Vui lòng chia nhỏ tệp.`);
      return;
    }

    try {
      const text = await file.text();
      const parsed = parseCSV(text);
      setCsvFileName(file.name);
      setCsvHeaders(parsed.headers);
      setCsvRawRows(parsed.rows);
      setSelectedAddressCol(parsed.detectedAddressColumn);
      // Tạo sẵn batchItems ban đầu
      const initialItems: BatchItemWithMeta[] = parsed.rows.map((row, idx) => ({
        id: `csv_row_${idx + 1}`,
        rowIndex: idx + 1,
        input: row[parsed.detectedAddressColumn] || '',
        status: 'pending',
        originalData: row,
      }));
      setBatchItems(initialItems);
      setProcessedCount(0);
      setTotalElapsedMs(0);
    } catch (err: any) {
      setErrorMessage(err.message || 'Lỗi khi đọc tệp CSV.');
    }
  };

  // Thay đổi cột địa chỉ được chọn trong CSV
  const handleAddressColChange = (newCol: string) => {
    setSelectedAddressCol(newCol);
    if (csvRawRows.length > 0) {
      const updated: BatchItemWithMeta[] = csvRawRows.map((row, idx) => ({
        id: `csv_row_${idx + 1}`,
        rowIndex: idx + 1,
        input: row[newCol] || '',
        status: 'pending',
        originalData: row,
      }));
      setBatchItems(updated);
      setProcessedCount(0);
    }
  };

  // Chuẩn bị danh sách BatchItems từ Textarea
  const prepareItemsFromPaste = (): BatchItemWithMeta[] => {
    const lines = parsePastedLines(pastedText);
    return lines.map((line, idx) => ({
      id: `paste_row_${idx + 1}`,
      rowIndex: idx + 1,
      input: line,
      status: 'pending',
      originalData: { dia_chi: line },
    }));
  };

  // --- TIẾN TRÌNH THỰC THI (CHUNK 20) ---

  const handleStartProcessing = async () => {
    setErrorMessage(null);

    let itemsToProcess: BatchItemWithMeta[] = [];
    if (inputMode === 'paste') {
      try {
        itemsToProcess = prepareItemsFromPaste();
        if (itemsToProcess.length === 0) {
          setErrorMessage('Vui lòng nhập hoặc dán ít nhất 1 dòng địa chỉ.');
          return;
        }
      } catch (err: any) {
        setErrorMessage(err.message || 'Lỗi phân tích cú pháp danh sách dán.');
        return;
      }
    } else {
      if (batchItems.length === 0) {
        setErrorMessage('Chưa có dữ liệu từ tệp CSV. Vui lòng tải tệp lên trước.');
        return;
      }
      itemsToProcess = batchItems.map(({ id, rowIndex, input, originalData }) => ({
        id, rowIndex, input, originalData, status: 'pending',
      }));
    }

    setBatchItems(itemsToProcess);
    const sessionId = Date.now();
    setActiveSessionId(sessionId);
    setIsProcessing(true);
    setProcessedCount(0);
    setTotalElapsedMs(0);
    setCurrentPage(1);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Chia thành các chunk kích thước 20
    const total = itemsToProcess.length;
    let completed = 0;
    let cumulativeElapsed = 0;

    for (let i = 0; i < total; i += CHUNK_SIZE) {
      if (abortController.signal.aborted) break;

      const chunk = itemsToProcess.slice(i, i + CHUNK_SIZE);
      const apiInputs: BatchInput[] = chunk.map(it => ({ id: it.id, address: it.input }));

      try {
        const response = await normalizeBatch(apiInputs, abortController.signal);
        cumulativeElapsed += response.elapsed_ms || 0;

        // Cập nhật từng item theo kết quả trả về từ API
        const resultMap = new Map(response.items.map(it => [it.id, it]));

        itemsToProcess = itemsToProcess.map(it => {
          const resItem = resultMap.get(it.id);
          if (resItem) {
            return {
              ...it,
              status: resItem.status,
              result: resItem.result,
              elapsed_ms: resItem.elapsed_ms,
              error: resItem.error,
            };
          }
          return it;
        });

        completed += chunk.length;
        setBatchItems([...itemsToProcess]);
        setProcessedCount(completed);
        setTotalElapsedMs(cumulativeElapsed);
      } catch (err: any) {
        if (abortController.signal.aborted) {
          break;
        }
        // Gán trạng thái error cho chunk gặp sự cố
        itemsToProcess = itemsToProcess.map(it => {
          if (chunk.some(c => c.id === it.id)) {
            return {
              ...it,
              status: 'error' as const,
              error: { code: 'NETWORK_ERROR', message: err.message || 'Lỗi kết nối máy chủ' },
            };
          }
          return it;
        });
        completed += chunk.length;
        setBatchItems([...itemsToProcess]);
        setProcessedCount(completed);
      }
    }

    setIsProcessing(false);
    abortControllerRef.current = null;
  };

  // Hủy tiến trình
  const handleCancelProcessing = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsProcessing(false);
  };

  // Thử lại các dòng bị lỗi (Retry Failed Rows)
  const handleRetryFailed = async () => {
    const failedItems = batchItems.filter(it => it.status === 'error');
    if (failedItems.length === 0) return;

    setErrorMessage(null);
    setIsProcessing(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    let itemsCopy = [...batchItems];
    let cumulativeElapsed = totalElapsedMs;

    for (let i = 0; i < failedItems.length; i += CHUNK_SIZE) {
      if (abortController.signal.aborted) break;

      const chunk = failedItems.slice(i, i + CHUNK_SIZE);
      const apiInputs: BatchInput[] = chunk.map(it => ({ id: it.id, address: it.input }));

      try {
        const response = await normalizeBatch(apiInputs, abortController.signal);
        cumulativeElapsed += response.elapsed_ms || 0;
        const resultMap = new Map(response.items.map(it => [it.id, it]));

        itemsCopy = itemsCopy.map(it => {
          const resItem = resultMap.get(it.id);
          if (resItem) {
            return {
              ...it,
              status: resItem.status,
              result: resItem.result,
              elapsed_ms: resItem.elapsed_ms,
              error: resItem.error,
            };
          }
          return it;
        });

        setBatchItems([...itemsCopy]);
        setTotalElapsedMs(cumulativeElapsed);
      } catch (err: any) {
        if (abortController.signal.aborted) break;
      }
    }

    setIsProcessing(false);
    abortControllerRef.current = null;
  };

  // --- THỐNG KÊ STATE THỰC TẾ ---
  const counts = useMemo(() => {
    const total = batchItems.length;
    let processed = 0;
    let needs_review = 0;
    let error = 0;

    for (const it of batchItems) {
      if (it.status === 'processed') processed++;
      else if (it.status === 'needs_review') needs_review++;
      else if (it.status === 'error') error++;
    }

    return { total, processed, needs_review, error };
  }, [batchItems]);

  // Lọc và Tìm kiếm
  const filteredItems = useMemo(() => {
    return batchItems.filter(it => {
      // 1. Lọc theo trạng thái
      if (statusFilter !== 'all' && it.status !== statusFilter) {
        return false;
      }
      // 2. Tìm kiếm chuỗi
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const inInput = it.input.toLowerCase().includes(q);
        const inOutput = it.result?.dia_chi_chuan?.toLowerCase().includes(q) || false;
        const inCodes = (it.result?.ma_xa || '').includes(q) || (it.result?.ma_tinh || '').includes(q);
        const inWarnings = it.result?.canh_bao?.some(w => w.toLowerCase().includes(q)) || false;
        return inInput || inOutput || inCodes || inWarnings;
      }
      return true;
    });
  }, [batchItems, statusFilter, searchQuery]);

  // Phân trang dữ liệu
  const totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredItems.slice(start, start + pageSize);
  }, [filteredItems, currentPage, pageSize]);

  // Xử lý xuất dữ liệu
  const handleExportCsv = (scope: 'all' | 'filtered') => {
    const itemsToExport = scope === 'filtered' ? filteredItems : batchItems;
    exportToCSV(itemsToExport, csvHeaders, `address_may_cry_${scope}_${Date.now()}.csv`);
  };

  const handleExportJson = (scope: 'all' | 'filtered') => {
    const itemsToExport = scope === 'filtered' ? filteredItems : batchItems;
    exportToJSON(itemsToExport, `address_may_cry_${scope}_${Date.now()}.json`);
  };

  return (
    <div className={styles.batchWorkspace}>
      {/* 1. Header & Lead Question */}
      <section className={styles.headerSection}>
        <div className={styles.titleRow}>
          <h1 className={styles.mainTitle}>Chuẩn hóa hàng loạt</h1>
        </div>
        <p className={styles.leadQuestion}>
          Dán danh sách hoặc tải tệp CSV. Xem các dòng có cảnh báo trước khi xuất kết quả.
        </p>
      </section>

      {/* 2. Tabs chuyển đổi luồng nhập */}
      <nav className={styles.modeTabs} aria-label="Phương thức nhập địa chỉ">
        <button
          type="button"
          className={`${styles.tabBtn} ${inputMode === 'paste' ? styles.activeTab : ''}`}
          aria-pressed={inputMode === 'paste'}
          onClick={() => { setInputMode('paste'); setErrorMessage(null); }}
        >
          Dán danh sách
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${inputMode === 'csv' ? styles.activeTab : ''}`}
          aria-pressed={inputMode === 'csv'}
          onClick={() => { setInputMode('csv'); setErrorMessage(null); }}
        >
          Tải tệp CSV
        </button>
      </nav>

      {/* 3. Thẻ nhập liệu */}
      <section className={styles.inputCard}>
        {inputMode === 'paste' ? (
          <div className={styles.textareaWrapper}>
            <textarea
              className={styles.addressTextarea}
              placeholder="Dán mỗi dòng một địa chỉ cần chuẩn hóa (tối đa 1.000 dòng, mỗi dòng tối đa 2.048 ký tự)…&#10;Ví dụ:&#10;268/10 NGUYỄN VĂN LINH, PHƯỜNG XUÂN KHÁNH, CẦN THƠ&#10;45 XÔ VIẾT NGHỆ TĨNH, P.AN CƯ, NINH KIỀU, CẦN THƠ"
              value={pastedText}
              onChange={e => setPastedText(e.target.value)}
              disabled={isProcessing}
              rows={6}
            />
            <div className={styles.textareaMeta}>
              <span>
                Số dòng hiện tại:{' '}
                <strong>{pastedText ? pastedText.split(/\r\n|\n|\r/).filter(l => l.trim()).length : 0}</strong> /{' '}
                {CSV_LIMITS.MAX_ROWS.toLocaleString('vi-VN')} dòng
              </span>
              <div className={styles.sampleChips}>
                <span>Mẫu thử nhanh:</span>
                <button type="button" className={styles.chipBtn} onClick={() => handleLoadSample(SAMPLE_ADDRESSES[0].address)}>
                  Cần Thơ (Sáp nhập)
                </button>
                <button type="button" className={styles.chipBtn} onClick={() => handleLoadSample(SAMPLE_ADDRESSES[1].address)}>
                  Xô Viết Nghệ Tĩnh
                </button>
                <button type="button" className={styles.chipBtn} onClick={() => handleLoadSample(SAMPLE_ADDRESSES[2].address)}>
                  Dịch Vọng (Chia tách)
                </button>
                <button type="button" className={styles.chipBtn} onClick={handleLoadAllSamples}>
                  Nạp tất cả 8 mẫu
                </button>
                {pastedText && (
                  <button type="button" className={styles.chipBtn} onClick={() => setPastedText('')}>
                    Xóa trắng
                  </button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className={styles.stackCol}>
            <div
              className={`${styles.dropzone} ${isDragOver ? styles.dragOver : ''}`}
              onDragOver={e => { e.preventDefault(); setIsDragOver(true); }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={async e => {
                e.preventDefault();
                setIsDragOver(false);
                const file = e.dataTransfer.files?.[0];
                if (file) await processUploadedFile(file);
              }}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click(); }}
            >
              <div className={styles.dropzoneIcon}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <p className={styles.dropzoneTitle}>
                {csvFileName ? `Đã nạp: ${csvFileName}` : 'Kéo thả tệp CSV vào đây hoặc bấm để chọn'}
              </p>
              <p className={styles.dropzoneSub}>
                Hỗ trợ UTF-8 có/không BOM, dấu phẩy/chấm phẩy/tab, tối đa 5MB và 1.000 dòng.
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,text/csv"
                className={styles.hiddenFileInput}
                onChange={handleFileChange}
              />
            </div>

            {/* Cấu hình cột sau khi đọc CSV */}
            {csvHeaders.length > 0 && (
              <div className={styles.csvPreviewCard}>
                <div className={styles.csvMetaRow}>
                  <span>
                    Tổng cộng: <strong>{csvRawRows.length.toLocaleString('vi-VN')}</strong> dòng dữ liệu ·{' '}
                    <strong>{csvHeaders.length}</strong> cột
                  </span>
                  <div className={styles.columnSelectorGroup}>
                    <label htmlFor="address-col-select" className={styles.strongLabel}>Cột chứa địa chỉ:</label>
                    <select
                      id="address-col-select"
                      className={styles.columnSelect}
                      value={selectedAddressCol}
                      onChange={e => handleAddressColChange(e.target.value)}
                      disabled={isProcessing}
                    >
                      {csvHeaders.map(h => (
                        <option key={h} value={h}>{h}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            )}

            <div className={styles.rowEnd}>
              <button type="button" className={styles.chipBtn} onClick={handleDownloadSampleCsv}>
                Tải tệp CSV mẫu chuẩn (.csv)
              </button>
            </div>
          </div>
        )}

        {/* Thông báo lỗi nếu có */}
        {errorMessage && (
          <div className={styles.errorBox} role="alert">
            {errorMessage}
          </div>
        )}

        {/* Nút hành động chính */}
        <div className={styles.actionRow}>
          <div className={styles.btnGroup}>
            {!isProcessing ? (
              <button
                type="button"
                className={styles.primaryBtn}
                onClick={handleStartProcessing}
                disabled={inputMode === 'paste' ? !pastedText.trim() : csvRawRows.length === 0}
              >
                Bắt đầu chuẩn hóa danh sách
              </button>
            ) : (
              <button
                type="button"
                className={styles.cancelBtn}
                onClick={handleCancelProcessing}
              >
                Hủy dừng tiến trình
              </button>
            )}

            {counts.error > 0 && !isProcessing && (
              <button
                type="button"
                className={styles.secondaryBtn}
                onClick={handleRetryFailed}
              >
                Thử lại {counts.error} dòng lỗi
              </button>
            )}
          </div>

          {/* Nhóm xuất tệp */}
          {batchItems.length > 0 && (
            <div className={styles.btnGroup}>
              <button
                type="button"
                className={styles.secondaryBtn}
                onClick={() => handleExportCsv(statusFilter === 'all' && !searchQuery ? 'all' : 'filtered')}
              >
                Xuất CSV (UTF-8 BOM)
              </button>
              <button
                type="button"
                className={styles.secondaryBtn}
                onClick={() => handleExportJson(statusFilter === 'all' && !searchQuery ? 'all' : 'filtered')}
              >
                Xuất JSON
              </button>
            </div>
          )}
        </div>
      </section>

      <aside className={styles.batchSummary} aria-labelledby="batch-summary-title">
        <h2 id="batch-summary-title">Tiến độ và kết quả</h2>
        {batchItems.length === 0 ? (
          <div className={styles.guideGrid}>
            <p>Thêm địa chỉ và bấm bắt đầu để xem tiến độ và các dòng cần kiểm tra.</p>
            <p>Khi nhập CSV, tệp xuất giữ cột ban đầu và thêm kết quả chuẩn hóa.</p>
          </div>
        ) : (
          <>
            <div className={styles.progressContainer}>
              <div className={styles.progressBarTrack} role="progressbar" aria-label="Tiến độ chuẩn hóa hàng loạt"
                aria-valuemax={counts.total} aria-valuenow={processedCount}>
                <div className={styles.progressBarFill} style={{ width: `${(processedCount / counts.total) * 100}%` }} />
              </div>
              <div className={styles.progressStatsRow} role="status">
                <span><strong>{processedCount}/{counts.total}</strong> dòng đã xử lý</span>
                <span>{isProcessing ? 'Đang xử lý…' : `${totalElapsedMs.toLocaleString('vi-VN')} ms`}</span>
              </div>
            </div>
            <dl className={styles.kpiStrip}>
              <div className={styles.kpiCard}>
                <dt className={styles.kpiLabel}>Tổng số dòng</dt>
                <dd className={styles.kpiValue}>{counts.total}</dd>
              </div>
              <div className={`${styles.kpiCard} ${counts.needs_review > 0 ? styles.kpiWarning : ''}`}>
                <dt className={styles.kpiLabel}>Cần xem lại</dt>
                <dd className={styles.kpiValue}>{counts.needs_review}</dd>
              </div>
              <div className={styles.kpiCard}>
                <dt className={styles.kpiLabel}>Không có cảnh báo</dt>
                <dd className={styles.kpiValue}>{counts.processed}</dd>
              </div>
              <div className={`${styles.kpiCard} ${counts.error > 0 ? styles.kpiNegative : ''}`}>
                <dt className={styles.kpiLabel}>Dòng lỗi</dt>
                <dd className={styles.kpiValue}>{counts.error}</dd>
              </div>
            </dl>
          </>
        )}
      </aside>

      {/* 6. Thanh công cụ Lọc & Tìm kiếm */}
      {batchItems.length > 0 && (
        <section className={styles.toolbarCard}>
          <div className={styles.filterTabs}>
            <button
              type="button"
              className={`${styles.filterBtn} ${statusFilter === 'all' ? styles.activeFilter : ''}`}
              onClick={() => { setStatusFilter('all'); setCurrentPage(1); }}
            >
              Tất cả <span className={styles.filterCountBadge}>{counts.total}</span>
            </button>
            <button
              type="button"
              className={`${styles.filterBtn} ${statusFilter === 'needs_review' ? styles.activeFilter : ''}`}
              onClick={() => { setStatusFilter('needs_review'); setCurrentPage(1); }}
            >
              Cần kiểm tra <span className={styles.filterCountBadge}>{counts.needs_review}</span>
            </button>
            <button
              type="button"
              className={`${styles.filterBtn} ${statusFilter === 'processed' ? styles.activeFilter : ''}`}
              onClick={() => { setStatusFilter('processed'); setCurrentPage(1); }}
            >
              Đã xử lý <span className={styles.filterCountBadge}>{counts.processed}</span>
            </button>
            {counts.error > 0 && (
              <button
                type="button"
                className={`${styles.filterBtn} ${statusFilter === 'error' ? styles.activeFilter : ''}`}
                onClick={() => { setStatusFilter('error'); setCurrentPage(1); }}
              >
                Lỗi <span className={styles.filterCountBadge}>{counts.error}</span>
              </button>
            )}
          </div>

          <div className={styles.searchBox}>
            <span className={styles.searchIcon}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </span>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Tìm theo địa chỉ, mã xã, cảnh báo…"
              value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); setCurrentPage(1); }}
            />
          </div>
        </section>
      )}

      {/* 7. Bảng kết quả (Desktop) & Thẻ kết quả (Mobile) */}
      {batchItems.length > 0 && (
        <section className={styles.tableContainer}>
          {/* Desktop Table View */}
          <div className={styles.tableScrollArea}>
            <table className={styles.dataTable}>
              <thead>
                <tr>
                  <th className={styles.thIdx}>STT</th>
                  <th>Địa chỉ đầu vào</th>
                  <th>Địa chỉ chuẩn hóa (01/07/2025)</th>
                  <th className={styles.thStatus}>Trạng thái</th>
                  <th className={styles.thWarn}>Cảnh báo / Ghi chú</th>
                  <th className={styles.thLatency}>Độ trễ</th>
                  <th className={styles.thAction}>Thành phần</th>
                </tr>
              </thead>
              <tbody>
                {paginatedItems.length === 0 ? (
                  <tr>
                    <td colSpan={7} className={styles.emptyCell}>
                      Không có dòng nào phù hợp với bộ lọc hoặc từ khóa tìm kiếm.
                    </td>
                  </tr>
                ) : (
                  paginatedItems.map(item => (
                    <tr
                      key={item.id}
                      className={`${styles.clickableRow} ${inspectingItem?.id === item.id ? styles.selectedRow : ''}`}
                    >
                      <td className={`${styles.monoCell} ${styles.tdCenter}`}>
                        {item.rowIndex}
                      </td>
                      <td className={styles.tdWrap}>
                        {item.input}
                      </td>
                      <td className={`${styles.tdWrap} ${styles.tdStrong}`}>
                        {item.result?.dia_chi_chuan || (
                          <span className={styles.mutedText}>
                            {item.status === 'error' ? `[Lỗi: ${item.error?.message || 'Không thể xử lý'}]` : 'Chưa xử lý'}
                          </span>
                        )}
                      </td>
                      <td>
                        <span className={`${styles.statusBadge} ${
                          item.status === 'processed' ? styles.statusProcessed :
                          item.status === 'needs_review' ? styles.statusReview :
                          item.status === 'error' ? styles.statusError : styles.statusPending
                        }`}>
                          {item.status === 'processed' ? 'Đã xử lý' :
                           item.status === 'needs_review' ? 'Cần xem lại' :
                           item.status === 'error' ? 'Lỗi' : 'Chờ xử lý'}
                        </span>
                      </td>
                      <td>
                        {item.result?.canh_bao && item.result.canh_bao.length > 0 ? (
                          <div className={styles.warningTagList}>
                            {item.result.canh_bao.map(w => (
                              <span key={w} className={styles.warningTag} title={describeWarning(w).desc}>
                                {describeWarning(w).label}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className={styles.mutedText}>—</span>
                        )}
                      </td>
                      <td className={`${styles.monoCell} ${styles.tdRight}`}>
                        {item.elapsed_ms != null ? `${item.elapsed_ms}ms` : '-'}
                      </td>
                      <td className={styles.tdCenter}>
                        <button
                          type="button"
                          className={`${styles.secondaryBtn} ${styles.rowBtn}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            setInspectingItem(item);
                          }}
                          title="Xem chi tiết từng thành phần"
                        >
                          Chi tiết
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards View (< 768px) */}
          <div className={styles.mobileCardsContainer}>
            {paginatedItems.length === 0 ? (
              <div className={styles.emptyCell}>
                Không tìm thấy dòng phù hợp.
              </div>
            ) : (
              paginatedItems.map(item => (
                <div
                  key={item.id}
                  className={`${styles.mobileCard} ${inspectingItem?.id === item.id ? styles.selectedMobileCard : ''}`}
                >
                  <div className={styles.mobileCardHeader}>
                    <span className={styles.monoCell}>#{item.rowIndex}</span>
                    <span className={`${styles.statusBadge} ${
                      item.status === 'processed' ? styles.statusProcessed :
                      item.status === 'needs_review' ? styles.statusReview :
                      item.status === 'error' ? styles.statusError : styles.statusPending
                    }`}>
                      {item.status === 'processed' ? 'Đã xử lý' :
                       item.status === 'needs_review' ? 'Cần xem lại' :
                       item.status === 'error' ? 'Lỗi' : 'Chờ'}
                    </span>
                  </div>
                  <div className={styles.mobileCardInput}>{item.input}</div>
                  {item.result?.dia_chi_chuan && (
                    <div className={styles.mobileCardOutput}>{item.result.dia_chi_chuan}</div>
                  )}
                  {item.result?.canh_bao && item.result.canh_bao.length > 0 && (
                    <div className={styles.warningTagList}>
                      {item.result.canh_bao.map(w => (
                        <span key={w} className={styles.warningTag}>
                          {describeWarning(w).label}
                        </span>
                      ))}
                    </div>
                  )}
                  <button
                    type="button"
                    className={`${styles.secondaryBtn} ${styles.cardBtn}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setInspectingItem(item);
                    }}
                  >
                    Xem chi tiết
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Thanh phân trang */}
          <div className={styles.paginationBar}>
            <div>
              Hiển thị <strong>{paginatedItems.length}</strong> / <strong>{filteredItems.length}</strong> dòng phù hợp
              {batchItems.length !== filteredItems.length && ` (trong tổng số ${batchItems.length} dòng)`}
            </div>
            <div className={styles.pageControls}>
              <button
                type="button"
                className={styles.pageBtn}
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              >
                Trước
              </button>
              <span>Trang {currentPage} / {totalPages}</span>
              <button
                type="button"
                className={styles.pageBtn}
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              >
                Sau
              </button>
              <select
                className={styles.columnSelect}
                value={pageSize}
                onChange={e => { setPageSize(Number(e.target.value)); setCurrentPage(1); }}
              >
                <option value={25}>25 dòng/trang</option>
                <option value={50}>50 dòng/trang</option>
                <option value={100}>100 dòng/trang</option>
              </select>
            </div>
          </div>
        </section>
      )}

      {/* 8. Ngăn xem chi tiết chuyên sâu (Detail Drawer Inspector) */}
      {inspectingItem && (
        <div className={styles.drawerBackdrop} onClick={() => setInspectingItem(null)}>
          <aside
            className={styles.drawerPanel}
            onClick={e => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Chi tiết chuẩn hóa địa chỉ"
          >
            <div className={styles.drawerHeader}>
              <h3 className={styles.drawerTitle}>
                Chi tiết dòng {inspectingItem.rowIndex}
              </h3>
              <button
                type="button"
                className={styles.closeDrawerBtn}
                ref={closeDrawerRef}
                onClick={() => setInspectingItem(null)}
                title="Đóng bảng chi tiết"
                aria-label="Đóng bảng chi tiết"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            <div className={styles.drawerBody}>
              <div className={styles.detailStatusRow}>
                {inspectingItem.status === 'processed' || inspectingItem.status === 'needs_review' || inspectingItem.status === 'error'
                  ? <StatusBadge status={inspectingItem.status} />
                  : <span className={`${styles.statusBadge} ${styles.statusPending}`}>Đang chờ</span>}
                <span className={styles.monoCell}>
                  {inspectingItem.elapsed_ms != null ? `Độ trễ: ${inspectingItem.elapsed_ms} ms` : ''}
                </span>
              </div>

              <div className={styles.detailSection}>
                <span className={styles.sectionLabel}>Địa chỉ chuẩn</span>
                <div className={`${styles.detailValueBox} ${styles.detailAccent}`}>
                  {inspectingItem.result?.dia_chi_chuan || (
                    <span className={styles.mutedText}>Chưa có kết quả hoặc gặp lỗi</span>
                  )}
                </div>
              </div>

              <div className={styles.detailSection}>
                <span className={styles.sectionLabel}>Địa chỉ gốc</span>
                <div className={styles.detailValueBox}>{inspectingItem.input}</div>
              </div>

              {inspectingItem.error && (
                <p className={styles.mutedText} role="status">{inspectingItem.error.message}</p>
              )}

              <ResultDetails data={inspectingItem} fileName={`dong_${inspectingItem.id}.json`} />
              {onInspect && inspectingItem.status !== 'pending' && (
                <div className={styles.rowEnd}>
                  <button
                    type="button"
                    className={styles.secondaryBtn}
                    onClick={() => {
                      onInspect(inspectingItem);
                      setInspectingItem(null);
                    }}
                  >
                    Mở ở màn một địa chỉ →
                  </button>
                </div>
              )}
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
