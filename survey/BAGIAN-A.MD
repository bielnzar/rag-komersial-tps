# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN A
## GAMBARAN UMUM PROJECT: TPS ENTERPRISE AI DATA AGENT

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Static Code Inspection, Configuration Review, & Runtime Trace Analysis (Project Lokal)

---

### 1. Struktur Folder Utama Project

Berdasarkan inspeksi langsung pada root direktori repository lokal (`/home/bosmuda/Intern/TPS/rag-komersial-tps`), berikut adalah struktur hierarki folder utama:

```text
rag-komersial-tps/
├── backend/                  # Layer backend FastAPI, ETL, dan AI Agents
│   ├── agents/               # Modul Multi-Agent LangGraph (Router, SQL Gen, Sanitizer, Execute, Viz)
│   ├── etl/                  # Pipeline Medallion Architecture (Bronze -> Silver -> Gold)
│   ├── tests/                # Automated unit tests (Pytest)
│   ├── main.py               # Entry point FastAPI & Pre-flight Guard
│   ├── db.py                 # DuckDB connection pool manager
│   ├── cache.py              # Redis semantic cache & session manager
│   ├── auth.py               # JWT authentication & PBKDF2 hashing
│   └── api_keys_manager.py   # Dedicated per-step API key pool manager
├── frontend/                 # Layer frontend antarmuka pengguna (SPA)
│   ├── src/
│   │   ├── components/       # Komponen Vue (Chat, Admin, ECharts, Sidebar, Modal)
│   │   ├── App.vue           # Root single-page application component
│   │   ├── main.js           # Entry point Vue 3
│   │   └── style.css         # Styling global Tailwind CSS
│   ├── index.html            # Entry point HTML & Apache ECharts CDN loader
│   ├── package.json          # Node dependencies & Vite build configuration
│   └── vite.config.js        # Konfigurasi bundler Vite
├── data/                     # Penyimpanan data multi-layer (Medallion & Sessions)
│   ├── raw/                  # Data mentah Excel (.xlsx) dari Google Drive / operasional
│   ├── bronze/               # Ekstraksi tabular mentah (.csv)
│   ├── silver/               # Data hasil pembersihan dan penyesuaian tipe data (.csv)
│   ├── gold/                 # Data mart siap analitik (.csv)
│   ├── processed/            # File database analitik akhir (tps_komersial.duckdb)
│   └── sessions/             # Riwayat percakapan persisten disk (user_<username>.json)
├── credentials/              # Kredensial lokal sensitif (Excluded dari Git)
│   ├── api_keys.json         # Pool API Key LLM (Gemini & Groq) per-step
│   └── users.json            # Database user, role, dan password hash (PBKDF2)
├── milestone/                # Dokumentasi arsitektur, walkthrough, & handover
│   ├── handover.md
│   ├── handover2.MD
│   └── handover3.MD
├── logs/                     # File log runtime (ETL system log & audit trace)
├── requirements.txt          # Python dependencies manifest
├── .gitignore                # Aturan pengecualian git repository
└── README.md                 # Dokumentasi umum project
```

---

### 2. Fungsi Masing-Masing Folder & File Penting

| Path File / Folder | Status | Fungsi Teknis dalam Sistem | Bukti Kode / Konfigurasi |
| :--- | :---: | :--- | :--- |
| **`backend/main.py`** | `IMPLEMENTED` | Entry point server FastAPI, routing HTTP REST API, otentikasi JWT, Pre-flight Specificity Guard, dan inisiasi pipeline LangGraph. | `app = FastAPI(...)`<br>`agent_app = build_graph()` |
| **`backend/agents/graph.py`** | `IMPLEMENTED` | Pusat orkestrasi alur Multi-Agent LangGraph (StateGraph) yang menghubungkan router, sql_gen, sanitizer, execute, dan viz_gen secara linier *fail-fast*. | `builder = StateGraph(AgentState)`<br>`builder.add_edge("router", "sql_gen")` |
| **`backend/agents/router.py`** | `IMPLEMENTED` | Router Agent (STEP 1): Memetakan pertanyaan pengguna ke tabel DuckDB yang relevan dan menyaring otorisasi peran (RBAC). | `def router_node(state: AgentState)`<br>`get_table_catalog()` |
| **`backend/agents/sql_gen.py`** | `IMPLEMENTED` | SQL Generator Agent (STEP 2): Merakit prompt Text-to-SQL dengan glosarium domain pelabuhan dan skema tabel terpilih. | `def sql_gen_node(state: AgentState)`<br>`SQL_SYSTEM_PROMPT` |
| **`backend/agents/sanitizer.py`** | `IMPLEMENTED` | Security Guardrail (STEP 3): Validasi keamanan kueri terhadap SQL Injection, DDL/DML berbahaya, dan validasi CTE alias tanpa LLM. | `def sanitize_sql(query, sql)`<br>`FORBIDDEN_KEYWORDS = ['DROP', ...]` |
| **`backend/agents/execute.py`** | `IMPLEMENTED` | Database Execution Node (STEP 4): Eksekusi SQL ke DuckDB, konversi NaN/Infinity ke null, dan deteksi data kosong (*Fail-Fast*). | `def execute_sql_node(state: AgentState)`<br>`con.execute(sql).fetchall()` |
| **`backend/agents/viz_gen.py`** | `IMPLEMENTED` | Visualization & Narrative Agent (STEP 5): Merangkum data tabel menjadi narasi bisnis eksekutif (format TEUs/Rp) dan memicu ECharts config. | `def viz_gen_node(state: AgentState)`<br>`format_data_compact(rows, 15)` |
| **`backend/agents/chart_gen.py`** | `IMPLEMENTED` | Generator konfigurasi JSON Apache ECharts jika pengguna meminta visualisasi grafik. | `def generate_chart_config(query, data, ...)` |
| **`backend/etl/main_etl.py`** | `IMPLEMENTED` | Pipeline orchestrator Medallion Architecture: Membaca 9 file Excel mentah, memicu transformer Silver/Gold, dan menyimpannya ke DuckDB. | `def jalankan_etl()`<br>`FILE_ROUTER = {...}` |
| **`backend/etl/transformers.py`** | `IMPLEMENTED` | Modul logika transformasi data: Pembersihan data kotor, pivot/unpivot matriks, dan pembentukan star schema/fact table. | `proses_throughput()`, `proses_komersial_dashboard()` |
| **`backend/etl/utils.py`** | `IMPLEMENTED` | Utilitas data: Penghapusan kolom kosong/hantu (`hapus_kolom_hantu`), konversi numerik paksa, dan penulisan log rotasi. | `hapus_kolom_hantu()`, `paksa_angka()` |
| **`backend/db.py`** | `IMPLEMENTED` | Connection Pool DuckDB thread-safe untuk mencegah *file locking* saat diakses bersamaan oleh backend & worker. | `class DuckDBPool:`<br>`duckdb.connect(db_path, read_only=True)` |
| **`backend/cache.py`** | `IMPLEMENTED` | Modul caching semantik berbasis Redis, rate limiter per IP/user, dan persistence manager riwayat sesi chat dual-layer (RAM + File). | `class SemanticCache:`<br>`redis.Redis(...)` |
| **`backend/auth.py`** | `IMPLEMENTED` | Keamanan otentikasi: Pembuatan dan verifikasi token JWT, PBKDF2 hashing dengan salt acak, dan verifikasi header bearer. | `create_jwt_token()`, `hash_password()`, `verify_password()` |
| **`backend/api_keys_manager.py`** | `IMPLEMENTED` | Manajemen independen API Key per-step (Router, SQL Gen, Viz) dengan rotasi multi-kunci otomatis dan *smart unmasking*. | `class APIKeysManager:`<br>`rotate_key_on_failure()` |
| **`frontend/src/App.vue`** | `IMPLEMENTED` | Komponen induk UI yang mengelola state chat aktif, modal login, modal admin, dan integrasi response backend. | `<template>`, `<ChatInput>`, `<Navbar>` |
| **`frontend/src/components/AdminDashboard.vue`** | `IMPLEMENTED` | Panel manajemen administrator untuk konfigurasi model AI, pergantian provider, dan pemantauan telemetri kuota API per-step. | `activeTab = 'keys'`, `saveStepModel()` |
| **`data/processed/tps_komersial.duckdb`** | `IMPLEMENTED` | File database analitik OLAP lokal yang menampung 9 fact table siap kueri. | File binary DuckDB (9 tabel hasil Medallion ETL) |

---

### 3. Identifikasi Komponen Teknologi & Dependencies

Berdasarkan inspeksi `requirements.txt`, `frontend/package.json`, dan file konfigurasi runtime:

#### A. Bahasa Pemrograman
* **Python (v3.11+):** `IMPLEMENTED` — Digunakan pada seluruh backend, pipeline ETL, agen LangGraph, dan layer database.
* **JavaScript (ECMAScript 2022+ / ES Modules):** `IMPLEMENTED` — Digunakan pada seluruh layer frontend (Vue 3 script setup).
* **SQL (DuckDB Dialect):** `IMPLEMENTED` — Digunakan sebagai bahasa query analitik hasil rakitan LLM.
* **HTML5 & CSS3:** `IMPLEMENTED` — Struktur antarmuka dan styling aplikasi.

#### B. Framework Utama
* **Backend Framework:** `FastAPI` (v0.115+) — `IMPLEMENTED` (`backend/main.py:L22`). Dipilih karena berbasis asynchronous ASGI dan validasi skema otomatis via Pydantic.
* **Frontend Framework:** `Vue 3` (v3.5.13) dengan Composition API `<script setup>` — `IMPLEMENTED` (`frontend/package.json:L13`).
* **Frontend Build Tool:** `Vite` (v6.2.0) — `IMPLEMENTED` (`frontend/package.json:L20`).
* **Styling Framework:** `Tailwind CSS` (v3.4.17) + `Autoprefixer` + `PostCSS` — `IMPLEMENTED` (`frontend/package.json:L17-19`).

#### C. Database Engine
* **Analytical Database (OLAP):** `DuckDB` (v1.1+) — `IMPLEMENTED` (`requirements.txt:L6`, `backend/db.py`). Menyimpan 9 tabel analitik hasil proses Medallion.
* **In-Memory Cache & Session State:** `Redis` (via `redis-py`) — `IMPLEMENTED` (`backend/cache.py:L14`). Menyimpan semantic cache, rate limit tracker, dan sliding-window session history.

#### D. Library Pengolahan Data (Data Engineering / ETL)
* **`pandas`:** `IMPLEMENTED` (`requirements.txt:L7`). Digunakan pada modul Medallion ETL (`backend/etl/`) untuk operasi DataFrame: pembersihan missing value, unpivot tabel Excel, normalisasi string, dan pembentukan struktur tabular.
* **`duckdb` (Python Client):** `IMPLEMENTED` (`requirements.txt:L6`). Digunakan untuk injeksi data dari Pandas DataFrame ke database relasional terindeks (`CREATE OR REPLACE TABLE ... AS SELECT * FROM df`).

#### E. Library LLM & Multi-Agent Framework
* **`langgraph`:** `IMPLEMENTED` (`requirements.txt:L4`). Framework orkestrasi graf stateful linier (*StateGraph*) untuk merangkai alur multi-agen.
* **`langchain` & `langchain-core`:** `IMPLEMENTED` (`requirements.txt:L3`). Abstraksi pesan (`HumanMessage`, `SystemMessage`), prompt templates, dan output parsing.
* **`langchain-google-genai`:** `IMPLEMENTED` (`requirements.txt:L5`). Driver koneksi ke Google Gemini API (model `gemini-3.1-flash-lite` untuk Router, `gemini-3.6-flash` untuk SQL Gen).
* **`langchain-groq`:** `IMPLEMENTED` (`requirements.txt:L9`). Driver koneksi ke Groq Cloud API (model `openai/gpt-oss-20b` untuk Viz Gen).
* **`langchain-ollama`:** `PARTIALLY IMPLEMENTED` (`requirements.txt:L10`, `backend/agents/llm_helper.py`). Terpasang di dependencies dan tercantum pada opsi dropdown Admin, namun mode operasi default saat ini menggunakan Cloud Provider (Gemini & Groq).

#### F. Visualisasi Data
* **`Apache ECharts` (v5.6.0):** `IMPLEMENTED` (`frontend/index.html:L13`, `frontend/src/components/EChartsViewer.vue`). Dimuat via CDN untuk merender grafik interaktif (Bar, Line, Donut) dari JSON config hasil rakitan agen visualisasi.

---

### 4. Cara Menjalankan Project Secara Lokal

Sistem ini dijalankan secara lokal dengan mengaktifkan 3 komponen utama secara berurutan:

#### Langkah 1: Memastikan Service Cache (Redis) Aktif
```bash
# Redis Server harus berjalan di port standar 6379 lokal
redis-server --daemonize yes
# Verifikasi koneksi Redis
redis-cli ping  # Output: PONG
```

#### Langkah 2: Menjalankan Backend Server (FastAPI)
```bash
# Mengaktifkan environment Conda / Python
conda activate tps-agent

# Masuk ke direktori backend
cd /home/bosmuda/Intern/TPS/rag-komersial-tps/backend

# Menjalankan uvicorn server dengan fitur auto-reload
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
*Bukti Eksekusi:* Terminal backend mendengarkan pada `http://127.0.0.1:8000`. Endpoint dokumentasi Swagger tersedia di `http://127.0.0.1:8000/docs`.

#### Langkah 3: Menjalankan Frontend Development Server (Vite)
```bash
# Masuk ke direktori frontend
cd /home/bosmuda/Intern/TPS/rag-komersial-tps/frontend

# Menjalankan Vite development server
npm run dev
```
*Bukti Eksekusi:* Vite menyajikan Single Page Application (SPA) pada `http://localhost:5173`.

#### Langkah Tambahan (Jika Ingin Membangun Ulang Database DuckDB):
```bash
# Menjalankan pipeline ETL Medallion untuk menyerap ulang 9 file Excel mentah
python backend/etl/main_etl.py
```

---

### 5. Identifikasi Entry Point Aplikasi

Sistem memiliki dua entry point utama yang terpisah antara Backend (API) dan Frontend (UI):

#### A. Entry Point Backend (REST API Server)
* **File:** [`backend/main.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/main.py)
* **Fungsi:** 
  - Menginisialisasi instance aplikasi FastAPI (`app = FastAPI(...)`).
  - Membaca konfigurasi middleware CORS (`allow_origins=["*"]`).
  - Menyiapkan pool database DuckDB dan instance cache Redis saat aplikasi booting.
  - Membangun graf state LangGraph saat startup:
    ```python
    # backend/main.py:L36
    agent_app = build_graph()
    ```
  - Menyediakan endpoint utama penerima query percakapan:
    ```python
    # backend/main.py:L175
    @app.post("/api/v1/chat", response_model=ChatResponse)
    async def chat_endpoint(request: ChatRequest, authorization: Optional[str] = Header(None)):
    ```

#### B. Entry Point Frontend (User Interface)
* **File Index:** [`frontend/index.html`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/frontend/index.html)  
  *Fungsi:* Menyediakan elemen mount DOM `<div id="app"></div>`, memuat font Google, dan me-load script runtime ECharts.
* **File JS Bootstrap:** [`frontend/src/main.js`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/frontend/src/main.js)  
  *Bukti Kode:*
  ```javascript
  import { createApp } from 'vue'
  import './style.css'
  import App from './App.vue'

  createApp(App).mount('#app')
  ```
* **File Root View:** [`frontend/src/App.vue`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/frontend/src/App.vue)  
  *Fungsi:* Mengatur tata letak global (Navbar, Sidebar History, Chat Panel, dan Admin Dashboard Modal).

---

### 6. File Utama Pusat Orkestrasi Sistem

Pusat orkestrasi sistem terbagi menjadi dua level: **Level State Machine Agent** dan **Level Request Dispatcher**.

#### A. Pusat Orkestrasi Multi-Agent: [`backend/agents/graph.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/graph.py)
* **Status:** `IMPLEMENTED`
* **Fungsi:** File ini adalah inti orkestrasi alur Multi-Agent LangGraph. Mendefinisikan graf alur kerja (*Workflow Graph*) yang mengatur perpindahan state data secara linier dan *fail-fast* antar agen spesialis.
* **Bukti Kode:**
  ```python
  # backend/agents/graph.py:L10-L40
  from langgraph.graph import StateGraph, START, END
  from agents.state import AgentState
  from agents.router import router_node
  from agents.sql_gen import sql_gen_node
  from agents.sanitizer import sanitizer_node
  from agents.execute import execute_sql_node
  from agents.viz_gen import viz_gen_node

  def build_graph():
      builder = StateGraph(AgentState)
      
      # 1. Daftarkan seluruh Node Spesialis
      builder.add_node("router", router_node)
      builder.add_node("sql_gen", sql_gen_node)
      builder.add_node("sanitizer", sanitizer_node)
      builder.add_node("execute_sql", execute_sql_node)
      builder.add_node("viz_gen", viz_gen_node)
      
      # 2. Rangkaikan Alur Eksekusi Linier (Fail-Fast Single Pass)
      builder.add_edge(START, "router")
      builder.add_edge("router", "sql_gen")
      builder.add_edge("sql_gen", "sanitizer")
      builder.add_edge("sanitizer", "execute_sql")
      builder.add_edge("execute_sql", "viz_gen")
      builder.add_edge("viz_gen", END)
      
      return builder.compile()
  ```

#### B. Pusat Integrasi Alur Request: [`backend/main.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/main.py)
* **Status:** `IMPLEMENTED`
* **Fungsi:** Menghubungkan lapisan HTTP Request dengan Graf LangGraph di atas, dengan urutan eksekusi:
  1. **Rate Limiting Check** (`semantic_cache.check_rate_limit`)
  2. **Pre-flight Specificity Check** (`check_query_specificity`) — Filter 0 Token untuk menolak kueri ambigu.
  3. **Semantic Cache Check** (`semantic_cache.get`) — Respon instan jika query persis sudah pernah dijawab.
  4. **Graph Execution** (`agent_app.ainvoke(initial_state)`) — Menjalankan orkestrasi multi-agent LangGraph.
  5. **Session Persistence** (`semantic_cache.save_chat_message_to_session`) — Menyimpan percakapan ke Redis RAM dan File Disk JSON.
