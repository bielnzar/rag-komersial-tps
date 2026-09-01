from langchain_core.prompts import ChatPromptTemplate
from .llm_helper import invoke_chain_with_fallback
import logging
import os
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

def format_data_compact(query_result: list, max_rows: int = 50) -> str:
    """
    Mengonversi list of dicts data mentah menjadi format CSV Compact.
    Menghemat hingga 50% token payload dibanding JSON verbose.
    """
    if not query_result or not isinstance(query_result, list) or len(query_result) == 0:
        return "Tidak ada data"
    
    limited = query_result[:max_rows]
    headers = list(limited[0].keys())
    lines = [",".join(headers)]
    
    for row in limited:
        vals = [str(row.get(h, '')).replace(',', ';') for h in headers]
        lines.append(",".join(vals))
        
    return "\n".join(lines)

class ChartOutput(BaseModel):
    """Skema JSON output khusus untuk Lapisan 3 (Pembuat Grafik ECharts)."""
    echarts_config: dict = Field(
        default_factory=dict,
        description="Konfigurasi JSON lengkap standar Apache ECharts (Bar, Line, atau Pie chart)."
    )

CHART_SYSTEM_PROMPT = """Anda adalah ECharts Generator. Tugas Anda adalah mengembalikan objek JSON valid dengan format persis:
{{
  "echarts_config": {{
    "title": {{"text": "Judul Grafik", "textStyle": {{"color": "#f8fafc"}}}},
    "tooltip": {{"trigger": "axis"}},
    "legend": {{"textStyle": {{"color": "#94a3b8"}}}},
    "xAxis": {{"type": "category", "data": ["Item1", "Item2"], "axisLabel": {{"color": "#94a3b8"}}}},
    "yAxis": {{"type": "value", "axisLabel": {{"color": "#94a3b8"}}}},
    "series": [{{"name": "Nilai", "type": "bar", "data": [10, 20], "label": {{"show": true, "position": "top", "color": "#38bdf8"}}}}]
  }}
}}

Aturan:
1. Pilih tipe grafik tepat (Bar=kategori, Line=tren bulan/tahun, Pie=market share/proporsi).
2. Gunakan warna teks terang ('#f8fafc' atau '#94a3b8') dan background transparan.
3. Wajib sertakan 'label': {{"show": true, "position": "top", "color": "#38bdf8"}} pada setiap series.
4. JANGAN gunakan sintaks formatter JS (seperti function(x)) atau karakter escape bergaris miring.
5. Keluarkan HANYA objek JSON valid sesuai struktur {{"echarts_config": ...}} di atas."""

def generate_chart_config(user_query: str, query_result: list) -> dict:
    """
    Fungsi khusus Lapisan 3 (On-Demand Chart Generator):
    - Utama: Memanggil Groq OpenAI/GPT-OSS-20B via LLM Helper.
    """
    if not query_result or not isinstance(query_result, list) or len(query_result) == 0:
        return {}

    data_str = format_data_compact(query_result, max_rows=50)

    prompt = ChatPromptTemplate.from_messages([
        ("system", CHART_SYSTEM_PROMPT),
        ("human", "Konteks: {question}\nData (CSV):\n{data}")
    ])

    try:
        response = invoke_chain_with_fallback(
            chain_prompt=prompt,
            prompt_inputs={
                "question": user_query,
                "data": data_str
            },
            structured_schema=ChartOutput,
            agent_name="chart_gen"
        )
        
        if response and hasattr(response, "echarts_config") and response.echarts_config:
            return response.echarts_config
            
    except Exception as e:
        logger.error(f"❌ Lapisan 3 (Chart Gen Error): {e}")

    return {}
