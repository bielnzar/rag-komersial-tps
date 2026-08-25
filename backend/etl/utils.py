import os
import pandas as pd
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ==========================================
# KONFIGURASI LOGGING (DUAL OUTPUT: Terminal & File)
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"

# 1. Pastikan folder logs eksis
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = LOG_DIR / "etl_system.log"

# 2. Setup Logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        # Rotasi log otomatis. Maksimal 5 MB per file, simpan hingga 5 file arsip (Total 25 MB)
        # Catatan: 5 GB terlalu besar untuk teks dan akan membuat VS Code/Notepad hang.
        RotatingFileHandler(
            LOG_FILE_PATH, 
            mode='a', 
            maxBytes=5 * 1024 * 1024, # 5 MB
            backupCount=5,
            encoding='utf-8'
        ),
        logging.StreamHandler() # Tetap tampilkan di terminal
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# FUNGSI-FUNGSI PEMBERSIHAN DATA (SILVER LAYER)
# ==========================================

def hapus_kolom_hantu(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghapus kolom 'Unnamed' (kolom hantu dari Excel) 
    serta baris dan kolom yang 100% kosong (NaN).
    """
    # Bersihkan spasi tak terlihat di awal/akhir nama kolom (misal "TEUS " jadi "TEUS")
    df.columns = df.columns.astype(str).str.strip()
    
    # Ubah nama kolom "%" menjadi "persentase" agar tidak hilang saat di-regex di fase Gold
    df.rename(columns={'%': 'persentase'}, inplace=True)
    
    # 💡 PERBAIKAN SEMANTIK (Mencegah Ambiguitas LLM):
    # Di dunia pelabuhan, sering ada 2 kolom TEUS (satu untuk BOXES, satu untuk MOVES)
    # Kita rename secara kontekstual dengan melihat kolom sebelumnya
    cols = list(df.columns)
    for i, col in enumerate(cols):
        col_str = str(col).strip().upper()
        if 'BOXES' in col_str and i + 1 < len(cols) and str(cols[i+1]).strip().upper() == 'TEUS':
            df.rename(columns={cols[i+1]: 'boxes_teus'}, inplace=True)
            cols[i+1] = 'boxes_teus'
        elif 'MOVES' in col_str and i + 1 < len(cols) and str(cols[i+1]).strip().upper() == 'TEUS':
            df.rename(columns={cols[i+1]: 'moves_teus'}, inplace=True)
            cols[i+1] = 'moves_teus'
            
    # Deteksi dan buang kolom yang mengandung kata 'Unnamed'
    df_bersih = df.loc[:, ~df.columns.str.contains('^Unnamed', case=False, na=False)]
    
    # Buang baris (axis=0) dan kolom (axis=1) yang isinya NaN semua
    df_bersih = df_bersih.dropna(axis=1, how='all').dropna(axis=0, how='all')
    
    # Bersihkan karakter "-" (strip/dash) yang sering dipakai Excel untuk angka 0
    # Kita replace string yang hanya berisi "-" (dengan atau tanpa spasi) menjadi angka 0
    df_bersih = df_bersih.replace(r'^\s*-\s*$', 0, regex=True)
    
    return df_bersih

def paksa_angka(df: pd.DataFrame, daftar_kolom: list) -> pd.DataFrame:
    """
    Memaksa kolom-kolom teks (seperti "1,500" atau "-") menjadi angka sungguhan.
    Jika ada teks aneh (seperti "N/A"), otomatis diubah menjadi 0.
    """
    for col in daftar_kolom:
        if col in df.columns:
            # Ubah ke string dulu, hapus koma pemisah ribuan, dan bersihkan spasi
            df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.strip()
            # Paksa jadi numerik (error 'coerce' akan mengubah teks gagal menjadi NaN)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            # Ubah ke tingkat debug agar log tidak dipenuhi warning wajar (beda sheet beda struktur itu biasa)
            logger.debug(f"ℹ️ Peringatan: Kolom '{col}' tidak ditemukan saat proses paksa angka (diabaikan).")
            
    return df

def pastikan_kolom_unik(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mencegah error 'Reindexing only valid with uniquely valued Index objects' saat pd.concat.
    Jika ada kolom dengan nama duplikat, tambahkan akhiran _1, _2, dst.
    """
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        mask = cols == dup
        cols[mask] = [f"{dup}_{i}" if i > 0 else dup for i in range(mask.sum())]
    df.columns = cols
    return df

# ==========================================
# FUNGSI DEBUGGING (CHECKPOINT)
# ==========================================

def simpan_debug_csv(df: pd.DataFrame, folder_tahap: str, nama_file_output: str, debug_mode: bool):
    """
    Mencetak DataFrame ke CSV jika DEBUG_MODE = True.
    Akan otomatis membuat folder (seperti data/silver/) jika belum ada.
    """
    if not debug_mode:
        return # Langsung berhenti jika tidak dalam mode debug
        
    try:
        # Memastikan foldernya eksis (membuat otomatis jika belum ada)
        os.makedirs(folder_tahap, exist_ok=True)
        
        # Merakit rute path (contoh: ../data/silver/debug_vessel.csv)
        path_file = os.path.join(folder_tahap, nama_file_output)
        
        # Cetak ke CSV
        df.to_csv(path_file, index=False)
        logger.info(f"✅ [DEBUG] Checkpoint CSV tercetak: {path_file}")
        
    except Exception as e:
        logger.error(f"❌ Gagal mencetak CSV {nama_file_output}: {e}")