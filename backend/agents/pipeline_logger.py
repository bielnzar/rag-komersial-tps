import os
import logging
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
PIPELINE_LOG_FILE = LOG_DIR / "pipeline.log"

# Logger terisolasi khusus RAG Pipeline Tracking
pipeline_logger = logging.getLogger("rag_pipeline")
pipeline_logger.setLevel(logging.INFO)
pipeline_logger.propagate = False  # Jangan duplikasi log ke root uvicorn logger

# File Handler khusus untuk logs/pipeline.log (100% Terpisah dari Terminal Backend)
file_handler = logging.FileHandler(PIPELINE_LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
file_handler.setFormatter(formatter)

if not pipeline_logger.handlers:
    pipeline_logger.addHandler(file_handler)

def log_step(stage: str, message: str, details: str = None):
    """Mencatat setiap langkah transisi antar agen RAG secara berurutan."""
    msg = f"[{stage.upper()}] {message}"
    if details:
        msg += f" | {details}"
    pipeline_logger.info(msg)

def log_error(stage: str, error: Exception, context: str = None):
    """Mencatat kesalahan/exception beserta Stack Trace lengkap jika terjadi error 500."""
    tb = traceback.format_exc()
    msg = f"[{stage.upper()}] ERROR: {error}"
    if context:
        msg += f" (Context: {context})"
    msg += f"\n--- STACK TRACE COMPLETE ---\n{tb}---------------------------"
    pipeline_logger.error(msg)
