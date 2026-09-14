import hashlib
import json
import logging
import math
import os
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = BASE_DIR / "data/sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Opsi import redis dengan fallback aman jika redis-py belum diinstall
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


def sanitize_json_obj(obj: Any) -> Any:
    """
    Mengganti nilai float NaN / Infinity secara rekursif menjadi None (JSON null).
    Mencegah crash 'ValueError: Out of range float values are not JSON compliant'.
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_json_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json_obj(v) for v in obj]
    return obj


# =============================================================
# TRUE SEMANTIC CANONICAL HASHING ENGINE (TUGAS 3.1)
# =============================================================

PHRASE_REPLACEMENTS = [
    (r'\b(market\s+share|pangsa\s+pasar)\b', ' market_share '),
    (r'\b(peti\s+kemas|petikemas)\b', ' petikemas '),
    (r'\b(antar\s+pulau|antarpulau)\b', ' domestik '),
    (r'\b(rata\s+rata|rataan)\b', ' rata '),
    (r'\b(line\s+operator|operator\s+kapal|operator\s+pelayaran|perusahaan\s+pelayaran)\b', ' operator '),
    (r'\b(cma\s+cgm)\b', ' cma '),
    (r'\b(maersk\s+line|maersk)\b', ' msk '),
    (r'\b(ocean\s+network\s+express)\b', ' one '),
    (r'\b(samudera\s+shipping)\b', ' ssl '),
    (r'\b(cosco\s+shipping)\b', ' cosco '),
    (r'\b(tempuran\s+emas)\b', ' temas '),
    (r'\b(salam\s+pacific)\b', ' spil '),
    (r'\b(tanto\s+intim)\b', ' tanto ')
]

SYNONYM_MAP = {
    # Metrics
    'throughput': 'throughput', 'arus': 'throughput', 'volume': 'throughput',
    'teus': 'throughput', 'teu': 'throughput', 'petikemas': 'throughput',
    'kontainer': 'throughput', 'container': 'throughput',
    'actual': 'throughput', 'realisasi': 'throughput', 'real': 'throughput',
    'kegiatan': 'throughput', 'aktivitas': 'throughput', 'muatan': 'throughput',
    'revenue': 'revenue', 'pendapatan': 'revenue', 'komersial': 'revenue',
    'omset': 'revenue', 'omzet': 'revenue', 'uang': 'revenue', 'biaya': 'revenue',
    'market_share': 'market_share', 'pangsa': 'market_share', 'share': 'market_share',
    'transhipment': 'transhipment', 'alih': 'transhipment',
    'call': 'call', 'kunjungan': 'call',
    'bmph': 'bmph',
    'rute': 'rute', 'route': 'rute', 'tujuan': 'rute',
    'box': 'box', 'boxes': 'box',
    'diskon': 'discount', 'keringanan': 'discount', 'restitusi': 'discount',
    
    # Segment
    'internasional': 'int', 'international': 'int', 'int': 'int',
    'ekspor': 'int', 'impor': 'int', 'export': 'int', 'import': 'int',
    'domestik': 'dom', 'domestic': 'dom', 'dom': 'dom',
    
    # Operators
    'cma': 'cma', 'msk': 'msk', 'msc': 'msc', 'one': 'one', 'emc': 'emc', 'evergreen': 'emc',
    'ool': 'ool', 'oocl': 'ool', 'pil': 'pil', 'hmm': 'hmm', 'sitc': 'sitc', 'ssl': 'ssl',
    'samudera': 'ssl', 'meratus': 'meratus', 'spil': 'spil', 'tanto': 'tanto',
    'temas': 'temas', 'cosco': 'cosco', 'wanhai': 'wanhai', 'zim': 'zim', 'kmtc': 'kmtc',
    
    # Ranks & Modifiers
    'top': 'top', 'terbesar': 'top', 'terbanyak': 'top', 'tertinggi': 'top',
    'teratas': 'top', 'ranking': 'top', 'peringkat': 'top',
    'terkecil': 'bottom', 'terendah': 'bottom',
    'rata': 'avg', 'average': 'avg', 'avg': 'avg',
    'grafik': 'chart', 'chart': 'chart', 'diagram': 'chart', 'plot': 'chart',
    'tren': 'chart', 'trend': 'chart'
}

STOPWORDS = {
    'berapa', 'apakah', 'apa', 'siapa', 'mana', 'bagaimana', 'coba', 'tolong', 'tampilkan',
    'lihat', 'lihatkan', 'tunjukkan', 'pada', 'di', 'ke', 'dari', 'untuk', 'oleh', 'yang',
    'nya', 'ada', 'lah', 'kah', 'dong', 'sih', 'ya', 'dan', 'atau', 'dengan', 'beserta',
    'tahun', 'thn', 'bulan', 'bln', 'ini', 'itu', 'tersebut', 'terkait', 'data', 'informasi',
    'hasil', 'total', 'jumlah', 'operator', 'daftar', 'perusahaan', 'sebutkan', 'berikan',
    'kategori', 'pasar', 'masing', 'nominal', 'saja', 'line', 'sheet', 'tiap', 'setiap', 'semua'
}

def clean_word(w: str) -> str:
    """Membersihkan klitika/akhiran kata bahasa Indonesia (-nya, -lah, -kah, -pun)."""
    for suf in ['nya', 'lah', 'kah', 'pun']:
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[:-len(suf)]
    return w

def extract_canonical_descriptor(query: str) -> str:
    """
    Mengekstrak deskriptor semantik canonical dari teks kueri analitik PT TPS.
    Menerjemahkan variasi kalimat berbeda frasa menjadi format identik.
    Contoh:
    - 'Berapa total actual throughput petikemas internasional dan domestik tahun 2024?' -> 'yr:2024|lim:none|concepts:dom_int_throughput'
    - 'Throughput internasional dan domestik tahun 2024 berapa?' -> 'yr:2024|lim:none|concepts:dom_int_throughput'
    """
    q = query.lower().strip()
    for pattern, repl in PHRASE_REPLACEMENTS:
        q = re.sub(pattern, repl, q)
        
    q_clean = re.sub(r'[^a-z0-9_\s]', ' ', q)
    raw_words = q_clean.split()
    
    # 1. Ekstraksi Tahun (2020 - 2030)
    years = re.findall(r'\b(202[0-9]|2030)\b', q)
    yr = years[0] if years else 'none'
    
    # 2. Ekstraksi Limit (Top N / N Teratas / N Operator Terbesar)
    limits = re.findall(r'\b(?:top|peringkat)\s*([0-9]+)\b|\b([0-9]+)\s*(?:line\s+)?(?:operator|terbesar|teratas|terbanyak|tertinggi|besar)\b', q)
    lim = 'none'
    if limits:
        lim = limits[0][0] or limits[0][1] or 'none'
    
    # 3. Ekstraksi Konsep Semantik & Sinonim
    concepts = set()
    for raw in raw_words:
        w = clean_word(raw)
        if w in SYNONYM_MAP:
            concepts.add(SYNONYM_MAP[w])
        elif w not in STOPWORDS and not re.match(r'^(202[0-9]|2030|[0-9]+)$', w):
            concepts.add(w)
            
    if not concepts and yr == 'none':
        return "raw:" + " ".join(raw_words)
        
    sorted_concepts = '_'.join(sorted(concepts))
    return f"yr:{yr}|lim:{lim}|concepts:{sorted_concepts}"


class SemanticCache:
    """
    Manajer Redis Semantic Cache, Persistent Multi-Session History & Security Limiter.
    - Menggunakan Redis jika server Redis berjalan di localhost:6379.
    - Persistent File Storage di data/sessions/ agar riwayat obrolan aman selamanya.
    - Menyimpan respon chat (Teks Naratif, SQL Executed, ECharts Config, Raw Data) dengan TTL 24 jam.
    - Menyimpan Sesi Percakapan Jangka Panjang per User / Role.
    """

    DEFAULT_RBAC_RULES = {
        "admin": ["fakta_vessel", "fakta_throughput", "fakta_market_share", "fakta_transhipment", "fakta_vessel_service", "fakta_komersial_dashboard", "fakta_realisasi_uc", "fakta_overview_box", "fakta_rest_n_disc", "dim_vessel_operator"],
        "user": ["fakta_vessel", "fakta_throughput", "fakta_market_share", "fakta_transhipment", "fakta_vessel_service", "fakta_komersial_dashboard", "fakta_overview_box", "fakta_rest_n_disc", "dim_vessel_operator"],
        "executive": ["fakta_vessel", "fakta_throughput", "fakta_market_share", "fakta_transhipment", "fakta_vessel_service", "fakta_komersial_dashboard", "fakta_realisasi_uc", "fakta_overview_box", "fakta_rest_n_disc", "dim_vessel_operator"],
        "commercial": ["fakta_vessel", "fakta_throughput", "fakta_market_share", "fakta_transhipment", "fakta_vessel_service", "fakta_komersial_dashboard", "fakta_overview_box", "fakta_rest_n_disc", "dim_vessel_operator"],
        "operation": ["fakta_vessel", "fakta_vessel_service", "fakta_throughput", "fakta_overview_box", "dim_vessel_operator"],
        "guest": ["fakta_throughput", "fakta_overview_box", "dim_vessel_operator"]
    }

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, ttl_seconds: int = 86400):
        self.ttl_seconds = ttl_seconds
        self.redis_client = None
        self.in_memory_cache: Dict[str, Dict[str, Any]] = {}
        self.in_memory_sessions: Dict[str, List[Dict[str, Any]]] = {}
        self.in_memory_rate_limits: Dict[str, Dict[str, Any]] = {}

        self.cache_file = SESSIONS_DIR / "semantic_cache_store.json"
        self._load_disk_cache()

        if REDIS_AVAILABLE:
            try:
                client = redis.Redis(host=host, port=port, db=db, socket_timeout=1.0)
                client.ping()
                self.redis_client = client
                logger.info(f"⚡ [RedisCache] Terhubung ke Redis Server ({host}:{port}/db{db}). TTL: {ttl_seconds}s")
            except Exception as e:
                logger.warning(f"⚠️ [RedisCache] Redis server tidak tersedia ({e}). Menggunakan Fallback Storage.")

    def _load_disk_cache(self):
        """Memuat semantic cache dari disk agar cache tetap awet meskipun server restart / reload."""
        if self.cache_file.exists():
            try:
                txt = self.cache_file.read_text(encoding='utf-8')
                data = json.loads(txt)
                now = time.time()
                valid_entries = {}
                for k, v in data.items():
                    if now - v.get("timestamp", 0) < self.ttl_seconds:
                        valid_entries[k] = v
                self.in_memory_cache.update(valid_entries)
                logger.info(f"📂 [CacheFile] Memuat {len(valid_entries)} entri cache dari {self.cache_file.name}")
            except Exception as e:
                logger.error(f"❌ [CacheFile] Gagal membaca disk cache: {e}")

    def _save_disk_cache(self):
        """Menyimpan semantic cache ke disk."""
        try:
            now = time.time()
            valid_entries = {k: v for k, v in self.in_memory_cache.items() if now - v.get("timestamp", 0) < self.ttl_seconds}
            self.cache_file.write_text(json.dumps(valid_entries, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"❌ [CacheFile] Gagal menulis disk cache: {e}")

    def get_canonical_descriptor(self, query: str) -> str:
        """Helper publik untuk melihat deskriptor semantik canonical."""
        return extract_canonical_descriptor(query)

    def _normalize_key(self, query: str) -> str:
        """
        Membuat hash kunci ter-normalisasi berbasis True Semantic Hashing (Tugas 3.1).
        Mengekstrak konsep semantik esensial (Tahun, Limit, Operator, Metrik) sehingga variasi
        kalimat yang berbeda frasa namun bermakna sama menghasilkan cache key yang identik (100% Cache Hit).
        """
        descriptor = extract_canonical_descriptor(query)
        hash_val = hashlib.md5(descriptor.encode("utf-8")).hexdigest()
        return f"tps_canon:{hash_val}"

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Mengambil data respon dari cache (Redis atau In-Memory)."""
        cache_key = self._normalize_key(query)

        if self.redis_client:
            try:
                data_bytes = self.redis_client.get(cache_key)
                if data_bytes:
                    logger.info(f"⚡ [REDIS HIT] Kunci: {cache_key} | Query: '{query}'")
                    return json.loads(data_bytes.decode("utf-8"))
            except Exception as e:
                logger.error(f"❌ [RedisCache] Gagal membaca Redis: {e}")

        if cache_key in self.in_memory_cache:
            entry = self.in_memory_cache[cache_key]
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                logger.info(f"⚡ [IN-MEMORY CACHE HIT] Kunci: {cache_key} | Query: '{query}'")
                return entry["payload"]
            else:
                del self.in_memory_cache[cache_key]
                self._save_disk_cache()

        return None

    def set(self, query: str, payload: Dict[str, Any]):
        """Menyimpan data respon ke cache (Redis atau In-Memory)."""
        cache_key = self._normalize_key(query)

        clean_payload = sanitize_json_obj(payload)

        if self.redis_client:
            try:
                json_data = json.dumps(clean_payload)
                self.redis_client.set(cache_key, json_data, ex=self.ttl_seconds)
                logger.info(f"💾 [REDIS SAVE] Kunci: {cache_key}")
                return
            except Exception as e:
                logger.error(f"❌ [RedisCache] Gagal menyimpan ke Redis: {e}")

        self.in_memory_cache[cache_key] = {
            "timestamp": time.time(),
            "payload": clean_payload
        }
        self._save_disk_cache()
        logger.info(f"💾 [IN-MEMORY CACHE SAVE] Kunci: {cache_key}")

    # =============================================================
    # PERSISTENT MULTI-SESSION CHAT HISTORY (Seperti ChatGPT / Claude)
    # =============================================================
    def _get_user_session_file(self, username: str) -> Path:
        return SESSIONS_DIR / f"user_{username}.json"

    def get_user_sessions(self, username: str) -> List[Dict[str, Any]]:
        """Mengambil daftar seluruh thread percakapan milik username/role."""
        redis_key = f"tps_user_sessions:{username}"

        if self.redis_client:
            try:
                raw_data = self.redis_client.get(redis_key)
                if raw_data:
                    return json.loads(raw_data.decode("utf-8"))
            except Exception as e:
                logger.error(f"❌ [RedisSessions] Gagal membaca user sessions: {e}")

        # Fallback Disk Persistence File
        session_file = self._get_user_session_file(username)
        if session_file.exists():
            try:
                txt = session_file.read_text(encoding='utf-8')
                cleaned_txt = re.sub(r':\s*NaN\b', ': null', txt)
                data = json.loads(cleaned_txt)
                return sanitize_json_obj(data.get("sessions", []))
            except Exception as e:
                logger.error(f"❌ Gagal membaca session file '{session_file}': {e}")
        return []

    def get_session_messages(self, username: str, session_id: str) -> List[Dict[str, Any]]:
        """Mengambil detail daftar pesan dalam satu sesi percakapan."""
        sessions = self.get_user_sessions(username)
        for s in sessions:
            if s.get("session_id") == session_id:
                return s.get("messages", [])
        return []

    def save_chat_message_to_session(
        self, 
        username: str, 
        role: str, 
        session_id: str, 
        user_query: str, 
        ai_answer: str, 
        sql: Optional[str] = None, 
        data: Optional[list] = None, 
        chart_config: Optional[dict] = None
    ):
        """Menyimpan pasangan pesan User & AI ke dalam sesi obrolan (Persistent Storage)."""
        sessions = self.get_user_sessions(username)
        now_str = time.strftime("%H:%M")
        date_str = time.strftime("%Y-%m-%d %H:%M")

        target_session = None
        for s in sessions:
            if s.get("session_id") == session_id:
                target_session = s
                break

        if not target_session:
            title = user_query[:35] + "..." if len(user_query) > 35 else user_query
            target_session = {
                "session_id": session_id,
                "title": title,
                "created_at": date_str,
                "role": role,
                "messages": []
            }
            sessions.insert(0, target_session)

        # Sanitasi data mentah dari NaN/inf
        clean_data = sanitize_json_obj(data) if data else None
        clean_chart = sanitize_json_obj(chart_config) if chart_config else None

        target_session["messages"].append({
            "role": "user",
            "content": user_query,
            "timestamp": now_str
        })

        target_session["messages"].append({
            "role": "assistant",
            "userQuery": user_query,
            "content": ai_answer,
            "sql": sql,
            "data": clean_data,
            "chartConfig": clean_chart,
            "timestamp": now_str
        })

        clean_sessions = sanitize_json_obj(sessions)

        if self.redis_client:
            try:
                redis_key = f"tps_user_sessions:{username}"
                self.redis_client.set(redis_key, json.dumps(clean_sessions))
            except Exception as e:
                logger.error(f"❌ [RedisSaveSession] Error: {e}")

        try:
            session_file = self._get_user_session_file(username)
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump({"username": username, "updated_at": date_str, "sessions": clean_sessions}, f, indent=2)
            logger.info(f"💬 [CHAT HISTORY SAVED] User '{username}' | Session '{session_id}' ({len(target_session['messages'])} msgs)")
        except Exception as e:
            logger.error(f"❌ [DiskSaveSession] Error: {e}")

    def delete_user_session(self, username: str, session_id: str) -> bool:
        """Menghapus satu thread percakapan milik pengguna."""
        sessions = self.get_user_sessions(username)
        updated_sessions = [s for s in sessions if s.get("session_id") != session_id]

        if self.redis_client:
            try:
                redis_key = f"tps_user_sessions:{username}"
                self.redis_client.set(redis_key, json.dumps(updated_sessions))
                self.redis_client.delete(f"tps_session:{session_id}")
            except Exception:
                pass

        try:
            session_file = self._get_user_session_file(username)
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump({"username": username, "sessions": updated_sessions}, f, indent=2)
            return True
        except Exception:
            return False

    def get_session_history(self, session_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        """Mengambil riwayat percakapan terakhir pengguna untuk prompt context."""
        session_key = f"tps_session:{session_id}"

        if self.redis_client:
            try:
                raw_items = self.redis_client.lrange(session_key, -limit, -1)
                if raw_items:
                    return [json.loads(item.decode("utf-8")) for item in raw_items]
            except Exception:
                pass

        return []

    def save_session_message(self, session_id: str, role: str, content: str, sql: Optional[str] = None):
        """Simpan konteks pesan terdekat."""
        session_key = f"tps_session:{session_id}"
        message_entry = {
            "role": role,
            "content": content,
            "sql": sql,
            "timestamp": time.time()
        }

        if self.redis_client:
            try:
                self.redis_client.rpush(session_key, json.dumps(message_entry))
                self.redis_client.expire(session_key, self.ttl_seconds)
            except Exception:
                pass

    # =============================================================
    # SHARED SCHEMA CATALOG CACHE
    # =============================================================
    def get_schema_cache(self, sub_key: str) -> Optional[Any]:
        cache_key = f"tps_schema:{sub_key}"
        if self.redis_client:
            try:
                data_bytes = self.redis_client.get(cache_key)
                if data_bytes:
                    return json.loads(data_bytes.decode("utf-8"))
            except Exception:
                pass

        if cache_key in self.in_memory_cache:
            return self.in_memory_cache[cache_key]["payload"]
        return None

    def set_schema_cache(self, sub_key: str, value: Any, ttl_seconds: int = 604800):
        cache_key = f"tps_schema:{sub_key}"
        clean_val = sanitize_json_obj(value)

        if self.redis_client:
            try:
                json_data = json.dumps(clean_val)
                self.redis_client.set(cache_key, json_data, ex=ttl_seconds)
                return
            except Exception:
                pass

        self.in_memory_cache[cache_key] = {
            "timestamp": time.time(),
            "payload": clean_val
        }

    # =============================================================
    # API RATE LIMITER
    # =============================================================
    def check_rate_limit(self, client_id: str, max_requests: int = 30, window_seconds: int = 60) -> tuple[bool, int]:
        rate_key = f"tps_rate:{client_id}"

        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr(rate_key)
                pipe.ttl(rate_key)
                res = pipe.execute()
                current_count = res[0]
                ttl = res[1]

                if ttl == -1:
                    self.redis_client.expire(rate_key, window_seconds)

                if current_count > max_requests:
                    return False, current_count
                return True, current_count
            except Exception:
                pass

        now = time.time()
        if client_id not in self.in_memory_rate_limits or (now - self.in_memory_rate_limits[client_id]["window_start"]) > window_seconds:
            self.in_memory_rate_limits[client_id] = {
                "window_start": now,
                "count": 1
            }
            return True, 1

        self.in_memory_rate_limits[client_id]["count"] += 1
        current_count = self.in_memory_rate_limits[client_id]["count"]

        if current_count > max_requests:
            return False, current_count

        return True, current_count

    # =============================================================
    # USER ROLE & RBAC PERMISSIONS CACHE
    # =============================================================
    def get_role_permissions(self, role: str) -> List[str]:
        role_clean = role.strip().lower() if role else "guest"
        rbac_key = f"tps_rbac:{role_clean}"

        if self.redis_client:
            try:
                data_bytes = self.redis_client.get(rbac_key)
                if data_bytes:
                    return json.loads(data_bytes.decode("utf-8"))
            except Exception:
                pass

        return self.DEFAULT_RBAC_RULES.get(role_clean, self.DEFAULT_RBAC_RULES["guest"])

    def clear(self):
        """Membersihkan seluruh isi semantic cache (Redis, memory, dan file disk)."""
        if self.redis_client:
            try:
                keys = self.redis_client.keys("tps_*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception:
                pass
        self.in_memory_cache.clear()
        self.in_memory_rate_limits.clear()
        try:
            if self.cache_file.exists():
                self.cache_file.write_text("{}", encoding='utf-8')
        except Exception as e:
            logger.error(f"Gagal mengosongkan cache file disk: {e}")
        logger.info("🧹 [Cache, Schema, Semantic & RateLimit] Seluruh isi cache telah dibersihkan total.")


# Instansiasi Singleton Global Cache & Session Manager
semantic_cache = SemanticCache()
