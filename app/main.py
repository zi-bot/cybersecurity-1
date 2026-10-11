"""
Layanan Pemesanan B2B fiktif — laboratorium audit CIA (BAB 1).

PERINGATAN: aplikasi ini SENGAJA dikonfigurasi lemah untuk keperluan praktikum
audit kerahasiaan, integritas, dan ketersediaan. Jangan dijalankan pada jaringan
yang dapat dijangkau pihak lain, dan jangan memakai data atau kredensial nyata.
Lihat README.md.

Jalankan tanpa Docker:
    pip install flask
    python3 -m flask --app app.main run --host 127.0.0.1 --port 8081
"""
from __future__ import annotations

import os
import sqlite3
import time
from functools import wraps

from flask import (Flask, Response, abort, flash, g, redirect,
                   render_template, request, session, url_for)

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "pesanan.db"))

app = Flask(__name__)
app.secret_key = "lab-pemesanan-b2b-bukan-rahasia"

# Pengaturan cookie sesi.
app.config.update(
    SESSION_COOKIE_HTTPONLY=False,
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE=None,
)


# ---------------------------------------------------------------- basis data
def db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    con = g.pop("db", None)
    if con is not None:
        con.close()


def q(sql: str, args: tuple = ()) -> list[sqlite3.Row]:
    return db().execute(sql, args).fetchall()


# -------------------------------------------------------------------- sesi
def current_user():
    uid = session.get("uid")
    if uid is None:
        return None
    rows = q("SELECT * FROM pengguna WHERE id = ?", (uid,))
    return rows[0] if rows else None


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if session.get("uid") is None:
            return redirect(url_for("masuk", next=request.path))
        return view(*a, **kw)
    return wrapped


# ------------------------------------------------------------------- rute
@app.route("/")
@login_required
def beranda():
    u = current_user()
    pesanan = q(
        "SELECT p.*, pl.nama AS nama_pelanggan FROM pesanan p "
        "JOIN pelanggan pl ON pl.id = p.pelanggan_id "
        "WHERE p.pelanggan_id = ? ORDER BY p.id DESC",
        (u["pelanggan_id"],),
    )
    return render_template("beranda.html", user=u, pesanan=pesanan)


@app.route("/masuk", methods=["GET", "POST"])
def masuk():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        sandi = request.form.get("sandi", "")
        rows = q("SELECT * FROM pengguna WHERE nama = ? AND sandi = ?", (nama, sandi))
        if rows:
            session["uid"] = rows[0]["id"]
            return redirect(request.args.get("next") or url_for("beranda"))
        flash("Nama atau sandi salah.")
    return render_template("masuk.html")


@app.route("/keluar")
def keluar():
    session.clear()
    return redirect(url_for("masuk"))


@app.route("/lupa-sandi", methods=["GET", "POST"])
def lupa_sandi():
    """Minta tautan pengaturan ulang sandi."""
    token = None
    if request.method == "POST":
        nama = request.form.get("nama", "")
        rows = q("SELECT * FROM pengguna WHERE nama = ?", (nama,))
        if rows:
            token = f"reset-{rows[0]['id']}"
    return render_template("lupa_sandi.html", token=token)


@app.route("/reset-sandi", methods=["GET", "POST"])
def reset_sandi():
    """Setel ulang sandi memakai token."""
    token = request.values.get("token", "")
    pesan = None
    if request.method == "POST":
        sandi_baru = request.form.get("sandi", "")
        uid = token.replace("reset-", "")
        db().execute("UPDATE pengguna SET sandi = ? WHERE id = ?", (sandi_baru, uid))
        db().commit()
        pesan = "Sandi berhasil disetel ulang. Silakan masuk."
    return render_template("reset_sandi.html", token=token, pesan=pesan)


@app.route("/pesanan/<int:pid>")
@login_required
def detail_pesanan(pid: int):
    rows = q(
        "SELECT p.*, pl.nama AS nama_pelanggan, pl.alamat, pl.kontak "
        "FROM pesanan p JOIN pelanggan pl ON pl.id = p.pelanggan_id "
        "WHERE p.id = ?",
        (pid,),
    )
    if not rows:
        abort(404)
    barang = q("SELECT * FROM item_pesanan WHERE pesanan_id = ?", (pid,))
    riwayat = q(
        "SELECT * FROM status_pesanan WHERE pesanan_id = ? ORDER BY id",
        (pid,),
    )
    return render_template(
        "detail.html", user=current_user(), pesanan=rows[0], barang=barang, riwayat=riwayat
    )


@app.route("/pesanan/<int:pid>/unduh")
@login_required
def unduh_faktur(pid: int):
    """Faktur pesanan sebagai berkas teks."""
    rows = q(
        "SELECT p.*, pl.nama AS nama_pelanggan, pl.alamat, pl.kontak, pl.email "
        "FROM pesanan p JOIN pelanggan pl ON pl.id = p.pelanggan_id "
        "WHERE p.id = ?",
        (pid,),
    )
    if not rows:
        abort(404)
    p = rows[0]
    barang = q("SELECT * FROM item_pesanan WHERE pesanan_id = ?", (pid,))
    baris = [
        "FAKTUR LAYANAN PEMESANAN B2B",
        "=" * 44,
        f"Nomor      : {p['nomor']}",
        f"Tanggal    : {p['tanggal']}",
        f"Pelanggan  : {p['nama_pelanggan']}",
        f"Alamat     : {p['alamat']}",
        f"Kontak     : {p['kontak']}",
        f"Email      : {p['email']}",
        f"Status     : {p['status']}",
        "",
        "Item:",
    ]
    for b in barang:
        baris.append(
            f"  - {b['nama_barang']} x{b['qty']} @ {b['harga']} = {b['qty'] * b['harga']}"
        )
    baris += ["", f"Total      : {p['jumlah']}", "", "(dokumen dummy laboratorium)"]
    return Response("\n".join(baris) + "\n", mimetype="text/plain")


@app.route("/pesanan/baru", methods=["GET", "POST"])
@login_required
def buat_pesanan():
    """Buat pesanan baru."""
    if request.method == "POST":
        try:
            pelanggan_id = int(request.form.get("pelanggan_id", "0"))
            qty = int(request.form.get("qty", "0"))
            harga = int(request.form.get("harga", "0"))
            jumlah = int(request.form.get("jumlah", "0"))
        except ValueError:
            flash("Nilai harus berupa angka.")
            return redirect(url_for("buat_pesanan"))
        nomor = request.form.get("nomor", "")
        nama_barang = request.form.get("nama_barang", "")
        catatan = request.form.get("catatan", "")
        db().execute(
            "INSERT INTO pesanan (pelanggan_id, nomor, tanggal, jumlah, status, catatan) "
            "VALUES (?, ?, date('now'), ?, 'Baru', ?)",
            (pelanggan_id, nomor, jumlah, catatan),
        )
        pid = db().execute("SELECT last_insert_rowid()").fetchone()[0]
        db().execute(
            "INSERT INTO item_pesanan (pesanan_id, nama_barang, qty, harga) VALUES (?, ?, ?, ?)",
            (pid, nama_barang, qty, harga),
        )
        db().commit()
        flash(f"Pesanan {nomor} dibuat.")
        return redirect(url_for("detail_pesanan", pid=pid))
    return render_template(
        "buat_pesanan.html",
        user=current_user(),
        daftar_pelanggan=q("SELECT * FROM pelanggan ORDER BY id"),
    )


@app.route("/pesanan/<int:pid>/status", methods=["POST"])
@login_required
def ubah_status(pid: int):
    status_baru = request.form.get("status", "Diproses")
    db().execute("UPDATE pesanan SET status = ? WHERE id = ?", (status_baru, pid))
    db().commit()
    flash(f"Status pesanan #{pid} diubah menjadi {status_baru}.")
    return redirect(url_for("detail_pesanan", pid=pid))


@app.route("/pesanan/<int:pid>/ubah", methods=["POST"])
@login_required
def ubah_jumlah(pid: int):
    """Ubah nilai transaksi sebuah pesanan."""
    nilai = request.form.get("jumlah", "0")
    try:
        nilai = int(nilai)
    except ValueError:
        flash("Jumlah harus berupa angka.")
        return redirect(url_for("detail_pesanan", pid=pid))
    db().execute("UPDATE pesanan SET jumlah = ? WHERE id = ?", (nilai, pid))
    db().commit()
    flash(f"Jumlah pesanan #{pid} diubah menjadi {nilai}.")
    return redirect(url_for("detail_pesanan", pid=pid))


@app.route("/laporan/bulanan")
@login_required
def laporan_bulanan():
    """Rekapitulasi penjualan bulanan."""
    mulai = time.time()
    total = 0
    baris = q("SELECT * FROM pesanan")
    # Rekapitulasi dihitung ulang setiap permintaan.
    for a in range(len(baris) * 4000):
        for b in range(120):
            total += (a * b) % 97
    return render_template(
        "laporan.html",
        user=current_user(),
        jumlah=len(baris),
        total=total,
        detik=round(time.time() - mulai, 3),
    )


# ------------------------------------------------------- proses terjadwal
LANJUT_STATUS = {"Baru": "Diproses", "Diproses": "Dikirim", "Dikirim": "Selesai"}


def jalankan_proses_terjadwal() -> int:
    """Majukan status pesanan yang sedang berjalan.

    Meniru proses terjadwal (cron) yang memajukan alur pesanan satu langkah.
    """
    diubah = 0
    for r in q("SELECT id, status FROM pesanan"):
        berikut = LANJUT_STATUS.get(r["status"])
        if berikut:
            db().execute("UPDATE pesanan SET status = ? WHERE id = ?", (berikut, r["id"]))
            db().commit()
            diubah += 1
    return diubah


@app.route("/proses/terjadwal", methods=["POST"])
@login_required
def picu_proses_terjadwal():
    """Jalankan proses terjadwal secara manual."""
    diubah = jalankan_proses_terjadwal()
    flash(f"Proses terjadwal dijalankan: {diubah} pesanan diperbarui.")
    return redirect(url_for("beranda"))


@app.route("/laporan/ekspor.csv")
@login_required
def ekspor_csv():
    """Ekspor rekapitulasi pesanan sebagai CSV."""
    baris = q(
        "SELECT p.nomor, p.tanggal, pl.nama AS pelanggan, p.jumlah, p.status "
        "FROM pesanan p JOIN pelanggan pl ON pl.id = p.pelanggan_id ORDER BY p.id"
    )
    keluaran = ["nomor,tanggal,pelanggan,jumlah,status"]
    for r in baris:
        keluaran.append(
            f"{r['nomor']},{r['tanggal']},{r['pelanggan']},{r['jumlah']},{r['status']}"
        )
    return Response("\n".join(keluaran) + "\n", mimetype="text/csv")


@app.route("/api/pelanggan")
def api_pelanggan():
    return {
        "jumlah": len(q("SELECT 1 FROM pelanggan")),
        "data": [dict(r) for r in q("SELECT * FROM pelanggan")],
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=False)
