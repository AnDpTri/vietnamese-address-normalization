import React from 'react';
import type { NormalizeResponse } from '../../shared/contracts';
import ReportWrong from '../../components/ReportWrong';
import { StatusBadge } from '../../components/StatusBadge';
import { CopyButton } from '../../components/CopyButton';

/** Ba dòng theo hai bước của hệ thống: đầu vào -> sau tiền xử lý (đúng mốc người dùng viết) -> sau chuyển đổi (mốc mới). */
export function PipelineView({ response }: { response: NormalizeResponse }) {
  const r = response.result;
  const dong = [
    { nhan: 'Đầu vào', phu: 'Người dùng nhập', giaTri: response.input, cls: 'is-input' },
    { nhan: 'Sau tiền xử lý', phu: 'Làm sạch, giữ mốc như người dùng viết', giaTri: r.dia_chi_sau_tien_xu_ly || '', cls: 'is-clean' },
    { nhan: 'Sau chuyển đổi', phu: 'Đơn vị hành chính mới, mốc 01/07/2025', giaTri: r.dia_chi_chuan, cls: 'is-new' },
  ];
  return (
    <div className="result-stack">
      <div className="result-head">
        <div className="result-head-main">
          <h2 className="card-title" id="result-title" tabIndex={-1}>Kết quả</h2>
          <StatusBadge status={response.status} />
          <span className="muted-note mono">{response.elapsed_ms}&nbsp;ms</span>
        </div>
        <ReportWrong key={response.log_id ?? response.input} input={response.input} logId={response.log_id} />
      </div>
      <ol className="pipeline">
        {dong.map((d, i) => (
          <li key={d.nhan} className={`pipeline-row ${d.cls}`}>
            <span className="pipeline-step" aria-hidden="true">{i + 1}</span>
            <div className="pipeline-text">
              <span className="pipeline-label">{d.nhan}<small>{d.phu}</small></span>
              {d.giaTri
                ? <p className="pipeline-value">{d.giaTri}</p>
                : <p className="pipeline-value is-empty">Không có</p>}
            </div>
            {d.giaTri && i > 0 && <CopyButton text={d.giaTri} what={d.nhan.toLowerCase()} />}
          </li>
        ))}
      </ol>
      {response.status === 'needs_review' && (
        <p className="review-note" role="note">Kết quả cần xem lại. Mở phần chi tiết để xem cảnh báo và lý do.</p>
      )}
    </div>
  );
}
