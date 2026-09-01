import re
import os
from pathlib import Path
from .state import AgentState
import logging

try:
    from db import get_db
except ImportError:
    from ..db import get_db

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))

# Keyword SQL DDL/DML yang berpotensi memodifikasi/merusak data yang dilarang keras
FORBIDDEN_KEYWORDS = [
    r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b', 
    r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bGRANT\b', 
    r'\bREVOKE\b', r'\bMERGE\b', r'\bEXEC\b', r'\bEXECUTE\b'
]

def sanitizer_node(state: AgentState) -> dict:
    """
    Node Sanitizer Dual-Layer (Input Guard + Output Guard):
    1. Input Guard: Memeriksa pertanyaan pengguna (user_query) terhadap percobaan SQL Injection / Prompt Injection.
    2. Output Guard: Memeriksa SQL rakitan (generated_sql) sebelum dieksekusi ke DuckDB.
    """
    user_query = state.get("user_query", "").strip()
    sql_query = state.get("generated_sql", "").strip()
    current_attempts = state.get("correction_attempts", 0)
    
    errors = []

    # -------------------------------------------------------------
    # TAHAP 1: INPUT GUARD (Memeriksa Input Pertanyaan Pengguna)
    # -------------------------------------------------------------
    upper_user_query = user_query.upper()
    
    # 1a. Cek karakter titik koma (;) pada pertanyaan user (Command Chaining / SQL Injection)
    cleaned_user_query = user_query.rstrip(";")
    if ";" in cleaned_user_query:
        errors.append("Pertanyaan mengandung karakter titik koma (;) yang mengindikasikan percobaan SQL Injection / Multiple Statements.")
        
    # 1b. Cek keyword terlarang DDL/DML pada pertanyaan user (misal: DROP, DELETE, INSERT, TRUNCATE)
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(keyword, upper_user_query):
            clean_keyword = keyword.replace(r'\b', '')
            errors.append(f"Pertanyaan mengandung kata kunci terlarang '{clean_keyword}' yang berpotensi merusak database.")

    # 1c. Cek sintaks komentar SQL (--) atau (/* */)
    if "--" in user_query or "/*" in user_query:
        errors.append("Pertanyaan mengandung karakter komentar SQL (--) atau (/*) yang dilarang.")

    # -------------------------------------------------------------
    # TAHAP 2: OUTPUT GUARD (Memeriksa Query SQL Hasil Rakitan LLM)
    # -------------------------------------------------------------
    if sql_query:
        # 2a. Cek multiple statements pada query SQL
        cleaned_sql = sql_query.rstrip(";")
        if ";" in cleaned_sql:
            errors.append("SQL rakitan mengandung titik koma (;) di tengah query. Pastikan hanya ada SATU blok SELECT.")
            
        # 2b. Cek keyword DDL/DML pada query SQL
        upper_sql = sql_query.upper()
        for keyword in FORBIDDEN_KEYWORDS:
            if re.search(keyword, upper_sql):
                clean_keyword = keyword.replace(r'\b', '')
                errors.append(f"Dilarang menggunakan keyword modifikasi data '{clean_keyword}'. Anda HANYA diizinkan menggunakan perintah SELECT.")
                
        # 2c. Verifikasi bahwa tabel yang dirujuk benar-benar ada di DuckDB schema via shared pool (mendukung CTE WITH ... AS)
        try:
            conn = get_db()
            valid_tables = {row[0].lower() for row in conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()}
            
            cte_matches = {m.lower() for m in re.findall(r'\b(?:WITH|,)\s*([a-zA-Z0-9_]+)\s+AS\s*\(', sql_query, re.IGNORECASE)}
            allowed_tables = valid_tables | cte_matches
            
            table_matches = re.findall(r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)', upper_sql, re.IGNORECASE)
            for tbl in table_matches:
                if tbl.lower() not in allowed_tables:
                    errors.append(f"Tabel '{tbl}' tidak ditemukan di skema database. Periksa kembali struktur tabel.")
        except Exception as e:
            logger.error(f"❌ Sanitizer gagal memvalidasi tabel terhadap DuckDB: {e}")

    # -------------------------------------------------------------
    # RESPON BLOKIR JIKA ADA PELANGGARAN ATURAN KEAMANAN (FAIL-FAST)
    # -------------------------------------------------------------
    if errors:
        error_msg = "SANITIZER BLOCKED: " + " | ".join(errors)
        logger.warning(f"🛡️ {error_msg}")
        return {
            "sql_error": error_msg,
            "correction_attempts": 0
        }
        
    return {"sql_error": None}
