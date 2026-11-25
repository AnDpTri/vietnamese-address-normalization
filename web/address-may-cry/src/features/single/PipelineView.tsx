import React from 'react';
import type { NormalizeResponse } from '../../shared/contracts';
import ReportWrong from '../../components/ReportWrong';
import { StatusBadge } from '../../components/StatusBadge';
import { CopyButton } from '../../components/CopyButton';

export function PipelineView({ response }: { response: NormalizeResponse }) {
  const r = response.result;
  const diaChiChuan = r.dia_chi_chuan;
  const daLamSach = r.dia_chi_sau_tien_xu_ly;
  return (
    <div className="result-stack">
      <div className="result-head">
        <div className="result-head-main">
          <h2 className="card-title" id="result-title" tabIndex={-1}>Kết quả</h2>
          <StatusBadge status={response.status} />
          <span className="muted-note result-time">{response.elapsed_ms}&nbsp;ms</span>
        </div>
        <ReportWrong key={response.log_id ?? response.input} input={response.input} logId={response.log_id} />
      </div>
      <div className="pipeline-row is-new">
        <div className="pipeline-text">
          <span className="pipeline-label">Địa chỉ chuẩn <small>Địa giới từ 01/07/2025</small></span>
          <p className={`pipeline-value${diaChiChuan ? '' : ' is-empty'}`}>{diaChiChuan || 'Chưa xác định được'}</p>
        </div>
        {diaChiChuan && <CopyButton text={diaChiChuan} what="địa chỉ chuẩn" />}
      </div>
      {response.status === 'needs_review' && (
        <p className="review-note" role="note">Mở chi tiết để xem phần địa chỉ cần kiểm tra và lý do.</p>
      )}
      <div className="pipeline">
        <div className="pipeline-row">
          <div className="pipeline-text">
            <span className="pipeline-label">Địa chỉ gốc</span>
            <p className="pipeline-value">{response.input}</p>
          </div>
        </div>
        <div className="pipeline-row">
          <div className="pipeline-text">
            <span className="pipeline-label">Sau tiền xử lý <small>Giữ địa giới như đầu vào</small></span>
            <p className={`pipeline-value${daLamSach ? '' : ' is-empty'}`}>{daLamSach || 'Chưa xác định được'}</p>
          </div>
          {daLamSach && <CopyButton text={daLamSach} what="địa chỉ sau tiền xử lý" />}
        </div>
      </div>
    </div>
  );
}
