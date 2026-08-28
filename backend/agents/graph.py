from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .sql_gen import sql_gen_node
from .execute import execute_sql_node
from .viz_gen import viz_gen_node
from .router import router_node
from .sanitizer import sanitizer_node
import logging

logger = logging.getLogger(__name__)

def should_continue(state: AgentState):
    """Router bersyarat standar untuk menentukan apakah harus self-healing atau lanjut."""
    error = state.get("sql_error")
    attempts = state.get("correction_attempts", 0)
    
    if error and attempts < 3:
        logger.warning(f"⚠️ Memicu Self-Healing! Percobaan ke-{attempts}. Error: {error}")
        return "sql_gen"
    
    if error and attempts >= 3:
        logger.error("❌ Maksimal percobaan Self-Healing tercapai. Menyerah.")
        
    return "viz_gen"

def should_continue_sanitizer(state: AgentState):
    """
    Router bersyarat khusus node Sanitizer:
    - Jika ada error & attempts < 3: putar balik ke 'sql_gen' untuk koreksi.
    - Jika terblokir total (attempts >= 3): langsung ke 'viz_gen' (JANGAN LEWATI execute_sql!).
    - Jika aman (tidak ada error): lanjut ke 'execute_sql'.
    """
    error = state.get("sql_error")
    attempts = state.get("correction_attempts", 0)
    
    if error:
        if attempts < 3:
            logger.warning(f"⚠️ Sanitizer memicu perbaikan SQL ({attempts}/3): {error}")
            return "sql_gen"
        else:
            logger.error(f"🛡️ SANITIZER BLOCKED TOTAL! Menghentikan eksekusi DB. Error: {error}")
            return "viz_gen"
            
    return "execute_sql"

def build_graph():
    """
    Membangun state machine LangGraph untuk alur Text-to-SQL.
    """
    workflow = StateGraph(AgentState)
    
    # Daftarkan node
    workflow.add_node("router", router_node)
    workflow.add_node("sql_gen", sql_gen_node)
    workflow.add_node("sanitizer", sanitizer_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("viz_gen", viz_gen_node)
    
    # Rangkai alur eksekusi dengan siklus Self-Healing (Milestone 3)
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "sql_gen")
    workflow.add_edge("sql_gen", "sanitizer")
    
    # Conditional Edges dari sanitizer: Lanjut ke eksekusi atau putar balik perbaiki SQL?
    workflow.add_conditional_edges(
        "sanitizer",
        should_continue_sanitizer,
        {
            "sql_gen": "sql_gen",         # Putar balik untuk koreksi
            "execute_sql": "execute_sql", # Lolos validasi -> eksekusi SQL ke DuckDB
            "viz_gen": "viz_gen"          # Terblokir total -> langsung ke viz_gen (SKIPS execute_sql)
        }
    )
    
    # Conditional Edges dari execute_sql: Maju ke viz_gen atau putar balik perbaiki SQL?
    workflow.add_conditional_edges(
        "execute_sql",
        should_continue,
        {
            "sql_gen": "sql_gen", # Putar balik untuk koreksi
            "viz_gen": "viz_gen"  # Lanjut sukses
        }
    )
    
    workflow.add_edge("viz_gen", END)
    
    # Kompilasi menjadi fungsi yang bisa dipanggil
    app = workflow.compile()
    return app
