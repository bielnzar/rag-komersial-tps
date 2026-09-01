import os
import duckdb
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "data/processed/tps_komersial.duckdb"))
TELEMETRY_DB_PATH = os.getenv("TELEMETRY_DUCKDB_PATH", str(BASE_DIR / "data/processed/telemetry.duckdb"))

class DuckDBPool:
    """
    Manager Koneksi Terpusat (Shared Connection Pool) untuk DuckDB.
    Mengelola koneksi read-only tunggal yang efisien untuk kueri AI (OLAP).
    """
    _instance = None
    _telemetry_instance = None

    @classmethod
    def get_connection(cls, db_path: str = None) -> duckdb.DuckDBPyConnection:
        target_path = db_path or DB_PATH
        if cls._instance is None:
            try:
                cls._instance = duckdb.connect(target_path, read_only=True)
                logger.info(f"🔌 [DuckDBPool] Buka koneksi shared read-only: {target_path}")
            except Exception as e:
                logger.error(f"❌ [DuckDBPool] Gagal membuka koneksi DuckDB shared: {e}")
                return duckdb.connect(target_path, read_only=True)
        return cls._instance

    @classmethod
    def get_telemetry_connection(cls) -> duckdb.DuckDBPyConnection:
        """
        Koneksi READ-WRITE khusus untuk sistem logging Telemetri (Token & Latency).
        Terpisah dari database analitik utama untuk mencegah masalah locking.
        """
        if cls._telemetry_instance is None:
            try:
                # Pastikan direktori ada
                os.makedirs(os.path.dirname(TELEMETRY_DB_PATH), exist_ok=True)
                cls._telemetry_instance = duckdb.connect(TELEMETRY_DB_PATH, read_only=False)
                
                # Inisialisasi tabel log_audit_token jika belum ada
                cls._telemetry_instance.execute("""
                    CREATE TABLE IF NOT EXISTS log_audit_token (
                        id VARCHAR PRIMARY KEY,
                        timestamp TIMESTAMP,
                        agent_name VARCHAR,
                        provider VARCHAR,
                        model_name VARCHAR,
                        input_tokens INTEGER,
                        output_tokens INTEGER,
                        total_tokens INTEGER,
                        latency_ms DOUBLE,
                        status VARCHAR
                    )
                """)
                logger.info(f"📊 [DuckDBPool] Telemetry DB Siap di {TELEMETRY_DB_PATH}")
            except Exception as e:
                logger.error(f"❌ [DuckDBPool] Gagal inisialisasi Telemetry DB: {e}")
                return duckdb.connect(TELEMETRY_DB_PATH, read_only=False)
        return cls._telemetry_instance

    @classmethod
    def close(cls):
        if cls._instance is not None:
            try:
                cls._instance.close()
                logger.info("🔌 [DuckDBPool] Koneksi shared DuckDB berhasil ditutup.")
            except Exception as e:
                pass
            cls._instance = None
            
        if cls._telemetry_instance is not None:
            try:
                cls._telemetry_instance.close()
                logger.info("🔌 [DuckDBPool] Koneksi Telemetry DuckDB berhasil ditutup.")
            except Exception as e:
                pass
            cls._telemetry_instance = None

def get_db(db_path: str = None) -> duckdb.DuckDBPyConnection:
    """Helper fungsi terpusat untuk mengambil koneksi DuckDB analitik read-only."""
    return DuckDBPool.get_connection(db_path)

def get_telemetry_db() -> duckdb.DuckDBPyConnection:
    """Helper fungsi terpusat untuk mengambil koneksi DuckDB telemetri read-write."""
    return DuckDBPool.get_telemetry_connection()
