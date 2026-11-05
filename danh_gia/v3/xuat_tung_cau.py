"""Chạy pipeline trên tập test cũ (đã mở để phát triển), ghi đầu ra từng câu (+ chẩn đoán nếu có).
Dùng: CODE_ROOT=<mã> xuat_tung_cau.py <char_cnn.pt> <ranker.txt> <out.jsonl> [test.csv]"""
import csv, json, os, sys
from dataclasses import asdict
from pathlib import Path

import duong_dan as dd  # gốc repo, CODE_ROOT vào sys.path
from src.cau_hinh import tao_bo_chuan_hoa  # noqa: E402  (cấu hình chung với web)

cnn, ranker, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
test = sys.argv[4] if len(sys.argv) > 4 else dd.TEST
# Chạy trên tập test nên giữ quy ước nhãn test: không tự thêm tiền tố.
pipe = tao_bo_chuan_hoa(cnn=cnn, ranker=ranker, tien_to_mac_dinh=False)
co_cd = hasattr(pipe, 'chuan_hoa_chan_doan')
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    for r in csv.DictReader(open(test, encoding='utf-8-sig')):
        if co_cd:
            kq, cd = pipe.chuan_hoa_chan_doan(r['dau_vao'])
        else:
            kq, cd = pipe.chuan_hoa(r['dau_vao']), None
        f.write(json.dumps({'id': r['id'], 'out': asdict(kq), 'chan_doan': cd}, ensure_ascii=False) + '\n')
print('xong', out)
