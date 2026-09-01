import os
import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "processed" / "tps_komersial.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("==================================================")
print("   EVALUASI 5 PERTANYAAN KOMPLEKS AGENT AI TPS    ")
print("==================================================")

# Q1: Top 3 LOP Market Share 2023
q1 = conn.execute("""
    SELECT lop, SUM(total_teus) as total 
    FROM fakta_market_share 
    WHERE tahun_kategori = '2023' AND lop IS NOT NULL AND lop != '' 
    GROUP BY lop 
    ORDER BY total DESC 
    LIMIT 3;
""").fetchall()
print("\n1. Top 3 LOP Market Share 2023:")
for row in q1:
    print(f"   - LOP '{row[0]}': {row[1]:,.2f} TEUs")

# Q2: Throughput Actual vs Budget International 2023
q2 = conn.execute("""
    SELECT SUM(actual) as total_actual, SUM(budget) as total_budget 
    FROM fakta_throughput 
    WHERE year = 2023 AND kategori_layanan = 'INTERNATIONAL';
""").fetchone()
print(f"\n2. Throughput International 2023:\n   - Actual: {q2[0]:,.2f} TEUs | Budget: {q2[1]:,.2f} TEUs")

# Q3: Top 5 BMPH Layanan Kapal
q3 = conn.execute("""
    SELECT lop, AVG(average_bmph) as avg_bmph 
    FROM fakta_vessel_service 
    WHERE lop IS NOT NULL AND lop != '' 
    GROUP BY lop 
    ORDER BY avg_bmph DESC 
    LIMIT 5;
""").fetchall()
print("\n3. Top 5 Operator BMPH Layanan Kapal:")
for row in q3:
    print(f"   - LOP '{row[0]}': {row[1]:,.2f} BMPH")

# Q4: Unit Cost Status FULL 2024
q4 = conn.execute("""
    SELECT SUM(total) as total_cost, SUM(total_teus) as total_teus 
    FROM fakta_realisasi_uc 
    WHERE status ILIKE '%FULL%' AND tahun = 2024;
""").fetchone()
print(f"\n4. Unit Cost Status FULL 2024:\n   - Total Biaya: Rp {q4[0]:,.2f} | Volume: {q4[1]:,.2f} TEUs")

# Q5: Transhipment DISCHARGE 2024
q5 = conn.execute("""
    SELECT SUM(yard_revenue) as total_revenue, SUM("20_") as total_20ft 
    FROM fakta_transhipment 
    WHERE tipe ILIKE 'DISCHARGE' AND year = 2024;
""").fetchone()
print(f"\n5. Transhipment DISCHARGE 2024:\n   - Yard Revenue: Rp {q5[0]:,.2f} | Container 20ft: {q5[1]:,} Boxes")

conn.close()
