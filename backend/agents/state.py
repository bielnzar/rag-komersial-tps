from typing import TypedDict, Optional, Any, List

class AgentState(TypedDict):
    """
    Definisi memori (state) untuk LangGraph.
    State ini akan dilempar dari node ke node selama siklus eksekusi.
    """
    user_query: str                  # Pertanyaan asli dari user
    generated_sql: Optional[str]     # SQL hasil rakitan Gemini
    sql_error: Optional[str]         # Pesan error jika SQL gagal dieksekusi (untuk self-healing nanti)
    correction_attempts: int         # Berapa kali sudah mencoba membenarkan SQL (untuk self-healing)
    query_result: Optional[List[dict]] # Hasil query dari DuckDB dalam bentuk list of dicts
    final_answer: Optional[str]      # Jawaban akhir naratif dari Gemini
    echarts_config: Optional[dict]   # Konfigurasi JSON untuk Apache ECharts
