import React, { useRef } from 'react';
import { IconClipboard, IconRefresh, IconX } from '../../components/Icons';

export const MAX_CHARS = 2048;

const SAMPLES = [
  { label: 'Viết tắt, đảo thứ tự', value: '45 XÔ VIẾT NGHỆ TĨNH P.AN CƯ- NINH KIỀU- CẦN THƠ' },
  { label: 'Đầy đủ số nhà, phường, quận', value: '313, NGUYỄN VĂN LINH, PHƯỜNG AN KHÁNH, QUẬN NINH KIỀU, THÀNH PHỐ CẦN THƠ' },
  { label: 'Tên đường viết tắt (CMT8)', value: '110A CMT8, Phường An Thới, Quận Bình Thủy, TP Cần Thơ' },
  { label: 'Phường cũ của Hà Nội', value: 'Số 42, Phố Bồ Đề, Phường Bồ Đề, Quận Long Biên, Hà Nội' },
  { label: 'Địa chỉ nông thôn có thôn', value: 'Thôn 4, Xã Hoằng Lộc, Huyện Hoằng Hóa, Tỉnh Thanh Hóa' },
];

// Ví dụ cho chế độ "Xem từng bước": bấm là chạy luôn. Tự đặt, không lấy từ tập test.
const SAMPLES_TRINH_BAY = [
  { label: 'Gõ tắt, không dấu, không dấu phẩy', value: 'so 12 ngo 5 tran thai tong cau giay hn' },
  { label: 'Ghi theo địa giới cũ (phường, quận cũ)', value: 'Số 10 Lê Lợi, Phường Bến Nghé, Quận 1, TP Hồ Chí Minh' },
  { label: 'Ca hệ thống còn sai: chọn nhầm phường', value: '12 ngo 5 tran thai tong p dich vong hau q cau giay hn' },
];

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
          placeholder="313 Nguyễn Văn Linh, P. An Khánh, Q. Ninh Kiều, TP Cần Thơ"
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
  const samples = showSteps ? SAMPLES_TRINH_BAY : SAMPLES;

  return (
    <section className="samples" aria-labelledby="address-samples-title">
      <h2 id="address-samples-title" className="card-title">{showSteps ? 'Ví dụ chạy từng bước' : 'Thử với địa chỉ mẫu'}</h2>
      <ul className="sample-list">
        {samples.map(({ label, value }) => (
          <li key={label}>
            <button type="button" className="sample-btn" disabled={disabled} onClick={() => onPick(value)}>
              <span className="sample-label">{label}</span>
              <span className="sample-value">{value}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
