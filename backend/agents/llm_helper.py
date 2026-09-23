import logging
import os
import time
import uuid
import warnings
from typing import Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

import threading

# Import dependencies untuk Telemetry & API Key Rotator
try:
    from db import get_telemetry_db
    from api_keys_manager import get_active_key_for_step, get_candidate_keys_for_step, record_key_usage_for_step, mark_key_cooldown, get_step_models
except ImportError:
    from ..db import get_telemetry_db
    from ..api_keys_manager import get_active_key_for_step, get_candidate_keys_for_step, record_key_usage_for_step, mark_key_cooldown, get_step_models

logger = logging.getLogger(__name__)

# Abaikan UserWarning bawaan pustaka langchain_google_genai dan google SDK
warnings.filterwarnings("ignore", message="Direct use of automatic function calling.*")
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_google_genai")

def _async_log_telemetry(agent_name: str, provider: str, model_name: str, 
                         input_tokens: int, output_tokens: int, total_tokens: int, 
                         latency_ms: float, status: str):
    """Fungsi fire-and-forget untuk menyisipkan log ke DuckDB agar tidak memblokir antarmuka."""
    def _insert():
        try:
            conn = get_telemetry_db()
            log_id = str(uuid.uuid4())
            # Insert ke tabel log_audit_token
            query = """
                INSERT INTO log_audit_token 
                (id, timestamp, agent_name, provider, model_name, input_tokens, output_tokens, total_tokens, latency_ms, status)
                VALUES (?, current_timestamp, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            conn.execute(query, (log_id, agent_name, provider, model_name, input_tokens, output_tokens, total_tokens, latency_ms, status))
        except Exception as e:
            logger.error(f"❌ Gagal menyimpan telemetri token ke DuckDB: {e}")
            
    threading.Thread(target=_insert, daemon=True).start()


def invoke_chain_with_fallback(chain_prompt: Any, prompt_inputs: dict, structured_schema: Optional[Any] = None, agent_name: str = "general_agent") -> Any:
    """
    Eksekutor LLM Multi-Agent Dinamis dengan Model & Kunci API Khusus Per-Step dari Portal Admin.
    """
    # 🌟 RESOLUSI MODEL & PROVIDER SECARA DINAMIS DARI ADMIN PORTAL
    step_models = get_step_models()
    step_key = "viz_gen" if agent_name == "chart_gen" else agent_name
    cfg = step_models.get(step_key, {})
    
    configured_provider = "google" if cfg.get("provider") in ["google", "google_gemini"] else "groq"
    configured_model = cfg.get("model")
    
    # Fallback defaults jika config belum ada
    if not configured_model:
        if agent_name == "router":
            configured_provider, configured_model = "google", "gemini-3.5-flash-lite"
        elif agent_name == "sql_gen":
            configured_provider, configured_model = "google", "gemini-3.5-flash-lite"
        else: # viz_gen / chart_gen
            configured_provider, configured_model = "groq", "openai/gpt-oss-20b"
            
    models_to_try = [
        (configured_provider, configured_model)
    ]

    last_err = None
    
    # Hitung perkiraan input token berdasarkan panjang prompt (1 token ~ 4 karakter)
    prompt_text_approx = str(prompt_inputs)
    est_input_tokens = len(prompt_text_approx) // 4

    for provider, model_name in models_to_try:
        api_key_group = "google_gemini" if provider == "google" else "groq"
        candidate_keys = get_candidate_keys_for_step(step_key, api_key_group)
        if not candidate_keys:
            candidate_keys = [None]
            
        for current_api_key in candidate_keys:
            start_time = time.time()
            try:
                if provider == "google":
                    llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=current_api_key, request_timeout=35) if current_api_key else ChatGoogleGenerativeAI(model=model_name, request_timeout=35)
                    if structured_schema:
                        llm = llm.with_structured_output(structured_schema)
                else:  # groq
                    if not current_api_key:
                        current_api_key = os.getenv("GROQ_API_KEY")
                    if not current_api_key:
                        continue
                        
                    llm = ChatGroq(model=model_name, temperature=0.1, groq_api_key=current_api_key, timeout=35, max_tokens=4096)
                    if structured_schema:
                        llm = llm.with_structured_output(structured_schema)

                chain = chain_prompt | llm
                res = chain.invoke(prompt_inputs)
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Ekstrak token penggunaan nyata
                output_tokens = 0
                if hasattr(res, 'usage_metadata') and res.usage_metadata:
                    output_tokens = res.usage_metadata.get('output_tokens', 0)
                    if res.usage_metadata.get('input_tokens'):
                        est_input_tokens = res.usage_metadata.get('input_tokens')
                elif hasattr(res, 'content'):
                    output_tokens = len(str(res.content)) // 4
                    
                total_tokens = est_input_tokens + output_tokens
                
                # Catat statistik & usage counter khusus step
                if current_api_key:
                    record_key_usage_for_step(step_key, api_key_group, current_api_key)

                # 📊 LOG TELEMETRI SUCCESS
                _async_log_telemetry(
                    agent_name=agent_name, provider=provider, model_name=model_name,
                    input_tokens=est_input_tokens, output_tokens=output_tokens, total_tokens=total_tokens,
                    latency_ms=latency_ms, status="SUCCESS"
                )

                logger.info(f"[LLM INVOKE SUCCESS] Agent: {agent_name} | Model: {provider}/{model_name} | Latency: {latency_ms:.0f}ms")
                return res
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                err_msg = str(e).lower()
                last_err = e
                
                # Cek jika error adalah 429 Rate Limit (Quota Exhausted) atau Timeout
                is_429 = "429" in err_msg or "resource_exhausted" in err_msg or "rate_limit" in err_msg
                is_timeout = "timeout" in err_msg or "timed out" in err_msg or "deadline" in err_msg
                status_code = "FAILED_429" if is_429 else ("FAILED_TIMEOUT" if is_timeout else "ERROR")
                
                # 📊 LOG TELEMETRI ERROR
                _async_log_telemetry(
                    agent_name=agent_name, provider=provider, model_name=model_name,
                    input_tokens=est_input_tokens, output_tokens=0, total_tokens=est_input_tokens,
                    latency_ms=latency_ms, status=status_code
                )

                logger.warning(f"[LLM INVOKE FAIL] Agent: {agent_name} | Model: {provider}/{model_name} | Status: {status_code} | Latency: {latency_ms:.0f}ms | Detail: {e}")
                
                # Jika 429 atau timeout dan ada kunci kandidat lain, tandai cooldown dan coba kunci berikutnya
                if (is_429 or is_timeout) and current_api_key:
                    mark_key_cooldown(api_key_group, current_api_key, cooldown_seconds=60)
                    logger.info(f"🔄 [Key Rotation] Key ...{current_api_key[-6:] if len(current_api_key)>6 else ''} ({status_code}), otomatis beralih ke kunci berikutnya...")
                    continue

    raise RuntimeError("Akses AI Terhenti: Kuota/Token API LLM saat ini telah habis atau bermasalah. Silakan hubungi Administrator Sistem perihal API LLM di Halaman Admin (/administrator).")
