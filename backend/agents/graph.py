from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .sql_gen import sql_gen_node
from .execute import execute_sql_node
from .viz_gen import viz_gen_node
from .router import router_node
from .sanitizer import sanitizer_node
import logging

logger = logging.getLogger(__name__)

def should_continue_sanitizer(state: AgentState):
    """
    Router bersyarat khusus node Sanitizer (Fail-Fast):
    - Jika terblokir Sanitizer: langsung ke 'viz_gen' untuk graceful rejection.
    - Jika lolos: lanjut ke 'execute_sql'.
    """
    error = state.get("sql_error")
    if error and "SANITIZER BLOCKED" in error:
        logger.warning(f"🛡️ SANITIZER BLOCKED! Menghentikan eksekusi DB dan lanjut ke graceful notification. Error: {error}")
        return "viz_gen"
            
    return "execute_sql"

def build_graph():
    """
    Membangun state machine LangGraph untuk alur Text-to-SQL dengan mekanisme Fail-Fast (Single-Pass).
    """
    workflow = StateGraph(AgentState)
    
    # Daftarkan node
    workflow.add_node("router", router_node)
    workflow.add_node("sql_gen", sql_gen_node)
    workflow.add_node("sanitizer", sanitizer_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("viz_gen", viz_gen_node)
    
    # Rangkai alur linier Fail-Fast (Tanpa looping / retry)
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "sql_gen")
    workflow.add_edge("sql_gen", "sanitizer")
    
    # Dari sanitizer: Eksekusi SQL atau langsung ke viz_gen jika diblokir
    workflow.add_conditional_edges(
        "sanitizer",
        should_continue_sanitizer,
        {
            "execute_sql": "execute_sql", # Lolos validasi -> eksekusi SQL ke DuckDB
            "viz_gen": "viz_gen"          # Terblokir total -> langsung ke viz_gen (SKIPS execute_sql)
        }
    )
    
    # Dari execute_sql SELALU langsung ke viz_gen (Fail-Fast, no retry loop)
    workflow.add_edge("execute_sql", "viz_gen")
    workflow.add_edge("viz_gen", END)
    
    # Kompilasi menjadi fungsi yang bisa dipanggil
    app = workflow.compile()
    return app
