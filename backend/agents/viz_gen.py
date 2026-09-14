from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
from .chart_gen import generate_chart_config
from .llm_helper import invoke_chain_with_fallback
from concurrent.futures import ThreadPoolExecutor
import logging
import re
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
    # Jika dataset wajar/ringkas (<= 30 baris seperti master 23 operator),
    # sertakan seluruhnya agar tidak terpotong menjadi placeholder [Operator 16], dst.
    if total_count <= 30:
        limited = query_result
    else:
        limited = query_result[:max_rows]
        
    headers = list(limited[0].keys())
    lines = [",".join(headers)]
    
    for row in limited:
        vals = [str(row.get(h, '')).replace(',', ';') for h in headers]
        lines.append(",".join(vals))
        
    if total_count > len(limited):
        lines.append(f"... (dan {total_count - len(limited)} baris data lainnya. Total keseluruhan baris: {total_count})")
        
    return "\n".join(lines)

class NarrativeOutput(BaseModel):
    """Skema JSON output khusus untuk Lapisan 2 (Narasi Jawaban)."""
    answer: Optional[str] = Field(default=None, description="Jawaban teks naratif.")
    response: Optional[str] = Field(default=None, description="Alternatif nama key jawaban.")
    final_answer: Optional[str] = Field(default=None, description="Alternatif nama key jawaban.")

    def get_text(self) -> str:
        return self.answer or self.response or self.final_answer or ""

VIZ_SYSTEM_PROMPT = """Anda adalah Data Analyst eksekutif PT TPS (Terminal Petikemas Surabaya).

TUGAS: Sajikan narasi eksekutif dalam Bahasa Indonesia yang ringkas, to-the-point, dan akurat berdasarkan Data CSV.

ATURAN PENULISAN:
1. Format Angka: Wajib gunakan titik (.) sebagai pemisah ribuan Rupiah dan volume (cth: Rp145.269.000.977, 12.085 TEUs).
2. Satuan: Gunakan 'TEUs' atau 'Boxes' untuk kontainer (jangan gunakan kata 'unit'). Untuk pendapatan, gunakan Rupiah saja.
3. Tata Letak Markdown:
   - Gunakan daftar bernomor (1., 2.) dengan jeda baris antar poin.
   - Jika data memiliki kode dan nama lengkap (seperti code & full_name), sebutkan keduanya secara lengkap dan rapi: `1. **NAMA LENGKAP** (KODE)` atau `1. **KODE** – NAMA LENGKAP` (contoh: `1. **ANL SINGAPORE PTE. LTD.** (ANL)`). DILARANG membuat placeholder seperti [Operator X].
   - Tebalkan (**Nama Operator / Kategori / Bulan**).
4. Analisis & Kesimpulan:
   - Tuliskan seluruh item yang ada di data secara lengkap tanpa ada yang terlewat.
   - Wajib selesaikan setiap kalimat hingga tuntas bertanda titik (.). DILARANG KERAS mengakhiri respons dengan kalimat menggantung atau kata sambung (seperti: Namun, Tetapi, Dan)."""


DOMAIN_SUGGESTIONS = {
    "throughput": [
        "Berapa total throughput internasional tahun 2024?",
        "Bandingkan throughput domestik dan internasional 2023",
        "Tampilkan tren throughput 2024 beserta grafiknya"
    ],
    "revenue": [
        "Berapa total pendapatan komersial tahun 2023?",
        "Siapa 5 operator dengan revenue terbesar tahun 2024?",
        "Tampilkan tren pendapatan komersial 2024 beserta grafiknya"
    ],
    "market_share": [
        "Siapa 3 operator dengan market share terbesar 2023?",
        "Berapa total volume TEUs operator CMA tahun 2023?",
        "Tampilkan proporsi market share operator 2024"
    ],
    "vessel": [
        "Berapa total box operasional kapal internasional tahun 2024?",
        "Tampilkan rute dan total call kapal tahun 2024",
        "Siapa operator dengan rata-rata BMPH tertinggi?"
    ],
    "general": [
        "Berapa total throughput internasional tahun 2024?",
        "Berapa total pendapatan komersial tahun 2023?",
        "Siapa 3 operator dengan market share terbesar 2023?"
    ]
}

def get_context_suggestions(user_query: str, relevant_tables: list[str] | None = None) -> list[str]:
    """
    Menghasilkan 3 rekomendasi pertanyaan interaktif berbasis konteks kueri/tabel (0 Token & 0 ms).
    Semua rekomendasi dijamin memiliki data valid di database DuckDB PT TPS.
    """
    q_lower = user_query.lower()
    tbls = relevant_tables or []
    
    # 1. Deteksi berbasis tabel terpilih oleh Router
    if any("throughput" in t or "overview_box" in t for t in tbls):
        return DOMAIN_SUGGESTIONS["throughput"]
    if any("komersial" in t or "disc" in t or "realisasi_uc" in t for t in tbls):
        return DOMAIN_SUGGESTIONS["revenue"]
    if any("market_share" in t for t in tbls):
        return DOMAIN_SUGGESTIONS["market_share"]
    if any("vessel" in t or "transhipment" in t for t in tbls):
        return DOMAIN_SUGGESTIONS["vessel"]
        
    # 2. Fallback deteksi kata kunci kueri
    if any(kw in q_lower for kw in ["throughput", "teus", "arus", "box", "petikemas", "kontainer"]):
        return DOMAIN_SUGGESTIONS["throughput"]
    if any(kw in q_lower for kw in ["pendapatan", "revenue", "uang", "rupiah", "biaya", "tarif", "diskon", "keringanan"]):
        return DOMAIN_SUGGESTIONS["revenue"]
    if any(kw in q_lower for kw in ["market", "pangsa", "share", "persen", "peringkat", "ranking", "top"]):
        return DOMAIN_SUGGESTIONS["market_share"]
    if any(kw in q_lower for kw in ["kapal", "vessel", "call", "bmph", "rute", "service"]):
        return DOMAIN_SUGGESTIONS["vessel"]
        
    return DOMAIN_SUGGESTIONS["general"]

from .pipeline_logger import log_step, log_error

def viz_gen_node(state: AgentState) -> dict:
    """
    Node Lapisan 2 & 3: Menghasilkan narasi eksekutif dan konfigurasi ECharts (jika diminta).
    """
    user_query = state.get("user_query", "")
    relevant_tables = state.get("relevant_tables")
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
            suggestions = get_context_suggestions(user_query, relevant_tables)
            return {
                "final_answer": "Maaf, data yang Anda cari tidak ditemukan atau bernilai kosong pada database PT TPS untuk kriteria atau periode waktu yang diminta.\n\n**Saran:** Anda dapat mencoba salah satu pertanyaan rekomendasi di bawah ini:",
                "echarts_config": None,
                "suggestions": suggestions
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

    data_str = format_data_compact(query_result, max_rows=15)
    error_str = sql_error if sql_error else "Tidak ada error"

    def _run_chart():
        if is_chart_requested and query_result:
            try:
                return generate_chart_config(user_query, query_result)
            except Exception as ce:
                logger.warning(f"⚠️ Gagal merakit ECharts di background thread: {ce}")
                return None
        return None

    def _run_narrative():
        prompt = ChatPromptTemplate.from_messages([
            ("system", VIZ_SYSTEM_PROMPT),
            ("human", "Pertanyaan: {question}\nError: {error}\nData (CSV):\n{data}")
        ])
        return invoke_chain_with_fallback(
            chain_prompt=prompt,
            prompt_inputs={
                "question": user_query,
                "error": error_str,
                "data": data_str
            },
            structured_schema=None,
            agent_name="viz_gen"
        )

    chart_config = None
    response = None

    try:
        if is_chart_requested and query_result:
            log_step("STEP 5: VIZ_PARALLEL", "Menjalankan generator Narasi & ECharts secara paralel (ThreadPool)")
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_chart = executor.submit(_run_chart)
                future_narrative = executor.submit(_run_narrative)
                chart_config = future_chart.result()
                response = future_narrative.result()
        else:
            response = _run_narrative()
        
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
            
        # Sanitasi kalimat menggantung: pangkas jika AI terputus tepat di kata sambung
        final_text = re.sub(r'\b(namun|tetapi|akan tetapi|dan|serta|sedangkan|meskipun|walaupun|sementara)\s*[\.,;:\-]*$', '', final_text.rstrip(), flags=re.IGNORECASE).rstrip()
        if final_text and not final_text.endswith(('.', '!', '?', '"', "'", '`', '*', ':')):
            final_text += '.'
            
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
