# Layanan Pemesanan B2B — laboratorium audit CIA (BAB 1)
# Aplikasi ini SENGAJA dikonfigurasi lemah untuk keperluan praktikum.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY db/  ./db/

# Seed dijalankan saat start bila basis data belum ada
# sed menghapus CR: klon di Windows dapat mengubah akhir baris menjadi CRLF
# sehingga shebang gagal dengan galat "no such file or directory".
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh && chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8081
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
