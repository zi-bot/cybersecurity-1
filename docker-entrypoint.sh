#!/bin/sh
set -e
DB=/srv/data/pesanan.db
mkdir -p /srv/data
if [ ! -f "$DB" ]; then
  echo "[seed] membuat basis data dummy di $DB"
  python3 - <<'PY'
import sqlite3, pathlib
db = pathlib.Path("/srv/data/pesanan.db")
sql = pathlib.Path("/srv/db/seed.sql").read_text(encoding="utf-8")
con = sqlite3.connect(db); con.executescript(sql); con.commit(); con.close()
print("[seed] selesai")
PY
fi
exec python3 -m flask --app app.main run --host 0.0.0.0 --port 8081
