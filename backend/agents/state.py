from typing import TypedDict, Optional, Any, List

class AgentState(TypedDict):
    """
    Definisi memori (state) untuk LangGraph.
    State ini akan dilempar dari node ke node selama siklus eksekusi.
    """
    user_query: str                  # Pertanyaan asli dari user
    relevant_tables: Optional[List[str]]  # Daftar tabel yang dipilih oleh Router Agent
    generated_sql: Optional[str]     # SQL hasil rakitan Gemini
    sql_error: Optional[str]         # Pesan error jika SQL gagal dieksekusi atau data kosong (Fail-Fast)
    correction_attempts: int         # Flag status eksekusi kueri
    query_result: Optional[List[dict]] # Hasil query dari DuckDB dalam bentuk list of dicts
    final_answer: Optional[str]      # Jawaban akhir naratif dari Gemini/Groq
    echarts_config: Optional[dict]   # Konfigurasi JSON untuk Apache ECharts
    force_chart: Optional[bool]      # Flag khusus jika user meminta grafik (On-Demand Chart)
    chat_history: Optional[List[dict]] # Riwayat percakapan sebelumnya dari Redis (Multi-Turn Memory)
    role: Optional[str]              # Peran pengguna untuk RBAC (executive, commercial, operation, guest)
