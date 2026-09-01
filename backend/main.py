from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# Load env variables
load_dotenv()

# Import graph agent, chart_gen, shared DuckDB pool, semantic cache & auth
from agents.graph import build_graph
from agents.chart_gen import generate_chart_config
from db import get_db, DuckDBPool, get_telemetry_db
from cache import semantic_cache
from auth import authenticate_user, get_current_user_from_header, verify_jwt_token
from agents.pipeline_logger import log_step, log_error

app = FastAPI(
    title="TPS Enterprise AI Data Agent",
    description="API untuk asisten AI komersial PT TPS dengan Otentikasi Terenkripsi & Persistent Chat History",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_app = build_graph()

# =============================================================
# PYDANTIC SCHEMAS
# =============================================================
class LoginRequest(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    username: str
    role: str
    name: str

class LoginResponse(BaseModel):
    status: str
    access_token: str
    token_type: str
    user: UserProfile

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    generate_chart: bool = False

class ChatResponse(BaseModel):
    status: str
    answer: str
    session_id: str
    chart_config: dict | None = None
    sql_executed: str | None = None
    error: str | None = None
    data: list | None = None

class VisualizeRequest(BaseModel):
    query: str
    data: list

class VisualizeResponse(BaseModel):
    status: str
    chart_config: dict | None = None
    error: str | None = None


# =============================================================
# AUTHENTICATION ENDPOINTS
# =============================================================
@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login_endpoint(request: LoginRequest):
    """Endpoint Otentikasi Login Aman (PBKDF2 Hashing & JWT Signing)."""
    if not request.username.strip() or not request.password.strip():
        raise HTTPException(status_code=400, detail="Username dan Password tidak boleh kosong.")

    result = authenticate_user(request.username, request.password)
    return LoginResponse(
        status="success",
        access_token=result["access_token"],
        token_type=result["token_type"],
        user=UserProfile(**result["user"])
    )

@app.get("/api/v1/auth/me", response_model=UserProfile)
async def get_me_endpoint(authorization: Optional[str] = Header(None)):
    """Verifikasi token aktif dan mengembalikan profil pengguna."""
    user = await get_current_user_from_header(authorization)
    return UserProfile(
        username=user["sub"],
        role=user["role"],
        name=user["name"]
    )


# =============================================================
# CHAT SESSIONS & HISTORY ENDPOINTS (Seperti ChatGPT / Claude UI)
# =============================================================
@app.get("/api/v1/sessions")
async def get_sessions_endpoint(authorization: Optional[str] = Header(None)):
    """Mengambil daftar seluruh thread percakapan milik pengguna aktif (terpisah per role)."""
    verified_user = await get_current_user_from_header(authorization)
    sessions = semantic_cache.get_user_sessions(verified_user["sub"])
    return {"status": "success", "sessions": sessions}

@app.get("/api/v1/sessions/{session_id}")
async def get_session_messages_endpoint(session_id: str, authorization: Optional[str] = Header(None)):
    """Mengambil riwayat pesan lengkap dari satu sesi obrolan."""
    verified_user = await get_current_user_from_header(authorization)
    messages = semantic_cache.get_session_messages(verified_user["sub"], session_id)
    return {"status": "success", "session_id": session_id, "messages": messages}

@app.delete("/api/v1/sessions/{session_id}")
async def delete_session_endpoint(session_id: str, authorization: Optional[str] = Header(None)):
    """Menghapus satu thread percakapan milik pengguna."""
    verified_user = await get_current_user_from_header(authorization)
    success = semantic_cache.delete_user_session(verified_user["sub"], session_id)
    return {"status": "success" if success else "error"}


VALID_METRIC_KEYWORDS = [
    # Volume & Throughput
    "throughput", "arus", "petikemas", "peti kemas", "teus", "teu", "box", "boxes", "volume", "kapasitas", "bongkar", "muat",
    # Finansial & Revenue
    "revenue", "pendapatan", "omset", "omzet", "biaya", "uang", "rupiah", "dolar", "tarif", "tagihan", "mooring", "dpp", "diskon", "keringanan", "restitusi", "budget", "actual", "anggaran", "realisasi", "capaian", "target", "persen", "persentase", "pertumbuhan", "kenaikan", "penurunan",
    # Operasional Kapal & Services
    "vessel", "kapal", "service", "layanan", "rute", "routes", "call", "kunjungan", "berthing", "bmph", "gmph", "bch", "bsh", "moves", "waktu",
    # Pangsa Pasar / Market Share
    "market share", "pangsa pasar", "market", "share",
    # Pelanggan / Operator (LOP)
    "pelanggan", "customer", "operator", "lop", "perusahaan", "cma", "ssl", "msk", "msc", "emc", "one", "cos", "evergreen", "mell", "benline", "rcl", "oocl", "samudera", "meratus", "spil", "habco", "maersk",
    # Kargo Khusus & Segmentasi
    "uncontainerized", "uc", "transhipment", "export", "import", "ekspor", "impor", "domestik", "internasional", "domestic", "international",
    # Skema & Overview
    "tabel", "skema", "daftar", "list", "kolom", "overview", "ringkasan", "database", "data apa"
]

def check_query_specificity(query: str) -> tuple[bool, Optional[str]]:
    """
    Validasi pre-flight untuk mendeteksi apakah pertanyaan memiliki metrik/atribut bisnis yang spesifik.
    Jika ambigu (misal: 'berapa total tahun 2025' atau 'kalau 2024'), langsung ditolak dengan panduan (0 LLM Token).
    """
    q_clean = query.lower().strip()
    has_metric = any(kw in q_clean for kw in VALID_METRIC_KEYWORDS)
    
    if not has_metric:
        guidance = (
            "⚠️ **Pertanyaan Kurang Spesifik**\n\n"
            "Pertanyaan Anda belum menyebutkan metrik atau atribut data yang ingin dicari (misalnya: *throughput*, *revenue*, *volume TEUs/box*, *market share*, atau *operasional kapal*).\n\n"
            "**Contoh Pertanyaan yang Spesifik & Benar:**\n"
            "- 📊 *\"Berapa total **throughput** tahun 2025?\"*\n"
            "- 💰 *\"Berapa total **revenue** / pendapatan di tahun 2025?\"*\n"
            "- 🚢 *\"Berapa volume **market share** operator di tahun 2025?\"*\n"
            "- 📦 *\"Berapa total **box** kegiatan uncontainerized (UC) tahun 2025?\"*"
        )
        return False, guidance
        
    return True, None

# =============================================================
# PROTECTED CHAT & VISUALIZE ENDPOINTS
# =============================================================
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, authorization: Optional[str] = Header(None)):
    """
    Endpoint utama percakapan diproteksi JWT Authentication, Pre-Flight Specificity Guard & Fail-Fast LangGraph.
    """
    verified_user = await get_current_user_from_header(authorization)
    user_id = verified_user["sub"]
    user_role = verified_user["role"]

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query tidak boleh kosong.")

    session_id = request.session_id if request.session_id else f"sess_{user_id}_{int(os.times().elapsed * 1000)}"

    try:
        log_step("CHAT_REQUEST", f"User: '{user_id}' ({user_role}) | Session: {session_id}", f"Query: '{request.query}'")

        # 🛡️ 1. CEK API RATE LIMITING (Maks 30 request per menit per user_id)
        is_allowed, count = semantic_cache.check_rate_limit(user_id, max_requests=30, window_seconds=60)
        if not is_allowed:
            log_step("RATE_LIMIT", f"User {user_id} terblokir rate limit ({count}/30)")
            raise HTTPException(
                status_code=429, 
                detail=f"Batasan kuota request terlampaui ({count}/30 request per menit). Harap tunggu beberapa detik."
            )

        # 🔍 2. VALIDASI PRE-FLIGHT KESPESIFIKAN PERTANYAAN (0 Token LLM / Anti-Ambigu)
        is_specific, guidance_msg = check_query_specificity(request.query)
        if not is_specific:
            log_step("QUERY_AMBIGUOUS", f"Query ditolak karena kurang spesifik: '{request.query}'")
            semantic_cache.save_chat_message_to_session(
                username=user_id,
                role=user_role,
                session_id=session_id,
                user_query=request.query,
                ai_answer=guidance_msg,
                sql=None,
                data=None,
                chart_config=None
            )
            return ChatResponse(
                status="success",
                answer=guidance_msg,
                session_id=session_id,
                chart_config=None,
                sql_executed=None,
                error=None,
                data=None
            )

        # 💬 3. AMBIL RIWAYAT PERCAKAPAN CONTEXT MEMORY
        session_history = semantic_cache.get_session_messages(user_id, session_id)

        # ⚡ 4. CEK SEMANTIC CACHE (Dengan Deteksi Pertanyaan Lanjutan)
        is_followup = len(session_history) > 0 and (
            len(request.query.split()) <= 6 or 
            any(kw in request.query.lower() for kw in ["bagaimana", "bagaimana dengan", "siapa", "tahun", "tersebut", "itu", "yang", "berapa"])
        )

        if not request.generate_chart and not is_followup:
            cached_res = semantic_cache.get(request.query)
            if cached_res:
                log_step("CACHE_HIT", f"Respon diambil langsung dari Semantic Cache", f"Query: '{request.query}'")
                cached_res["session_id"] = session_id
                
                semantic_cache.save_chat_message_to_session(
                    username=user_id,
                    role=user_role,
                    session_id=session_id,
                    user_query=request.query,
                    ai_answer=cached_res.get("answer", ""),
                    sql=cached_res.get("sql_executed"),
                    data=cached_res.get("data"),
                    chart_config=cached_res.get("chart_config")
                )
                return ChatResponse(**cached_res)

        # 4. CACHE MISS / CONTEXTUAL FOLLOW-UP — Menjalankan LangGraph
        log_step("PIPELINE_START", "Memulai eksekusi alur Multi-Agent LangGraph", f"FollowUp: {is_followup}")
        initial_state = {
            "user_query": request.query,
            "relevant_tables": None,
            "generated_sql": None,
            "sql_error": None,
            "correction_attempts": 0,
            "query_result": None,
            "final_answer": None,
            "echarts_config": None,
            "force_chart": request.generate_chart,
            "chat_history": session_history[-6:] if session_history else [],
            "role": user_role
        }
        
        result_state = agent_app.invoke(initial_state)
        
        final_answer = result_state.get("final_answer")
        if not final_answer or not str(final_answer).strip():
            final_answer = "Berikut adalah rincian data mentah yang berhasil diperoleh dari database DuckDB:"
        sql_exec = result_state.get("generated_sql")
        q_result = result_state.get("query_result")
        c_config = result_state.get("echarts_config")
        has_error = result_state.get("sql_error")

        log_step("PIPELINE_END", f"Alur selesai. Status: {'SUCCESS' if not has_error else 'ERROR'}", f"Err: {has_error if has_error else 'None'}")

        resp_payload = {
            "status": "success" if not has_error else "error",
            "answer": final_answer,
            "session_id": session_id,
            "chart_config": c_config,
            "sql_executed": sql_exec,
            "error": has_error,
            "data": q_result
        }

        # 💾 5. SIMPAN KE PERSISTENT CHAT HISTORY & SEMANTIC CACHE
        if not has_error:
            semantic_cache.save_chat_message_to_session(
                username=user_id,
                role=user_role,
                session_id=session_id,
                user_query=request.query,
                ai_answer=final_answer,
                sql=sql_exec,
                data=q_result,
                chart_config=c_config
            )
            
            if q_result and not is_followup:
                semantic_cache.set(request.query, resp_payload)

        return ChatResponse(**resp_payload)
        
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e)
        log_error("CHAT_ENDPOINT_EXCEPTION", e, context=f"User: '{user_id}', Query: '{request.query}'")
        if "Akses AI Terhenti" in err_msg:
            return ChatResponse(
                status="error",
                answer=err_msg,
                session_id=session_id,
                chart_config=None,
                sql_executed=None,
                error=err_msg,
                data=None
            )
        raise HTTPException(status_code=500, detail=err_msg)

@app.post("/api/v1/visualize", response_model=VisualizeResponse)
async def visualize_endpoint(request: VisualizeRequest, authorization: Optional[str] = Header(None)):
    """Endpoint Lapisan 3 On-Demand diproteksi JWT."""
    await get_current_user_from_header(authorization)
    
    if not request.data:
        raise HTTPException(status_code=400, detail="Data tidak boleh kosong.")
        
    try:
        chart_config = generate_chart_config(request.query, request.data)
        
        return VisualizeResponse(
            status="success" if chart_config else "error",
            chart_config=chart_config if chart_config else None,
            error=None if chart_config else "Gagal merakit konfigurasi grafik dari data yang diberikan."
        )
    except Exception as e:
        return VisualizeResponse(
            status="error",
            error=str(e)
        )

@app.delete("/api/v1/cache")
async def clear_cache(authorization: Optional[str] = Header(None)):
    """Endpoint untuk membersihkan seluruh isi cache (Memerlukan Login)."""
    await get_current_user_from_header(authorization)
    semantic_cache.clear()
    return {"status": "success", "message": "Cache dan riwayat percakapan berhasil dibersihkan."}

# =============================================================
# ADMIN ENDPOINTS (API KEYS & TELEMETRY)
# =============================================================
from api_keys_manager import get_all_keys, save_all_keys, get_step_configs, save_step_configs, get_model_catalog

@app.get("/api/v1/admin/step_configs")
async def admin_get_step_configs(authorization: Optional[str] = Header(None)):
    """Mengambil konfigurasi lengkap per tahapan (Provider, Model, List Kunci per-Step) dan Katalog."""
    user = await get_current_user_from_header(authorization)
    if user["role"] not in ["executive", "admin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak.")
        
    configs = get_step_configs()
    all_keys = get_all_keys()
    
    # Mask keys inside step_configs
    masked_configs = {}
    for step_name, cfg in configs.items():
        step_dict = dict(cfg)
        masked_api_keys = []
        for k in step_dict.get("api_keys", []):
            safe_k = dict(k)
            if safe_k.get("key") and len(safe_k["key"]) > 10:
                safe_k["key"] = safe_k["key"][:8] + "..." + safe_k["key"][-4:]
            masked_api_keys.append(safe_k)
        step_dict["api_keys"] = masked_api_keys
        masked_configs[step_name] = step_dict
        
    # Mask registered pool keys
    masked_pool = {"google_gemini": [], "groq": []}
    for provider in ["google_gemini", "groq"]:
        for k in all_keys.get(provider, []):
            safe_k = dict(k)
            if safe_k.get("key") and len(safe_k["key"]) > 10:
                safe_k["key"] = safe_k["key"][:8] + "..." + safe_k["key"][-4:]
            masked_pool[provider].append(safe_k)
            
    return {
        "status": "success",
        "step_configs": masked_configs,
        "catalog": get_model_catalog(),
        "pool_keys": masked_pool
    }

def _unmask_key_value(input_key: str, existing_key_list: list, idx: int) -> str:
    """Helper untuk mengembalikan API Key asli jika di-submit dalam bentuk ter-mask (...)."""
    if not input_key or "..." not in input_key:
        return input_key
        
    parts = input_key.split("...")
    prefix = parts[0]
    suffix = parts[-1] if len(parts) > 1 else ""

    # 1. Prioritas Utama: Cocokkan index eksak jika prefix & suffix sama persis
    if idx < len(existing_key_list):
        cand = existing_key_list[idx].get("key", "")
        if cand.startswith(prefix) and (not suffix or cand.endswith(suffix)):
            return cand

    # 2. Prioritas Kedua: Cari di list yang cocok KEDUA-DUANYA (prefix DAN suffix)
    for ek in existing_key_list:
        cand = ek.get("key", "")
        if cand and cand.startswith(prefix) and (not suffix or cand.endswith(suffix)):
            return cand

    # 3. Prioritas Ketiga: Cocokkan suffix unik saja
    if suffix:
        for ek in existing_key_list:
            cand = ek.get("key", "")
            if cand and cand.endswith(suffix):
                return cand

    # 4. Prioritas Keempat: Jika index valid dan ada key, kembalikan key di index tersebut
    if idx < len(existing_key_list) and existing_key_list[idx].get("key"):
        return existing_key_list[idx]["key"]

    return input_key

@app.post("/api/v1/admin/step_configs")
async def admin_save_step_configs(request: Request, authorization: Optional[str] = Header(None)):
    """Menyimpan konfigurasi per tahapan Multi-Agent dengan menjaga integritas kunci."""
    user = await get_current_user_from_header(authorization)
    if user["role"] not in ["executive", "admin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak.")
        
    try:
        payload = await request.json()
        step_configs = payload.get("step_configs", {})
        all_data = get_all_keys()
        existing_steps = all_data.get("step_configs", {})
        
        # Unmask keys jika tidak diubah
        for step_name, step_cfg in step_configs.items():
            exist_step = existing_steps.get(step_name, {})
            exist_keys = exist_step.get("api_keys", [])
            for idx, k in enumerate(step_cfg.get("api_keys", [])):
                k["key"] = _unmask_key_value(k.get("key", ""), exist_keys, idx)
                        
        all_data["step_configs"] = step_configs
        save_all_keys(all_data)
        
        return {
            "status": "success",
            "message": "Konfigurasi Provider, Model, & Kunci API per-tahapan berhasil disimpan!",
            "step_configs": step_configs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/admin/keys")
async def admin_get_keys(authorization: Optional[str] = Header(None)):
    """Mendapatkan daftar API Keys dengan masking."""
    user = await get_current_user_from_header(authorization)
    if user["role"] not in ["executive", "admin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak. Fitur khusus Admin/Eksekutif.")
        
    keys = get_all_keys()
    
    # Mask API keys for security (only show first 8 chars)
    masked_keys = {"google_gemini": [], "groq": []}
    for provider in ["google_gemini", "groq"]:
        for k in keys.get(provider, []):
            safe_k = dict(k)
            if safe_k.get("key"):
                safe_k["key"] = safe_k["key"][:8] + "..." + safe_k["key"][-4:]
            masked_keys[provider].append(safe_k)
            
    return {"status": "success", "data": masked_keys}

@app.post("/api/v1/admin/keys")
async def admin_save_keys(request: Request, authorization: Optional[str] = Header(None)):
    """Menyimpan pembaruan daftar API Keys tanpa menghapus step_configs."""
    user = await get_current_user_from_header(authorization)
    if user["role"] not in ["executive", "admin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak.")
        
    try:
        payload = await request.json()
        all_data = get_all_keys()
        
        for provider in ["google_gemini", "groq"]:
            if provider in payload:
                exist_keys = all_data.get(provider, [])
                for idx, k in enumerate(payload[provider]):
                    k["key"] = _unmask_key_value(k.get("key", ""), exist_keys, idx)
                all_data[provider] = payload[provider]
                            
        save_all_keys(all_data)
        return {"status": "success", "message": "Kunci Pool Global berhasil diperbarui."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/admin/metrics")
async def admin_get_metrics(authorization: Optional[str] = Header(None)):
    """Mengambil agregasi telemetri token dan latensi dari DuckDB log_audit_token."""
    user = await get_current_user_from_header(authorization)
    if user["role"] not in ["executive", "admin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak.")
        
    try:
        conn = get_telemetry_db()
        
        # Total Token (Gemini & Groq)
        q_tokens = """
            SELECT provider, SUM(total_tokens) as tokens 
            FROM log_audit_token 
            GROUP BY provider
        """
        token_rows = conn.execute(q_tokens).fetchall()
        tokens = {r[0]: r[1] for r in token_rows}
        
        # Avg Latency & Total Request
        q_stats = """
            SELECT 
                COUNT(*) as total_req,
                AVG(latency_ms) as avg_latency,
                SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
            FROM log_audit_token
        """
        stats = conn.execute(q_stats).fetchone()
        
        # Recent 10 Logs
        q_recent = """
            SELECT timestamp, agent_name, provider, model_name, latency_ms, status, total_tokens
            FROM log_audit_token 
            ORDER BY timestamp DESC LIMIT 10
        """
        df_recent = conn.execute(q_recent).df()
        
        # Format datetime ke string untuk JSON serialization
        df_recent['timestamp'] = df_recent['timestamp'].astype(str)
        recent_logs = df_recent.to_dict(orient='records')
        
        return {
            "status": "success",
            "metrics": {
                "gemini_tokens": tokens.get("google", 0) or 0,
                "groq_tokens": tokens.get("groq", 0) or 0,
                "total_requests": stats[0] or 0,
                "avg_latency_ms": round(stats[1] or 0, 2),
                "success_rate": round(stats[2] or 0, 1)
            },
            "recent_logs": recent_logs
        }
    except Exception as e:
        logger.error(f"Gagal mengambil metrik telemetri: {e}")
        return {"status": "error", "detail": str(e), "metrics": {}, "recent_logs": []}

@app.get("/api/v1/data/status")
async def get_data_status():
    """Endpoint kesehatan database DuckDB secara live realtime."""
    from pathlib import Path

    BASE_DIR = Path(__file__).resolve().parent.parent
    db_path = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))

    try:
        db_size_mb = round(Path(db_path).stat().st_size / (1024 * 1024), 2) if Path(db_path).exists() else 0

        conn = get_db(db_path)
        tables = conn.execute("SHOW TABLES;").fetchall()

        table_stats = {}
        for t in tables:
            tbl_name = t[0]
            count = conn.execute(f"SELECT COUNT(*) FROM {tbl_name};").fetchone()[0]
            table_stats[tbl_name] = count

        status_payload = {
            "status": "healthy",
            "database_path": db_path,
            "database_size_mb": db_size_mb,
            "total_tables": len(tables),
            "tables": table_stats
        }

        semantic_cache.set_schema_cache("db_status", status_payload, ttl_seconds=600)
        return status_payload
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }

@app.get("/api/v1/admin/table_preview/{table_name}")
async def get_table_preview(table_name: str):
    """Mengembalikan skema kolom dan sampel data dari tabel DuckDB untuk Admin Data Explorer."""
    try:
        import pandas as pd
        conn = get_db()
        clean_table_name = table_name.strip()
        
        # Flexibel query information_schema dengan LOWER()
        cols_query = f"SELECT column_name, data_type AS column_type FROM information_schema.columns WHERE LOWER(table_name) = LOWER('{clean_table_name}') ORDER BY ordinal_position;"
        cols_df = conn.execute(cols_query).df()
        
        # Fallback serbaguna jika information_schema tidak menemukan kolom: gunakan DESCRIBE
        if cols_df.empty:
            try:
                desc_df = conn.execute(f'DESCRIBE "{clean_table_name}";').df()
                cols_df = pd.DataFrame({
                    'column_name': desc_df.iloc[:, 0],
                    'column_type': desc_df.iloc[:, 1]
                })
            except Exception:
                pass
                
        columns = cols_df.to_dict(orient="records")
        
        # Ambil 25 baris data mentah
        sample_df = conn.execute(f'SELECT * FROM "{clean_table_name}" LIMIT 25;').df()
        for col in sample_df.columns:
            sample_df[col] = sample_df[col].apply(lambda x: None if pd.isna(x) or x is None else str(x))
            
        sample_rows = sample_df.to_dict(orient="records")
        
        return {
            "status": "success",
            "table_name": clean_table_name,
            "columns": columns,
            "sample_rows": sample_rows
        }
    except Exception as e:
        logger.error(f"Gagal mengambil preview tabel {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/admin/re_etl")
async def trigger_re_etl():
    """Memicu eksekusi ulang ETL Medallion Pipeline untuk memproses ulang 9 file Excel ke DuckDB."""
    try:
        from etl.main_etl import jalankan_etl
        
        # 1. Tutup koneksi DuckDB sementara agar file lock dilepas
        DuckDBPool.close()
        
        # 2. Jalankan ETL Medallion lengkap
        jalankan_etl()
        
        # 3. Reset koneksi pool agar mengacu ke DB baru
        DuckDBPool.get_connection()
        
        return {
            "status": "success",
            "message": "🔥 ETL Medallion Pipeline berhasil diproses ulang! Seluruh tabel DuckDB kini telah terperbarui."
        }
    except Exception as e:
        logger.error(f"Gagal menjalankan Re-ETL: {e}")
        DuckDBPool.get_connection()
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
def shutdown_event():
    """Tutup shared connection pool DuckDB secara bersih saat server berhenti."""
    DuckDBPool.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
