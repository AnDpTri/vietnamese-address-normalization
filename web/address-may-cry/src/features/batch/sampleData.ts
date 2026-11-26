import { ADDRESS_SAMPLES } from '../../shared/addressSamples';
import { escapeCsvField } from './exportUtils';

export function getSampleCsvContent(): string {
  const headers = ['stt', 'ma_khach_hang', 'dia_chi', 'ghi_chu_don_hang', 'dia_chi_doi_chieu', 'nguon'];
  const rows = ADDRESS_SAMPLES.map(({ label, address, reference, source }, index) => [
    String(index + 1), `KH_${String(index + 1).padStart(3, '0')}`, address, label, reference, source,
  ]);
  return '\uFEFF' + [headers, ...rows].map(row => row.map(escapeCsvField).join(',')).join('\r\n');
}
