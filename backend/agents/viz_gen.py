from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
import json
from pydantic import BaseModel, Field

class VizOutput(BaseModel):
    """Skema JSON output wajib untuk agen visualisasi."""
    answer: str = Field(description="Jawaban teks naratif yang ramah dan profesional berdasarkan data.")
    echarts_config: dict = Field(
        default_factory=dict, 
        description="Konfigurasi JSON lengkap standar Apache ECharts (opsional, hasilkan jika data cocok untuk divisualisasikan dengan Bar, Line, atau Pie chart. Jika tidak, kosongkan)."
    )

VIZ_SYSTEM_PROMPT = """
Anda adalah AI Assistant profesional dan Data Analyst dari divisi komersial PT TPS (Terminal Petikemas Surabaya).
Pengguna menanyakan sebuah pertanyaan, dan sistem telah mengeksekusi SQL untuk mengambil datanya.

Tugas Anda:
1. Jawab pertanyaan pengguna secara LENGKAP berdasarkan HASIL DATA yang diberikan. Jika pengguna meminta Top 5, sebutkan kelima-limanya di dalam teks 'answer'. Jangan hanya merangkum peringkat pertama saja.
2. ATURAN SATUAN PELABUHAN: Di PT TPS, satuan volume kontainer/throughput SELALU menggunakan istilah 'TEUs' (atau 'Boxes' jika spesifik), DILARANG MENGGUNAKAN kata generik 'unit'.
3. Jika datanya cocok untuk divisualisasikan, buatlah konfigurasi JSON Apache ECharts murni ke dalam atribut 'echarts_config' yang mencakup SELURUH baris data.
4. Gunakan warna elegan dan modern untuk grafik ECharts Anda.
5. ATURAN FORMATTER GRAFIK: Di dalam 'echarts_config', DILARANG menggunakan sintaks formatter khusus seperti '{{c:,}}' atau karakter escape bergaris miring. Gunakan format sederhana seperti '{{c}}' atau biarkan ECharts menggunakan bawaan.
6. ATURAN KONTRAST GRAFIK: Gunakan warna teks terang ('#f8fafc' atau '#94a3b8') pada 'xAxis', 'yAxis', dan 'title'. Wajib sertakan 'label': {{'show': true, 'position': 'top', 'color': '#38bdf8'}} pada setiap series agar nilai/angka data selalu terlihat jelas di atas batang grafik.
7. Jika datanya kosong atau terjadi error SQL, sampaikan permohonan maaf dan biarkan echarts_config kosong.
"""

def viz_gen_node(state: AgentState) -> dict:
    """
    Node untuk merangkum hasil SQL menjadi teks naratif.
    """
    user_query = state["user_query"]
    query_result = state.get("query_result")
    sql_error = state.get("sql_error")
    
    # PENANGANAN BLOCKER SANITIZER: Jika diblokir oleh Sanitizer, kembalikan respon penolakan keamanan
    if sql_error and "SANITIZER BLOCKED" in sql_error:
        return {
            "final_answer": f"🛡️ **Permintaan Ditolak oleh Sistem Keamanan Sanitizer PT TPS**\n\n{sql_error}\n\nSistem mengidentifikasi adanya klausa/simbol yang tidak diizinkan demi menjaga integritas database pelabuhan. Harap ajukan pertanyaan analisis data secara normal.",
            "echarts_config": None
        }
    
    # Menggunakan Gemini 3.6 Flash (Sama dengan SQL Gen & Router) untuk menghindari TPM Limit Groq
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash"
    ).with_structured_output(VizOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", VIZ_SYSTEM_PROMPT),
        ("human", "Pertanyaan Pengguna: {question}\n\nError Database: {error}\n\nHasil Data: {data}")
    ])
    
    # Batasi data_str maksimal 50 baris pertama untuk efisiensi token
    limited_result = query_result[:50] if query_result and isinstance(query_result, list) else query_result
    data_str = json.dumps(limited_result, indent=2) if limited_result else "Tidak ada data"
    error_str = sql_error if sql_error else "Tidak ada error"
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "question": user_query,
            "error": error_str,
            "data": data_str
        })
        
        if not response:
            return {
                "final_answer": "Maaf, tidak ada respon dari agen visualisasi.",
                "echarts_config": None
            }
            
        return {
            "final_answer": response.answer,
            "echarts_config": response.echarts_config
        }
    except Exception as e:
        # Fallback jika Groq gagal parse tool arguments: buatkan narasi sederhana dari query_result
        logger_msg = f"⚠️ Groq tool parse error: {e}. Fallback ke narasi data langsung."
        print(logger_msg)
        
        fallback_answer = f"Berdasarkan data hasil query database:\n\n"
        if query_result:
            for idx, row in enumerate(query_result, 1):
                items = [f"**{k}**: {v}" for k, v in row.items()]
                fallback_answer += f"{idx}. " + ", ".join(items) + "\n"
        else:
            fallback_answer += "Tidak ada baris data yang ditemukan."
            
        return {
            "final_answer": fallback_answer,
            "echarts_config": None
        }
