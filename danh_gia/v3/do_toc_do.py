"""Đo thời gian chuẩn hóa mỗi câu (ms), CPU 1 luồng, cùng 300 câu dev cho mọi mô hình.
Dùng: do_toc_do.py <char_cnn.pt> <ranker.txt> [ten]"""
import csv, sys, time
from pathlib import Path

import duong_dan as dd  # gốc repo, CODE_ROOT vào sys.path
from src.cau_hinh import tao_bo_chuan_hoa  # noqa: E402  (cấu hình chung với web)

mo_hinh, ranker = Path(sys.argv[1]), Path(sys.argv[2])
pipe = tao_bo_chuan_hoa(cnn=mo_hinh, ranker=ranker)
cau = [r['dau_vao'] for r in csv.DictReader(open(dd.DEV / 'dev_goc.csv', encoding='utf-8-sig'))][:300]
for c in cau[:20]:
    pipe.chuan_hoa(c)  # làm nóng
ms = []
for c in cau:
    t0 = time.perf_counter(); pipe.chuan_hoa(c); ms.append((time.perf_counter() - t0) * 1000)
ms.sort()
print(f"{sys.argv[3] if len(sys.argv) > 3 else mo_hinh.name}: n={len(ms)} trung binh {sum(ms) / len(ms):.1f} ms | "
      f"trung vi {ms[len(ms) // 2]:.1f} | p95 {ms[int(len(ms) * .95)]:.1f}")
