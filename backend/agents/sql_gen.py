import os
import pandas as pd
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
from .llm_helper import invoke_chain_with_fallback

try:
    from db import get_db
    from cache import semantic_cache
except ImportError:
    from ..db import get_db
    from ..cache import semantic_cache

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))

def get_duckdb_schema(relevant_tables: list[str] | None = None) -> str:
    """Mengambil skema tabel dan kolom secara dinamis dari DuckDB via Shared Schema Cache."""
    try:
        cached_df_records = semantic_cache.get_schema_cache("full_schema_records")
        if cached_df_records:
            df_schema = pd.DataFrame(cached_df_records)
        else:
            conn = get_db()
            query = """
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema='main' 
                ORDER BY table_name, ordinal_position;
            """
            df_schema = conn.execute(query).df()
            semantic_cache.set_schema_cache("full_schema_records", df_schema.to_dict(orient="records"))
            
        if relevant_tables:
            df_schema = df_schema[df_schema['table_name'].isin(relevant_tables)]
            
        schema_str = "Skema Database DuckDB:\n"
        current_table = ""
        for _, row in df_schema.iterrows():
            if row['table_name'] != current_table:
                current_table = row['table_name']
                schema_str += f"\nTable {current_table}:\n"
            schema_str += f"- {row['column_name']} ({row['data_type']})\n"
        return schema_str
    except Exception as e:
        return f"Gagal mengambil schema: {str(e)}"

SQL_SYSTEM_PROMPT = """Rakit query DuckDB SQL murni berdasarkan pertanyaan pengguna dan riwayat percakapan terdekat.

Glosarium & Semantik:
- Domestik -> 'DOMESTIC' / 'DOM'
- Internasional -> 'INTERNATIONAL' / 'INT'
- Tabel fakta_throughput: Seluruh baris adalah data volume peti kemas (TEUs). JANGAN filter kata 'peti kemas' / 'container'. Cukup filter tahun dan kategori_layanan (misal: kategori_layanan ILIKE '%international%').
- Kolom pendapatan utama di fakta_komersial_dashboard: HARUS gabungkan COALESCE(total_all_revenue, total_revenue) AS total_revenue karena data pendapatan terpisah di dua kolom tersebut.
- Gunakan perbandingan case-insensitive (ILIKE) untuk pencarian string.

{history}
Skema Tabel Terpilih:
{schema}

Aturan:
1. PERHATIKAN DENGAN SEKSAMA riwayat percakapan terdekat tepat di atas. Jika pertanyaan merujuk pada konteks sebelumnya (misal 'bagaimana dengan tahun 2023?' atau 'siapa nomor 1 nya?'), gunakan tabel, filter, dan klausa dari obrolan tepat sebelumnya!
2. Hanya gunakan tabel & kolom dari skema di atas.
3. Kembalikan HANYA sintaks SQL murni tanpa backticks dan tanpa penjelasan."""


from .pipeline_logger import log_step, log_error

def sql_gen_node(state: AgentState) -> dict:
    """
    Node Single-Pass untuk memanggil LLM merakit SQL dengan pemahaman konteks Multi-Turn Terdekat & Multi-Provider Fallback.
    """
    user_query = state.get("user_query", "")
    relevant_tables = state.get("relevant_tables")
    chat_history = state.get("chat_history", [])
    
    log_step("STEP 2: SQL_GEN", f"Merakit SQL via LLM (Fail-Fast Single Pass)", f"Tabel: {relevant_tables}")

    history_str = ""
    if chat_history and len(chat_history) > 0:
        # 💡 HEMAT TOKEN: Ambil maksimal 3 percakapan terakhir & hanya sertakan SQL (tanpa narasi panjang)
        recent_history = chat_history[-6:]
        history_lines = []
        for h in recent_history:
            role = h.get("role", "")
            if role == "user":
                history_lines.append(f"- User: {h.get('content', '')}")
            elif role == "assistant" and h.get("sql"):
                history_lines.append(f"- AI SQL: {h.get('sql')}")
        if history_lines:
            history_str = "Konteks Obrolan Terdekat:\n" + "\n".join(history_lines) + "\n\n"
    
    schema = get_duckdb_schema(relevant_tables)
    user_message = f"Pertanyaan: {user_query}"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", SQL_SYSTEM_PROMPT),
        ("human", user_message)
    ])
    
    try:
        response = invoke_chain_with_fallback(
            chain_prompt=prompt,
            prompt_inputs={
                "history": history_str,
                "schema": schema
            },
            agent_name="sql_gen"
        )
        
        raw_sql = response.content if hasattr(response, "content") else str(response)
        if isinstance(raw_sql, list):
            raw_sql = raw_sql[0] if isinstance(raw_sql[0], str) else raw_sql[0].get("text", "")
            
        cleaned_sql = str(raw_sql).replace("```sql", "").replace("```", "").strip()
        
        log_step("STEP 2: SQL_GEN_DONE", f"SQL Berhasil Dirakit: {cleaned_sql}")
        return {"generated_sql": cleaned_sql, "correction_attempts": 0}
    except Exception as e:
        log_error("STEP 2: SQL_GEN_FAIL", e)
        raise e
