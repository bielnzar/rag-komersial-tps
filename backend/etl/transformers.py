import pandas as pd
import logging
from etl.utils import hapus_kolom_hantu, paksa_angka, pastikan_kolom_unik

logger = logging.getLogger(__name__)

# 💡 PEMETAAN NORMALISASI KATEGORI
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
    
    kolom_angka = ['TEUS', 'Boxes', 'BCH', 'BSH']
    df_silver = paksa_angka(df_silver, kolom_angka)
    
    df_gold = df_silver.copy()
    df_gold['kategori_layanan'] = _normalisasi_nama_sheet(nama_sheet)
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_vessel"


# ==========================================
# 2. TRANSFORMER: CONTAINER THROUGHPUT
# ==========================================
def proses_throughput(df: pd.DataFrame, nama_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Mengolah data KPI Throughput Pelabuhan."""
    df_silver = hapus_kolom_hantu(df)
    
    kolom_angka = ['ACTUAL', 'BUDGET', 'ACTUAL VS BUDGET', 'TEUS']
    df_silver = paksa_angka(df_silver, kolom_angka)
    
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
    
    df_silver.rename(columns=lambda x: "LOP" if str(x).strip().upper() == "VESSEL OPERATOR" else x, inplace=True)
    df_silver = paksa_angka(df_silver, ['TEUS', 'persentase', '2022 ACTUAL', '2023 ACTUAL'])
    
    df_gold = df_silver.copy()
    kolom_tahun_menyamping = [col for col in df_gold.columns if '(TEUS)' in str(col)]
    
    if len(kolom_tahun_menyamping) > 0 and 'LOP' in df_gold.columns:
        logger.info(f"🔄 Mendeteksi format Pivot pada sheet '{nama_sheet}'. Melakukan Unpivot...")
        kolom_tetap = [col for col in df_gold.columns if col not in kolom_tahun_menyamping]
        df_gold = pd.melt(
            df_gold, 
            id_vars=kolom_tetap, 
            value_vars=kolom_tahun_menyamping, 
            var_name='tahun_kategori', 
            value_name='total_teus'
        )
        df_gold['tahun_kategori'] = df_gold['tahun_kategori'].str.replace(' (TEUS)', '', regex=False)
        df_gold = paksa_angka(df_gold, ['total_teus'])
    
    df_gold['sumber_sheet'] = nama_sheet.upper()
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_market_share"


# ==========================================
# 4. TRANSFORMER: TRANSHIPMENT
# ==========================================
def proses_transhipment(df: pd.DataFrame, nama_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Mengolah data transaksi alih muat kontainer (Transhipment)."""
    df_silver = hapus_kolom_hantu(df)
    
    # Standarisasi kolom LOP / Vessel Operator
    df_silver.rename(columns=lambda x: "LOP" if str(x).strip().upper() in ["VESSEL OPERATOR", "OPERATOR"] else x, inplace=True)
    df_silver = paksa_angka(df_silver, ['SIZE', 'YEAR', 'YARD REVENUE', "20'", "40'", "45'", 'TEUS', 'BOXES'])
    
    df_gold = df_silver.copy()
    df_gold['sumber_sheet'] = nama_sheet.strip().upper()
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_transhipment"


# ==========================================
# 5. TRANSFORMER: VESSEL SERVICE
# ==========================================
def proses_vessel_service(df: pd.DataFrame, nama_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Mengolah data performa & rute layanan kapal (Vessel Service)."""
    df_silver = hapus_kolom_hantu(df)
    
    df_silver.rename(columns=lambda x: "LOP" if str(x).strip().upper() in ["VESSEL OPERATOR", "OPERATOR"] else x, inplace=True)
    df_silver = paksa_angka(df_silver, ['YEAR', 'MONTH', 'TOTAL CALL', 'AVERAGE BMPH', 'AVERAGE GMPH', 'MOVES', 'TEUS'])
    
    df_gold = df_silver.copy()
    df_gold['sumber_sheet'] = nama_sheet.strip().upper()
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_vessel_service"


# ==========================================
# 6. TRANSFORMER: KOMERSIAL DASHBOARD
# ==========================================
def proses_komersial_dashboard(df: pd.DataFrame, nama_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Mengolah data ringkasan KPI Finansial & Komersial."""
    df_silver = hapus_kolom_hantu(df)
    
    df_silver.rename(columns=lambda x: "LOP" if str(x).strip().upper() in ["VESSEL OPERATOR", "OPERATOR"] else x, inplace=True)
    df_silver = paksa_angka(df_silver, ['Tahun', 'TAHUN', 'TOTAL ALL REVENUE', 'MOORING REVENUE', 'TOTAL REVENUE', 'TOTAL TEUs'])
    
    df_gold = df_silver.copy()
    df_gold['sumber_sheet'] = nama_sheet.strip().upper()
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_komersial_dashboard"


# ==========================================
# 7. TRANSFORMER: REALISASI UC (UNIT COST)
# ==========================================
def proses_realisasi_uc(df: pd.DataFrame, nama_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Mengolah data Realisasi Unit Cost operasional."""
    df_silver = hapus_kolom_hantu(df)
    
    df_silver = paksa_angka(df_silver, ['Tahun', 'TAHUN', "20'", "40'", "45'", 'TOTAL BOX', 'TOTAL TEUs', 'TOTAL'])
    
    df_gold = df_silver.copy()
    df_gold['sumber_sheet'] = nama_sheet.strip().upper()
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_realisasi_uc"


# ==========================================
# 8. TRANSFORMER: OVERVIEW BOX
# ==========================================
def proses_overview_box(df: pd.DataFrame, nama_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Mengolah data ringkasan volume box kontainer (Domestik/Internasional)."""
    df_silver = hapus_kolom_hantu(df)
    
    df_silver = paksa_angka(df_silver, ['YEAR', 'TEUS', 'Boxes'])
    
    df_gold = df_silver.copy()
    df_gold['kategori_layanan'] = _normalisasi_nama_sheet(nama_sheet)
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_overview_box"


# ==========================================
# 9. TRANSFORMER: REST & DISC (RESTITUSI & DISKON)
# ==========================================
def proses_rest_n_disc(df: pd.DataFrame, nama_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Mengolah data Restitusi & Diskon Komersial."""
    df_silver = hapus_kolom_hantu(df)
    
    df_gold = df_silver.copy()
    df_gold['sumber_sheet'] = nama_sheet.strip().upper()
    df_gold.columns = df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True).str.replace(r'_+', '_', regex=True).str.strip('_')
    
    return df_silver, pastikan_kolom_unik(df_gold), "fakta_rest_n_disc"