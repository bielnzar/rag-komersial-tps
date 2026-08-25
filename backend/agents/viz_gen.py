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
2. Jika datanya cocok untuk divisualisasikan, buatlah konfigurasi JSON Apache ECharts murni ke dalam atribut 'echarts_config' yang mencakup SELURUH baris data.
3. Gunakan warna elegan dan modern untuk grafik ECharts Anda.
4. Jika datanya kosong atau terjadi error SQL, sampaikan permohonan maaf dan biarkan echarts_config kosong.
"""

def viz_gen_node(state: AgentState) -> dict:
    """
    Node untuk merangkum hasil SQL menjadi teks naratif.
    """
    user_query = state["user_query"]
    query_result = state.get("query_result")
    sql_error = state.get("sql_error")
    
    # Menggunakan gemini-3.5-flash-lite karena sangat andal dalam penguraian JSON terstruktur
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite"
    ).with_structured_output(VizOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", VIZ_SYSTEM_PROMPT),
        ("human", "Pertanyaan Pengguna: {question}\n\nError Database: {error}\n\nHasil Data: {data}")
    ])
    
    # Format data ke JSON string agar mudah dibaca LLM
    data_str = json.dumps(query_result, indent=2) if query_result else "Tidak ada data"
    error_str = sql_error if sql_error else "Tidak ada error"
    
    chain = prompt | llm
    response = chain.invoke({
        "question": user_query,
        "error": error_str,
        "data": data_str
    })
    
    # response sekarang otomatis berupa object Pydantic (VizOutput)
    if not response:
        return {
            "final_answer": "Maaf, terjadi kesalahan saat merakit visualisasi. Coba lagi.",
            "echarts_config": None
        }
        
    return {
        "final_answer": response.answer,
        "echarts_config": response.echarts_config
    }
