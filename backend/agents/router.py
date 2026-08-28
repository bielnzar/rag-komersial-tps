import os
import re
from pathlib import Path
import duckdb
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))

def get_table_catalog() -> str:
    """
    Mengambil daftar tabel beserta ringkasan kolomnya dari DuckDB.
    Format ringkas: hanya nama tabel + daftar kolom (tanpa tipe data)
    agar hemat token untuk prompt Router.
    """
    try:
        conn = duckdb.connect(DB_PATH, read_only=True)
        query = """
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema='main' 
            ORDER BY table_name, ordinal_position;
        """
        df = conn.execute(query).df()
        conn.close()
        
        catalog = "Daftar Tabel di Database:\n"
        current_table = ""
        for _, row in df.iterrows():
            if row['table_name'] != current_table:
                current_table = row['table_name']
                catalog += f"\n- {current_table}: "
                cols = df[df['table_name'] == current_table]['column_name'].tolist()
                catalog += ", ".join(cols)
        return catalog
    except Exception as e:
        logger.error(f"❌ Gagal membaca katalog tabel: {e}")
        return f"Gagal membaca katalog: {str(e)}"


# Prompt khusus Router Agent — sangat ringkas agar cepat dan hemat token
ROUTER_SYSTEM_PROMPT = """Anda adalah Router Agent untuk database komersial PT TPS (Terminal Petikemas Surabaya).

Tugas Anda: Tentukan tabel database mana yang PALING RELEVAN untuk menjawab pertanyaan pengguna.

--- GLOSARIUM SINGKAT ---
- fakta_vessel: data operasional kapal (LOP/operator, TEUS, boxes, BCH, BSH) per bulan, domestik & internasional.
- fakta_throughput: KPI capaian container (actual vs budget) per bulan, domestik & internasional.
- fakta_market_share: pangsa pasar per operator kapal (LOP, TEUS, persentase), multi-tahun, multi-sheet.

{catalog}

ATURAN:
1. Kembalikan HANYA nama tabel yang relevan, dipisahkan koma.
2. Jika ragu, sertakan SEMUA tabel yang mungkin terkait.
3. Jangan tambahkan penjelasan apapun, hanya nama tabel."""


def router_node(state: AgentState) -> dict:
    """
    Node Router (Agen 1): Menganalisis pertanyaan user dan memilih 
    tabel DuckDB yang relevan. Hasilnya disimpan ke state['relevant_tables']
    agar sql_gen hanya melihat skema tabel terpilih (hemat token).
    """
    user_query = state["user_query"]
    
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ROUTER_SYSTEM_PROMPT),
        ("human", "Pertanyaan Pengguna: {question}")
    ])
    
    catalog = get_table_catalog()
    
    chain = prompt | llm
    response = chain.invoke({
        "catalog": catalog,
        "question": user_query
    })
    
    # Parse response: ambil nama tabel dari output LLM
    raw_content = response.content
    if isinstance(raw_content, list):
        raw_content = raw_content[0] if isinstance(raw_content[0], str) else raw_content[0].get("text", "")
    
    raw_text = str(raw_content).strip()
    
    # Bersihkan dan split berdasarkan koma
    # Hapus spasi, backtick, dan newline
    cleaned = raw_text.replace("`", "").replace("\n", ",")
    table_names = [t.strip() for t in cleaned.split(",") if t.strip()]
    
    # Validasi: pastikan nama tabel benar-benar ada di DuckDB
    try:
        conn = duckdb.connect(DB_PATH, read_only=True)
        existing_tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        conn.close()
        valid_tables = {t[0] for t in existing_tables}
        
        # Filter hanya tabel yang valid
        filtered = [t for t in table_names if t in valid_tables]
        
        if not filtered:
            # Jika tidak ada yang valid, kembalikan semua tabel (fallback aman)
            logger.warning(f"⚠️ Router tidak menemukan tabel valid dari output LLM: '{raw_text}'. Menggunakan semua tabel sebagai fallback.")
            filtered = list(valid_tables)
        
        logger.info(f"🔀 Router memilih tabel: {filtered}")
        return {"relevant_tables": filtered}
        
    except Exception as e:
        logger.error(f"❌ Router gagal validasi tabel: {e}. Menggunakan semua tabel.")
        return {"relevant_tables": None}  # None = sql_gen akan pakai semua skema
