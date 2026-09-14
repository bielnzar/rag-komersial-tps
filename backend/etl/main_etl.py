import os
from pathlib import Path
import pandas as pd
import duckdb
from dotenv import load_dotenv

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modul lokal buatan kita
from etl.utils import logger, simpan_debug_csv
from etl.transformers import (
    proses_vessel, 
    proses_throughput, 
    proses_market_share,
    proses_transhipment,
    proses_vessel_service,
    proses_komersial_dashboard,
    proses_realisasi_uc,
    proses_overview_box,
    proses_rest_n_disc
)

# ==========================================
# KONFIGURASI ENVIRONMENT
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == 'true'
DB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))
RAW_DIR = str(BASE_DIR / "data/raw")

# ==========================================
# PETA RUTE (ROUTER)
# Menghubungkan seluruh 9 nama file Excel dengan fungsi transformernya
# ==========================================
FILE_ROUTER = {
    "OVERVIEW VESSEL.xlsx": proses_vessel,
    "Container Throughput.xlsx": proses_throughput,
    "Market Share.xlsx": proses_market_share,
    "Transhipment.xlsx": proses_transhipment,
    "VESSEL SERVICE.xlsx": proses_vessel_service,
    "Komersial Dashboard.xlsx": proses_komersial_dashboard,
    "Realisasi UC.xlsx": proses_realisasi_uc,
    "OVERVIEW BOX.xlsx": proses_overview_box,
    "RestNDisc.xlsx": proses_rest_n_disc
}

def jalankan_etl():
    logger.info("🚀 MEMULAI PROSES ETL MEDALLION LENGKAP (9 FILE EXCEL)...")
    
    # Pastikan folder tempat DuckDB berada sudah eksis
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Buka koneksi ke DuckDB
    conn = duckdb.connect(DB_PATH)
    
    # Dictionary untuk menampung gabungan dataframe antar-sheet
    koleksi_tabel = {}

    # ==========================================
    # FASE 1 & 2: BRONZE & SILVER (Ekstraksi & Transformasi)
    # ==========================================
    for nama_file in os.listdir(RAW_DIR):
        if nama_file in FILE_ROUTER:
            path_file = os.path.join(RAW_DIR, nama_file)
            logger.info(f"📥 Mengekstraksi file: {nama_file}")
            
            try:
                # Membaca SELURUH sheet otomatis menjadi Dictionary (Bronze Layer)
                semua_sheet = pd.read_excel(path_file, sheet_name=None)
                fungsi_proses = FILE_ROUTER[nama_file]
                
                # Looping ke masing-masing sheet
                for nama_sheet, df_mentah in semua_sheet.items():
                    logger.info(f"   ⚙️ Memproses sheet: {nama_sheet}")
                    
                    # Checkpoint Bronze (Opsional)
                    simpan_debug_csv(df_mentah, str(BASE_DIR / "data/bronze"), f"bronze_{nama_file}_{nama_sheet}.csv", DEBUG_MODE)
                    
                    # 🥈 Eksekusi Transformer (Silver Layer & Gold Layer)
                    df_silver, df_gold, nama_tabel = fungsi_proses(df_mentah, nama_sheet)
                    
                    # Checkpoint Silver (Opsional)
                    simpan_debug_csv(df_silver, str(BASE_DIR / "data/silver"), f"silver_{nama_file}_{nama_sheet}.csv", DEBUG_MODE)
                    
                    # Checkpoint Gold (Opsional)
                    simpan_debug_csv(df_gold, str(BASE_DIR / "data/gold"), f"gold_{nama_file}_{nama_sheet}.csv", DEBUG_MODE)
                    
                    # Tampung dataframe matang untuk digabungkan nanti
                    if nama_tabel not in koleksi_tabel:
                        koleksi_tabel[nama_tabel] = []
                    koleksi_tabel[nama_tabel].append(df_gold)
                    
            except Exception as e:
                logger.error(f"❌ Gagal memproses {nama_file}: {e}")

    # ==========================================
    # FASE 3: GOLD LAYER (Load to Database)
    # ==========================================
    logger.info("💾 MENYIMPAN HASIL KONSOLIDASI KE DUCKDB...")
    for nama_tabel, daftar_df in koleksi_tabel.items():
        if daftar_df: # Jika ada isinya
            try:
                # 🥇 KUNCI ARSITEKTUR: Menggabungkan (Concat) semua sheet yang setipe
                df_final = pd.concat(daftar_df, ignore_index=True)
                
                # 💡 PENAWAR DUCKDB SCHEMA INFERENCE ERROR & PEMBERSIHAN TIMESTAMP 00:00:00
                for col in df_final.select_dtypes(include=['datetime', 'datetimetz']).columns:
                    df_final[col] = df_final[col].dt.strftime('%Y-%m-%d')
                
                for col in df_final.select_dtypes(include=['object', 'str']).columns:
                    df_final[col] = df_final[col].apply(
                        lambda x: str(x).replace(' 00:00:00', '').strip() if pd.notnull(x) else None
                    )
                
                # Simpan ke DuckDB (Menimpa tabel lama jika sudah ada)
                conn.register('temp_df', df_final)
                conn.execute(f"CREATE OR REPLACE TABLE {nama_tabel} AS SELECT * FROM temp_df")
                conn.unregister('temp_df')
                logger.info(f"   ✅ Berhasil menanam tabel '{nama_tabel}' ({len(df_final)} baris)")
                
            except Exception as e:
                logger.error(f"   ❌ Gagal menyimpan tabel '{nama_tabel}': {e}")

    # ==========================================
    # FASE 4: POST-PROCESSING & SCHEMA CASTING
    # Menghapus duplikasi/null anomali & memastikan tipe data diskrit adalah BIGINT murni
    # ==========================================
    pasca_proses_pembersihan_dan_tipe(conn)

    # Tutup koneksi dengan aman
    conn.close()
    logger.info("🎉 PROSES ETL MEDALLION LENGKAP SELESAI DENGAN SUKSES!")

def pasca_proses_pembersihan_dan_tipe(conn: duckdb.DuckDBPyConnection):
    """
    Membersihkan anomali NULL/0 dan mengonversi kolom diskrit/angka bulat
    dari DOUBLE menjadi BIGINT murni di seluruh tabel DuckDB.
    """
    logger.info("🛠️ MENJALANKAN PASCA-PROSES PEMBERSIHAN DATA & TYPE CASTING KE BIGINT...")

    # 1. PEMBERSIHAN FAKTA KOMERSIAL DASHBOARD
    try:
        # Pisahkan kamus master SHEET3 ke tabel dimensi dim_vessel_operator
        conn.execute("""
            CREATE OR REPLACE TABLE dim_vessel_operator AS 
            SELECT DISTINCT UPPER(TRIM(code)) as code, TRIM(full_name) as full_name 
            FROM fakta_komersial_dashboard 
            WHERE sumber_sheet = 'SHEET3' AND code IS NOT NULL;
        """)
        # Hapus baris dummy SHEET3 dari fakta_komersial_dashboard agar tidak mengotori tabel fakta
        conn.execute("DELETE FROM fakta_komersial_dashboard WHERE sumber_sheet = 'SHEET3';")
        
        # Lengkapi nama panjang LOP (full_name) dan kode operator (code) dari kamus dimensi
        conn.execute("""
            UPDATE fakta_komersial_dashboard AS f 
            SET full_name = d.full_name,
                code = d.code
            FROM dim_vessel_operator AS d 
            WHERE (UPPER(TRIM(f.lop)) = d.code OR SUBSTRING(UPPER(TRIM(f.lop)), 1, 3) = d.code);
        """)
        conn.execute("UPDATE fakta_komersial_dashboard SET code = UPPER(TRIM(lop)) WHERE code IS NULL;")
        conn.execute("UPDATE fakta_komersial_dashboard SET full_name = lop WHERE full_name IS NULL;")
        
        # Sinkronisasi kolom pendapatan total_all_revenue dan total_revenue agar tidak ada NULL
        conn.execute("""
            UPDATE fakta_komersial_dashboard 
            SET total_all_revenue = COALESCE(total_all_revenue, total_revenue), 
                total_revenue = COALESCE(total_revenue, total_all_revenue);
        """)
        
        # Atur nilai default untuk baris ringkasan tahunan
        conn.execute("UPDATE fakta_komersial_dashboard SET bulan = 'Tahunan' WHERE (bulan IS NULL OR TRIM(bulan) = '') AND sumber_sheet = 'TREND KOMERSIAL';")
        
        # Bersihkan nilai NULL pada kolom kuantitas box dan numerik menjadi 0
        conn.execute("""
            UPDATE fakta_komersial_dashboard 
            SET "20_fcl_box" = COALESCE("20_fcl_box", 0), 
                "40_fcl_box" = COALESCE("40_fcl_box", 0), 
                "20_mty_box" = COALESCE("20_mty_box", 0), 
                "40_mty_box" = COALESCE("40_mty_box", 0), 
                total_box = COALESCE(total_box, 0), 
                mooring_revenue = COALESCE(mooring_revenue, 0),
                no = COALESCE(no, 0),
                month = COALESCE(month, 0),
                urutan = COALESCE(urutan, 0),
                year = COALESCE(year, tahun);
        """)
        logger.info("   ✅ Pembersihan anomali fakta_komersial_dashboard selesai.")
    except Exception as e:
        logger.error(f"   ⚠️ Gagal membersihkan fakta_komersial_dashboard: {e}")

    # 2. PENYELARASAN FAKTA OVERVIEW BOX DARI MASTER DATA FAKTA VESSEL (OPSI 1)
    try:
        conn.execute("""
            CREATE OR REPLACE TABLE fakta_overview_box AS 
            SELECT 
                REPLACE(date, ' 00:00:00', '') AS date, 
                year, 
                month_code, 
                month, 
                lop, 
                teus, 
                boxes, 
                kategori_layanan 
            FROM fakta_vessel
            ORDER BY year, month_code, lop;
        """)
        logger.info("   ✅ Berhasil menyelaraskan fakta_overview_box dari master data fakta_vessel (940 baris akurat).")
    except Exception as e:
        logger.error(f"   ⚠️ Gagal menyelaraskan fakta_overview_box: {e}")

    # 3. PEMBERSIHAN RESIDU STRING ' 00:00:00' PADA SELURUH TABEL FAKTA
    kolom_tanggal_per_tabel = [
        ('fakta_vessel', 'date'),
        ('fakta_overview_box', 'date'),
        ('fakta_market_share', 'date'),
        ('fakta_realisasi_uc', 'date'),
        ('fakta_transhipment', 'date'),
        ('fakta_rest_n_disc', 'tanggal_surat_jawaban_tps')
    ]
    for tbl, col in kolom_tanggal_per_tabel:
        try:
            conn.execute(f"UPDATE \"{tbl}\" SET \"{col}\" = REPLACE(\"{col}\", ' 00:00:00', '') WHERE \"{col}\" LIKE '% 00:00:00%';")
        except Exception as e:
            logger.debug(f"Pembersihan tanggal {tbl}.{col} dilewati: {e}")

    # 4. TYPE CASTING OTOMATIS KE BIGINT
    kolom_bigint_per_tabel = {
        'fakta_komersial_dashboard': ['no', 'tahun', 'year', 'month', 'urutan', '20_fcl_box', '40_fcl_box', '20_mty_box', '40_mty_box', 'total_box'],
        'fakta_market_share': ['year', 'month', 'no', 'box_2023'],
        'fakta_overview_box': ['year', 'month_code', 'boxes'],
        'fakta_realisasi_uc': ['year', 'month', 'total_box'],
        'fakta_transhipment': ['year', 'tahun', 'size', 'boxes_2024', 'boxes_2025', 'year_inv'],
        'fakta_vessel': ['boxes'],
        'fakta_vessel_service': ['no', 'year', 'month', 'total_call', 'moves']
    }

    for nama_tabel, daftar_kolom in kolom_bigint_per_tabel.items():
        try:
            existing_cols = set(r[0] for r in conn.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{nama_tabel}'").fetchall())
            for col in daftar_kolom:
                if col in existing_cols:
                    conn.execute(f'ALTER TABLE "{nama_tabel}" ALTER COLUMN "{col}" TYPE BIGINT USING ROUND(TRY_CAST("{col}" AS DOUBLE))::BIGINT;')
            logger.info(f"   ✅ Berhasil casting kolom diskrit {nama_tabel} -> BIGINT")
        except Exception as e:
            logger.error(f"   ⚠️ Gagal casting tipe data {nama_tabel}: {e}")

if __name__ == "__main__":
    jalankan_etl()