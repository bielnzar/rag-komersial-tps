import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from auth import authenticate_user, create_jwt_token, get_all_users_safe

@pytest.mark.anyio
async def test_auth_unified_login_success():
    """Menguji otentikasi login terpadu untuk user dan admin."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login sebagai admin
        res_admin = await ac.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert res_admin.status_code == 200
        data_admin = res_admin.json()
        assert data_admin["user"]["role"] == "admin"
        assert "access_token" in data_admin
        # Pastikan tidak ada kebocoran hash/salt
        assert "password" not in data_admin["user"]
        assert "salt" not in data_admin["user"]
        assert "hash" not in data_admin["user"]

        # 2. Login sebagai user
        res_user = await ac.post("/api/v1/auth/login", json={"username": "user", "password": "tps123"})
        assert res_user.status_code == 200
        data_user = res_user.json()
        assert data_user["user"]["role"] == "user"
        assert "access_token" in data_user


@pytest.mark.anyio
async def test_auth_login_invalid_credentials():
    """Menguji penolakan kredensial tidak valid."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Password salah
        res = await ac.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})
        assert res.status_code == 401
        assert "salah" in res.json()["detail"].lower()

        # Username tidak ada
        res_none = await ac.post("/api/v1/auth/login", json={"username": "ghost_user", "password": "tps123"})
        assert res_none.status_code == 401


@pytest.mark.anyio
async def test_admin_endpoint_forbidden_for_regular_user():
    """Menguji proteksi 403 Forbidden pada endpoint admin jika diakses role non-admin."""
    user_token = create_jwt_token({"sub": "user", "role": "user", "name": "TPS Staff"})
    headers = {"Authorization": f"Bearer {user_token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Akses /api/v1/admin/users
        res1 = await ac.get("/api/v1/admin/users", headers=headers)
        assert res1.status_code == 403

        # Akses /api/v1/admin/keys
        res2 = await ac.get("/api/v1/admin/keys", headers=headers)
        assert res2.status_code == 403

        # Akses /api/v1/admin/table_preview
        res3 = await ac.get("/api/v1/admin/table_preview/fakta_throughput", headers=headers)
        assert res3.status_code == 403


@pytest.mark.anyio
async def test_admin_user_crud_flow():
    """Menguji alur lengkap CRUD user oleh admin (Get, Create, Edit, Delete)."""
    admin_token = create_jwt_token({"sub": "admin", "role": "admin", "name": "Administrator"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    test_username = "test_pegawai_tps"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Bersihkan dulu jika ada
        await ac.delete(f"/api/v1/admin/users/{test_username}", headers=admin_headers)

        # 2. Tambah user baru
        new_user_payload = {
            "username": test_username,
            "name": "Budi Karyawan Baru",
            "role": "user",
            "password": "password_awal_123"
        }
        res_create = await ac.post("/api/v1/admin/users", json=new_user_payload, headers=admin_headers)
        assert res_create.status_code == 200
        assert res_create.json()["status"] == "success"

        # 3. Verifikasi user baru bisa login
        res_login = await ac.post("/api/v1/auth/login", json={"username": test_username, "password": "password_awal_123"})
        assert res_login.status_code == 200
        assert res_login.json()["user"]["name"] == "Budi Karyawan Baru"

        # 4. Ambil daftar user & verifikasi no password leaks
        res_list = await ac.get("/api/v1/admin/users", headers=admin_headers)
        assert res_list.status_code == 200
        users = res_list.json()["users"]
        found = next((u for u in users if u["username"] == test_username), None)
        assert found is not None
        assert "password" not in found
        assert "hash" not in found
        assert "salt" not in found

        # 5. Update user (ganti nama & reset password)
        update_payload = {
            "name": "Budi Santoso Senior",
            "role": "user",
            "password": "password_baru_456"
        }
        res_update = await ac.put(f"/api/v1/admin/users/{test_username}", json=update_payload, headers=admin_headers)
        assert res_update.status_code == 200

        # 6. Verifikasi login dengan password baru
        res_login_old = await ac.post("/api/v1/auth/login", json={"username": test_username, "password": "password_awal_123"})
        assert res_login_old.status_code == 401

        res_login_new = await ac.post("/api/v1/auth/login", json={"username": test_username, "password": "password_baru_456"})
        assert res_login_new.status_code == 200
        assert res_login_new.json()["user"]["name"] == "Budi Santoso Senior"

        # 7. Hapus user
        res_del = await ac.delete(f"/api/v1/admin/users/{test_username}", headers=admin_headers)
        assert res_del.status_code == 200

        # 8. Verifikasi sudah tidak bisa login
        res_login_deleted = await ac.post("/api/v1/auth/login", json={"username": test_username, "password": "password_baru_456"})
        assert res_login_deleted.status_code == 401


@pytest.mark.anyio
async def test_admin_self_delete_protection():
    """Menguji proteksi bahwa admin tidak dapat menghapus akunnya sendiri."""
    admin_token = create_jwt_token({"sub": "admin", "role": "admin", "name": "Administrator"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.delete("/api/v1/admin/users/admin", headers=admin_headers)
        assert res.status_code == 400
        assert "sedang anda gunakan" in res.json()["detail"].lower()
