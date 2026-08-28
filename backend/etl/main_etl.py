import os
from pathlib import Path
import pandas as pd
import duckdb
from dotenv import load_dotenv

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modul lokal buatan kita
from etl.utils import logger, simpan_debug_csv
from etl.transformers import proses_vessel, proses_throughput, proses_market_share

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
# Menghubungkan nama file Excel dengan fungsi transformernya
# ==========================================
FILE_ROUTER = {
    "OVERVIEW VESSEL.xlsx": proses_vessel,
    "Container Throughput.xlsx": proses_throughput,
    "Market Share.xlsx": proses_market_share
}

def jalankan_etl():
    logger.info("🚀 MEMULAI PROSES ETL MEDALLION...")
    
    # Pastikan folder tempat DuckDB berada sudah eksis
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Buka koneksi ke DuckDB
    conn = duckdb.connect(DB_PATH)
    
    # Dictionary untuk menampung gabungan dataframe antar-sheet
    # Contoh isi: {"fakta_vessel": [df_domestik, df_internasional]}
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
                    simpan_debug_csv(df_mentah, str(BASE_DIR / "data/bronze"), f"bronze_{nama_sheet}.csv", DEBUG_MODE)
                    
                    # 🥈 Eksekusi Transformer (Silver Layer & Gold Layer)
                    df_silver, df_gold, nama_tabel = fungsi_proses(df_mentah, nama_sheet)
                    
                    # Checkpoint Silver (Opsional)
                    simpan_debug_csv(df_silver, str(BASE_DIR / "data/silver"), f"silver_{nama_sheet}.csv", DEBUG_MODE)
                    
                    # Checkpoint Gold (Opsional)
                    simpan_debug_csv(df_gold, str(BASE_DIR / "data/gold"), f"gold_{nama_sheet}.csv", DEBUG_MODE)
                    
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
                # Misal: df_vessel_domestik + df_vessel_internasional digabung memanjang ke bawah
                df_final = pd.concat(daftar_df, ignore_index=True)
                
                # 💡 PENAWAR DUCKDB SCHEMA INFERENCE ERROR (BIGINT -> TIMESTAMP, dsb)
                # DuckDB sering crash jika satu kolom berisi campuran (misal teks "-" dan angka, atau Timestamp dan Integer)
                # Solusinya: Konversi kolom bertipe 'object' (campuran) atau 'datetime' menjadi String secara aman
                for col in df_final.select_dtypes(include=['object', 'str', 'datetime']).columns:
                    # Pastikan nilai kosong (NaN/None) tidak berubah menjadi teks "nan"
                    df_final[col] = df_final[col].apply(lambda x: str(x) if pd.notnull(x) else None)
                
                # Simpan ke DuckDB (Menimpa tabel lama jika sudah ada)
                conn.register('temp_df', df_final)
                conn.execute(f"CREATE OR REPLACE TABLE {nama_tabel} AS SELECT * FROM temp_df")
                conn.unregister('temp_df')
                logger.info(f"   ✅ Berhasil menanam tabel '{nama_tabel}' ({len(df_final)} baris)")
                
            except Exception as e:
                logger.error(f"   ❌ Gagal menyimpan tabel '{nama_tabel}': {e}")

    # Tutup koneksi dengan aman
    conn.close()
    logger.info("🎉 PROSES ETL SELESAI DENGAN SUKSES!")

if __name__ == "__main__":
    jalankan_etl()