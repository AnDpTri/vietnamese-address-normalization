import React, { useRef } from 'react';
import { IconClipboard, IconRefresh, IconX } from '../../components/Icons';
import { AddressSampleList } from '../../components/AddressSampleList';
import { ADDRESS_SAMPLES } from '../../shared/addressSamples';

export const MAX_CHARS = 2048;

interface InputPanelProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (text?: string) => void;
  loading: boolean;
  elapsed: number;
  error: string | null;
  tungBuoc: boolean;
  onTungBuoc: (v: boolean) => void;
}

export function InputPanel({ value, onChange, onSubmit, loading, elapsed, error, tungBuoc, onTungBuoc }: InputPanelProps) {
  const ref = useRef<HTMLTextAreaElement | null>(null);

  const paste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) onChange(text.slice(0, MAX_CHARS));
    } catch {
      /* trình duyệt từ chối quyền đọc bộ nhớ tạm: người dùng vẫn có thể dán thủ công */
    }
    ref.current?.focus();
  };

  return (
    <section className="card input-card" aria-labelledby="input-title">
      <div className="input-heading">
        <h2 id="input-title" className="card-title">Nhập địa chỉ</h2>
        <a className="sample-jump" href="#address-samples-title">Chọn mẫu</a>
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); onSubmit(); }}
        noValidate
      >
        <label htmlFor="address-input" className="field-label">Địa chỉ cần chuẩn hóa</label>
        <textarea
          id="address-input"
          name="address"
          ref={ref}
          rows={4}
          value={value}
          onChange={(e) => onChange(e.target.value.slice(0, MAX_CHARS))}
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
              e.preventDefault();
              onSubmit();
            }
          }}
          placeholder={ADDRESS_SAMPLES[0].address}
          autoComplete="off"
          autoCapitalize="off"
          spellCheck={false}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? 'address-error address-hint' : 'address-hint'}
          className="address-textarea"
        />
        <div className="field-meta">
          <span id="address-hint"><kbd>Ctrl</kbd>&nbsp;+&nbsp;<kbd>Enter</kbd> để chuẩn hóa</span>
          <span aria-label={`${value.length} trên ${MAX_CHARS} ký tự`}>{value.length}&nbsp;/&nbsp;{MAX_CHARS}</span>
        </div>
        {error && <p id="address-error" className="field-error" role="alert">{error}</p>}

        <div className="action-row">
          <button type="submit" className="btn btn-primary btn-main" disabled={loading}>
            {loading ? (
              <><IconRefresh size={17} className="spin" aria-hidden="true" /> Đang xử lý… {elapsed}&nbsp;ms</>
            ) : (
              'Chuẩn hóa địa chỉ'
            )}
          </button>
          <button type="button" className="btn" onClick={paste}>
            <IconClipboard size={16} aria-hidden="true" /> Dán
          </button>
          {value && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => { onChange(''); ref.current?.focus(); }}
            >
              <IconX size={16} aria-hidden="true" /> Xóa
            </button>
          )}
        </div>

        <label className="mode-switch">
          <input type="checkbox" checked={tungBuoc} onChange={(e) => onTungBuoc(e.target.checked)} />
          <span>
            <strong>Xem từng bước xử lý</strong>
            <span>Mở chế độ trình bày quy trình xử lý.</span>
          </span>
        </label>
      </form>

    </section>
  );
}

export function AddressSamples({ showSteps, disabled, onPick }: {
  showSteps: boolean;
  disabled: boolean;
  onPick: (address: string) => void;
}) {
  const samples = showSteps ? ADDRESS_SAMPLES.slice(0, 4) : ADDRESS_SAMPLES;

  return (
    <section className="samples" aria-labelledby="address-samples-title">
      <h2 id="address-samples-title" className="card-title">{showSteps ? 'Ví dụ chạy từng bước' : 'Thử với địa chỉ mẫu'}</h2>
      <AddressSampleList samples={samples} disabled={disabled} onPick={onPick} />
    </section>
  );
}
