import os
import re
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
from .llm_helper import invoke_chain_with_fallback
from .pipeline_logger import log_step, log_error
import logging

try:
    from db import get_db
    from cache import semantic_cache
except ImportError:
    from ..db import get_db
    from ..cache import semantic_cache

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))

def get_table_catalog() -> str:
    """
    Mengambil daftar tabel beserta ringkasan kolom dan deskripsi semantik.
    """
    cached_catalog = semantic_cache.get_schema_cache("catalog")
    if cached_catalog:
        return cached_catalog

    table_descriptions = {
        "fakta_throughput": "Throughput bulanan/tahunan (actual, budget, variansi, capaian) untuk kategori International / Domestic.",
        "fakta_komersial_dashboard": "Pendapatan/revenue, total box, dan total TEUs per pelanggan/operator (LOP) dan per bulan/tahun.",
        "fakta_market_share": "Pangsa pasar (market share), persentase, dan volume TEUs per operator kapal (LOP).",
        "fakta_realisasi_uc": "Data kegiatan Uncontainerized (UC), kargo non-kontainer, revenue dan volume per activity (Export/Import).",
        "fakta_rest_n_disc": "Permohonan restitusi, diskon, dan keringanan biaya pelanggan (nama perusahaan, status, nominal disetujui).",
        "fakta_vessel": "Data operasional kapal, BCH, BSH, box, dan TEUs per operator.",
        "fakta_vessel_service": "Rute pelayaran, service mode, total call kapal, BMPH, GMPH per operator pelayaran.",
        "fakta_transhipment": "Aktivitas transhipment kontainer (20ft, 40ft, 45ft), vessel revenue, yard revenue.",
        "fakta_overview_box": "Ringkasan jumlah box dan TEUs per kategori layanan."
    }

    try:
        conn = get_db()
        query = """
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema='main' 
            ORDER BY table_name, ordinal_position;
        """
        df = conn.execute(query).df()
        
        catalog = "Daftar Tabel, Deskripsi & Kolom:\n"
        current_table = ""
        for _, row in df.iterrows():
            tbl = row['table_name']
            if tbl != current_table:
                current_table = tbl
                desc = table_descriptions.get(tbl, "")
                catalog += f"\n- {current_table} (Deskripsi: {desc})\n  Kolom: "
            else:
                catalog += f"{row['column_name']}, "
                
        catalog = catalog.strip()
        semantic_cache.set_schema_cache("catalog", catalog)
        return catalog
    except Exception as e:
        logger.error(f"Gagal membaca catalog DuckDB: {e}")
        return "Daftar Tabel: fakta_throughput, fakta_komersial_dashboard, fakta_market_share, fakta_realisasi_uc, fakta_rest_n_disc, fakta_vessel, fakta_vessel_service, fakta_transhipment, fakta_overview_box"

def get_valid_tables() -> set:
    try:
        conn = get_db()
        df = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main';").df()
        return set(df['table_name'].tolist())
    except Exception:
        return {"data_komersial", "trend_komersial", "target_komersial", "capaian_komersial", "market_share", "dw_komersial"}

ROUTER_SYSTEM_PROMPT = """Anda adalah Routing Agent database PT TPS.
Tugas Anda: Memilih nama tabel DuckDB yang RELEVAN untuk menjawab pertanyaan pengguna.

Katalog Tabel Tersedia:
{catalog}

Riwayat Obrolan Terdekat:
{history}

ATURAN PENTING:
1. KONTEKS PERTANYAAN LANJUTAN: Jika pertanyaan pengguna singkat atau merujuk pada obrolan sebelumnya (contoh: "sekarang coba yang 2027", "bagaimana dengan 2023?", "siapa nomor 1 nya?"), WAJIB LIHAT RIWAYAT OBROLAN dan PILIH TABEL YANG SAMA dengan pertanyaan sebelumnya!
2. Kembalikan HANYA nama tabel relevan dipisahkan koma. Contoh: fakta_throughput, fakta_overview_box
3. DILARANG mengembalikan seluruh tabel kecuali pengguna meminta overview seluruh database."""

def router_node(state: AgentState) -> dict:
    user_query = state.get("user_query", "")
    chat_history = state.get("chat_history", [])
    user_role = state.get("role", "guest")
    
    log_step("STEP 1: ROUTER", f"Evaluasi konteks & hak akses tabel RBAC untuk Role: '{user_role}'", f"Query: '{user_query}'")

    history_context = ""
    if chat_history:
        # 💡 HEMAT TOKEN: Ambil 3 percakapan terakhir (max 6 pesan)
        recent = chat_history[-6:]
        turns = []
        for m in recent:
            if m.get("role") == "user":
                turns.append(f"User: {m.get('content', '')}")
            elif m.get("role") == "assistant" and m.get("sql"):
                turns.append(f"AI SQL: {m.get('sql')}")
        if turns:
            history_context = "\n".join(turns)

    prompt = ChatPromptTemplate.from_messages([
        ("system", ROUTER_SYSTEM_PROMPT),
        ("human", "Pertanyaan: {question}")
    ])
    
    catalog = get_table_catalog()
    
    try:
        response = invoke_chain_with_fallback(
            chain_prompt=prompt,
            prompt_inputs={
                "catalog": catalog,
                "history": history_context,
                "question": user_query
            },
            agent_name="router"
        )
        
        raw_content = response.content if hasattr(response, "content") else str(response)
        if isinstance(raw_content, list):
            raw_content = raw_content[0] if isinstance(raw_content[0], str) else raw_content[0].get("text", "")
        
        raw_text = str(raw_content).strip()
        cleaned = raw_text.replace("`", "").replace("\n", ",")
        table_names = [t.strip() for t in cleaned.split(",") if t.strip()]
        
        valid_set = get_valid_tables()
        filtered_tables = [t for t in table_names if t in valid_set] if valid_set else table_names
        
        allowed_tables = semantic_cache.get_role_permissions(user_role)
        rbac_filtered_tables = [t for t in filtered_tables if t in allowed_tables]
        
        # Smart Fallback: Jangan memilih SELURUH tabel database jika AI ragu!
        if not rbac_filtered_tables:
            default_smart_tables = ["fakta_throughput", "data_komersial", "trend_komersial"]
            rbac_filtered_tables = [t for t in default_smart_tables if t in allowed_tables]
            if not rbac_filtered_tables:
                rbac_filtered_tables = list(allowed_tables)[:2]
            
        log_step("STEP 1: ROUTER_DONE", f"Tabel terpilih pasca RBAC Filter: {rbac_filtered_tables}")
        return {"relevant_tables": rbac_filtered_tables}
    except Exception as e:
        log_error("STEP 1: ROUTER_FAIL", e)
        raise e
