import os
import json
import time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
API_KEYS_FILE = CREDENTIALS_DIR / "api_keys.json"

DEFAULT_KEYS_STRUCTURE = {
    "google_gemini": [],
    "groq": [],
    "step_configs": {
        "router": {
            "provider": "google_gemini",
            "model": "gemini-3.5-flash-lite",
            "api_keys": []
        },
        "sql_gen": {
            "provider": "google_gemini",
            "model": "gemini-3.6-flash",
            "api_keys": []
        },
        "viz_gen": {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "api_keys": []
        }
    }
}

AVAILABLE_MODELS_CATALOG = {
    "google_gemini": [
        { "id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash-Lite (Ultra Hemat & Cepat)", "tier": "light" },
        { "id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash-Lite (Ringan & Cepat)", "tier": "light" },
        { "id": "gemini-3.6-flash", "name": "Gemini 3.6 Flash (Akurasi Tinggi & Standar)", "tier": "standard" },
        { "id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash (Kapasitas Menengah)", "tier": "standard" },
        { "id": "gemini-3.1-pro", "name": "Gemini 3.1 Pro (Penalaran Kompleks)", "tier": "pro" },
        { "id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro (Penalaran Lanjutan)", "tier": "pro" }
    ],
    "groq": [
        { "id": "openai/gpt-oss-20b", "name": "Groq OpenAI GPT-OSS-20B (Ultra Cepat & Stabil)", "tier": "standard" },
        { "id": "qwen/qwen3.6-27b", "name": "Groq Qwen 3.6 27B (Bahasa & Format Kuat)", "tier": "standard" },
        { "id": "openai/gpt-oss-120b", "name": "Groq OpenAI GPT-OSS-120B (Kapasitas Besar)", "tier": "pro" }
    ]
}

def get_model_catalog() -> dict:
    """Mengembalikan katalog pilihan model resmi yang didukung sistem."""
    return AVAILABLE_MODELS_CATALOG

def get_step_configs() -> dict:
    """Mengambil seluruh konfigurasi tahapan Multi-Agent (Provider, Model, dan List Kunci per-Step)."""
    data = get_all_keys()
    if "step_configs" not in data:
        data["step_configs"] = DEFAULT_KEYS_STRUCTURE["step_configs"]
        save_all_keys(data)
    return data.get("step_configs", DEFAULT_KEYS_STRUCTURE["step_configs"])

def save_step_configs(step_configs: dict):
    """Menyimpan pembaruan konfigurasi per tahapan."""
    data = get_all_keys()
    data["step_configs"] = step_configs
    save_all_keys(data)

def get_step_models() -> dict:
    """Helper kompatibilitas untuk mengambil provider dan model saja."""
    configs = get_step_configs()
    models = {}
    for step_name, cfg in configs.items():
        models[step_name] = {
            "provider": cfg.get("provider", "google_gemini"),
            "model": cfg.get("model", "gemini-3.6-flash")
        }
    return models

def get_active_key_for_step(step_name: str, provider: str) -> str:
    """
    Mengambil API Key aktif khusus untuk STEP tertentu.
    Jika step tersebut belum memiliki kunci aktif, otomatis fallback ke Kunci Pool Utama provider, lalu OS ENV.
    """
    configs = get_step_configs()
    step_cfg = configs.get(step_name, {})
    step_keys = step_cfg.get("api_keys", [])
    
    # 1. Cek Kunci Aktif Khusus Step ini
    for k in step_keys:
        if k.get("status") == "active" and k.get("key"):
            return k.get("key")
            
    # 2. Fallback ke Pool Kunci Global Provider
    pool_key = get_active_key(provider)
    if pool_key:
        return pool_key
        
    # 3. Fallback ke OS ENV
    if provider in ["google", "google_gemini"]:
        return os.getenv("GOOGLE_API_KEY")
    elif provider == "groq":
        return os.getenv("GROQ_API_KEY")
        
    return None

def record_key_usage_for_step(step_name: str, provider: str, key_val: str):
    """Mencatat jumlah penggunaan kunci di step dan di pool global."""
    if not key_val: return
    data = get_all_keys()
    
    # Update di step_configs
    configs = data.get("step_configs", {})
    if step_name in configs:
        for k in configs[step_name].get("api_keys", []):
            if k.get("key") == key_val:
                k["usage"] = k.get("usage", 0) + 1
                break
                
    # Update di global pool
    keys = data.get(provider, [])
    for k in keys:
        if k.get("key") == key_val:
            k["usage"] = k.get("usage", 0) + 1
            break
            
    save_all_keys(data)

def _ensure_file_exists():
    os.makedirs(CREDENTIALS_DIR, exist_ok=True)
    if not API_KEYS_FILE.exists():
        with open(API_KEYS_FILE, 'w') as f:
            json.dump(DEFAULT_KEYS_STRUCTURE, f, indent=2)

def get_all_keys() -> dict:
    """Membaca seluruh konfigurasi API Keys dari JSON."""
    _ensure_file_exists()
    try:
        with open(API_KEYS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Gagal membaca api_keys.json: {e}")
        return DEFAULT_KEYS_STRUCTURE

def save_all_keys(data: dict):
    """Menyimpan konfigurasi API Keys ke JSON."""
    _ensure_file_exists()
    try:
        with open(API_KEYS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Gagal menyimpan api_keys.json: {e}")

def get_active_key(provider: str) -> str:
    """
    Mengambil API Key tunggal yang aktif (ditentukan secara manual oleh Admin).
    Jika tidak ada kunci di JSON, fallback ke OS ENV variabel utama.
    """
    data = get_all_keys()
    keys = data.get(provider, [])
    
    # Ambil kunci pertama yang berstatus 'active'
    for k in keys:
        if k.get("status") == "active" and k.get("key"):
            return k.get("key")
                
    # Fallback OS ENV jika JSON tidak memiliki kunci aktif
    if provider == "google_gemini":
        return os.getenv("GOOGLE_API_KEY")
    elif provider == "groq":
        return os.getenv("GROQ_API_KEY")
        
    return None

def record_key_usage(provider: str, key_val: str):
    """Mencatat jumlah penggunaan (usage counter) pada kunci."""
    if not key_val: return
    data = get_all_keys()
    keys = data.get(provider, [])
    updated = False
    for k in keys:
        if k.get("key") == key_val:
            k["usage"] = k.get("usage", 0) + 1
            updated = True
            break
    if updated:
        save_all_keys(data)

def mark_key_cooldown(provider: str, key_val: str, cooldown_seconds: int = 60):
    """Menandai kunci terkena 429 Limit dan masuk cooldown sementara."""
    if not key_val: return
    data = get_all_keys()
    keys = data.get(provider, [])
    updated = False
    for k in keys:
        if k.get("key") == key_val:
            k["cooldown_until"] = time.time() + cooldown_seconds
            updated = True
            logger.warning(f"⏳ API Key {provider} diset COOLDOWN selama {cooldown_seconds} detik.")
            break
    if updated:
        save_all_keys(data)
