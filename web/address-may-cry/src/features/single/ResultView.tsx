import React from 'react';
import type { NormalizeResponse } from '../../shared/contracts';
import ReportWrong from '../../components/ReportWrong';
import { ComponentBreakdown } from '../../components/ComponentBreakdown';
import { StatusBadge } from '../../components/StatusBadge';
import { TwoLineResult } from '../../components/TwoLineResult';
import { WarningList, CandidateList } from '../../components/WarningList';
import { TechTrace } from '../../components/TechTrace';
import { CopyButton } from '../../components/CopyButton';

interface FieldDef { label: string; value: string; code?: string; codeLabel?: string }

function Fields({ fields }: { fields: FieldDef[] }) {
  return (
    <section className="panel-block" aria-label="Các trường tách riêng">
      <h3 className="block-title">Các trường tách riêng</h3>
      <dl className="fields">
        {fields.map((f) => (
          <div className="field-item" key={f.label}>
            <dt>{f.label}</dt>
            <dd>
              {f.value ? (
                <>
                  <span className="field-value">{f.value}</span>
                  {f.code && <span className="field-code">{f.codeLabel}: <code>{f.code}</code></span>}
                </>
              ) : (
                <span className="field-empty">Không có</span>
              )}
            </dd>
            {f.value && <CopyButton text={f.value} what={f.label.toLowerCase()} className="field-copy" />}
          </div>
        ))}
      </dl>
    </section>
  );
}

export function ResultView({ response, anDau = false }: { response: NormalizeResponse; anDau?: boolean }) {
  const result = response.result;
  const haiDong = response.ket_qua_hai_dong || result.ket_qua_hai_dong;
  const thanhPhan = response.thanh_phan || result.thanh_phan;
  const needsReview = response.status === 'needs_review';

  const fields: FieldDef[] = [
    { label: 'Số nhà', value: result.so_nha },
    { label: 'Ngõ / ngách / hẻm', value: result.ngo_ngach_hem },
    { label: 'Thôn / xóm / ấp', value: result.thon_xom },
    { label: 'Đường / phố', value: result.duong },
    { label: 'Xã / phường mới', value: result.xa_phuong, code: result.ma_xa, codeLabel: 'Mã xã' },
    { label: 'Tỉnh / thành phố mới', value: result.tinh, code: result.ma_tinh, codeLabel: 'Mã tỉnh' },
  ];

  return (
    <div className="result-stack">
      {!anDau && (
        <div className="result-head">
          <div className="result-head-main">
            <h2 className="card-title" id="result-title" tabIndex={-1}>Kết quả</h2>
            <StatusBadge status={response.status} />
            <span className="muted-note mono">{response.elapsed_ms}&nbsp;ms</span>
          </div>
          <ReportWrong key={response.log_id ?? response.input} input={response.input} logId={response.log_id} />
        </div>
      )}

      {needsReview && (
        <p className="review-note" role="note">
          Kết quả này cần được xem lại. Hãy đọc phần “Cần lưu ý” bên dưới trước khi dùng.
        </p>
      )}

      {haiDong && <TwoLineResult data={haiDong} />}

      {result.dia_chi_chuan && (
        <section className="panel-block full-line" aria-label="Địa chỉ ghép đầy đủ">
          <div className="full-line-text">
            <h3 className="block-hint">Địa chỉ ghép đầy đủ</h3>
            <p className="full-line-value">{result.dia_chi_chuan}</p>
          </div>
          <CopyButton text={result.dia_chi_chuan} what="địa chỉ ghép đầy đủ" />
        </section>
      )}

      {thanhPhan && thanhPhan.length > 0 && (
        <ComponentBreakdown rawAddress={response.input} thanhPhan={thanhPhan} />
      )}

      <WarningList codes={result.canh_bao} />

      {result.phan_chua_phan_loai && (
        <section className="panel-block" aria-label="Phần chưa phân loại">
          <h3 className="block-title">Phần chữ chưa phân loại</h3>
          <p><code className="unclassified">{result.phan_chua_phan_loai}</code></p>
        </section>
      )}

      <CandidateList items={result.xa_moi_ung_vien} />

      <Fields fields={fields} />

      <TechTrace data={response} />
    </div>
  );
}
