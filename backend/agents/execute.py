import os
import pandas as pd
from pathlib import Path
from .state import AgentState

from .pipeline_logger import log_step, log_error

try:
    from db import get_db
except ImportError:
    from ..db import get_db

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))

def execute_sql_node(state: AgentState) -> dict:
    """
    Node Fail-Fast untuk mengeksekusi SQL ke DuckDB.
    Jika terjadi error atau data kosong, langsung dilaporkan tanpa memicu retry loop.
    Memastikan sanitasi nilai float NaN / inf menjadi None agar kompatibel dengan JSON standar.
    """
    sql_query = state.get("generated_sql")
    sql_error = state.get("sql_error")
    
    log_step("STEP 4: DUCKDB_EXEC", "Mengeksekusi SQL kueri pada DuckDB Engine...", f"SQL: {sql_query}")
    
    # KUNCI KEAMANAN: Jika Sanitizer memblokir, JANGAN SEKALI-KALI mengeksekusi SQL ke DuckDB!
    if sql_error and "SANITIZER BLOCKED" in sql_error:
        log_step("STEP 4: DUCKDB_SKIP", "Eksekusi dibatalkan karena Sanitizer melempar blokir keamanan")
        return {"query_result": None}
        
    if not sql_query:
        return {
            "query_result": None,
            "sql_error": "DATA_EMPTY: Tidak ada kueri SQL yang berhasil dirakit."
        }
        
    try:
        conn = get_db()
        # Eksekusi dan konversi ke dictionary records via shared pool
        result_df = conn.execute(sql_query).df()
        
        # Handle datetime/timestamp dengan cast ke string
        for col in result_df.select_dtypes(include=['datetime', 'datetimetz']).columns:
            result_df[col] = result_df[col].astype(str)
            
        # PENTING: Ganti seluruh float NaN / inf dengan None (JSON null) agar tidak crash "Out of range float values"
        result_df = result_df.where(pd.notnull(result_df), None)
            
        result_dict = result_df.to_dict(orient='records')
        
        log_step("STEP 4: DUCKDB_SUCCESS", f"Hasil kueri DuckDB: {len(result_dict)} baris data diperoleh")
        
        # LOGIKA FAIL-FAST: Deteksi Data Kosong
        is_empty = False
        if len(result_dict) == 0:
            is_empty = True
        elif len(result_dict) == 1:
            # Fungsi agregat SQL (SUM/AVG) akan mengembalikan 1 baris berisi 'null' jika tidak ada data
            if all(v is None or pd.isna(v) for v in result_dict[0].values()):
                is_empty = True
                
        if is_empty:
            return {
                "query_result": None,
                "sql_error": "DATA_EMPTY: Data yang dicari tidak ditemukan atau bernilai kosong pada database."
            }
        
        return {
            "query_result": result_dict,
            "sql_error": None
        }
    except Exception as e:
        log_error("STEP 4: DUCKDB_FAIL", e, context=f"SQL: {sql_query}")
        return {
            "query_result": None,
            "sql_error": f"DB_SYNTAX_ERROR: {str(e)}"
        }
