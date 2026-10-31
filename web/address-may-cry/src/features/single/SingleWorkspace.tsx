import React, { useState, useRef, useEffect, useCallback } from 'react';
import type { NormalizeResponse } from '../../shared/contracts';
import { normalizeAddress } from '../../shared/api';
import { IconAlertTriangle } from '../../components/Icons';
import { InputPanel, MAX_CHARS } from './InputPanel';
import { ResultView } from './ResultView';
import { PipelineView } from './PipelineView';
import { SessionHistory, type HistoryItem } from './SessionHistory';
import './single.css';

const GUIDE = [
  { n: '1', t: 'Nhập địa chỉ', d: 'Gõ hoặc dán địa chỉ, viết tắt hay đảo thứ tự đều được.' },
  { n: '2', t: 'Xem ba dòng kết quả', d: 'Đầu vào, sau tiền xử lý (làm sạch, giữ mốc như người dùng viết) và sau chuyển đổi (đơn vị hành chính mới).' },
  { n: '3', t: 'Xem chi tiết khi cần', d: 'Bấm “Xem chi tiết” để biết từng chữ được nhận là gì, đổi thế nào và vì sao.' },
];

export const SingleWorkspace: React.FC = () => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [response, setResponse] = useState<NormalizeResponse | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [chiTiet, setChiTiet] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<number | null>(null);

  const stopTimer = () => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const submit = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed) {
      setFieldError('Hãy nhập địa chỉ cần chuẩn hóa rồi bấm “Chuẩn hóa địa chỉ”.');
      document.getElementById('address-input')?.focus();
      return;
    }
    if (trimmed.length > MAX_CHARS) {
      setFieldError(`Địa chỉ dài quá ${MAX_CHARS} ký tự. Hãy rút ngắn rồi thử lại.`);
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    setFieldError(null);
    setElapsed(0);
    const start = performance.now();
    stopTimer();
    timerRef.current = window.setInterval(() => setElapsed(Math.round(performance.now() - start)), 100);

    try {
      const res = await normalizeAddress(trimmed, controller.signal);
      setResponse(res);
      setHistory((prev) => [{ timestamp: Date.now(), input: trimmed, response: res }, ...prev].slice(0, 10));
    } catch (err: unknown) {
      if ((err as Error).name === 'AbortError') return;
      setError((err as Error).message || 'Không chuẩn hóa được địa chỉ. Hãy kiểm tra kết nối rồi thử lại.');
    } finally {
      if (abortRef.current === controller) {
        setLoading(false);
        stopTimer();
      }
    }
  }, [input]);

  // Trên màn hình hẹp kết quả nằm dưới ô nhập: đưa tiêu đề kết quả vào tầm nhìn sau mỗi lần xử lý xong
  useEffect(() => {
    if (!response || loading || !window.matchMedia('(max-width: 1023px)').matches) return;
    const el = document.getElementById('result-title');
    el?.scrollIntoView({ block: 'start' });
    el?.focus({ preventScroll: true });
  }, [response, loading]);

  useEffect(() => () => {
    abortRef.current?.abort();
    stopTimer();
  }, []);

  const showEmpty = !response && !loading && !error;

  return (
    <div className="single-page">
      <div className="page-intro">
        <h1>Chuẩn hóa một địa chỉ</h1>
        <p>
          Đưa địa chỉ viết tay, viết tắt hoặc lẫn tên cũ và mới về cách viết chuẩn theo
          đơn vị hành chính áp dụng từ <strong>01/07/2025</strong>.
        </p>
      </div>

      <div className="single-grid">
        <div className="single-side">
          <InputPanel
            value={input}
            onChange={(v) => { setInput(v); setFieldError(null); }}
            onSubmit={submit}
            loading={loading}
            elapsed={elapsed}
            error={fieldError}
          />
          <SessionHistory
            items={history}
            onPick={(it) => { setInput(it.input); setResponse(it.response); setError(null); }}
            onClear={() => setHistory([])}
          />
        </div>

        <section className="single-main" aria-labelledby="result-region" aria-busy={loading}>
          <h2 id="result-region" className="sr-only">Vùng kết quả</h2>

          {error && (
            <div className="alert-box" role="alert">
              <IconAlertTriangle size={20} aria-hidden="true" />
              <div>
                <strong>Chưa hoàn tất yêu cầu</strong>
                <p>{error}</p>
                <button type="button" className="btn btn-sm" onClick={submit}>Thử lại</button>
              </div>
            </div>
          )}

          {loading && (
            <div className="skeleton" role="status">
              <p>Đang chuẩn hóa… {elapsed}&nbsp;ms</p>
              <div className="skel-bar" />
              <div className="skel-bar" />
              <div className="skel-bar short" />
            </div>
          )}

          {showEmpty && (
            <div className="empty-state">
              <h2 className="card-title">Cách đọc kết quả</h2>
              <ol className="guide">
                {GUIDE.map((g) => (
                  <li key={g.n}>
                    <span className="guide-n" aria-hidden="true">{g.n}</span>
                    <div><strong>{g.t}</strong><p>{g.d}</p></div>
                  </li>
                ))}
              </ol>
              <p className="muted-note">
                Hệ thống không đưa ra độ tin cậy. Khi chưa chắc chắn, kết quả được đánh dấu “Cần xem lại” kèm lý do.
              </p>
            </div>
          )}

          {response && !loading && (
            <>
              <PipelineView response={response} />
              <button type="button" className="btn btn-ghost chi-tiet-toggle" aria-expanded={chiTiet}
                onClick={() => setChiTiet((v) => !v)}>
                {chiTiet ? 'Ẩn chi tiết' : 'Xem chi tiết từng thành phần'}
              </button>
              {chiTiet && <ResultView response={response} anDau />}
            </>
          )}
        </section>
      </div>
    </div>
  );
};
