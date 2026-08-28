import os
import pandas as pd
import duckdb
from pathlib import Path
from .state import AgentState

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))

def execute_sql_node(state: AgentState) -> dict:
    """
    Node untuk mengeksekusi SQL yang dihasilkan agen ke dalam DuckDB.
    """
    sql_query = state.get("generated_sql")
    sql_error = state.get("sql_error")
    
    # KUNCI KEAMANAN: Jika Sanitizer memblokir, JANGAN SEKALI-KALI mengeksekusi SQL ke DuckDB!
    if sql_error and "SANITIZER BLOCKED" in sql_error:
        return {"query_result": None}
        
    if not sql_query:
        return {"sql_error": "Tidak ada SQL yang dihasilkan."}
        
    try:
        conn = duckdb.connect(DB_PATH, read_only=True)
        # Eksekusi dan konversi ke dictionary records
        result_df = conn.execute(sql_query).df()
        conn.close()
        
        # Konversi pandas DataFrame ke list of dicts agar mudah dibaca LLM
        # Handle datetime/timestamp dengan cast ke string
        for col in result_df.select_dtypes(include=['datetime', 'datetimetz']).columns:
            result_df[col] = result_df[col].astype(str)
            
        result_dict = result_df.to_dict(orient='records')
        
        current_attempts = state.get("correction_attempts", 0)
        
        # LOGIKA SELF-HEALING: Deteksi Data Kosong
        is_empty = False
        if len(result_dict) == 0:
            is_empty = True
        elif len(result_dict) == 1:
            # Fungsi agregat SQL (SUM/AVG) akan mengembalikan 1 baris berisi 'null' jika tidak ada data
            # Kita anggap ini juga sebagai data kosong
            if all(v is None or pd.isna(v) for v in result_dict[0].values()):
                is_empty = True
                
        if is_empty:
            return {
                "query_result": None,
                "sql_error": "Eksekusi berhasil namun DATA KOSONG (0 baris)! Coba periksa kembali ejaan string filter Anda (gunakan Glosarium) atau periksa struktur skema tabel. Jangan menyerah!",
                "correction_attempts": current_attempts + 1
            }
        
        return {
            "query_result": result_dict,
            "sql_error": None, # Reset error jika sukses
            "correction_attempts": 0 # Reset attempts jika sukses
        }
    except Exception as e:
        current_attempts = state.get("correction_attempts", 0)
        return {
            "query_result": None,
            "sql_error": f"SYNTAX ERROR: {str(e)}",
            "correction_attempts": current_attempts + 1
        }
