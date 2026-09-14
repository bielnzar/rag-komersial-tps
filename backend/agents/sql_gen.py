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

import re

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))

CORE_DIMENSION_COLS = {
    'year', 'tahun', 'tahun_kategori', 'month', 'bulan', 'date', 'tanggal',
    'lop', 'kategori_layanan', 'kategori', 'sumber_sheet', 'category'
}

CORE_METRIC_COLS = {
    'teus', 'total_teus', 'box', 'boxes', 'total_box',
    'total_revenue', 'total_all_revenue'
}

SEMANTIC_KEYWORD_MAP = {
    'persen': ['persen', 'share'],
    'share': ['persen', 'share'],
    'pasar': ['share', 'market'],
    'market': ['share', 'market'],
    'pendapatan': ['revenue', 'pendapatan'],
    'revenue': ['revenue', 'pendapatan'],
    'rkap': ['budget', 'target'],
    'anggaran': ['budget', 'target'],
    'budget': ['budget', 'target'],
    'realisasi': ['actual', 'realisasi'],
    'actual': ['actual', 'realisasi'],
    'kapal': ['vessel', 'call', 'bmph', 'gmph'],
    'call': ['call', 'kunjungan'],
    'bmph': ['bmph'],
    'gmph': ['gmph'],
    'bch': ['bch'],
    'bsh': ['bsh'],
    'diskon': ['discount', 'diskon', 'keringanan'],
    'restitusi': ['restitusi', 'keringanan'],
    'rute': ['route', 'service'],
    'service': ['service', 'route'],
    'yard': ['yard'],
    'transhipment': ['transhipment', 'ts', 'trans']
}

def prune_columns(table_name: str, columns: list[str], user_query: str) -> list[str]:
    """
    Column-Level Schema Pruning (TUGAS 3.2):
    Memangkas kolom untuk tabel lebar (> 20 kolom) seperti fakta_market_share (54 kolom)
    sehingga hanya mempertahankan kolom esensial (dimensi & waktu) serta kolom data
    yang relevan dengan kata kunci pertanyaan pengguna.
    Menghemat ~300-500 token prompt SQL generator.
    """
    if len(columns) <= 20 or not user_query:
        return columns
    
    q_lower = user_query.lower()
    selected = set()
    
    # 1. Kolom esensial wajib ada (dimensi waktu, operator, segmentasi, metrik utama)
    for c in columns:
        cl = c.lower()
        if cl in CORE_DIMENSION_COLS or cl in CORE_METRIC_COLS:
            selected.add(c)
            
    # 2. Ekstrak tahun dari kueri (cth: 2021, 2022, 2023, 2024, 2025, 2026)
    years = re.findall(r'\b(202[0-9])\b', q_lower)
    
    # 3. Ekstrak kata kunci dari kueri pengguna
    keywords = re.findall(r'\b[a-z0-9_]{3,}\b', q_lower)
    
    search_terms = set(keywords)
    for kw in keywords:
        if kw in SEMANTIC_KEYWORD_MAP:
            search_terms.update(SEMANTIC_KEYWORD_MAP[kw])
            
    for c in columns:
        c_lower = c.lower()
        # Cocokkan tahun jika kueri mengandung tahun spesifik
        for y in years:
            if y in c_lower:
                selected.add(c)
                break
        # Cocokkan kata kunci semantik
        for term in search_terms:
            if term in c_lower:
                selected.add(c)
                break
                
    # Jika kueri menyebutkan tahun tertentu, pangkas kolom tahun lain
    if years:
        filtered = set()
        for c in selected:
            c_lower = c.lower()
            has_other_year = False
            for y_other in ['2021', '2022', '2023', '2024', '2025', '2026']:
                if y_other not in years and y_other in c_lower:
                    has_other_year = True
                    break
            if not has_other_year:
                filtered.add(c)
        selected = filtered

    # Pertahankan urutan asli tabel
    pruned = [c for c in columns if c in selected]
    
    # Safety guard: Jika hasil pruning terlalu sedikit (< 5 kolom), kembalikan kolom asli
    if len(pruned) < 5:
        return columns
        
    return pruned

def get_duckdb_schema(relevant_tables: list[str] | None = None, user_query: str = "") -> str:
    """
    Mengambil skema tabel dan kolom secara dinamis dari DuckDB via Shared Schema Cache,
    dengan Column-Level Schema Pruning otomatis jika tabel memiliki > 20 kolom.
    """
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
        for tbl_name, group in df_schema.groupby('table_name', sort=False):
            col_names = group['column_name'].tolist()
            data_types = dict(zip(group['column_name'], group['data_type']))
            
            # Terapkan column pruning jika tabel lebar (> 20 kolom)
            if len(col_names) > 20 and user_query:
                selected_cols = prune_columns(tbl_name, col_names, user_query)
            else:
                selected_cols = col_names
                
            schema_str += f"\nTable {tbl_name}:\n"
            for col in selected_cols:
                schema_str += f"- {col} ({data_types.get(col, 'VARCHAR')})\n"
                
        return schema_str
    except Exception as e:
        return f"Gagal mengambil schema: {str(e)}"

FEW_SHOT_EXAMPLES = {
    "fakta_throughput": """-- Contoh Kueri fakta_throughput:
-- User: "Berapa total throughput internasional tahun 2024?"
SELECT SUM(actual) AS total_throughput_teus FROM fakta_throughput WHERE year = 2024 AND kategori_layanan ILIKE '%international%';""",

    "fakta_komersial_dashboard": """-- Contoh Kueri fakta_komersial_dashboard:
-- User: "Berapa total pendapatan komersial tahun 2023?"
SELECT SUM(COALESCE(total_all_revenue, total_revenue)) AS total_pendapatan FROM fakta_komersial_dashboard WHERE tahun = 2023;

-- User: "Siapa 5 operator dengan revenue terbesar tahun 2024?"
SELECT lop, SUM(COALESCE(total_all_revenue, total_revenue)) AS total_revenue FROM fakta_komersial_dashboard WHERE tahun = 2024 GROUP BY lop ORDER BY total_revenue DESC LIMIT 5;""",

    "fakta_market_share": """-- Contoh Kueri fakta_market_share:
-- User: "Siapa 3 operator dengan volume market share terbesar tahun 2023?"
SELECT lop, SUM(total_teus) AS total_volume_teus FROM fakta_market_share WHERE tahun_kategori = '2023' GROUP BY lop ORDER BY total_volume_teus DESC LIMIT 3;""",

    "fakta_vessel": """-- Contoh Kueri fakta_vessel:
-- User: "Berapa total box dan TEUs kapal internasional tahun 2024?"
SELECT SUM(boxes) AS total_boxes, SUM(teus) AS total_teus FROM fakta_vessel WHERE year = 2024 AND kategori_layanan ILIKE '%international%';""",

    "fakta_vessel_service": """-- Contoh Kueri fakta_vessel_service:
-- User: "Tampilkan rute dan total call kapal per operator tahun 2024"
SELECT lop, routes, SUM(total_call) AS total_calls FROM fakta_vessel_service WHERE year = 2024 GROUP BY lop, routes ORDER BY total_calls DESC LIMIT 5;
-- User: "Siapa operator dengan rata-rata BMPH tertinggi tahun 2024?"
-- CATATAN PENTING: Gunakan kolom numerik 'average_bmph' (DOUBLE), JANGAN kolom 'bmph' (VARCHAR).
SELECT lop, AVG(average_bmph) AS avg_bmph FROM fakta_vessel_service WHERE year = 2024 AND average_bmph IS NOT NULL GROUP BY lop ORDER BY avg_bmph DESC LIMIT 5;""",

    "fakta_transhipment": """-- Contoh Kueri fakta_transhipment:
-- User: "Berapa total revenue transhipment per operator tahun 2024?"
SELECT lop, SUM(vessel_revenue) AS total_vessel_rev, SUM(yard_revenue) AS total_yard_rev FROM fakta_transhipment WHERE year = 2024 GROUP BY lop ORDER BY total_vessel_rev DESC LIMIT 5;""",

    "fakta_realisasi_uc": """-- Contoh Kueri fakta_realisasi_uc:
-- User: "Berapa total kegiatan uncontainerized (UC) tahun 2024?"
SELECT activity, SUM(total_box) AS total_boxes, SUM(total_teus) AS total_teus FROM fakta_realisasi_uc WHERE tahun = 2024 GROUP BY activity;""",

    "fakta_overview_box": """-- Contoh Kueri fakta_overview_box:
-- User: "Berapa perbandingan TEUs domestik dan internasional tahun 2024?"
SELECT kategori_layanan, SUM(teus) AS total_teus, SUM(boxes) AS total_boxes FROM fakta_overview_box WHERE year = 2024 GROUP BY kategori_layanan;""",

    "fakta_rest_n_disc": """-- Contoh Kueri fakta_rest_n_disc:
-- User: "Tampilkan permohonan diskon dan keringanan biaya pelanggan"
SELECT nama_perusahaan, aktivitas, status, nominal_persetujuan_keringanan FROM fakta_rest_n_disc;""",

    "dim_vessel_operator": """-- Contoh Kueri dim_vessel_operator:
-- User: "Operator vessel apa saja yang pernah sandar di TPS?"
-- User: "Tampilkan daftar nama operator kapal / pelayaran yang ada di TPS"
SELECT code, full_name FROM dim_vessel_operator ORDER BY full_name ASC;"""
}

def get_few_shot_examples(relevant_tables: list[str] | None = None) -> str:
    """Mengambil contoh kueri hanya untuk tabel yang dipilih oleh Router (Dynamic Selective Few-Shot)."""
    if not relevant_tables:
        return ""
    
    selected_examples = []
    for tbl in relevant_tables:
        if tbl in FEW_SHOT_EXAMPLES:
            selected_examples.append(FEW_SHOT_EXAMPLES[tbl].strip())
            
    if selected_examples:
        return "Contoh Kueri Referensi yang Benar:\n" + "\n\n".join(selected_examples) + "\n\n"
    return ""

SQL_SYSTEM_PROMPT = """Rakit query DuckDB SQL murni berdasarkan pertanyaan pengguna dan riwayat percakapan terdekat.

Glosarium & Semantik:
- Domestik -> 'DOMESTIC' / 'DOM'
- Internasional -> 'INTERNATIONAL' / 'INT'
- Tabel fakta_throughput: Seluruh baris adalah data volume peti kemas (TEUs). JANGAN filter kata 'peti kemas' / 'container'. Cukup filter tahun dan kategori_layanan (misal: kategori_layanan ILIKE '%international%').
- Kolom pendapatan utama di fakta_komersial_dashboard: HARUS gabungkan COALESCE(total_all_revenue, total_revenue) AS total_revenue karena data pendapatan terpisah di dua kolom tersebut.
- Daftar Operator Kapal / Pelayaran (Vessel Operator): Jika pengguna menanyakan "siapa saja operator kapal/vessel operator", "daftar pelayaran", atau nama-nama operator kapal yang pernah ada/sandar di TPS tanpa meminta angka finansial/volume, WAJIB kueri dari tabel master dimensi `dim_vessel_operator` (SELECT code, full_name FROM dim_vessel_operator ORDER BY full_name ASC). DILARANG menggunakan `SELECT DISTINCT lop FROM fakta_komersial_dashboard` karena tabel fakta komersial memuat duplikasi kode dan nama panjang!
- Gunakan perbandingan case-insensitive (ILIKE) untuk pencarian string.

{few_shot}{history}Skema Tabel Terpilih:
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
    
    few_shot_str = get_few_shot_examples(relevant_tables)
    schema = get_duckdb_schema(relevant_tables, user_query=user_query)
    user_message = f"Pertanyaan: {user_query}"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", SQL_SYSTEM_PROMPT),
        ("human", user_message)
    ])
    
    try:
        response = invoke_chain_with_fallback(
            chain_prompt=prompt,
            prompt_inputs={
                "few_shot": few_shot_str,
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
