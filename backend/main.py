from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load env variables (memastikan GEMINI_API_KEY terbaca)
load_dotenv()

# Import graph agent
from agents.graph import build_graph

app = FastAPI(
    title="TPS Enterprise AI Data Agent",
    description="API untuk asisten AI komersial PT TPS",
    version="1.0.0"
)

# Konfigurasi CORS agar bisa diakses dari Frontend Vue (Port berapapun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Mengizinkan semua origin untuk tujuan prototyping
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inisialisasi LangGraph app
agent_app = build_graph()

class ChatRequest(BaseModel):
    query: str
    user_id: str = "guest"
    role: str = "commercial"

class ChatResponse(BaseModel):
    status: str
    answer: str
    chart_config: dict | None = None
    sql_executed: str | None = None
    error: str | None = None
    data: list | None = None

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint utama untuk menerima pertanyaan bahasa natural, 
    menjalankan LangGraph Text-to-SQL, dan mengembalikan jawaban.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query tidak boleh kosong.")
        
    try:
        # Menjalankan LangGraph
        initial_state = {
            "user_query": request.query,
            "generated_sql": None,
            "sql_error": None,
            "correction_attempts": 0,
            "query_result": None,
            "final_answer": None
        }
        
        # Invoke graph
        result_state = agent_app.invoke(initial_state)
        
        return ChatResponse(
            status="success" if not result_state.get("sql_error") else "error",
            answer=result_state.get("final_answer", "Maaf, gagal merangkum jawaban."),
            chart_config=result_state.get("echarts_config"),
            sql_executed=result_state.get("generated_sql"),
            error=result_state.get("sql_error"),
            data=result_state.get("query_result")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/data/status")
async def get_data_status():
    """
    Endpoint untuk mengecek kesehatan integrasi ETL.
    (Di-mock untuk Milestone 2)
    """
    return {
        "status": "healthy",
        "last_sync": "2024-10-01 10:00:00",
        "database": "tps_komersial.duckdb"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
