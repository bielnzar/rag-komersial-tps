import os
from pathlib import Path
import duckdb
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))

def get_duckdb_schema(relevant_tables: list[str] | None = None) -> str:
    """Mengambil skema tabel dan kolom secara dinamis dari DuckDB."""
    try:
        conn = duckdb.connect(DB_PATH, read_only=True)
        query = """
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema='main' 
            ORDER BY table_name, ordinal_position;
        """
        df_schema = conn.execute(query).df()
        conn.close()
        
        # Filter hanya tabel yang relevan jika tersedia
        if relevant_tables:
            df_schema = df_schema[df_schema['table_name'].isin(relevant_tables)]
            
        schema_str = "Katalog Tabel Database DuckDB:\n"
        current_table = ""
        for _, row in df_schema.iterrows():
            if row['table_name'] != current_table:
                current_table = row['table_name']
                schema_str += f"\nTable: {current_table}\n"
            schema_str += f" - {row['column_name']} ({row['data_type']})\n"
        return schema_str
    except Exception as e:
        return f"Gagal mengambil schema: {str(e)}"

# Prompt system khusus untuk DuckDB SQL
SQL_SYSTEM_PROMPT = """
Anda adalah AI Data Engineer ahli dari PT TPS (Terminal Petikemas Surabaya).
Tugas Anda adalah merakit query DuckDB SQL murni berdasarkan pertanyaan pengguna.

--- GLOSARIUM BISNIS & SEMANTIK ---
- "Jalur Domestik" atau "Domestik": selalu tertulis sebagai 'DOMESTIC' atau 'DOM' di database.
- "Jalur Internasional" atau "Internasional": selalu tertulis sebagai 'INTERNATIONAL' atau 'INT' di database.
- Kolom "Unit" pada tabel throughput biasanya berisi 'TEUs'. Kata 'BOXES' tidak ada di dalam kolom unit tersebut.
- Selalu gunakan perbandingan yang case-insensitive (ILIKE) saat memfilter string.

Aturan Ketat:
1. Hanya gunakan tabel dan kolom yang ada pada skema berikut:
{schema}
2. Kembalikan HANYA syntax SQL murni, tanpa backticks (```sql ... ```) dan tanpa penjelasan apapun.
3. Wajib menggunakan dialek DuckDB.
"""

def sql_gen_node(state: AgentState) -> dict:
    """
    Node untuk memanggil LLM merakit SQL.
    """
    user_query = state["user_query"]
    
    # Inisialisasi LLM Gemini (Pastikan GEMINI_API_KEY ada di .env)
    # Menggunakan gemini-3.6-flash karena perakitan SQL membutuhkan penalaran tingkat tinggi (Code Generation)
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SQL_SYSTEM_PROMPT),
        ("human", "Pertanyaan Pengguna: {question}\n\n[INFO SELF-HEALING]\nPesan Error/Feedback dari eksekusi sebelumnya (jika ada, tolong perbaiki SQL Anda): {error}")
    ])
    
    relevant_tables = state.get("relevant_tables")
    schema = get_duckdb_schema(relevant_tables)
    sql_error = state.get("sql_error") or "Tidak ada error sebelumnya."
    
    chain = prompt | llm
    response = chain.invoke({
        "schema": schema,
        "question": user_query,
        "error": sql_error
    })
    
    # Tangani jika Gemini mengembalikan content berupa list
    raw_content = response.content
    if isinstance(raw_content, list):
        # Ambil elemen pertama, misal [{'text': 'SELECT ...'}]
        raw_content = raw_content[0] if isinstance(raw_content[0], str) else raw_content[0].get("text", "")
        
    generated_sql = str(raw_content).strip()
    
    # Bersihkan markdown formatting jika LLM nakal
    if generated_sql.startswith("```sql"):
        generated_sql = generated_sql[6:]
    if generated_sql.startswith("```"):
        generated_sql = generated_sql[3:]
    if generated_sql.endswith("```"):
        generated_sql = generated_sql[:-3]
        
    return {"generated_sql": generated_sql.strip()}
