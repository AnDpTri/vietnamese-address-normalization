import React, { useState, useRef, useEffect, useCallback } from 'react';
import type { NormalizeResponse } from '../../shared/contracts';
import { normalizeAddress } from '../../shared/api';
import { IconAlertTriangle } from '../../components/Icons';
import { AddressSamples, InputPanel, MAX_CHARS } from './InputPanel';
import { ResultDetails } from '../../components/ResultDetails';
import { PipelineView } from './PipelineView';
import { StepsView } from './StepsView';
import { SessionHistory, type HistoryItem } from './SessionHistory';
import './single.css';

export const SingleWorkspace: React.FC = () => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [response, setResponse] = useState<NormalizeResponse | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [tungBuoc, setTungBuoc] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<number | null>(null);

  const stopTimer = () => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const submit = useCallback(async (text?: string) => {
    const trimmed = (text ?? input).trim();
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
      const res = await normalizeAddress(trimmed, controller.signal, tungBuoc);
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
  }, [input, tungBuoc]);

  // Bật "Xem từng bước" khi đang có kết quả thường: chạy lại địa chỉ đó để lấy các bước trung gian
  useEffect(() => {
    if (tungBuoc && response && !response.giai_thich && !loading) submit(response.input);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tungBuoc]);

  // Trên màn hình hẹp, đưa tiêu đề kết quả dưới ô nhập vào tầm nhìn.
  useEffect(() => {
    if (!response || loading || !window.matchMedia('(max-width: 799px)').matches) return;
    const el = document.getElementById('steps-title') ?? document.getElementById('result-title');
    el?.scrollIntoView({ block: 'start' });
    el?.focus({ preventScroll: true });
  }, [response, loading]);

  useEffect(() => () => {
    abortRef.current?.abort();
    stopTimer();
  }, []);

  const showEmpty = !response && !loading && !error;

  // Chế độ trình bày: chỉ còn các bước, ẩn ô nhập, lịch sử và phần giới thiệu để vừa một màn hình
  if (response && !loading && tungBuoc && response.giai_thich) {
    return (
      <div className="single-page is-present">
        <StepsView response={response} onDoiDiaChi={() => setResponse(null)} />
      </div>
    );
  }

  return (
    <div className="single-page">
      <div className="page-intro">
        <h1>Chuẩn hóa một địa chỉ</h1>
        <p>
          Gõ hoặc dán địa chỉ viết tắt, thiếu dấu hoặc theo địa giới cũ.
        </p>
      </div>

      <div className="single-grid">
        <InputPanel
          value={input}
          onChange={(v) => { setInput(v); setFieldError(null); }}
          onSubmit={submit}
          loading={loading}
          elapsed={elapsed}
          error={fieldError}
          tungBuoc={tungBuoc}
          onTungBuoc={setTungBuoc}
        />
        <section className="single-main" aria-labelledby="result-region" aria-busy={loading}>
          <h2 id="result-region" className="sr-only">Vùng kết quả</h2>

          {error && (
            <div className="alert-box" role="alert">
              <IconAlertTriangle size={20} aria-hidden="true" />
              <div>
                <strong>Chưa hoàn tất yêu cầu</strong>
                <p>{error}</p>
                <button type="button" className="btn btn-sm" onClick={() => submit()}>Thử lại</button>
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
              <div>
                <h2 className="card-title">Kết quả</h2>
                <p>Địa chỉ chuẩn và cảnh báo sẽ hiển thị ở đây.</p>
              </div>
              <div className="address-preview">
                <h3>Ví dụ đối chiếu</h3>
                <dl>
                  <div>
                    <dt>Địa chỉ gốc</dt>
                    <dd>Thôn 4, Xã Hoằng Lộc, Huyện Hoằng Hóa, Tỉnh Thanh Hóa</dd>
                  </div>
                  <div>
                    <dt>Địa chỉ sau chuyển đổi</dt>
                    <dd>Thôn 4, Xã Hoằng Lộc, Tỉnh Thanh Hóa</dd>
                  </div>
                </dl>
              </div>
            </div>
          )}

          {response && !loading && (
            <>
              <PipelineView response={response} />
              <details className="result-disclosure" key={response.log_id ?? response.input}>
                <summary className="chi-tiet-toggle">Xem chi tiết</summary>
                <ResultDetails data={response} />
              </details>
            </>
          )}
        </section>
      </div>
      <AddressSamples showSteps={tungBuoc} disabled={loading} onPick={(address) => {
        setInput(address);
        setFieldError(null);
        if (tungBuoc) void submit(address);
        else document.getElementById('address-input')?.focus();
      }} />
      <SessionHistory
        items={history}
        onPick={(it) => { setInput(it.input); setResponse(it.response); setError(null); }}
        onClear={() => setHistory([])}
      />
    </div>
  );
};
