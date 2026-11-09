import React, { useEffect, useRef, useState } from 'react';
import type { DonViBuoc, GiaiThich, NormalizeResponse } from '../../shared/contracts';
import { KIND_SHORT, KIND_ORDER, kindOf } from '../../lib/kinds';
import { WarningList } from '../../components/WarningList';
import { StatusBadge } from '../../components/StatusBadge';
import './steps.css';

const CAP: Record<string, string> = { xa: 'Xã / phường', huyen: 'Quận / huyện', tinh: 'Tỉnh / TP' };
const MOC: Record<string, string> = { cu: 'cũ', moi: 'mới' };
const KHOP: Record<string, string> = {
  chinh_xac: 'Khớp đúng',
  khong_dau: 'Không dấu',
  viet_tat: 'Viết tắt',
  sai_chinh_ta: 'Sai chính tả',
};
const TRUONG_DUONG: Record<string, string> = {
  so_nha: 'Số nhà', ngo_ngach_hem: 'Ngõ / hẻm', thon_xom: 'Thôn / xóm', duong: 'Đường / phố',
};

/** Câu gốc tô màu theo vai trò mà Char-CNN + CRF đoán. */
function ToMau({ chuoi, vaiTro }: { chuoi: string; vaiTro: GiaiThich['vai_tro'] }) {
  const doan: React.ReactNode[] = [];
  let con = 0;
  [...vaiTro].sort((a, b) => a.bat_dau - b.bat_dau).forEach((v, i) => {
    if (v.bat_dau < con) return;
    if (v.bat_dau > con) doan.push(<span key={`g${i}`} className="hl-gap">{chuoi.slice(con, v.bat_dau)}</span>);
    const kind = kindOf(v.truong);
    doan.push(
      <mark key={i} className="hl-chip" data-kind={kind}>
        <span className="hl-text">{chuoi.slice(v.bat_dau, v.ket_thuc)}</span>
        <span className="hl-cap">{KIND_SHORT[kind]}</span>
      </mark>,
    );
    con = v.ket_thuc;
  });
  if (con < chuoi.length) doan.push(<span key="cuoi" className="hl-gap">{chuoi.slice(con)}</span>);
  const dung = new Set(vaiTro.map((v) => kindOf(v.truong)));
  return (
    <>
      <p className="hl-string" lang="vi">{doan}</p>
      <ul className="legend" aria-label="Chú thích màu">
        {KIND_ORDER.filter((k) => dung.has(k)).map((k) => (
          <li key={k}><span className="kind-tag" data-kind={k}>{KIND_SHORT[k]}</span></li>
        ))}
      </ul>
    </>
  );
}

function TheDonVi({ u }: { u: DonViBuoc }) {
  return (
    <span className="unit-chip" data-kind={kindOf(u.cap)}>
      <span className="unit-name">{u.ten}</span>
      {u.moc && <span className="unit-moc">{MOC[u.moc] ?? u.moc}</span>}
      {u.doan && <span className="unit-src">← “{u.doan}”</span>}
    </span>
  );
}

function BuocTachTu({ g }: { g: GiaiThich }) {
  return (
    <ol className="token-row" aria-label="Các từ sau khi tách">
      {g.token.map((t, i) => (
        <li key={i} className="token"><span className="token-i">{i}</span>{t}</li>
      ))}
    </ol>
  );
}

function BuocUngVien({ g }: { g: GiaiThich }) {
  const dong = g.ung_vien.flatMap((nhom) => nhom.top.map((u, j) => ({ nhom, u, dau: j === 0 })));
  if (dong.length === 0) return <p className="step-empty">Không tra được đơn vị hành chính nào.</p>;
  return (
    <div className="table-wrap">
      <table className="steps-table">
        <thead>
          <tr><th scope="col">Đoạn chữ</th><th scope="col">Tìm thấy trong danh mục</th><th scope="col">Cách khớp</th><th scope="col" className="num">Điểm</th></tr>
        </thead>
        <tbody>
          {dong.map(({ nhom, u, dau }, i) => (
            <tr key={i} className={dau ? 'is-first' : ''}>
              <td className="mono">{dau ? nhom.doan : ''}</td>
              <td>
                <span className="kind-tag" data-kind={kindOf(u.cap)}>{CAP[u.cap] ?? u.cap}</span>{' '}
                {u.ten} <span className="moc">({MOC[u.moc] ?? u.moc})</span>
              </td>
              <td><span className="badge badge-neutral">{KHOP[u.kieu_khop ?? ''] ?? u.kieu_khop}</span></td>
              <td className="num mono">{u.diem?.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BuocGhep({ g }: { g: GiaiThich }) {
  const soUngVien = g.ung_vien.reduce((s, n) => s + n.so_ung_vien, 0);
  const so = [
    { n: g.token.length, t: 'từ' },
    { n: soUngVien, t: 'ứng viên' },
    { n: g.so_gia_thuyet, t: 'cách ghép hợp lệ' },
    { n: g.so_gia_thuyet_gan, t: 'cách hiểu ngang nhau' },
  ];
  return (
    <ol className="funnel" aria-label="Số lượng qua từng bước">
      {so.map((s) => (
        <li key={s.t}><strong>{s.n}</strong><span>{s.t}</span></li>
      ))}
    </ol>
  );
}

function BuocXepHang({ g }: { g: GiaiThich }) {
  if (g.gia_thuyet.length === 0) return <p className="step-empty">Không có giả thuyết nào.</p>;
  const cao = Math.max(...g.gia_thuyet.map((x) => x.diem));
  const thap = Math.min(0, ...g.gia_thuyet.map((x) => x.diem));
  return (
    <ol className="hyp-list">
      {g.gia_thuyet.map((h, i) => (
        <li key={i} className={`hyp${i === 0 ? ' is-top' : ''}`}>
          <div className="hyp-head">
            <span className="hyp-rank">#{i + 1}</span>
            {i === 0 && <span className="badge badge-ok">Được chọn</span>}
            <span className="hyp-score mono">{h.diem.toFixed(3)}</span>
          </div>
          <div className="hyp-bar" aria-hidden="true">
            <span style={{ width: `${Math.max(4, ((h.diem - thap) / (cao - thap || 1)) * 100)}%` }} />
          </div>
          <div className="hyp-units">
            {[...h.don_vi].reverse().map((u, j) => <TheDonVi key={j} u={u} />)}
          </div>
          {h.chua_phan_loai && (
            <p className="hyp-left">Bỏ sót: <del className="mono">{h.chua_phan_loai}</del></p>
          )}
        </li>
      ))}
    </ol>
  );
}

function BuocDuong({ g }: { g: GiaiThich }) {
  if (g.duong.length === 0) return <p className="step-empty">Không có tên cần đổi.</p>;
  return (
    <ul className="change-list">
      {g.duong.map((d) => (
        <li key={d.truong}>
          <span className="change-label">{TRUONG_DUONG[d.truong] ?? d.truong}</span>
          <span className="change-before mono">{d.truoc || '(trống)'}</span>
          <span className="change-arrow" aria-label="đổi thành">→</span>
          <span className="change-after">{d.sau || '(trống)'}</span>
        </li>
      ))}
    </ul>
  );
}

function BuocChuyenDoi({ g }: { g: GiaiThich }) {
  if (g.chuyen_doi.length === 0) return <p className="step-empty">Không có đơn vị hành chính để chuyển.</p>;
  return (
    <div className="convert-list">
      {g.chuyen_doi.map((c, i) => {
        const daMoi = c.cu.length > 0 && c.cu.every((u) => u.moc === 'moi');
        return (
          <div key={i} className="convert">
            <div className="convert-col">
              <h4>{daMoi ? 'Địa chỉ đã ghi theo đơn vị mới' : 'Đơn vị cũ (trước 01/07/2025)'}</h4>
              <ul>{c.cu.map((u) => <li key={u.cap + u.ma}><TheDonVi u={{ ...u, doan: undefined }} /></li>)}</ul>
            </div>
            <span className="convert-arrow" aria-hidden="true">→</span>
            <div className="convert-col">
              <h4>Đơn vị mới</h4>
              <ul>
                {c.tinh_moi.map((t) => <li key={t.ma}><span className="unit-chip" data-kind="tinh"><span className="unit-name">{t.ten}</span></span></li>)}
                {c.xa_moi.length === 1 && (
                  <li><span className="unit-chip" data-kind="xa"><span className="unit-name">{c.xa_moi[0].ten}</span></span></li>
                )}
              </ul>
              {c.xa_moi.length > 1 && (
                <div className="split-note">
                  <strong>Xã cũ bị chia về {c.xa_moi.length} nơi</strong>, không đủ thông tin để chọn:
                  <ul>{c.xa_moi.map((x) => <li key={x.ma}>{x.ten} <span className="moc mono">{x.ma}</span></li>)}</ul>
                </div>
              )}
              {c.xa_moi.length === 0 && <p className="step-empty">Không xác định được xã mới.</p>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface BuocDef { tieu_de: string; mo_ta: string; tep: string; noi_dung: React.ReactNode }

function dsBuoc(r: NormalizeResponse, g: GiaiThich): BuocDef[] {
  return [
    { tieu_de: 'Tách từ', tep: 'src/tien_xu_ly/tien_xu_ly.py',
      mo_ta: 'Cắt chuỗi thành từng từ, tách dấu câu và chữ dính số (ví dụ “P.5” thành “P”, “5”).',
      noi_dung: <BuocTachTu g={g} /> },
    { tieu_de: 'Mô hình đoán vai trò từng chữ', tep: 'src/tien_xu_ly/char_cnn.py · Char-CNN + CRF',
      mo_ta: 'Mạng CNN đọc từng ký tự, lớp CRF chọn chuỗi nhãn hợp lệ. Đây mới là dự đoán ban đầu, các bước sau có thể sửa lại.',
      noi_dung: <ToMau chuoi={r.input} vaiTro={g.vai_tro} /> },
    { tieu_de: 'Tra danh mục hành chính', tep: 'src/tien_xu_ly/tim_kiem.py · trie',
      mo_ta: 'Dò từng đoạn chữ trong danh mục cũ và mới, chấp nhận không dấu, viết tắt, sai chính tả.',
      noi_dung: <BuocUngVien g={g} /> },
    { tieu_de: 'Ghép thành các cách hiểu hợp lệ', tep: 'src/tien_xu_ly/giai_ma.py · beam search',
      mo_ta: 'Chỉ giữ những cách ghép đúng cây hành chính: xã phải thuộc huyện, huyện phải thuộc tỉnh.',
      noi_dung: <BuocGhep g={g} /> },
    { tieu_de: 'Xếp hạng, chọn cách hiểu tốt nhất', tep: 'src/tien_xu_ly/xep_hang.py · LightGBM LambdaRank',
      mo_ta: 'Mô hình xếp hạng chấm điểm từng cách hiểu theo 28 đặc trưng. Điểm dùng để so sánh, không phải xác suất.',
      noi_dung: <BuocXepHang g={g} /> },
    { tieu_de: 'Chuẩn hóa tên đường', tep: 'src/tien_xu_ly/chuan_ten_duong.py',
      mo_ta: 'Đưa tên đường gõ không dấu hoặc sai về đúng tên trong từ điển đường.',
      noi_dung: <BuocDuong g={g} /> },
    { tieu_de: 'Chuyển sang đơn vị hành chính mới', tep: 'src/chuyen_doi/doi_chieu.py',
      mo_ta: 'Tra bảng đối chiếu cũ → mới theo mốc 01/07/2025. Xã cũ bị chia mà thiếu bằng chứng thì để trống, không đoán.',
      noi_dung: <BuocChuyenDoi g={g} /> },
  ];
}

export function StepsView({ response }: { response: NormalizeResponse }) {
  const g = response.giai_thich;
  const [hien, setHien] = useState(1);
  const cuoiRef = useRef<HTMLLIElement | null>(null);

  useEffect(() => { setHien(1); }, [response]);

  const buoc = g ? dsBuoc(response, g) : [];
  const tong = buoc.length + 1; // + bước kết quả
  const xong = hien >= tong;

  useEffect(() => {
    if (hien > 1) cuoiRef.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [hien]);

  // Phím → hoặc PageDown để trình bày bước tiếp, khi không gõ trong ô nhập
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target;
      if (el instanceof Element && el.closest('input, textarea, select, button, [contenteditable]')) return;
      if (e.key === 'ArrowRight' || e.key === 'PageDown') { e.preventDefault(); setHien((h) => Math.min(tong, h + 1)); }
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); setHien((h) => Math.max(1, h - 1)); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [tong]);

  if (!g) {
    return <p className="review-note" role="note">Máy chủ chưa trả về các bước trung gian. Hãy chuẩn hóa lại.</p>;
  }

  const r = response.result;
  return (
    <section className="steps" aria-labelledby="steps-title">
      <div className="steps-head">
        <div>
          <h2 className="card-title" id="steps-title" tabIndex={-1}>Hệ thống xử lý địa chỉ qua {buoc.length} bước</h2>
          <p className="steps-input mono">{response.input}</p>
        </div>
        <div className="steps-controls">
          <span className="steps-progress mono" aria-live="polite">{Math.min(hien, tong)}&nbsp;/&nbsp;{tong}</span>
          <button type="button" className="btn btn-sm" onClick={() => setHien((h) => Math.max(1, h - 1))} disabled={hien <= 1}>‹ Lùi</button>
          <button type="button" className="btn btn-sm btn-primary" onClick={() => setHien((h) => Math.min(tong, h + 1))} disabled={xong}>Bước tiếp ›</button>
          <button type="button" className="btn btn-sm btn-ghost" onClick={() => setHien(xong ? 1 : tong)}>{xong ? 'Từ đầu' : 'Hiện tất cả'}</button>
        </div>
      </div>
      <p className="muted-note steps-hint">Mẹo khi trình bày: bấm phím <kbd>→</kbd> để sang bước tiếp, <kbd>←</kbd> để lùi.</p>

      <ol className="step-list">
        {buoc.slice(0, hien).map((b, i) => (
          <li key={b.tieu_de} className="step" ref={i === hien - 1 ? cuoiRef : undefined}>
            <span className="step-n" aria-hidden="true">{i + 1}</span>
            <div className="step-body">
              <div className="step-title">
                <h3>{b.tieu_de}</h3>
                <code className="step-file">{b.tep}</code>
              </div>
              <p className="step-desc">{b.mo_ta}</p>
              <div className="step-visual">{b.noi_dung}</div>
            </div>
          </li>
        ))}
        {xong && (
          <li className="step is-result" ref={cuoiRef}>
            <span className="step-n" aria-hidden="true">✓</span>
            <div className="step-body">
              <div className="step-title">
                <h3>Kết quả</h3>
                <StatusBadge status={response.status} />
                <span className="muted-note mono">{response.elapsed_ms}&nbsp;ms</span>
              </div>
              <p className="result-line">{r.dia_chi_chuan || 'Không ghép được địa chỉ chuẩn.'}</p>
              {r.phan_chua_phan_loai && (
                <p className="hyp-left">Phần chữ chưa dùng tới: <del className="mono">{r.phan_chua_phan_loai}</del></p>
              )}
              <WarningList codes={r.canh_bao} />
            </div>
          </li>
        )}
      </ol>
    </section>
  );
}
