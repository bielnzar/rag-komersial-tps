import os
from pathlib import Path
from db import get_db

BASE_DIR = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == 'backend' else Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'data' / 'processed' / 'tps_komersial.duckdb'

if not DB_PATH.exists():
    print(f"❌ Error: Database tidak ditemukan di lokasi: {DB_PATH}")
    exit(1)

conn = get_db(str(DB_PATH))

print("==========================================")
print("   DUCKDB PT TPS KOMERSIAL INSPECTION     ")
print(f"   Database Path: {DB_PATH}")
print("==========================================")

tables = conn.execute("SHOW TABLES;").fetchall()
for t in tables:
    tbl_name = t[0]
    count = conn.execute(f"SELECT COUNT(*) FROM {tbl_name};").fetchone()[0]
    print(f"\n📌 Tabel: '{tbl_name}' | Total: {count:,} baris")
    
    # Tampilkan struktur kolom
    cols = conn.execute(f"PRAGMA table_info('{tbl_name}');").fetchall()
    col_str = ", ".join([f"{c[1]} ({c[2]})" for c in cols])
    print(f"   Kolom: {col_str}")
