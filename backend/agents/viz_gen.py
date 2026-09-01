from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
from .chart_gen import generate_chart_config
from .llm_helper import invoke_chain_with_fallback
import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

def format_data_compact(query_result: list, max_rows: int = 15) -> str:
    """
    Mengonversi list of dicts data mentah menjadi format CSV Compact dengan Row Sampling cerdas.
    Menghemat hingga 80% token payload dibanding JSON mentah.
    """
    if not query_result or not isinstance(query_result, list) or len(query_result) == 0:
        return "Tidak ada data"
    
    total_count = len(query_result)
    limited = query_result[:max_rows]
    headers = list(limited[0].keys())
    lines = [",".join(headers)]
    
    for row in limited:
        vals = [str(row.get(h, '')).replace(',', ';') for h in headers]
        lines.append(",".join(vals))
        
    if total_count > max_rows:
        lines.append(f"... (dan {total_count - max_rows} baris data lainnya. Total keseluruhan baris: {total_count})")
        
    return "\n".join(lines)

class NarrativeOutput(BaseModel):
    """Skema JSON output khusus untuk Lapisan 2 (Narasi Jawaban)."""
    answer: Optional[str] = Field(default=None, description="Jawaban teks naratif.")
    response: Optional[str] = Field(default=None, description="Alternatif nama key jawaban.")
    final_answer: Optional[str] = Field(default=None, description="Alternatif nama key jawaban.")

    def get_text(self) -> str:
        return self.answer or self.response or self.final_answer or ""

VIZ_SYSTEM_PROMPT = """Anda adalah Data Analyst eksekutif PT TPS (Terminal Petikemas Surabaya).

ATURAN UTAMA PENULISAN JAWABAN:
1. Jawab LENGKAP sesuai data (jika Top 5, sebutkan kelima-limanya).
2. Satuan volume kontainer SELALU 'TEUs' atau 'Boxes', DILARANG menggunakan kata 'unit'.
3. FORMAT ANGKA & NOMINAL (WAJIB): SELALU gunakan pemisah ribuan berupa TITIK (.) untuk seluruh angka volume dan nominal mata uang Rupiah (misal: Rp168.136.527.278, 134.129 TEUs, 88.148 Boxes). DILARANG KERAS menulis angka besar tanpa titik pemisah ribuan!
4. Bahasa ramah, eksekutif, profesional, dan berstruktur rapi.

FORMAT LAYOUT MARKDOWN & PENOMORAN (WAJIB DIPATUHI):
- Penomoran HARUS menggunakan format `1. `, `2. `, `3. ` (wajib titik dan spasi setelah nomor). CONTOH BENAR: `1. **CMA** – Rp302.788.976.564, 252.355 TEUs`. DILARANG KERAS menempelkan angka langsung ke teks (seperti 1CMA atau 2SSL)!
- SELALU gunakan baris baru (newline `\n\n`) untuk memisahkan setiap poin daftar bernomor (1., 2., 3.) atau bullet point (- ). DILARANG KERAS menggabungkan daftar bernomor dalam satu paragraf!
- Jika ada daftar setelah tanda titik dua (:), SELALU beri 2 baris baru (newline `\n\n`) sebelum memulai poin 1.
- Gunakan cetak tebal (**Nama Perusahaan / Operator / Layanan**) untuk menyoroti entitas utama.
- Jika satu poin memiliki beberapa sub-layanan yang dipisahkan titik koma (;), pisahkan sub-layanan tersebut menjadi bullet point berindented di baris baru."""

from .pipeline_logger import log_step, log_error

def viz_gen_node(state: AgentState) -> dict:
    """
    Node Lapisan 2 & 3: Menghasilkan narasi eksekutif dan konfigurasi ECharts (jika diminta).
    """
    user_query = state.get("user_query", "")
    query_result = state.get("query_result")
    sql_error = state.get("sql_error")
    force_chart = state.get("force_chart", False)
    
    if sql_error:
        if "SANITIZER BLOCKED" in sql_error:
            log_step("STEP 5: VIZ_GEN_SKIP", "Pertanyaan diblokir oleh Sanitizer")
            return {
                "final_answer": f"**Permintaan Ditolak oleh Sistem Keamanan Sanitizer PT TPS**\n\n{sql_error}\n\nSistem mengidentifikasi adanya klausa/simbol yang tidak diizinkan demi menjaga integritas database pelabuhan. Harap ajukan pertanyaan analisis data secara normal.",
                "echarts_config": None
            }
        elif "DATA_EMPTY" in sql_error:
            log_step("STEP 5: VIZ_GEN_EMPTY", "Data tidak ditemukan (Fail-Fast Graceful Degradation)")
            return {
                "final_answer": "Maaf, data yang Anda cari tidak ditemukan atau bernilai kosong pada database PT TPS untuk kriteria atau periode waktu yang diminta.\n\n**Saran:**\n- Pastikan penulisan nama operator/layanan sudah sesuai (misal: *CMA*, *SSL*, *MSK*, *Internasional*, atau *Domestik*).\n- Coba perjelas atau sesuaikan parameter rentang tahun/bulan yang ingin dianalisis.",
                "echarts_config": None
            }
        elif "DB_SYNTAX_ERROR" in sql_error:
            log_step("STEP 5: VIZ_GEN_ERROR", "Kueri mengalami kendala eksekusi (Fail-Fast)")
            return {
                "final_answer": "Maaf, sistem tidak dapat memproses kueri untuk pertanyaan tersebut secara langsung.\n\n**Saran:** Mohon ajukan kembali pertanyaan dengan kata kunci atau parameter yang lebih spesifik.",
                "echarts_config": None
            }
    
    chart_keywords = ["grafik", "chart", "diagram", "visualisasi", "visualisasikan", "plot", "tren", "trend"]
    is_chart_requested = force_chart or any(kw in user_query.lower() for kw in chart_keywords)
    
    log_step("STEP 5: VIZ_GEN", f"Merangkum narasi bisnis & ECharts via Groq gpt-oss-20b", f"Chart: {is_chart_requested}")

    prompt = ChatPromptTemplate.from_messages([
        ("system", VIZ_SYSTEM_PROMPT),
        ("human", "Pertanyaan: {question}\nError: {error}\nData (CSV):\n{data}")
    ])
    
    data_str = format_data_compact(query_result, max_rows=50)
    error_str = sql_error if sql_error else "Tidak ada error"
    
    chart_config = None
    if is_chart_requested and query_result:
        chart_config = generate_chart_config(user_query, query_result)

    try:
        response = invoke_chain_with_fallback(
            chain_prompt=prompt,
            prompt_inputs={
                "question": user_query,
                "error": error_str,
                "data": data_str
            },
            structured_schema=None,
            agent_name="viz_gen"
        )
        
        if not response:
            return {
                "final_answer": "Maaf, tidak ada respon dari agen visualisasi.",
                "echarts_config": chart_config
            }
            
        final_text = response.content if hasattr(response, "content") else str(response)
        if isinstance(final_text, list):
            final_text = final_text[0] if isinstance(final_text[0], str) else final_text[0].get("text", "")
            
        if not final_text or not str(final_text).strip():
            logger.warning("⚠️ Groq/LLM mengembalikan narasi kosong. Menggunakan fallback generator.")
            fallback_answer = f"Berdasarkan data hasil query database:\n\n"
            if query_result:
                for idx, row in enumerate(query_result, 1):
                    items = [f"**{k}**: {v}" for k, v in row.items()]
                    fallback_answer += f"{idx}. " + ", ".join(items) + "\n\n"
            else:
                fallback_answer += "Tidak ada baris data yang ditemukan."
            final_text = fallback_answer
            
        log_step("STEP 5: VIZ_GEN_DONE", f"Narasi berhasil disusun ({len(final_text)} karakter)")
        return {
            "final_answer": final_text,
            "echarts_config": chart_config
        }
    except Exception as e:
        log_error("STEP 5: VIZ_GEN_FAIL", e)
        err_text = str(e)
        if "Akses AI Terhenti" in err_text:
            return {
                "final_answer": err_text,
                "echarts_config": None
            }
        fallback_answer = f"Berdasarkan data hasil query database:\n\n"
        if query_result:
            for idx, row in enumerate(query_result, 1):
                items = [f"**{k}**: {v}" for k, v in row.items()]
                fallback_answer += f"{idx}. " + ", ".join(items) + "\n\n"
        else:
            fallback_answer += "Tidak ada baris data yang ditemukan."
            
        return {
            "final_answer": fallback_answer,
            "echarts_config": chart_config
        }
