import pandas as pd
import logging
from etl.utils import hapus_kolom_hantu, paksa_angka, pastikan_kolom_unik

logger = logging.getLogger(__name__)

# 💡 PEMETAAN NORMALISASI KATEGORI
# Nama sheet Excel kadang dalam bahasa Indonesia (misal "Domestik").
# Setelah .upper(), ini menghasilkan 'DOMESTIK' alih-alih 'DOMESTIC'.
# Pemetaan ini memastikan semua tabel fakta menggunakan standar bahasa Inggris.
NORMALISASI_KATEGORI = {
    'DOMESTIK': 'DOMESTIC',
    'INTERNASIONAL': 'INTERNATIONAL',
}

def _normalisasi_nama_sheet(nama_sheet: str) -> str:
    """Normalisasi nama sheet ke standar bahasa Inggris."""
    upper = nama_sheet.upper()
    return NORMALISASI_KATEGORI.get(upper, upper)

# ==========================================
# 1. TRANSFORMER: OVERVIEW VESSEL
# ==========================================
def proses_vessel(df: pd.DataFrame, nama_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Mengolah data operasional kapal."""
    df_silver = hapus_kolom_hantu(df)
    
    # Paksa kolom target menjadi angka (menghindari error teks)
    kolom_angka = ['TEUS', 'Boxes', 'BCH', 'BSH']
    df_silver = paksa_angka(df_silver, kolom_angka)
    
    # --- BATAS SILVER LAYER ---
    df_gold = df_silver.copy()
    
    # Beri label dari mana data ini berasal (Domestik / Internasional)
    df_gold['kategori_layanan'] = _normalisasi_nama_sheet(nama_sheet)
    
    # Standarisasi nama kolom ke format database (lowercase & snake_case) yang aman
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    # Kembalikan dataframe silver, gold, dan nama tabel tujuan di DuckDB
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_vessel"


# ==========================================
# 2. TRANSFORMER: CONTAINER THROUGHPUT
# ==========================================
def proses_throughput(df: pd.DataFrame, nama_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Mengolah data KPI Throughput Pelabuhan."""
    df_silver = hapus_kolom_hantu(df)
    
    kolom_angka = ['ACTUAL', 'BUDGET', 'ACTUAL VS BUDGET', 'TEUS']
    df_silver = paksa_angka(df_silver, kolom_angka)
    
    # --- BATAS SILVER LAYER ---
    df_gold = df_silver.copy()
    
    df_gold['kategori_layanan'] = _normalisasi_nama_sheet(nama_sheet)
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_throughput"


# ==========================================
# 3. TRANSFORMER: MARKET SHARE
# ==========================================
def proses_market_share(df: pd.DataFrame, nama_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Mengolah data persaingan pasar dan melakukan Unpivot otomatis."""
    df_silver = hapus_kolom_hantu(df)
    
    # 💡 STANDARISASI SKEMA (Mengatasi halusinasi AI karena 2 kolom berbeda untuk hal yang sama)
    # Sheet12 memakai 'Vessel Operator', sedangkan Sheet lain memakai 'LOP'. 
    # Kita satukan menjadi 'LOP' agar digabung dengan rapi oleh Pandas
    df_silver.rename(columns=lambda x: "LOP" if str(x).strip().upper() == "VESSEL OPERATOR" else x, inplace=True)
    
    # Paksa angka untuk kolom standar (sebelum dilipat)
    df_silver = paksa_angka(df_silver, ['TEUS', 'persentase', '2022 ACTUAL', '2023 ACTUAL'])
    
    # --- BATAS SILVER LAYER ---
    df_gold = df_silver.copy()
    
    # 💡 LOGIKA UNPIVOT (MELT) OTOMATIS
    # Mencari kolom yang namanya mengandung '(TEUS)', misal '2022 (TEUS)'
    kolom_tahun_menyamping = [col for col in df_gold.columns if '(TEUS)' in str(col)]
    
    # Jika terdeteksi ada kolom pivot dan ada kolom 'LOP' (Line Operator)
    if len(kolom_tahun_menyamping) > 0 and 'LOP' in df_gold.columns:
        logger.info(f"🔄 Mendeteksi format Pivot pada sheet '{nama_sheet}'. Melakukan Unpivot...")
        
        # Pisahkan mana kolom yang tetap (tidak ikut dilipat)
        kolom_tetap = [col for col in df_gold.columns if col not in kolom_tahun_menyamping]
        
        # Lipat kolom tahun ke bawah
        df_gold = pd.melt(
            df_gold, 
            id_vars=kolom_tetap, 
            value_vars=kolom_tahun_menyamping, 
            var_name='tahun_kategori', 
            value_name='total_teus'
        )
        
        # Bersihkan teks tahun (Misal: "2022 (TEUS)" diubah jadi "2022" saja)
        df_gold['tahun_kategori'] = df_gold['tahun_kategori'].str.replace(' (TEUS)', '', regex=False)
        df_gold = paksa_angka(df_gold, ['total_teus'])
    
    df_gold['sumber_sheet'] = nama_sheet.upper()
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_market_share"