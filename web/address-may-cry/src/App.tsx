import React, { useState, useEffect, useCallback } from 'react';
import { Header, type TabId } from './components/Header';
import { SingleWorkspace } from './features/single/SingleWorkspace';
import { getHealth } from './shared/api';
import type { HealthResponse, BatchItem } from './shared/contracts';
import BatchWorkspace from './features/batch/BatchWorkspace';
import ExcelWorkspace from './features/excel/ExcelWorkspace';
import './app.css';

const HASH_BY_TAB: Record<TabId, string> = { single: '#mot-dia-chi', batch: '#hang-loat', excel: '#file-excel' };

function tabFromHash(): TabId {
  const h = window.location.hash;
  return h === HASH_BY_TAB.batch ? 'batch' : h === HASH_BY_TAB.excel ? 'excel' : 'single';
}

export function App() {
  const [activeTab, setActiveTab] = useState<TabId>(tabFromHash);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);

  const fetchHealth = useCallback(async () => {
    setHealthLoading(true);
    try {
      setHealth(await getHealth());
    } catch {
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  }, []);

  useEffect(() => { void fetchHealth(); }, [fetchHealth]);

  // Địa chỉ URL phản ánh tab đang mở (có thể chia sẻ, dùng nút Quay lại)
  useEffect(() => {
    const onHash = () => setActiveTab(tabFromHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const handleInspectFromBatch = useCallback((_item: BatchItem) => {
    window.location.hash = HASH_BY_TAB.single;
  }, []);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#noi-dung-chinh">Bỏ qua tới nội dung chính</a>
      <Header
        activeTab={activeTab}
        hrefs={HASH_BY_TAB}
        health={health}
        healthLoading={healthLoading}
        onRefreshHealth={fetchHealth}
      />

      <main id="noi-dung-chinh" className="app-main" tabIndex={-1}>
        {activeTab === 'single' ? (
          <SingleWorkspace />
        ) : activeTab === 'excel' ? (
          <ExcelWorkspace />
        ) : (
          <BatchWorkspace onInspect={handleInspectFromBatch} />
        )}
      </main>

      <footer className="app-footer">
        <div className="app-footer-inner">
          <p><strong translate="no">Address May Cry</strong> — chuẩn hóa địa chỉ Việt Nam về mốc hành chính 01/07/2025.</p>
          <p>Kết quả mang tính hỗ trợ, hãy kiểm tra lại các cảnh báo trước khi dùng chính thức.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
