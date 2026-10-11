-- Seed basis data dummy — Layanan Pemesanan B2B (BAB 1)
-- Seluruh data fiktif. Tidak ada data pribadi yang nyata.
-- Dimuat otomatis oleh docker-entrypoint.sh, atau manual:
--   sqlite3 data/pesanan.db < db/seed.sql

DROP TABLE IF EXISTS status_pesanan;
DROP TABLE IF EXISTS item_pesanan;
DROP TABLE IF EXISTS pesanan;
DROP TABLE IF EXISTS pengguna;
DROP TABLE IF EXISTS pelanggan;

CREATE TABLE pelanggan (
    id       INTEGER PRIMARY KEY,
    nama     TEXT NOT NULL,
    alamat   TEXT,
    kontak   TEXT,
    email    TEXT,
    segmen   TEXT
);

CREATE TABLE pengguna (
    id           INTEGER PRIMARY KEY,
    nama         TEXT NOT NULL,
    sandi        TEXT NOT NULL,
    peran        TEXT NOT NULL,          -- pelanggan | operator | admin
    pelanggan_id INTEGER REFERENCES pelanggan(id)
);

CREATE TABLE pesanan (
    id           INTEGER PRIMARY KEY,
    pelanggan_id INTEGER NOT NULL REFERENCES pelanggan(id),
    nomor        TEXT NOT NULL,
    tanggal      TEXT NOT NULL,
    jumlah       INTEGER NOT NULL,       -- rupiah
    status       TEXT NOT NULL,          -- Baru | Diproses | Dikirim | Selesai
    catatan      TEXT
);

CREATE TABLE item_pesanan (
    id           INTEGER PRIMARY KEY,
    pesanan_id   INTEGER NOT NULL REFERENCES pesanan(id),
    nama_barang  TEXT NOT NULL,
    qty          INTEGER NOT NULL,
    harga        INTEGER NOT NULL
);

-- Riwayat status pesanan.
CREATE TABLE status_pesanan (
    id          INTEGER PRIMARY KEY,
    pesanan_id  INTEGER NOT NULL REFERENCES pesanan(id),
    status      TEXT NOT NULL,
    diubah_oleh TEXT,
    waktu       TEXT
);

-- ---------------------------------------------------------------- pelanggan
INSERT INTO pelanggan (id, nama, alamat, kontak, email, segmen) VALUES
 (1, 'PT Sinar Baja Nusantara',   'Jl. Industri Raya 12, Makassar',   '0411-555-0101', 'proc@sinarbaja.example',  'Korporat'),
 (2, 'CV Mitra Katering Sejahtera','Jl. Perintis Kemerdekaan 88',     '0411-555-0102', 'order@mitrakatering.example','UMKM'),
 (3, 'Koperasi Karyawan Andalan', 'Jl. Perdagangan 5, Gowa',          '0411-555-0103', 'kop@andalan.example',      'Koperasi'),
 (4, 'PT Anugerah Logistik Timur','Jl. Pelabuhan Baru 3',             '0411-555-0104', 'logistik@alt.example',     'Korporat'),
 (5, 'Toko Bangunan Sumber Jaya','Jl. Rappocini 21',                  '0411-555-0105', 'sumberjaya@example',       'UMKM'),
 (6, 'RS Sehat Bersama',          'Jl. Perintis 100',                 '0411-555-0106', 'pengadaan@rssehat.example','Korporat');

-- ----------------------------------------------------------------- pengguna
INSERT INTO pengguna (id, nama, sandi, peran, pelanggan_id) VALUES
 (1, 'pelanggan1', 'rahasia',   'pelanggan', 1),
 (2, 'pelanggan2', 'rahasia',   'pelanggan', 2),
 (3, 'pelanggan3', 'rahasia',   'pelanggan', 3),
 (4, 'operator1',  'operator',  'operator',  NULL),
 (5, 'admin1',     'admin',     'admin',     NULL);

-- ------------------------------------------------------------------ pesanan
INSERT INTO pesanan (id, pelanggan_id, nomor, tanggal, jumlah, status, catatan) VALUES
 (1, 1, 'PO-2026-0001', '2026-08-04', 48500000, 'Selesai',  'Pengiriman bertahap 3 kali'),
 (2, 1, 'PO-2026-0007', '2026-08-19', 12750000, 'Dikirim',  'Besi hollow 40x40'),
 (3, 2, 'PO-2026-0002', '2026-08-06',  3850000, 'Selesai',  'Paket katering bulanan'),
 (4, 2, 'PO-2026-0009', '2026-08-22',  4120000, 'Diproses', 'Tambahan untuk acara pelatihan'),
 (5, 3, 'PO-2026-0003', '2026-08-08',  9750000, 'Dikirim',  'Sembako koperasi'),
 (6, 3, 'PO-2026-0011', '2026-08-26',  6250000, 'Baru',     'Pesanan ulang sembako'),
 (7, 4, 'PO-2026-0004', '2026-08-11', 21400000, 'Selesai',  'Palet kayu ekspedisi'),
 (8, 4, 'PO-2026-0013', '2026-08-28', 16800000, 'Diproses', 'Perbaikan palet rusak'),
 (9, 5, 'PO-2026-0005', '2026-08-14',  1840000, 'Selesai',  'Semen 40 sak'),
 (10,6, 'PO-2026-0006', '2026-08-16', 33200000, 'Dikirim',  'Alat kesehatan habis pakai'),
 (11,6, 'PO-2026-0015', '2026-08-30', 11500000, 'Baru',     'Masker dan sarung tangan');

-- ------------------------------------------------------------- item pesanan
INSERT INTO item_pesanan (pesanan_id, nama_barang, qty, harga) VALUES
 (1, 'Plat baja lembaran',      120, 250000),
 (1, 'Besi beton ulir 10mm',    300,  62000),
 (2, 'Besi hollow 40x40',       150,  85000),
 (3, 'Paket katering harian',    80,  45000),
 (3, 'Air mineral kemasan',      25,  10000),
 (4, 'Paket katering pelatihan', 90,  43000),
 (5, 'Beras premium 25kg',       60, 155000),
 (5, 'Minyak goreng 18L',        10,  185000),
 (6, 'Gula pasir 50kg',          25, 250000),
 (7, 'Palet kayu standar',      400,  53500),
 (8, 'Jasa perbaikan palet',    320,  52500),
 (9, 'Semen 50kg',               40,  46000),
 (10,'Sarung tangan medis',    2000,  12000),
 (10,'Masker bedah',           3000,   4400),
 (11,'Masker N95',             1000,   9500),
 (11,'Hand sanitizer 500ml',    250,   8000);

-- --------------------------------------------------------- riwayat status
INSERT INTO status_pesanan (pesanan_id, status, diubah_oleh, waktu) VALUES
 (1, 'Baru',     'operator1', '2026-08-04 09:12:00'),
 (1, 'Diproses', 'operator1', '2026-08-05 08:30:00'),
 (1, 'Dikirim',  'operator1', '2026-08-07 14:05:00'),
 (1, 'Selesai',  'operator1', '2026-08-12 10:44:00'),
 (2, 'Baru',     'operator1', '2026-08-19 11:02:00'),
 (2, 'Diproses', 'operator1', '2026-08-20 09:15:00'),
 (2, 'Dikirim',  'operator1', '2026-08-23 16:20:00'),
 (3, 'Baru',     'operator1', '2026-08-06 08:55:00'),
 (3, 'Selesai',  'operator1', '2026-08-10 15:10:00'),
 (5, 'Baru',     'operator1', '2026-08-08 10:00:00'),
 (5, 'Dikirim',  'operator1', '2026-08-13 09:30:00'),
 (7, 'Baru',     'operator1', '2026-08-11 13:20:00'),
 (7, 'Selesai',  'operator1', '2026-08-18 11:45:00'),
 (9, 'Baru',     'operator1', '2026-08-14 09:05:00'),
 (9, 'Selesai',  'operator1', '2026-08-17 14:00:00'),
 (10,'Baru',     'operator1', '2026-08-16 10:30:00'),
 (10,'Dikirim',  'operator1', '2026-08-21 08:50:00');
