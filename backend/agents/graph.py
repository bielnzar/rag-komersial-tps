from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .sql_gen import sql_gen_node
from .execute import execute_sql_node
from .viz_gen import viz_gen_node
import logging

logger = logging.getLogger(__name__)

def should_continue(state: AgentState):
    """Router bersyarat untuk menentukan apakah harus self-healing atau lanjut."""
    error = state.get("sql_error")
    attempts = state.get("correction_attempts", 0)
    
    if error and attempts < 3:
        logger.warning(f"⚠️ Memicu Self-Healing! Percobaan ke-{attempts}. Error: {error}")
        return "sql_gen"
    
    if error and attempts >= 3:
        logger.error("❌ Maksimal percobaan Self-Healing tercapai. Menyerah.")
        
    return "viz_gen"

def build_graph():
    """
    Membangun state machine LangGraph untuk alur Text-to-SQL.
    """
    workflow = StateGraph(AgentState)
    
    # Daftarkan node
    workflow.add_node("sql_gen", sql_gen_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("viz_gen", viz_gen_node)
    
    # Rangkai alur eksekusi dengan siklus Self-Healing (Milestone 3)
    workflow.add_edge(START, "sql_gen")
    workflow.add_edge("sql_gen", "execute_sql")
    
    # Conditional Edges: Dari execute_sql, apakah maju atau putar balik?
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
