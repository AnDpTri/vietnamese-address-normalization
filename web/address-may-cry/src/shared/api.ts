import type { BatchInput, BatchResponse, HealthResponse, NormalizeResponse } from './contracts';
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch('/api/v1/' + path, {
    ...init, headers: { 'Content-Type': 'application/json', ...init.headers },
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.error?.message || `Yêu cầu thất bại (${response.status})`);
  if (data === null) throw new Error('Máy chủ trả về dữ liệu không hợp lệ.');
  return data as T;
}
export const getHealth = (signal?: AbortSignal) => request<HealthResponse>('health', { signal });
export const normalizeAddress = (address: string, signal?: AbortSignal, giaiThich = false) =>
  request<NormalizeResponse>('normalize', {
    method: 'POST', body: JSON.stringify(giaiThich ? { address, giai_thich: true } : { address }), signal,
  });
export const sendFeedback = (input: string, log_id: string | null, ghi_chu: string) =>
  request<{ saved: boolean; log_id: string | null }>('feedback', { method: 'POST', body: JSON.stringify({ input, log_id, ghi_chu }) });
export const normalizeBatch = (addresses: BatchInput[], signal?: AbortSignal) =>
  request<BatchResponse>('batch', { method: 'POST', body: JSON.stringify({ addresses }), signal });
