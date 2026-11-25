import React, { useId, useState } from 'react';
import type { BatchItem, AddressResult } from '../shared/contracts';
import { ComponentBreakdown } from './ComponentBreakdown';
import { CopyButton } from './CopyButton';
import { TechTrace } from './TechTrace';
import { TwoLineResult } from './TwoLineResult';
import { WarningList, CandidateList } from './WarningList';
import './result-details.css';

interface FieldDef {
  label: string;
  value: string;
  code?: string;
  codeLabel?: string;
}

function Fields({ result }: { result: AddressResult }) {
  const fields: FieldDef[] = [
    { label: 'Xã / phường mới', value: result.xa_phuong, code: result.ma_xa, codeLabel: 'Mã xã' },
    { label: 'Tỉnh / thành phố mới', value: result.tinh, code: result.ma_tinh, codeLabel: 'Mã tỉnh' },
    { label: 'Số nhà', value: result.so_nha },
    { label: 'Đường / phố', value: result.duong },
    { label: 'Ngõ / ngách / hẻm', value: result.ngo_ngach_hem },
    { label: 'Thôn / xóm / ấp', value: result.thon_xom },
  ];

  return (
    <dl className="detail-fields" aria-label="Các trường địa chỉ">
      {fields.map(({ label, value, code, codeLabel }) => (
        <div className="detail-field" key={label}>
          <dt>{label}</dt>
          <dd>
            {value || <span className="detail-empty-value" aria-label="Không có">—</span>}
            {code && <small>{codeLabel} <span>{code}</span></small>}
          </dd>
          {value && <CopyButton text={value} what={label.toLowerCase()} className="detail-copy" />}
        </div>
      ))}
    </dl>
  );
}

type DetailSection = 'fields' | 'reconcile' | 'warnings';
type DetailData = Pick<BatchItem, 'input' | 'result' | 'ket_qua_hai_dong' | 'thanh_phan'>;

export function ResultDetails({ data, fileName }: { data: DetailData; fileName?: string }) {
  const groupId = useId();
  const [active, setActive] = useState<DetailSection>('fields');
  const result = data.result;
  if (!result) return <TechTrace data={data} fileName={fileName} />;

  const split = data.ket_qua_hai_dong || result.ket_qua_hai_dong;
  const components = data.thanh_phan || result.thanh_phan;
  const warnings = result.canh_bao ?? [];
  const showWarnings = warnings.length > 0 || !!result.xa_moi_ung_vien?.length || !!result.phan_chua_phan_loai;
  const sections: { id: DetailSection; label: string; count?: number }[] = [
    { id: 'fields', label: 'Thành phần' },
    { id: 'reconcile', label: 'Đối chiếu' },
    { id: 'warnings', label: 'Cảnh báo', count: warnings.length },
  ];

  return (
    <div className="result-details">
      <div className="detail-sheet">
        <fieldset className="detail-switch">
          <legend className="sr-only">Nội dung chi tiết địa chỉ</legend>
          {sections.map(({ id, label, count }) => (
            <label key={id} className="detail-choice">
              <input type="radio" className="sr-only" name={groupId} checked={active === id}
                aria-controls={`${groupId}-${id}`} onChange={() => setActive(id)} />
              <span>{label}{!!count && <small>{count}</small>}</span>
            </label>
          ))}
        </fieldset>

        <div id={`${groupId}-fields`} className="detail-content" hidden={active !== 'fields'}>
          <Fields result={result} />
        </div>

        <div id={`${groupId}-reconcile`} className="detail-content" hidden={active !== 'reconcile'}>
          {active === 'reconcile' && (
            <>
              {components && components.length > 0 && (
                <ComponentBreakdown rawAddress={data.input} thanhPhan={components} />
              )}
              {split && (
                <details className="trace">
                  <summary>Kết quả theo khả năng đối chiếu</summary>
                  <div className="trace-body"><TwoLineResult data={split} /></div>
                </details>
              )}
              {!components?.length && !split && <p className="detail-empty">Chưa có dữ liệu đối chiếu.</p>}
            </>
          )}
        </div>

        <div id={`${groupId}-warnings`} className="detail-content" hidden={active !== 'warnings'}>
          <WarningList codes={warnings} />
          <CandidateList items={result.xa_moi_ung_vien} />
          {result.phan_chua_phan_loai && (
            <section className="panel-block">
              <h3 className="block-title">Phần chữ chưa phân loại</h3>
              <p className="detail-unclassified">{result.phan_chua_phan_loai}</p>
            </section>
          )}
          {!showWarnings && <p className="detail-empty">Không có cảnh báo.</p>}
        </div>
      </div>
      <TechTrace data={data} fileName={fileName} summary="Dữ liệu kỹ thuật (JSON)" />
    </div>
  );
}
