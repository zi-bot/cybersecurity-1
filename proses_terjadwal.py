#!/usr/bin/env python3
"""Proses terjadwal — memajukan status pesanan satu langkah.

Meniru tugas berkala (mis. lewat cron) yang memajukan alur pesanan:

    Baru -> Diproses -> Dikirim -> Selesai

Pemakaian:
    python3 proses_terjadwal.py

Di dalam kontainer, basis datanya ada di /srv/data/pesanan.db:
    DB_PATH=/srv/data/pesanan.db python3 proses_terjadwal.py
"""
from __future__ import annotations

import os
import sqlite3

DB_PATH = os.environ.get(
    "DB_PATH", os.path.join(os.path.dirname(__file__), "data", "pesanan.db")
)

LANJUT_STATUS = {"Baru": "Diproses", "Diproses": "Dikirim", "Dikirim": "Selesai"}


def main() -> int:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    diubah = 0
    for r in con.execute("SELECT id, status FROM pesanan").fetchall():
        berikut = LANJUT_STATUS.get(r["status"])
        if berikut:
            con.execute("UPDATE pesanan SET status = ? WHERE id = ?", (berikut, r["id"]))
            con.commit()
            diubah += 1
    con.close()
    print(f"[proses terjadwal] {diubah} pesanan diperbarui.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
