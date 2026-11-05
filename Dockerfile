# Address May Cry: web chuẩn hóa địa chỉ, đóng gói để chạy trên máy chủ đám mây.
# Tầng 1 build giao diện React, tầng 2 chạy API Python phục vụ cả giao diện lẫn /api/v1.

FROM node:22-slim AS giao_dien
WORKDIR /app
COPY web/address-may-cry/package.json web/address-may-cry/package-lock.json ./
RUN npm ci
COPY web/address-may-cry/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1 \
    OMP_NUM_THREADS=1 PORT=8080
# libgomp1 cần cho lightgbm
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir numpy==2.5.4 lightgbm==4.7.0 openpyxl==3.1.5

WORKDIR /app
# Chỉ chép những gì engine cần: mã, danh mục, mô hình, từ điển đường
COPY src/ src/
COPY data/clean/ data/clean/
COPY data/ten_cu/ data/ten_cu/
COPY data/xa_chia_theo_duong/ data/xa_chia_theo_duong/
COPY data/duong/ data/duong/
COPY mo_hinh/thu_nghiem/char_v3_tc/ mo_hinh/thu_nghiem/char_v3_tc/
COPY data/train/tu_dien_train.json data/train/tu_dien_train.json
COPY web/address-may-cry/api/ web/address-may-cry/api/
COPY --from=giao_dien /app/dist/ web/address-may-cry/dist/

RUN useradd -m app && chown -R app /app
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import os,urllib.request;urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/v1/health',timeout=4)"
CMD ["python", "web/address-may-cry/api/chay_may_chu.py"]
