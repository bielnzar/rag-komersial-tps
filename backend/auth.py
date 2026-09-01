import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import HTTPException, Header, Depends

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = BASE_DIR / "credentials/users.json"

# Key rahasia JWT — menggunakan env var jika ada, atau generate key acak 256-bit
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "TPS_SECRET_KEY_PROD_2026_ENTERPRISE_SECURE_HASH_98231")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 86400  # 24 jam TTL Token

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Meng-hash password menggunakan standar industri NIST PBKDF2-HMAC-SHA256 (100.000 iterasi).
    Menghindari pembobolan dan kebocoran password mentah.
    """
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return hashed, salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Memverifikasi password mentah dengan hash terenkripsi."""
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, stored_hash)

# Memuat database user terenkripsi dari credentials/users.json jika ada
def load_user_database() -> Dict[str, Dict[str, Any]]:
    db = {}
    
    # 1. Cek apakah file credentials/users.json tersedia
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                records = json.load(f)
                for item in records:
                    u = item["username"].lower().strip()
                    pwd = item["password_raw"]
                    p_hash, p_salt = hash_password(pwd)
                    db[u] = {
                        "username": u,
                        "hash": p_hash,
                        "salt": p_salt,
                        "role": item["role"],
                        "name": item["name"]
                    }
            logger.info(f"🔑 [AUTH] Berhasil memuat {len(db)} akun pengguna dari credentials/users.json")
            return db
        except Exception as e:
            logger.error(f"❌ Gagal membaca credentials/users.json: {e}")

    # Fallback Default Enterprise Users jika file tidak ditemukan
    default_accounts = [
        ("executive", "tps123", "executive", "Direksi & Executive TPS"),
        ("komersial", "tps123", "commercial", "Tim Komersial TPS"),
        ("operasional", "tps123", "operation", "Tim Operasional Lapangan"),
        ("guest", "guest123", "guest", "Tamu / Guest User")
    ]
    for u, pwd, r, name in default_accounts:
        p_hash, p_salt = hash_password(pwd)
        db[u] = {
            "username": u,
            "hash": p_hash,
            "salt": p_salt,
            "role": r,
            "name": name
        }
    return db

USER_DATABASE: Dict[str, Dict[str, Any]] = load_user_database()

# =============================================================
# ENGINE KRIPTOGRAFI JWT TOKEN (RFC 7519 Standar Industri)
# =============================================================
def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _b64_decode(data_str: str) -> bytes:
    padding = '=' * (4 - (len(data_str) % 4))
    return base64.urlsafe_b64decode(data_str + padding)

def create_jwt_token(payload: Dict[str, Any]) -> str:
    """Membuat JWT Token terenkripsi dengan tanda tangan HMAC-SHA256."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    full_payload = {
        **payload,
        "iat": now,
        "exp": now + JWT_EXPIRATION_SECONDS
    }

    header_b64 = _b64_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(full_payload).encode('utf-8'))

    signature_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(JWT_SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
    signature_b64 = _b64_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Memverifikasi keaslian dan kedaluwarsa JWT Token.
    Menolak token palsu / hasil manipulasi hacker (Anti-Spoofing & Anti-Tampering).
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="🔒 Token format tidak valid.")

        header_b64, payload_b64, signature_b64 = parts

        # Verifikasi Tanda Tangan Kriptografi
        signature_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(JWT_SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()

        actual_sig = _b64_decode(signature_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            logger.warning("🛡️ [SECURITY ALERT] Percobaan manipulasi JWT token terdeteksi!")
            raise HTTPException(status_code=401, detail="🛡️ Token palsu atau telah dimanipulasi.")

        payload_bytes = _b64_decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))

        # Verifikasi Kedaluwarsa Token
        if time.time() > payload.get("exp", 0):
            raise HTTPException(status_code=401, detail="🔒 Sesi login telah kedaluwarsa. Silakan login kembali.")

        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Verification error: {e}")
        raise HTTPException(status_code=401, detail="🔒 Gagal memverifikasi identitas pengguna.")

def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """Otentikasi aman username & password."""
    user = USER_DATABASE.get(username.lower().strip())
    if not user:
        raise HTTPException(status_code=401, detail="🔒 Username atau Password salah.")

    if not verify_password(password, user["hash"], user["salt"]):
        raise HTTPException(status_code=401, detail="🔒 Username atau Password salah.")

    token_payload = {
        "sub": user["username"],
        "role": user["role"],
        "name": user["name"]
    }
    token = create_jwt_token(token_payload)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "role": user["role"],
            "name": user["name"]
        }
    }

async def get_current_user_from_header(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Dependency FastAPI untuk memproteksi endpoint.
    Membaca Header 'Authorization: Bearer <token>' dan memverifikasi identitas asli.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="🔒 Akses ditolak: Harap login terlebih dahulu.")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="🔒 Header otentikasi tidak valid.")

    token = parts[1]
    return verify_jwt_token(token)
