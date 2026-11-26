import type { AddressSample } from '../shared/addressSamples';
import './address-samples.css';

export function AddressSampleList({ samples, disabled, onPick, action = 'Thử' }: {
  samples: readonly AddressSample[];
  disabled: boolean;
  onPick: (address: string) => void;
  action?: 'Thử' | 'Thêm';
}) {
  return (
    <ul className="address-sample-list">
      {samples.map(({ id, label, address, reference, source }) => (
        <li className="address-sample" key={id}>
          <h3>{label}</h3>
          <dl>
            <div>
              <dt>Bản gõ mẫu</dt>
              <dd>{address}</dd>
            </div>
            <div className="address-sample-reference">
              <dt>Địa chỉ đã xác minh</dt>
              <dd>{reference}</dd>
            </div>
          </dl>
          <div className="address-sample-actions">
            <button type="button" className="btn" aria-label={`${action} bản gõ của ${label}`}
              disabled={disabled} onClick={() => onPick(address)}>
              {action} bản gõ
            </button>
            <button type="button" className="btn btn-ghost" aria-label={`${action} địa chỉ đúng của ${label}`}
              disabled={disabled} onClick={() => onPick(reference)}>
              {action} địa chỉ đúng
            </button>
            <a href={source} target="_blank" rel="noreferrer" aria-label={`Nguồn địa chỉ của ${label}`}>Nguồn</a>
          </div>
        </li>
      ))}
    </ul>
  );
}
