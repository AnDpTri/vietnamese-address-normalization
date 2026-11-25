import React, { useEffect, useState } from 'react';
import type { DonViBuoc, GiaiThich, NormalizeResponse } from '../../shared/contracts';
import { KIND_SHORT, kindOf } from '../../lib/kinds';
import { describeWarning } from '../../lib/warnings';
import { IconCheck } from '../../components/Icons';
import { StatusBadge } from '../../components/StatusBadge';
import './steps.css';

const MOC: Record<string, string> = { cu: 'cũ', moi: 'mới' };
const KHOP: Record<string, string> = {
  chinh_xac: 'đúng',
  khong_dau: 'không dấu',
  viet_tat: 'viết tắt',
  sai_chinh_ta: 'sai chính tả',
};
const TRUONG_DUONG: Record<string, string> = {
  so_nha: 'Số nhà', ngo_ngach_hem: 'Ngõ', thon_xom: 'Thôn', duong: 'Đường',
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
  return <p className="hl-string sv-roles" lang="vi">{doan}</p>;
}

function Don({ u, nguon = false }: { u: DonViBuoc; nguon?: boolean }) {
  return (
    <span className="sv-unit" data-kind={kindOf(u.cap)} title={u.doan ? `từ “${u.doan}”` : undefined}>
      {u.ten}<small>{MOC[u.moc] ?? u.moc}</small>
      {nguon && u.doan && <em>“{u.doan}”</em>}
    </span>
  );
}

function BuocTachTu({ g }: { g: GiaiThich }) {
  return (
    <p className="sv-tokens">
      {g.token.map((t, i) => <span key={i}>{t}</span>)}
    </p>
  );
}

function BuocUngVien({ g }: { g: GiaiThich }) {
  if (g.ung_vien.length === 0) return <p className="sv-empty">Không tra được đơn vị nào.</p>;
  return (
    <ul className="sv-rows">
      {g.ung_vien.map((nhom) => {
        const u = nhom.top[0];
        return (
          <li key={nhom.doan}>
            <code>{nhom.doan}</code>
            <span className="sv-arrow">→</span>
            <Don u={u} />
            <span className="sv-meta">khớp {KHOP[u.kieu_khop ?? ''] ?? u.kieu_khop}</span>
            {nhom.so_ung_vien > 1 && <span className="sv-meta">(và {nhom.so_ung_vien - 1} nơi khác)</span>}
          </li>
        );
      })}
    </ul>
  );
}

function BuocGhep({ g }: { g: GiaiThich }) {
  const soUngVien = g.ung_vien.reduce((s, n) => s + n.so_ung_vien, 0);
  return (
    <p className="sv-funnel">
      <b>{g.token.length}</b> từ <span>→</span> <b>{soUngVien}</b> tên tìm được <span>→</span>{' '}
      <b>{g.so_gia_thuyet}</b> cách ghép hợp lệ
    </p>
  );
}

function BuocXepHang({ g }: { g: GiaiThich }) {
  if (g.gia_thuyet.length === 0) return <p className="sv-empty">Không có giả thuyết.</p>;
  const cao = Math.max(...g.gia_thuyet.map((x) => x.diem));
  const thap = Math.min(0, ...g.gia_thuyet.map((x) => x.diem));
  return (
    <ol className="sv-hyps">
      {g.gia_thuyet.map((h, i) => (
        <li key={i} className={i === 0 ? 'is-top' : ''}>
          <span className="sv-rank">#{i + 1}</span>
          <span className="sv-bar" aria-hidden="true">
            <span style={{ width: `${Math.max(6, ((h.diem - thap) / (cao - thap || 1)) * 100)}%` }} />
          </span>
          <span className="sv-score">{h.diem.toFixed(1)}</span>
          <span className="sv-units">
            {[...h.don_vi].reverse().map((u, j) => <Don key={j} u={u} />)}
            {h.chua_phan_loai && <span className="sv-left">bỏ sót <del>{h.chua_phan_loai}</del></span>}
          </span>
        </li>
      ))}
    </ol>
  );
}

function BuocDuong({ g }: { g: GiaiThich }) {
  if (g.duong.length === 0) return <p className="sv-empty">Không cần đổi.</p>;
  return (
    <ul className="sv-rows">
      {g.duong.map((d) => (
        <li key={d.truong}>
          <span className="sv-meta">{TRUONG_DUONG[d.truong] ?? d.truong}</span>
          <s>{d.truoc || '(trống)'}</s>
          <span className="sv-arrow">→</span>
          <b>{d.sau || '(trống)'}</b>
        </li>
      ))}
    </ul>
  );
}

function BuocChuyenDoi({ g }: { g: GiaiThich }) {
  if (g.chuyen_doi.length === 0) return <p className="sv-empty">Không có đơn vị để chuyển.</p>;
  return (
    <ul className="sv-rows">
      {g.chuyen_doi.map((c, i) => (
        <li key={i} className="sv-convert">
          <span className="sv-units">{c.cu.map((u) => <Don key={u.cap + u.ma} u={u} />)}</span>
          <span className="sv-arrow">→</span>
          <span className="sv-units">
            {c.tinh_moi.map((t) => <span key={t.ma} className="sv-unit" data-kind="tinh">{t.ten}<small>mới</small></span>)}
            {c.xa_moi.length === 1 && <span className="sv-unit" data-kind="xa">{c.xa_moi[0].ten}<small>mới</small></span>}
            {c.xa_moi.length > 1 && (
              <span className="sv-split" title={c.xa_moi.map((x) => x.ten).join(', ')}>
                Xã cũ bị chia: {c.xa_moi.map((x) => x.ten).join(' / ')}
              </span>
            )}
            {c.xa_moi.length === 0 && <span className="sv-split">Không xác định được xã mới</span>}
          </span>
        </li>
      ))}
    </ul>
  );
}

interface CongNghe { ten: string[]; lam_gi: string; vi_sao: string }
interface BuocDef { tieu_de: string; tom_tat: string; module: 1 | 2; cong_nghe: CongNghe; noi_dung: React.ReactNode; rong?: boolean }

const TEN_VAI_TRO: Record<string, string> = {
  so_nha: 'số nhà', ngo_ngach_hem: 'ngõ', thon_xom: 'thôn', duong: 'tên đường', xa: 'xã/phường', huyen: 'quận/huyện', tinh: 'tỉnh',
};

const lietKe = (ds: string[]) => (ds.length <= 1 ? ds.join('') : `${ds.slice(0, -1).join(', ')} và ${ds[ds.length - 1]}`);

/** Một câu nói thường cho từng bước, viết từ chính đầu ra của câu đang xem. */
function tomTat(g: GiaiThich) {
  const chon = g.gia_thuyet[0];
  const tenChon = chon ? [...chon.don_vi].reverse().map((u) => u.ten) : [];
  const cd = g.chuyen_doi[0];
  const xaCu = cd?.cu.find((u) => u.cap === 'xa');
  const daMoi = !!cd && cd.cu.length > 0 && cd.cu.every((u) => u.moc === 'moi');
  let chuyen = 'Không có đơn vị hành chính để chuyển.';
  if (cd && daMoi) chuyen = 'Địa chỉ đã ghi theo đơn vị mới nên giữ nguyên.';
  else if (cd && cd.xa_moi.length > 1) chuyen = `${xaCu?.ten ?? 'Xã cũ'} đã bị chia về ${cd.xa_moi.length} nơi, không đủ thông tin để chọn nên để trống phần xã.`;
  else if (cd && cd.xa_moi.length === 1) chuyen = `${xaCu?.ten ?? 'Xã cũ'} nay thuộc ${cd.xa_moi[0].ten}, ${cd.tinh_moi[0]?.ten ?? ''}.`;
  else if (cd) chuyen = `Đổi được tỉnh sang ${cd.tinh_moi[0]?.ten ?? '(không rõ)'}, chưa xác định được xã.`;
  return {
    tach: `Câu được cắt thành ${g.token.length} từ.`,
    vai_tro: g.vai_tro.length
      ? `Mô hình đoán: ${lietKe(g.vai_tro.map((v) => `“${v.doan}” là ${TEN_VAI_TRO[v.truong] ?? v.truong}`))}.`
      : 'Mô hình không nhận ra phần nào.',
    tra: `Tìm thấy ${g.ung_vien.length} đoạn chữ khớp với tên đơn vị hành chính.`,
    ghep: `Có ${g.so_gia_thuyet} cách ghép đúng cấp bậc hành chính.`,
    xep: chon
      ? `Chọn ${lietKe(tenChon)}${chon.chua_phan_loai ? `, bỏ sót chữ “${chon.chua_phan_loai}”` : ''}.`
      : 'Không có cách hiểu nào.',
    duong: g.duong.length ? `Sửa ${lietKe(g.duong.map((d) => `“${d.truoc}” thành “${d.sau}”`))}.` : 'Tên đường không cần sửa.',
    chuyen,
  };
}

function dsBuoc(r: NormalizeResponse, g: GiaiThich): BuocDef[] {
  const t = tomTat(g);
  return [
    { tieu_de: 'Tách từ', tom_tat: t.tach, module: 1,
      cong_nghe: {
        ten: ['Quy tắc tách chữ'],
        lam_gi: 'Cắt câu thành từng từ, tách dấu câu và chữ dính số, nhớ vị trí của từng từ.',
        vi_sao: 'Việc này đơn giản nên dùng quy tắc là đủ. Nhớ vị trí để các bước sau tô màu đúng chỗ người dùng gõ.',
      },
      noi_dung: <BuocTachTu g={g} /> },
    { tieu_de: 'Đoán vai trò từng chữ', tom_tat: t.vai_tro, module: 1,
      cong_nghe: {
        ten: ['Mạng nơ-ron Char-CNN', 'CRF', 'PyTorch'],
        lam_gi: 'Mô hình đọc từng ký tự và đoán nó thuộc phần nào của địa chỉ: số nhà, ngõ, thôn, đường, xã, huyện hay tỉnh. Đây chỉ là đoán ban đầu, các bước sau sẽ kiểm lại.',
        vi_sao: 'Đọc từng ký tự nên vẫn hiểu khi gõ không dấu, viết dính hay sai chính tả. Mô hình nhỏ (1,4 MB), chạy nhanh trên máy thường. Đã thử mô hình lớn hơn (ViDeBERTa) nhưng kém hơn và chậm gấp đôi.',
      },
      noi_dung: <ToMau chuoi={r.input} vaiTro={g.vai_tro} />, rong: true },
    { tieu_de: 'Tra danh mục hành chính', tom_tat: t.tra, module: 1,
      cong_nghe: {
        ten: ['Cây tra cứu (trie)', 'Chấp nhận sai 1 ký tự'],
        lam_gi: 'Dò từng cụm chữ trong danh sách mọi tỉnh, huyện, xã cả cũ lẫn mới, chấp nhận không dấu, viết tắt, sai một ký tự.',
        vi_sao: 'Tra hàng chục nghìn tên chỉ mất vài phần nghìn giây. Bước này không dựa vào bước 2, nên nếu mô hình đoán sai thì ở đây vẫn có tên đúng.',
      },
      noi_dung: <BuocUngVien g={g} /> },
    { tieu_de: 'Ghép thành cách hiểu', tom_tat: t.ghep, module: 1,
      cong_nghe: {
        ten: ['Beam search', 'Kiểm tra cấp bậc hành chính'],
        lam_gi: 'Ghép các tên tìm được thành bộ tỉnh – huyện – xã, chỉ giữ bộ nào mà xã thật sự thuộc huyện, huyện thật sự thuộc tỉnh.',
        vi_sao: 'Cả nước có nhiều xã trùng tên. Kiểm cấp bậc giúp loại ngay những nơi không khớp; beam search giữ lại các cách ghép tốt nhất để không phải thử hết mọi khả năng.',
      },
      noi_dung: <BuocGhep g={g} /> },
    { tieu_de: 'Chấm điểm, chọn cách hiểu', tom_tat: t.xep, module: 1,
      cong_nghe: {
        ten: ['LightGBM', 'Học xếp hạng (LambdaRank)'],
        lam_gi: 'Mô hình chấm điểm từng cách hiểu dựa trên 28 dấu hiệu: dùng được bao nhiêu chữ, khớp đúng hay khớp gần, có trộn tên cũ với tên mới không… rồi chọn cách điểm cao nhất. Nếu vài cách sát điểm nhau mà chỉ ra các xã khác nhau thì hệ thống không khẳng định.',
        vi_sao: 'Mô hình học từ ví dụ nên tốt hơn tự đặt luật bằng tay. Mô hình nhẹ, chạy nhanh, xem được dấu hiệu nào quan trọng. Điểm chỉ để so sánh, không phải phần trăm đúng.',
      },
      noi_dung: <BuocXepHang g={g} />, rong: true },
    { tieu_de: 'Sửa tên đường', tom_tat: t.duong, module: 1,
      cong_nghe: {
        ten: ['Từ điển tên đường'],
        lam_gi: 'Tra tên đường trong từ điển của đúng tỉnh vừa chọn để thêm dấu, viết đầy đủ, viết hoa đúng.',
        vi_sao: 'Không có danh sách đường chính thức, nên chỉ sửa khi trong tỉnh có đúng một tên khớp, và luôn báo khi phải đoán.',
      },
      noi_dung: <BuocDuong g={g} /> },
    { tieu_de: 'Đổi sang địa giới mới', tom_tat: t.chuyen, module: 2,
      cong_nghe: {
        ten: ['Tra bảng đối chiếu'],
        lam_gi: 'Tra bảng đối chiếu chính thức để đổi tỉnh, xã cũ sang tỉnh, xã mới từ ngày 01/07/2025.',
        vi_sao: 'Việc sáp nhập do nhà nước quy định, tra bảng là chắc chắn đúng, không cần mô hình đoán. Xã cũ bị chia mà không đủ thông tin thì để trống chứ không đoán bừa.',
      },
      noi_dung: <BuocChuyenDoi g={g} /> },
  ];
}

export function StepsView({ response, onDoiDiaChi }: { response: NormalizeResponse; onDoiDiaChi?: () => void }) {
  const g = response.giai_thich;
  const [giaiThich, setGiaiThich] = useState(false);
  const [hien, setHien] = useState(Number.MAX_SAFE_INTEGER);

  useEffect(() => { setHien(Number.MAX_SAFE_INTEGER); }, [response]);

  const buoc = g ? dsBuoc(response, g) : [];
  const tong = buoc.length + 1;

  // Trình chiếu: → hiện thêm một bước, ← bớt một bước (khi không gõ trong ô nhập)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target;
      if (el instanceof Element && el.closest('input, textarea, select, button, [contenteditable]')) return;
      if (e.key === 'ArrowRight' || e.key === 'PageDown') { e.preventDefault(); setHien((h) => Math.min(tong, h + 1)); }
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); setHien((h) => Math.max(1, Math.min(tong, h) - 1)); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [tong]);

  if (!g) {
    return <p className="review-note" role="note">Máy chủ chưa trả về các bước trung gian. Hãy chuẩn hóa lại.</p>;
  }

  const r = response.result;
  const dangChieu = hien < tong;
  const canhBao = Array.from(new Set(r.canh_bao));

  return (
    <section className={`sv${giaiThich ? ' is-explain' : ''}`} aria-labelledby="steps-title">
      <header className="sv-head">
        <div className="sv-head-main">
          {onDoiDiaChi && <button type="button" className="btn btn-sm btn-ghost" onClick={onDoiDiaChi}>← Địa chỉ khác</button>}
          <h2 id="steps-title" tabIndex={-1} className="sv-input">{response.input}</h2>
        </div>
        <div className="sv-controls">
          <label className="sv-toggle">
            <input type="checkbox" checked={giaiThich} onChange={(e) => setGiaiThich(e.target.checked)} />
            Giải thích công nghệ
          </label>
          <button type="button" className="btn btn-sm" onClick={() => setHien(dangChieu ? tong : 1)}
            title="Trình chiếu: bấm → để hiện từng bước, ← để lùi">
            {dangChieu ? `Hiện hết (${Math.min(hien, tong)}/${tong})` : 'Trình chiếu từng bước'}
          </button>
        </div>
      </header>

      <p className="sv-arch">
        <span><b>Module 1 · Tiền xử lý</b> (bước 1–6): chuỗi bẩn → địa chỉ sạch</span>
        <span className="sv-arrow">→</span>
        <span><b>Module 2 · Chuyển đổi</b> (bước 7): cũ → mới 01/07/2025</span>
      </p>

      <ol className="sv-grid">
        {buoc.slice(0, hien).map((b, i) => (
          <li key={b.tieu_de} className={`sv-step${b.rong ? ' is-wide' : ''}`} data-module={b.module} data-n={i + 1}>
            <div className="sv-title">
              <span className="sv-n">{i + 1}</span>
              <h3>{b.tieu_de}</h3>
              <span className="sv-tags">{b.cong_nghe.ten.map((t) => <span key={t}>{t}</span>)}</span>
            </div>
            <p className="sv-summary">{b.tom_tat}</p>
            {giaiThich && (
              <p className="sv-explain"><b>Làm gì:</b> {b.cong_nghe.lam_gi} <b>Vì sao dùng cách này:</b> {b.cong_nghe.vi_sao}</p>
            )}
            <div className="sv-out">{b.noi_dung}</div>
          </li>
        ))}
        {hien >= tong && (
          <li className="sv-step is-wide is-result" data-n="kq">
            <div className="sv-title">
              <span className="sv-n"><IconCheck aria-hidden="true" /></span>
              <h3>Kết quả</h3>
              <StatusBadge status={response.status} />
              <span className="sv-meta">xử lý trong {Math.round(response.elapsed_ms)} ms</span>
            </div>
            <p className="sv-result">{r.dia_chi_chuan || 'Không ghép được địa chỉ chuẩn.'}</p>
            {(canhBao.length > 0 || r.phan_chua_phan_loai) && (
              <p className="sv-warns">
                {r.phan_chua_phan_loai && <span className="sv-warn">Chưa dùng tới: <del>{r.phan_chua_phan_loai}</del></span>}
                {canhBao.map((c) => {
                  const info = describeWarning(c);
                  return <span key={c} className="sv-warn" title={info.desc}>{info.label}</span>;
                })}
              </p>
            )}
          </li>
        )}
      </ol>
    </section>
  );
}
