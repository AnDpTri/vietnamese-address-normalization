import React, { useEffect, useState } from 'react';
import { IconLogo } from './Icons';
import type { HealthResponse } from '../shared/contracts';
import './header.css';

export type TabId = 'single' | 'batch' | 'excel';

interface HeaderProps {
  activeTab: TabId;
  hrefs: Record<TabId, string>;
  health: HealthResponse | null;
  healthLoading: boolean;
  onRefreshHealth: () => void;
}

type Theme = 'light' | 'dark';

const svg = { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8,
  strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true };
const IconHome = () => <svg {...svg}><path d="M3 10.5 12 3l9 7.5" /><path d="M5 9.5V21h14V9.5" /></svg>;
const IconList = () => <svg {...svg}><path d="M8 6h13M8 12h13M8 18h13" /><path d="M3 6h.01M3 12h.01M3 18h.01" /></svg>;
const IconSheet = () => <svg {...svg}><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18M3 15h18M9 3v18" /></svg>;
const IconMoon = () => <svg {...svg}><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></svg>;
const IconSun = () => <svg {...svg}><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>;

function themeHienTai(): Theme {
  try {
    const luu = localStorage.getItem('amc-theme');
    if (luu === 'light' || luu === 'dark') return luu;
  } catch { /* trình duyệt chặn lưu trữ: theo hệ thống */ }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/** Thanh bên kiểu Wallet May Cry: tên app, điều hướng, trạng thái máy chủ và nút sáng/tối ở đáy. */
export const Header: React.FC<HeaderProps> = ({ activeTab, hrefs, health, healthLoading, onRefreshHealth }) => {
  const [theme, setTheme] = useState<Theme>(themeHienTai);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('amc-theme', theme); } catch { /* bỏ qua */ }
  }, [theme]);

  const ok = health?.status === 'ok';
  const loadingEngine = health?.status === 'loading';
  const statusText = healthLoading
    ? 'Đang kiểm tra máy chủ…'
    : ok ? 'Máy chủ sẵn sàng' : loadingEngine ? 'Máy chủ đang khởi động…' : 'Chưa kết nối máy chủ';
  const dotClass = healthLoading || loadingEngine ? 'is-wait' : ok ? 'is-ok' : 'is-bad';
  const muc: { id: TabId; nhan: string; icon: React.ReactNode }[] = [
    { id: 'single', nhan: 'Một địa chỉ', icon: <IconHome /> },
    { id: 'batch', nhan: 'Hàng loạt', icon: <IconList /> },
    { id: 'excel', nhan: 'File Excel', icon: <IconSheet /> },
  ];

  return (
    <header className="sidebar">
      <a className="brand" href={hrefs.single} aria-label="Address May Cry, về trang một địa chỉ">
        <IconLogo size={30} aria-hidden="true" />
        <span className="brand-text">
          <span className="brand-name" translate="no">Address May Cry</span>
          <span className="brand-sub">Chuẩn hóa địa chỉ · mốc 01/07/2025</span>
        </span>
      </a>

      <nav className="main-nav" aria-label="Chế độ làm việc">
        {muc.map((m) => (
          <a key={m.id} href={hrefs[m.id]} aria-current={activeTab === m.id ? 'page' : undefined}>
            {m.icon}<span>{m.nhan}</span>
          </a>
        ))}
      </nav>

      <div className="sidebar-foot">
        <button type="button" className="health" onClick={onRefreshHealth} aria-label={`${statusText}. Bấm để kiểm tra lại`}>
          <span className={`health-dot ${dotClass}`} aria-hidden="true" />
          <span className="health-text" aria-live="polite">{statusText}</span>
        </button>
        <button type="button" className="theme-toggle" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          aria-label={theme === 'dark' ? 'Chuyển sang nền sáng' : 'Chuyển sang nền tối'}>
          {theme === 'dark' ? <IconSun /> : <IconMoon />}
          <span>{theme === 'dark' ? 'Nền sáng' : 'Nền tối'}</span>
        </button>
      </div>
    </header>
  );
};
