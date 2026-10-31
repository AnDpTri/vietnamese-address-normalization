import React, { useCallback, useEffect, useRef, useState } from 'react';
import './excel.css';

interface SheetInfo { ten: string; tieu_de: string[]; so_dong: number; mau: string[][]; cot_goi_y: number }
interface XemResponse { file_id: string; ten_tep: string; sheets: SheetInfo[]; max_dong: number }
interface TienDo { tong: number; xong: number; trang_thai: 'dang_chay' | 'xong' | 'loi'; loi: string | null; thieu_xa: number; ten_ra: string }

async function docLoi(res: Response): Promise<string> {
  const data = await res.json().catch(() => null);
  return data?.error?.message || `Yêu cầu thất bại (${res.status})`;
}

/** Chuẩn hóa một cột địa chỉ trong file Excel: tải lên, chọn cột, chạy nền, tải về chính file đó đã chuẩn hóa. */
export function ExcelWorkspace() {
  const [xem, setXem] = useState<XemResponse | null>(null);
  const [sheet, setSheet] = useState<string>('');
  const [cot, setCot] = useState<number>(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [tienDo, setTienDo] = useState<TienDo | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [dangTai, setDangTai] = useState(false);
  const [keoTha, setKeoTha] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const sheetInfo = xem?.sheets.find(s => s.ten === sheet) ?? null;

  const taiLen = useCallback(async (file: File) => {
    setLoi(null); setXem(null); setJobId(null); setTienDo(null);
    if (!file.name.toLowerCase().endsWith('.xlsx')) {
      setLoi('Chỉ hỗ trợ file Excel .xlsx. File .xls cũ hoặc .csv hãy mở bằng Excel rồi lưu lại thành .xlsx.');
      return;
    }
    setDangTai(true);
    try {
      const res = await fetch('/api/v1/excel/xem', {
        method: 'POST', body: file,
        headers: { 'Content-Type': 'application/octet-stream', 'X-File-Name': encodeURIComponent(file.name) },
      });
      if (!res.ok) throw new Error(await docLoi(res));
      const data: XemResponse = await res.json();
      setXem(data);
      setSheet(data.sheets[0].ten);
      setCot(data.sheets[0].cot_goi_y);
    } catch (e) {
      setLoi(e instanceof Error ? e.message : 'Không tải được file.');
    } finally {
      setDangTai(false);
    }
  }, []);

  const chay = useCallback(async () => {
    if (!xem) return;
    setLoi(null); setTienDo(null);
    try {
      const res = await fetch('/api/v1/excel/chay', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_id: xem.file_id, sheet, cot }),
      });
      if (!res.ok) throw new Error(await docLoi(res));
      setJobId((await res.json()).job_id);
    } catch (e) {
      setLoi(e instanceof Error ? e.message : 'Không chạy được.');
    }
  }, [xem, sheet, cot]);

  // Hỏi tiến độ mỗi giây tới khi xong.
  useEffect(() => {
    if (!jobId) return;
    let dung = false;
    const hoi = async () => {
      try {
        const res = await fetch(`/api/v1/excel/tien_do?job=${jobId}`);
        if (!res.ok) throw new Error(await docLoi(res));
        const td: TienDo = await res.json();
        if (dung) return;
        setTienDo(td);
        if (td.trang_thai === 'dang_chay') setTimeout(hoi, 1000);
        else if (td.trang_thai === 'loi') setLoi(td.loi || 'Lỗi khi xử lý file.');
      } catch (e) {
        if (!dung) setLoi(e instanceof Error ? e.message : 'Mất kết nối khi hỏi tiến độ.');
      }
    };
    void hoi();
    return () => { dung = true; };
  }, [jobId]);

  const dangChay = tienDo?.trang_thai === 'dang_chay' || (jobId !== null && tienDo === null);
  const xong = tienDo?.trang_thai === 'xong';
  const phanTram = tienDo && tienDo.tong ? Math.round((tienDo.xong / tienDo.tong) * 100) : 0;

  return (
    <div className="excel-page">
      <div className="page-intro">
        <h1>Chuẩn hóa cột địa chỉ trong file Excel</h1>
        <p>Tải file <strong>.xlsx</strong> lên, chọn cột địa chỉ. Kết quả là chính file đó, cột địa chỉ được thay bằng địa chỉ
          chuẩn theo mốc <strong>01/07/2025</strong>; các cột khác giữ nguyên. Ô chưa chắc chắn được tô vàng, kèm ghi chú địa chỉ gốc.</p>
      </div>

      <section className="excel-card" aria-labelledby="buoc-1">
        <h2 id="buoc-1"><span className="excel-step">1</span> Tải file lên</h2>
        <div
          className={`excel-drop${keoTha ? ' is-over' : ''}`}
          onDragOver={e => { e.preventDefault(); setKeoTha(true); }}
          onDragLeave={() => setKeoTha(false)}
          onDrop={e => { e.preventDefault(); setKeoTha(false); const f = e.dataTransfer.files[0]; if (f) void taiLen(f); }}
        >
          <p>Kéo thả file .xlsx vào đây, hoặc</p>
          <button type="button" className="btn btn-primary" onClick={() => inputRef.current?.click()} disabled={dangTai || dangChay}>
            {dangTai ? 'Đang đọc file…' : 'Chọn file'}
          </button>
          <input ref={inputRef} type="file" accept=".xlsx" hidden
            onChange={e => { const f = e.target.files?.[0]; if (f) void taiLen(f); e.target.value = ''; }} />
          {xem && <p className="excel-file">Đã tải: <strong>{xem.ten_tep}</strong></p>}
        </div>
      </section>

      {loi && <div className="alert-box" role="alert">{loi}</div>}

      {xem && sheetInfo && (
        <section className="excel-card" aria-labelledby="buoc-2">
          <h2 id="buoc-2"><span className="excel-step">2</span> Chọn cột địa chỉ</h2>
          <div className="excel-controls">
            {xem.sheets.length > 1 && (
              <label>Sheet
                <select value={sheet} disabled={dangChay}
                  onChange={e => { const s = xem.sheets.find(x => x.ten === e.target.value)!; setSheet(s.ten); setCot(s.cot_goi_y); }}>
                  {xem.sheets.map(s => <option key={s.ten} value={s.ten}>{s.ten} ({s.so_dong} dòng)</option>)}
                </select>
              </label>
            )}
            <label>Cột địa chỉ
              <select value={cot} onChange={e => setCot(Number(e.target.value))} disabled={dangChay}>
                {sheetInfo.tieu_de.map((t, i) => <option key={i} value={i}>{t}</option>)}
              </select>
            </label>
            <span className="excel-count">{sheetInfo.so_dong} dòng dữ liệu
              {sheetInfo.so_dong > xem.max_dong && <> · vượt giới hạn {xem.max_dong} dòng</>}</span>
          </div>
          <div className="excel-table-wrap">
            <table className="excel-table">
              <thead>
                <tr>{sheetInfo.tieu_de.map((t, i) => (
                  <th key={i} className={i === cot ? 'is-chosen' : undefined} onClick={() => !dangChay && setCot(i)}>{t}</th>
                ))}</tr>
              </thead>
              <tbody>
                {sheetInfo.mau.map((r, k) => (
                  <tr key={k}>{r.map((v, i) => <td key={i} className={i === cot ? 'is-chosen' : undefined}>{v}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="excel-hint">Bấm vào tiêu đề để chọn cột. Bảng chỉ hiện {sheetInfo.mau.length} dòng đầu.</p>
        </section>
      )}

      {xem && sheetInfo && (
        <section className="excel-card" aria-labelledby="buoc-3">
          <h2 id="buoc-3"><span className="excel-step">3</span> Chuẩn hóa và tải về</h2>
          {!dangChay && !xong && (
            <button type="button" className="btn btn-primary" onClick={chay} disabled={sheetInfo.so_dong > xem.max_dong}>
              Chuẩn hóa cột “{sheetInfo.tieu_de[cot]}”
            </button>
          )}
          {(dangChay || xong) && (
            <div className="excel-progress" aria-live="polite">
              <div className="excel-bar"><span style={{ width: `${xong ? 100 : phanTram}%` }} /></div>
              <p>{xong ? 'Xong' : 'Đang chuẩn hóa'} {tienDo?.xong ?? 0}/{tienDo?.tong ?? sheetInfo.so_dong} dòng
                {tienDo && tienDo.thieu_xa > 0 && <> · {tienDo.thieu_xa} dòng cần kiểm lại (tô vàng trong file)</>}</p>
            </div>
          )}
          {xong && jobId && (
            <div className="excel-done">
              <a className="btn btn-primary" href={`/api/v1/excel/tai?job=${jobId}`} download={tienDo?.ten_ra}>
                Tải file đã chuẩn hóa ({tienDo?.ten_ra})
              </a>
              <button type="button" className="btn" onClick={() => { setJobId(null); setTienDo(null); }}>Chọn cột khác</button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default ExcelWorkspace;
