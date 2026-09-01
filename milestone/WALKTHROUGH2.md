# 🔎 Audit Proyek: RAG Komersial TPS — Status, Celah, dan Rencana Optimasi

Audit terakhir: **28 Agustus 2026, 08:44 WIB**

---

## 1. Ringkasan Status Per-Milestone

| Milestone | Status | Detail |
|---|---|---|
| **M1** — ETL Medallion Pipeline | ✅ Selesai | Bronze → Silver → Gold → DuckDB. 3 transformer aktif. |
| **M2** — Text-to-SQL Core | ✅ Selesai | FastAPI + LangGraph (`sql_gen` → `execute_sql`) |
| **M3** — Self-Healing & Semantic | ✅ Selesai | Max 3 retry, Glosarium Bisnis di prompt, deteksi data kosong |
| **M4** — Visualisasi ECharts | ✅ Selesai | Dedicated Groq ECharts Generator (`chart_gen.py`) + Compact CSV Payload |
| **M5** — Frontend UI/UX | ✅ Selesai | Vue 3 + Sidebar Chat History (ChatGPT Style) + Login Gate + JWT + RBAC |

---

## 2. Pekerjaan yang SUDAH Selesai (✅)

### Backend — AI Agents (`backend/agents/`)

- [x] **Router Agent** (`router.py`) — Gemini 3.6 Flash menganalisis pertanyaan pengguna dan memilih tabel DuckDB relevan sebelum memasuki SQL Gen. Fallback ke semua tabel jika output Router tidak valid.
- [x] **SQL Generator** (`sql_gen.py`) — Gemini 3.6 Flash merakit DuckDB SQL murni. Dynamic schema injection dari `information_schema.columns` yang difilter oleh `relevant_tables` dari Router.
- [x] **Hard Rules Sanitizer Dual-Layer** (`sanitizer.py`) — Input Guard (cek `user_query` terhadap `;`, `DROP`, `DELETE`, `--`, `/*`) + Output Guard (cek `generated_sql`). Jika terdeteksi serangan, `correction_attempts` dipaksa ke 3 → langsung blokir.
- [x] **Execute SQL** (`execute.py`) — Koneksi DuckDB read-only, deteksi data kosong (0 baris atau aggregat null), defense-in-depth guard terhadap `SANITIZER BLOCKED`.
- [x] **Visualization Generator** (`viz_gen.py`) — Diganti dari Groq (`openai/gpt-oss-20b`) ke **Gemini 3.6 Flash** untuk menghindari Groq TPM limit 8000 token. Pydantic `VizOutput` → `answer` + `echarts_config`. Fallback narasi jika LLM gagal parse.
- [x] **LangGraph State Machine** (`graph.py`) — `START → router → sql_gen → sanitizer → [execute_sql | viz_gen] → viz_gen → END`. Dual conditional edges: `should_continue_sanitizer` (3-way: sql_gen/execute_sql/viz_gen) dan `should_continue` (2-way: sql_gen/viz_gen).

### Backend — ETL (`backend/etl/`)

- [x] 3 transformer aktif: `proses_vessel`, `proses_throughput`, `proses_market_share`
- [x] Normalisasi `DOMESTIK → DOMESTIC` via `_normalisasi_nama_sheet()`
- [x] Unpivot otomatis untuk kolom pivot `(TEUS)` pada Market Share
- [x] Logging RotatingFileHandler + debug CSV checkpoint per layer

### Backend — Lainnya

- [x] Unit tests: `test_etl.py` (4 test), `test_router.py` (1 test), `test_sanitizer.py` (5 test termasuk prompt injection)
- [x] Path absolut otomatis `BASE_DIR` di semua file agent & ETL
- [x] `lihatdata.py` helper script untuk inspeksi DuckDB

### Frontend (`frontend/`)

- [x] Vue 3 + Vite + Tailwind CSS + ECharts CDN
- [x] 8 komponen: `Navbar`, `PromptSuggestions`, `ChatMessage`, `ChatInput`, `SqlAccordion`, `EChartsViewer`, `DataTableModal`, `Icons.js`
- [x] Executive Dark Theme (Slate Maritime) dengan glassmorphism ringan
- [x] Markdown parser (bold/italic) pada bubble jawaban AI
- [x] Dynamic rotating loading messages (bukan Pipeline jargon teknis)
- [x] ECharts `sanitizeChartOption()` — auto-fix warna gelap, paksa label angka, grid padding
- [x] Logo TPS fallback otomatis (ikon kapal jika gambar belum ada)
- [x] Proxy `/api` → `localhost:8000` di `vite.config.js`

---

## 3. Pekerjaan yang BELUM Selesai (❌)

### 🔴 Prioritas Tinggi

| # | Item | Dampak | Estimasi Effort |
|---|---|---|---|
| 1 | **6 dari 9 file Excel belum punya transformer ETL** | LLM hanya bisa jawab tentang vessel, throughput, market share — TIDAK bisa menjawab tentang Transhipment (1.4 MB, data terbesar!), Komersial Dashboard, Realisasi UC, RestNDisc, VESSEL SERVICE, OVERVIEW BOX | Besar (perlu analisis skema tiap Excel + tulis transformer baru) |
| 2 | **Dokumen `WALKTHROUGH.md` belum diperbarui** (lihat Isu #1 di bawah) | Diagram arsitektur & tabel Tech Stack masih menunjukkan status lama (Groq, belum ada Router, belum ada Sanitizer) — menyesatkan pembaca/penguji | Kecil |

### 🟡 Prioritas Sedang

| # | Item | Dampak |
|---|---|---|
| 3 | **RBAC (Role-Based Access Control)** — `user_id` & `role` diterima di request tapi TIDAK digunakan di LangGraph | Semua user dapat akses seluruh data tanpa filter |
| 4 | **Redis Semantic Cache** — disebut di arsitektur tapi belum ada | Setiap pertanyaan identik mengonsumsi token LLM baru |
| 5 | **Validasi Data Contract (Pandera/Pydantic)** — ETL hanya cleaning manual | Tidak ada jaminan skema data konsisten antar-run ETL |
| 6 | **CORS `allow_origins=["*"]`** — harus diubah untuk production | Kerentanan keamanan jika di-deploy ke server publik |

---

## 4. ISU & CELAH yang Ditemukan 🚨

### ISU #1 — Dokumen `WALKTHROUGH.md` Sudah Kedaluwarsa (STALE DOCUMENTATION)

> [!WARNING]
> File [WALKTHROUGH.md](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/milestone/WALKTHROUGH.md) memiliki **beberapa informasi yang sudah tidak akurat** setelah perubahan terakhir kita:

| Baris | Isi Lama (Kedaluwarsa) | Fakta Terkini |
|---|---|---|
| L32 | `viz_gen (Groq GPT-OSS-20B)` | **Sudah diganti ke Gemini 3.6 Flash** sejak sesi terakhir |
| L65 | Tidak ada `router.py` dan `sanitizer.py` di struktur dir | **Keduanya sudah ada** dan aktif di LangGraph graph |
| L193 | `AgentState` tidak mencantumkan `relevant_tables` | **Sudah ditambahkan** sebagai `Optional[List[str]]` |
| L197-204 | Diagram state machine: `sql_gen → execute_sql → viz_gen` (linear) | **Sudah berubah** ke `router → sql_gen → sanitizer → [execute_sql/viz_gen] → viz_gen` |
| L230 | `openai/gpt-oss-20b` via `langchain-groq` | **Sudah diganti** ke `gemini-3.6-flash` via `langchain-google-genai` |
| L236 | Catatan tentang "Dual-LLM strategy (Gemini + Groq)" | **Sudah Single-LLM**: semua node kini menggunakan Gemini 3.6 Flash |
| L281 | M5 Frontend: ✅ Selesai tapi tidak ada detail komponen | **Perlu ditambahkan** daftar 8 komponen Vue yang sudah dibuat |
| L304 | "Hard Rules Sanitizer belum ada" | **Sudah ada** dengan Dual-Layer Guard (Input + Output) |
| L293-295 | "Belum ada Router Agent" | **Sudah ada** di `router.py` |
| L340-345 | Tech Stack: Frontend ❌, Cache ❌, LLM Viz Groq ⚠️ | Frontend ✅, LLM Viz **Gemini** (bukan Groq lagi) |

---

### ISU #2 — Komentar Fallback di `viz_gen.py` Masih Menyebut "Groq"

> [!NOTE]
> Di [viz_gen.py](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/viz_gen.py#L79-L80), komentar pada blok `except` masih tertulis:
> ```python
> # Fallback jika Groq gagal parse tool arguments
> logger_msg = f"⚠️ Groq tool parse error: {e}..."
> ```
> Padahal LLM sudah diubah ke **Gemini 3.6 Flash**. Komentar dan log message ini harus diperbarui agar tidak membingungkan developer.

---

### ISU #3 — `initial_state` di `main.py` Tidak Menyertakan `echarts_config`

> [!NOTE]
> Di [main.py](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/main.py#L55-L63), `initial_state` tidak menyertakan key `echarts_config`. Meskipun LangGraph TypedDict bersifat toleran, ini bisa menyebabkan peringatan atau perilaku tidak terduga jika state diakses sebelum `viz_gen` mengisinya.

---

### ISU #4 — `data/status` Endpoint Masih Di-Mock

> [!NOTE]
> Endpoint [GET /api/v1/data/status](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/main.py#L80-L90) mengembalikan data statis hardcoded (`last_sync: "2024-10-01"`). Sebaiknya query langsung ke DuckDB untuk menampilkan jumlah tabel & baris aktual.

---

### ISU #5 — Sanitizer `REPLACE` Keyword Bisa False Positive

> [!WARNING]
> Di [sanitizer.py](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/sanitizer.py#L17), `r'\bREPLACE\b'` ada di `FORBIDDEN_KEYWORDS`. Namun DuckDB menggunakan fungsi `REPLACE()` yang sah (string manipulation). Jika LLM merakit query seperti `SELECT REPLACE(lop, 'x', 'y')`, Sanitizer akan mem-blokir secara keliru.
>
> **Saran:** Hapus `REPLACE` dari forbidden list, atau ubah aturan agar hanya blokir `CREATE OR REPLACE` (bukan fungsi `REPLACE()` biasa).

---

### ISU #6 — Koneksi DuckDB Dibuka Berulang Kali (Connection Pooling)

> [!NOTE]
> Saat ini setiap node (`router.py`, `sanitizer.py`, `execute.py`, `sql_gen.py`) membuka dan menutup koneksi DuckDB sendiri-sendiri. Pada satu request, DuckDB dibuka setidaknya **4 kali**. Untuk efisiensi, sebaiknya menggunakan koneksi tunggal yang di-pass via state atau singleton.

---

### ISU #7 — `kategori_layanan` Masih Tidak Konsisten di `fakta_throughput`

> [!IMPORTANT]
> Meskipun `_normalisasi_nama_sheet()` sudah ada, perlu dicek apakah data di DuckDB sudah di-re-ETL setelah fix ini. Jika tidak, data lama dengan `DOMESTIK` (Indonesia) mungkin masih tersimpan di tabel.

---

## 5. Rencana Optimasi — Urutan Prioritas

### Fase A: Quick Wins (< 30 menit per item) — ✅ SELESAI
1. [x] **Perbarui `WALKTHROUGH.md`** — sinkronkan dengan arsitektur terkini (Router, Sanitizer, Groq Viz, 8 komponen Vue)
2. [x] **Perbaiki komentar di `viz_gen.py`** — disesuaikan dengan agen Groq
3. [x] **Tambahkan `echarts_config: None` di `initial_state`** (`main.py`)
4. [x] **Perbaiki false positive `REPLACE` di Sanitizer** — dihapus dari FORBIDDEN agar fungsi DuckDB `REPLACE()` bisa digunakan
5. [x] **Implementasikan `/api/v1/data/status` riil** — query DuckDB table count & size riil

### Fase B: Medium Effort (1–3 jam) — ✅ SELESAI
6. [x] **Re-ETL** — memastikan seluruh data `DOMESTIK` ternormalisasi menjadi `DOMESTIC` di DuckDB
7. [x] **Connection Pooling DuckDB** — membuat `backend/db.py` (`DuckDBPool` singleton) untuk mengelola shared read-only connection terpusat bagi seluruh agen AI (`router`, `sql_gen`, `sanitizer`, `execute`, `main.py`)

### Fase C: Large Effort — (FOKUS 1, FOKUS 2, & FOKUS 3 SELESAI 100% ✅)
8. [x] **Tambah transformer untuk 6 file Excel sisa** — `Transhipment.xlsx`, `VESSEL SERVICE.xlsx`, `Komersial Dashboard.xlsx`, `Realisasi UC.xlsx`, `OVERVIEW BOX.xlsx`, `RestNDisc.xlsx` (100% 9/9 file Excel terproses ke DuckDB!)
9. [x] **Implementasi RBAC (Role-Based Access Control) & Login Gate** — Enforce filter tabel berdasarkan `role` terverifikasi via JWT (`executive`, `commercial`, `operation`, `guest`)
10. [x] **Redis Enterprise Store (5 Fitur Terintegrasi)** —
    - ⚡ **Fitur 1:** Multi-Turn Session Context Memory (Redis List TTL)
    - 🌐 **Fitur 2:** Shared Schema Catalog Cache (Multi-Worker Production Ready)
    - 🛡️ **Fitur 3:** Security API Rate Limiting & Throttling (30 req/min)
    - 📊 **Fitur 4:** DB Health & Metadata Status Cache (< 1ms latency)
    - 🔑 **Fitur 5:** RBAC Role Permissions Cache (`tps_rbac:{role}`)
11. [x] **Otentikasi & Keamanan Enterprise (`auth.py` & `LoginModal.vue`)** — PBKDF2 Hashing (100k iterasi), JWT Signed Tokens (HS256), Authorization Bearer Header Protection, Auto Anti-Spoofing.
12. [x] **Persistent Multi-Session History UI (`SidebarHistory.vue`)** — Riwayat obrolan lengkap per User / Role disimpan di Redis & File Storage (`data/sessions/`), lengkap dengan tombol Chat Baru, Pindah Thread, dan Hapus Sesi.

---

## 6. Tech Stack Aktual (Per 28 Agustus 2026)

| Komponen | Status | Detail |
|---|---|---|
| Backend | ✅ | FastAPI 0.x, Python 3.11, `uvicorn` |
| Database | ✅ | DuckDB persistent (`tps_komersial.duckdb`, ~2.1 MB) |
| ETL | ✅ (partial) | Pandas Medallion, 3/9 file diproses |
| Orchestrator | ✅ | LangGraph StateGraph, 5 nodes |
| LLM (Router) | ✅ | Gemini 3.6 Flash |
| LLM (SQL Gen) | ✅ | Gemini 3.6 Flash |
| LLM (Sanitizer) | ✅ | Rule-based (no LLM) |
| LLM (Viz Gen) | ✅ | Groq `openai/gpt-oss-20b` |
| Security | ✅ | Dual-Layer Sanitizer (Input + Output Guard) |
| Frontend | ✅ | Vue 3 + Vite + Tailwind CSS + ECharts CDN |
| Unit Tests | ✅ | pytest: 10 test cases (ETL, Router, Sanitizer) |
| RBAC | ❌ | Belum diimplementasi |
| Cache | ❌ | Belum diimplementasi |
| Data Validation | ❌ | Belum ada Pandera/Pydantic contract |
