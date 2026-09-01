import os
import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "tps_komersial.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("--- EVALUASI DATASET TABEL BARU ---")

# Q1: Transhipment
r1 = conn.execute("SELECT SUM(yard_revenue) FROM fakta_transhipment WHERE year = 2024").fetchone()[0]
print(f"1. Total Yard Revenue Transhipment 2024: Rp {r1:,.2f}" if r1 else "Q1 None")

# Q2: Vessel Service
r2 = conn.execute("SELECT SUM(moves) FROM fakta_vessel_service WHERE lop ILIKE 'COS'").fetchone()[0]
print(f"2. Total Moves Vessel Service Operator COS: {r2:,} Moves" if r2 else "Q2 None")

# Q3: Realisasi UC
r3 = conn.execute("SELECT SUM(total_teus) FROM fakta_realisasi_uc WHERE tahun = 2024").fetchone()[0]
print(f"3. Total TEUs Realisasi UC 2024: {r3:,.2f} TEUs" if r3 else "Q3 None")

# Q4: Komersial Dashboard
r4 = conn.execute("SELECT SUM(total_all_revenue) FROM fakta_komersial_dashboard WHERE tahun = 2023").fetchone()[0]
print(f"4. Total Revenue Komersial Dashboard 2023: Rp {r4:,.2f}" if r4 else "Q4 None")

# Q5: Overview Box
r5 = conn.execute("SELECT SUM(teus) FROM fakta_overview_box WHERE kategori_layanan = 'DOMESTIC'").fetchone()[0]
print(f"5. Total TEUs Overview Box Domestik: {r5:,.2f} TEUs" if r5 else "Q5 None")

conn.close()
