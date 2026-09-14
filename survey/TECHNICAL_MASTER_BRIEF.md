# 📘 TECHNICAL MASTER BRIEF: AUDIT ARSITEKTUR & IMPLEMENTASI SISTEM
## TPS Enterprise AI Data Agent (Studi Kasus: PT Terminal Petikemas Surabaya)

**Dokumen Rujukan:** Hasil Audit Komprehensif Bagian A s/d Bagian M (`survey/BAGIAN-*.MD`)  
**Tujuan Dokumen:** Satu-satunya sumber fakta teknis utama (*Single Technical Source of Truth*) mengenai sistem yang sedang berjalan di lokal untuk penyusunan **BAB 3 METODOLOGI SKRIPSI / TUGAS AKHIR**.  
**Prinsip Audit:** Berbasis kode nyata (*Evidence-Based*), membedakan fakta vs rencana, tanpa data fiktif (*Zero Hallucination*).

---

# 1. PROJECT OVERVIEW

### A. Tujuan Project
Mengembangkan asisten analitik data percakapan berbasis Text-to-SQL dan Multi-Agent State Machine yang mampu mengolah data operasional petikemas, finansial, dan komersial PT TPS dari berkas spreadsheet menjadi wawasan terstruktur, grafik interaktif, dan narasi bisnis eksekutif secara lokal, aman (*Zero Data Leakage*), dan hemat token.

### B. Kondisi Project Saat Ini
* **Status:** `IMPLEMENTED (Production-Ready / Version 3.0)`
* Sistem berjalan penuh di lingkungan lokal dengan backend FastAPI, database analitik DuckDB, in-memory cache Redis, frontend SPA Vue 3 + Vite, dan orkestrasi LangGraph linier Fail-Fast.

### C. Entry Point Aplikasi
1. **Backend Entry Point:** [`backend/main.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/main.py)
   - Menginisialisasi instance `app = FastAPI(...)`.
   - Mengompilasi graf LangGraph saat startup: `agent_app = build_graph()`.
   - Endpoint utama: `POST /api/v1/chat` (dilengkapi proteksi JWT Bearer Auth & Pre-Flight Specificity Guard).
2. **Frontend Entry Point:** [`frontend/index.html`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/frontend/index.html) ➔ [`frontend/src/main.js`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/frontend/src/main.js) ➔ [`frontend/src/App.vue`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/frontend/src/App.vue).

### D. Cara Menjalankan Project Secara Lokal
```bash
# 1. Service In-Memory Cache (Wajib aktif)
redis-server --daemonize yes

# 2. Backend Server (FastAPI / Uvicorn di port 8000)
cd backend && uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 3. Frontend Development Server (Vite di port 5173)
cd frontend && npm run dev

# 4. (Opsional) Pembangunan Ulang Database Analitik dari File Mentah
python backend/etl/main_etl.py
```

### E. Arsitektur Umum Sistem
Arsitektur terdiri dari 4 layer terpisah:
1. **Data Engineering Layer:** Medallion Ingestion (`backend/etl/`) mengonversi berkas `.xlsx` menjadi database relasional OLAP DuckDB.
2. **Storage & Cache Layer:** File lokal DuckDB (`tps_komersial.duckdb`), file log telemetri (`telemetry.duckdb`), dan Redis RAM cache.
3. **AI Cognitive & Orchestration Layer:** LangGraph State Machine linier 5 node didukung Asymmetric LLM Tiering (Google Gemini + Groq).
4. **Presentation Layer:** Vue 3 SPA, Tailwind CSS, dan Apache ECharts.

---

# 2. DATA SOURCES

* **Asal Sumber Data:** 100% Data Riil Operasional PT TPS yang disinkronisasi dari Cloud Storage perusahaan (`data/raw/OneDrive_1_8-25-2026.zip`). Bukan dataset publik Kaggle.
* **Format Sumber:** Microsoft Excel Workbook (`.xlsx`).
* **Jumlah Berkas Saat Ini:** Tepat **9 file Excel mentah** di folder `data/raw/`:
  1. `Container Throughput.xlsx`
  2. `Komersial Dashboard.xlsx`
  3. `Market Share.xlsx`
  4. `OVERVIEW BOX.xlsx`
  5. `OVERVIEW VESSEL.xlsx`
  6. `Realisasi UC.xlsx`
  7. `RestNDisc.xlsx`
  8. `Transhipment.xlsx`
  9. `VESSEL SERVICE.xlsx`
* **Struktur Dataset & Tabel di DuckDB (`data/processed/tps_komersial.duckdb`):**
  - Total 9 Tabel Fakta (~32.054 baris data relasional terakumulasi).
  - Skema Denormalized Star Schema (OLAP Optimized).
* **Kunci Relasi Antar Tabel (Logical Foreign Keys):**
  - `lop` (*Line Operating Partner* / Operator Pelayaran / Pelanggan): Menghubungkan 7 tabel.
  - `year`/`tahun` dan `month`/`bulan`: Dimensi waktu agregasi.
  - `kategori_layanan`: Segmentasi kargo (`INTERNATIONAL` vs `DOMESTIC`).
* **Periode Data:** Data historis mencakup rentang transaksi **2021 hingga awal 2026**, dengan konsentrasi analitik terpadat pada **2023, 2024, dan 2025**.
* **Proses Preprocessing Data:**
  - *Cleaning:* Pembuangan kolom hantu `Unnamed` dan baris kosong NaN via `hapus_kolom_hantu()`.
  - *Type Casting:* Pemaksaan tipe numerik via `paksa_angka()` (pembersihan koma ribuan dan parsing float).
  - *Standardisasi Kolom:* Konversi huruf kecil snake_case, rename `%` ➔ `persentase`, rename operator ➔ `lop`.
  - *Reshaping:* Unpivot otomatis matriks pivot tahunan pada data Market Share via `pd.melt()`.

---

# 3. MEDALLION ARCHITECTURE

* **Status:** `IMPLEMENTED (Lightweight Batch In-Memory Medallion Pattern)`

| Layer | Bentuk Komputasi | Bentuk Penyimpanan | Lokasi Path | Proses Transformasi yang Terjadi |
| :--- | :--- | :--- | :--- | :--- |
| **BRONZE** | `pandas.DataFrame` (Mentah) | File CSV Mentah | `data/bronze/` | Ekstraksi langsung multi-sheet dari `.xlsx` tanpa filter dan tanpa pembersihan. |
| **SILVER** | `pandas.DataFrame` (Bersih) | File CSV Bersih | `data/silver/` | Hapus kolom hantu `Unnamed`, standardisasi nama `lop`, pemaksaan numerik `paksa_angka()`. |
| **GOLD** | `pandas.DataFrame` (Konsolidasi) | File CSV Model + **Tabel DuckDB** | `data/gold/`<br>`data/processed/tps_komersial.duckdb` | Penyeragaman identifier snake_case, penambahan dimensi `kategori_layanan`, unpivot matriks pivot, penggabungan multi-sheet (`pd.concat`). |

* **Hubungan dengan Database:** DataFrame Gold akhir dimuat ke DuckDB secara in-memory via `conn.register('temp_df', df_final)` lalu dimaterialisasi fisik menggunakan perintah SQL DDL:  
  `CREATE OR REPLACE TABLE {nama_tabel} AS SELECT * FROM temp_df`.

---

# 4. ANALYTIC DATABASE

* **Database Engine:** `DuckDB` (v1.1+) — `IMPLEMENTED (100% Aktif & Digunakan Nyata)`.
* **Karakteristik Komputasi:** Berjalan 100% lokal (*Embedded In-Process OLAP Engine*). Tidak ada koneksi database cloud eksternal untuk data analitik.
* **Cara Data Dimuat:** Dimuat saat fase Gold ETL Medallion melalui registrasi memori Pandas-to-DuckDB tanpa perantara ekspor file manual.
* **Bentuk Penyimpanan:** **Tabel Fisik Materialized Persisten** (bukan sekadar view virtual) di dalam berkas biner `data/processed/tps_komersial.duckdb`.
* **Katalog Tabel Fisik yang Dibuat:**
  1. `fakta_throughput` (94 baris, 8 kolom)
  2. `fakta_komersial_dashboard` (910 baris, 26 kolom)
  3. `fakta_market_share` (7.657 baris, 54 kolom)
  4. `fakta_realisasi_uc` (1.686 baris, 19 kolom)
  5. `fakta_rest_n_disc` (5 baris, 11 kolom)
  6. `fakta_vessel` (940 baris, 10 kolom)
  7. `fakta_vessel_service` (2.410 baris, 26 kolom)
  8. `fakta_transhipment` (17.626 baris, 33 kolom)
  9. `fakta_overview_box` (726 baris, 9 kolom)
* **Mekanisme Query Execution:**
  - Dijalankan via `DuckDBPool.get_connection()` dengan mode penguncian fisik **`read_only=True`** di `backend/db.py`.
  - Eksekusi kueri dilakukan di `backend/agents/execute.py` menggunakan metode `conn.execute(sql).df()`, disanitasi nilai `NaN/Infinity` ke `null`, dan dikonversi ke list of dicts.

---

# 5. MULTI-AGENT ARCHITECTURE

Berikut adalah pemetaan seluruh komponen analitik dalam sistem:

| Component | Type | Role | Input | Output | LLM? | Model | Status | File |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| `pre_flight_guard` | Deterministic Process | Gatekeeper Anti-Ambigu | `request.query` | `is_specific` (Bool), Guidance string | **TIDAK** | *None (Regex/Rules)* | `IMPLEMENTED` | `backend/main.py` |
| `router` | Agent / Node | Semantic Dispatcher & Access Controller | `user_query`, Catalog 9 Tabel, `role`, `history[-6:]` | `relevant_tables` (List str) | **YA** | `gemini-3.1-flash-lite` | `IMPLEMENTED` | `backend/agents/router.py` |
| `schema_linking` | Function / Tool | Schema Pruner & Extractor | `relevant_tables` | `schema` string (`PRAGMA table_info`) | **TIDAK** | *None (DuckDB Driver)* | `IMPLEMENTED` | `backend/agents/sql_gen.py` |
| `sql_gen` | Agent / Node | Data Engineer & SQL Synthesizer | `user_query`, `schema`, Glosarium TPS, `history[-6:]` | `generated_sql` (String SQL) | **YA** | `gemini-3.6-flash` | `IMPLEMENTED` | `backend/agents/sql_gen.py` |
| `sanitizer` | Deterministic Node | Security Firewall & AST Inspector | `user_query`, `generated_sql`, valid tables | `sql_error` (None atau Error string) | **TIDAK** | *None (Regex / Python Rule)* | `IMPLEMENTED` | `backend/agents/sanitizer.py` |
| `execute_sql` | Tool / Node | Database Query Runner & Fast-Fail Detector | `generated_sql`, `DuckDBPool` | `query_result` (List dict) / `DATA_EMPTY` | **TIDAK** | *None (DuckDB Engine)* | `IMPLEMENTED` | `backend/agents/execute.py` |
| `viz_gen` | Agent / Node | Executive Narrative Analyst & Communicator | `user_query`, `query_result` (max 15 rows), `sql_error` | `final_answer` (Markdown string) | **YA** | `openai/gpt-oss-20b` (Groq) | `IMPLEMENTED` | `backend/agents/viz_gen.py` |
| `chart_gen` | Sub-Agent / Function | Visual Analytics Architect | `user_query`, `query_result` | `echarts_config` (JSON dict) | **YA** | `openai/gpt-oss-20b` (Groq) | `IMPLEMENTED` | `backend/agents/chart_gen.py` |

---

# 6. ORCHESTRATION

* **Orchestration Framework:** `LangGraph` (v0.2+) berbasis `StateGraph(AgentState)` linier.
* **Memori State (`AgentState` di `backend/agents/state.py`):**
  `user_query`, `relevant_tables`, `generated_sql`, `sql_error`, `correction_attempts`, `query_result`, `final_answer`, `echarts_config`, `force_chart`, `chat_history`, `role`.
* **Node Terdaftar (5 Node):** `"router"`, `"sql_gen"`, `"sanitizer"`, `"execute_sql"`, `"viz_gen"`.
* **Edge Statis:** `START ➔ "router"`, `"router" ➔ "sql_gen"`, `"sql_gen" ➔ "sanitizer"`, `"execute_sql" ➔ "viz_gen"`, `"viz_gen" ➔ END`.
* **Conditional Edge:** Terpasang pada node `"sanitizer"` menggunakan fungsi router `should_continue_sanitizer()`:
  - Jika `sql_error` mengandung `"SANITIZER BLOCKED"` ➔ cabang ke `"viz_gen"` (melompati `execute_sql` demi keamanan).
  - Jika lolos validasi ➔ cabang ke `"execute_sql"`.
* **Start / End Point:** Dimulai dari `START` (menuju router) dan berakhir di `END` (keluar dari viz_gen).
* **Alur Normal (Happy Path):**  
  `START ➔ router ➔ sql_gen ➔ sanitizer ➔ (Lolos) ➔ execute_sql ➔ viz_gen ➔ END`.
* **Alur Error / Fail-Fast:**
  - *Sanitizer Terblokir:* `START ➔ router ➔ sql_gen ➔ sanitizer ➔ (Blokir) ➔ viz_gen ➔ END`.
  - *Data Empty / DB Syntax Error:* `START ➔ router ➔ sql_gen ➔ sanitizer ➔ execute_sql ➔ (Flag Error) ➔ viz_gen ➔ END`.

---

# 7. TEXT-TO-SQL PIPELINE

Alur komputasi Text-to-SQL berlangsung dalam 7 tahapan sekuensial:
1. **Natural Language Question:** Pengguna memasukkan pertanyaan (misal: *"Berapa throughput internasional tahun 2024?"*).
2. **Schema Selection (Router Agent):** Router menganalisis pertanyaan dan memilih 1–2 tabel relevan (`['fakta_throughput']`). Skema tabel lain dipangkas (*Schema Pruning*).
3. **Prompt Construction (SQL Generator):** Sistem menyusun prompt menggabungkan:
   - Skema kolom tabel terpilih dari DuckDB (`get_duckdb_schema`).
   - Riwayat 3 kueri SQL sebelumnya (*SQL-Only History*).
   - Glosarium aturan bisnis pelabuhan PT TPS.
   - Teks pertanyaan user.
4. **SQL Generation (LLM Gemini 3.6 Flash):** Menghasilkan satu baris kueri DuckDB SQL murni secara *Zero-Shot* tanpa markdown formatting.
5. **Validation (Security Sanitizer):** Regex Python memverifikasi kueri dari multiple statements (`;`), kata kunci berbahaya (DROP/DELETE), dan mencocokkan eksistensi nama tabel/CTE.
6. **Execution (DuckDB Engine):** Eksekusi kueri read-only ke `tps_komersial.duckdb`. Sanitasi float NaN ke null.
7. **Result Delivery (Viz Gen):** 15 baris sampel data disintesis menjadi narasi bisnis eksekutif dan tabel dikirimkan ke frontend.

---

# 8. SCHEMA LINKING / SCHEMA PRUNING

* **Bagaimana Dilakukan:** Menggunakan teknik **Two-Stage Selective Filtering**:
  - *Tahap 1 (Pruning Tingkat Tabel):* Dieksekusi oleh Router Agent (`router.py`) menggunakan LLM `gemini-3.1-flash-lite`. Dari total 9 tabel database, Router memilih hanya 1–2 tabel yang relevan berdasarkan katalog semantik.
  - *Tahap 2 (Linking Tingkat Kolom):* Dieksekusi secara terprogram (*deterministic*) oleh fungsi `get_duckdb_schema(relevant_tables)` di `sql_gen.py`. Fungsi ini mengekstrak kolom dan tipe data dari DuckDB `information_schema.columns` **hanya untuk tabel hasil saringan Tahap 1**.
* **Input:** `user_query`, katalog semantik 9 tabel, dan `relevant_tables`.
* **Output:** String teks skema ter-pruning: `Table {nama_tabel}: - {nama_kolom} ({tipe_data})`.
* **Cakupan Seleksi:** Tabel + Kolom (Tabel disaring oleh LLM, kolom diekstrak secara dinamis dari database).
* **Model/Function yang Digunakan:** `router_node` (LLM Gemini Lite) + `get_duckdb_schema()` (Python Driver DuckDB).
* **Status:** `IMPLEMENTED`.

---

# 9. LLM MODEL USAGE

| Role | Model AI Aktif | Provider | Purpose / Tugas Utama | Input Payload | Output Payload | Sifat Pemilihan | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Router (STEP 1)** | `gemini-3.1-flash-lite` | Google GenAI | Pemetaan kueri ke nama tabel & filter RBAC | Pertanyaan user, ringkasan katalog 9 tabel, role | List string nama tabel | Dynamic via Admin | `IMPLEMENTED` |
| **SQL Gen (STEP 2)** | `gemini-3.6-flash` | Google GenAI | Sintesis kueri analitik SQL DuckDB | Pertanyaan user, skema kolom terpilih, glosarium TPS | String query SQL murni | Dynamic via Admin | `IMPLEMENTED` |
| **Viz Gen (STEP 5)** | `openai/gpt-oss-20b` | Groq Cloud | Sintesis narasi bisnis eksekutif & graceful degradation | Pertanyaan user, max 15 baris sampel data CSV | Markdown narasi resmi | Dynamic via Admin | `IMPLEMENTED` |
| **Chart Gen** | `openai/gpt-oss-20b` | Groq Cloud | Pembuatan struktur JSON Apache ECharts | Pertanyaan user, data tabular CSV | JSON config ECharts | Dynamic via Admin | `IMPLEMENTED` |

---

# 10. SECURITY / SANITIZER

* **SQL Validation Engine:** `sanitizer_node` di `backend/agents/sanitizer.py` (*Deterministic Python Rule Engine - 0 Token LLM*).
* **Allowed Statements:** **HANYA PERINTAH `SELECT`** (Read-Only).
* **Blocked Statements & Keywords:**
  - Multiple Statements (karakter titik koma `;` di tengah kueri).
  - Komentar SQL (`--`, `/*`, `*/`).
  - Blacklist DDL/DML: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `MERGE`, `EXEC`, `EXECUTE`.
* **Raw Company Data Exposure:** **TIDAK ADA (ZERO DATA LEAKAGE).** Seluruh file Excel mentah dan database DuckDB (~32.054 baris) berada 100% di server lokal.
* **Cloud LLM Exposure:** Cloud LLM hanya menerima metadata katalog, nama kolom/tipe data, dan maksimal 15 baris sampel data teratas hasil kueri lokal.
* **Physical Database Protection:** Koneksi DuckDB saat melayani AI dikunci pada tingkat driver dengan **`read_only=True`** di `backend/db.py`.
* **Status Keamanan:** `IMPLEMENTED`.

---

# 11. FAIL-FAST

* **Trigger Condition:** Kueri ambigu (Pre-Flight), pelanggaran rate limit (>30 req/menit), pelanggaran keamanan (Sanitizer), kesalahan sintaks database (`DB_SYNTAX_ERROR`), atau data kosong (`DATA_EMPTY`).
* **Error Handling Strategy:** **Single-Pass Fail-Fast dengan Graceful Degradation**.
* **Retry Mechanism:** **TIDAK ADA RETRY (0 KALI)**.
* **Self-Healing Loop:** **TIDAK ADA (TELAH DIHAPUSKAN SEPENUHNYA)**. Siklus coba-ulang re-prompting yang sebelumnya mencoba hingga 3 kali telah dibongkar demi menghemat token dan latensi.
* **Response to User:** Pengguna tidak pernah melihat layar error mentah (*raw traceback*). Sistem selalu mengembalikan HTTP 200 OK dengan respons bahasa manusia yang santun:
  - *Kasus Keamanan:* Menerangkan adanya klausa tidak diizinkan demi menjaga integritas database pelabuhan.
  - *Kasus Data Kosong:* Memberitahu data kosong dan menyarankan pengecekan ejaan operator kapal (misal: *CMA, SSL, MSK*) atau rentang tahun.
* **Status:** `IMPLEMENTED`.

---

# 12. ANALYTIC OUTPUT

* **Bentuk Output:** Multi-Modal (Narasi Eksekutif Markdown + Grafik Dinamis ECharts + Modal Tabel Data Mentah + SQL Accordion).
* **Peran LLM dalam Output:** Model `openai/gpt-oss-20b` (Groq) membaca sampel data untuk menyusun narasi formal, menyoroti entitas utama (*bold*), dan merumuskan JSON chart.
* **Data yang Dikirim ke LLM Narasi:** Teks pertanyaan user dan **maksimal 15 baris data sampel teratas** dalam format *Compact CSV String* via `format_data_compact(rows, 15)`.
* **User Feedback (Rating):** `NOT FOUND (Belum Diimplementasikan di UI)`. Belum ada tombol jempol *thumbs up/down* atau formulir penilaian pengguna di `ChatMessage.vue`.
* **Machine Feedback & Storage:** `IMPLEMENTED`. Sistem telemetri otomatis mencatat latensi ms, konsumsi token masuk/keluar, nama model, dan status ke dalam database **`data/processed/telemetry.duckdb`** pada tabel **`log_audit_token`**.

---

# 13. EVALUATION AUDIT

Audit mendalam terhadap 6 metrik evaluasi ilmiah yang diwajibkan dalam metodologi:

| Metrik Evaluasi | Status Ketersediaan | Implementasi Nyata di Kode | Bagaimana Diukur | Sumber Data Uji | Output Pengukuran |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **1. Execution Accuracy** | `PARTIALLY IMPLEMENTED` | Diuji via skrip mandiri `backend/tes_kompleks.py`. | Mencocokkan nilai numerik/nominal hasil kueri AI terhadap perhitungan manual ground truth. | Database DuckDB lokal (5 kasus analitik kompleks). | Nilai nominal/volume TEUs identik 100%. |
| **2. Exact Match (EM)** | `NOT FOUND` | Belum ada framework evaluasi string-to-string SQL exact match otomatis. | - | - | - |
| **3. Syntactic Validity** | `IMPLEMENTED` | Divalidasi oleh AST regex Sanitizer (`test_sanitizer.py`) dan eksekusi DuckDB driver. | Evaluasi parsing SQL di DuckDB tanpa menghasilkan `Parser Error`. | Kueri uji Pytest dan benchmark kompleks. | 100% Valid pada seluruh skenario uji terdefinisi. |
| **4. End-to-End Latency** | `IMPLEMENTED` | Dihitung di `backend/agents/llm_helper.py:L133`. | `latency_ms = (time.time() - start_time) * 1000` di setiap pemanggilan model. | Pencatatan runtime real-time. | Nilai milidetik tersimpan di `telemetry.duckdb` (rata-rata 500–1200 ms). |
| **5. Token Reduction Ratio** | `PARTIALLY IMPLEMENTED` | Diimplementasikan melalui aturan row sampling (15 baris) dan pemangkasan history obrolan. | Dihitung dari penghematan byte payload prompt dibanding data mentah 50 baris JSON. | Payload prompt di `viz_gen.py` dan `sql_gen.py`. | Estimasi penghematan ~80% token (belum ada skrip benchmarking komparatif otomatis). |
| **6. User Testing (UAT)** | `NOT FOUND / PLANNED` | Belum dilakukan pengujian formal ke staf/eksekutif PT TPS. | - | - | - |

---

# 14. TECHNICAL FLOW (DIAGRAM TEKS)

### A. Data Flow (Ingestion & Storage)
```text
[9 Berkas Excel Mentah (.xlsx) di data/raw/]
       │
       ▼ (pd.read_excel - multi-sheet auto ingestion)
[Bronze Layer: DataFrames mentah + Checkpoint CSV di data/bronze/]
       │
       ▼ (transformers.py: hapus_kolom_hantu, normalisasi lop, paksa_angka)
[Silver Layer: DataFrames bersih + Checkpoint CSV di data/silver/]
       │
       ▼ (transformers.py: unpivot matriks pivot, standardisasi snake_case, concat)
[Gold Layer: DataFrames konsolidasi + Checkpoint CSV di data/gold/]
       │
       ▼ (DuckDB Zero-Copy In-Memory Registration: CREATE OR REPLACE TABLE)
[Analytical Data Warehouse: 9 Tabel Fakta di data/processed/tps_komersial.duckdb]
```

### B. User Query Flow (Request Entry & Validation)
```text
[User Input Pertanyaan di Frontend Vue 3]
       │
       ▼ (HTTP POST /api/v1/chat + Bearer JWT Header)
[FastAPI Entry Point: backend/main.py]
       │
       ├──► [Rate Limiting Check: >30 req/min?] ──(Ya)──► [HTTP 429 Rate Limit Error]
       │
       ├──► [Pre-Flight Specificity Check] ──────(Ambigu)► [Tolak Instan 0 Token + Contoh Kueri]
       │
       ├──► [Semantic Cache Redis Check] ────────(Hit)───► [Kembalikan Jawaban Instan 0 Token]
       │
       ▼ (Miss / Lolos Validasi)
[Masuk ke Multi-Agent LangGraph Pipeline]
```

### C. Agent Orchestration Flow (LangGraph State Machine)
```text
START
  │
  ▼
[Node 1: router (Gemini 3.1 Flash-Lite)]
  │  - Input  : user_query, katalog 9 tabel, role
  │  - Output : relevant_tables (Schema Pruning)
  ▼
[Tool: get_duckdb_schema (PRAGMA table_info)]
  │  - Mengambil skema kolom DuckDB hanya untuk tabel terpilih
  ▼
[Node 2: sql_gen (Gemini 3.6 Flash)]
  │  - Input  : user_query, schema, glosarium bisnis TPS, history[-6:]
  │  - Output : generated_sql (Zero-Shot)
  ▼
[Node 3: sanitizer (Python Rule Engine - 0 Token)]
  │  - Memeriksa multiple statements (;), komentar SQL, keyword DDL/DML, dan CTE
  │
  ├─── (Terblokir / Malicious) ─────────────────────────┐
  │                                                      │ (Bypass Database)
  └─── (Lolos Keamanan)                                  │
            │                                            │
            ▼                                            │
[Node 4: execute_sql (DuckDB Engine)]                    │
  │  - Eksekusi read-only ke tps_komersial.duckdb        │
  │  - Sanitasi NaN/Inf ke null                          │
  │  - Deteksi Fail-Fast (DATA_EMPTY / DB_SYNTAX_ERROR)  │
  │         │                                            │
  │         ▼ (query_result / error flag)                │
  │         │                                            │
  └─────────┼────────────────────────────────────────────┘
            │
            ▼
[Node 5: viz_gen (Groq OpenAI GPT-OSS-20B)]
  │  - Jika Sukses : Narasi Eksekutif (Max 15 baris sampel) + ECharts Config
  │  - Jika Error  : Respons Graceful Degradation (Saran kata kunci)
  ▼
END
```

---

# 15. IMPLEMENTATION STATUS MATRIX

| Komponen Sistem | Proposed / Intended Role | Actual Implementation di Proyek | Status | Bukti File Kode | Kesenjangan (Gap) |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **Medallion Ingestion** | Pipeline 3-layer data cleansing | Batch script Pandas membaca 9 berkas Excel dan menyimpan 9 tabel ke DuckDB | `IMPLEMENTED` | `backend/etl/main_etl.py`<br>`backend/etl/transformers.py` | Berbasis in-memory batch, bukan Delta Lake/Spark streaming. |
| **Pre-Flight Guard** | Pencegah kueri ambigu 0-token | Regex/Rule validator kata kunci metrik bisnis di FastAPI sebelum LangGraph | `IMPLEMENTED` | `backend/main.py:L150-L223` | Menggunakan keyword matching statis, belum menggunakan fuzzy similarity. |
| **Router Node** | Pemilah tabel relevan & RBAC | LLM Gemini 3.1 Flash-Lite memilih tabel dari katalog 9 tabel DuckDB | `IMPLEMENTED` | `backend/agents/router.py` | Berjalan optimal untuk kueri tabel tunggal dan gabungan. |
| **Text-to-SQL Generator** | Perakit SQL berbasis AI | LLM Gemini 3.6 Flash merakit sintaks SQL dengan glosarium semantik TPS | `IMPLEMENTED` | `backend/agents/sql_gen.py` | Bersifat Zero-Shot (belum ada pasangan Few-Shot dinamis). |
| **Security Sanitizer** | Penangkal SQL Injection & DDL | Regex validator mendeteksi titik koma, komentar, dan kata kunci DDL/DML | `IMPLEMENTED` | `backend/agents/sanitizer.py` | Berbasis rule matching lokal, belum menggunakan AST SQL compiler penuh. |
| **DuckDB Connection Pool** | Akses database analitik bersama | Singleton class mengelola koneksi read-only tunggal yang thread-safe | `IMPLEMENTED` | `backend/db.py` | Tidak ada kendala concurrency lock saat diuji bersamaan. |
| **Fail-Fast Error Handling** | Penanganan gagal kueri instan | Exception DuckDB ditangkap dan dialihkan ke viz_gen tanpa siklus retry | `IMPLEMENTED` | `backend/agents/execute.py`<br>`backend/agents/graph.py` | Mekanisme Self-Healing lama telah dibongkar sepenuhnya. |
| **Executive Viz Analyst** | Perangkum narasi bisnis | LLM Groq GPT-OSS-20B merangkum maksimal 15 baris sampel ke teks formal | `IMPLEMENTED` | `backend/agents/viz_gen.py` | Terbatas pada 15 baris sampel teratas. |
| **Apache ECharts Viewer** | Visualisasi grafik dinamis | Sub-generator JSON config ECharts dan viewer interaktif di Vue 3 | `IMPLEMENTED` | `backend/agents/chart_gen.py`<br>`frontend/.../EChartsViewer.vue` | Mendukung Bar, Line, dan Pie Chart. |
| **Asymmetric Model Tiering** | Pemisahan model heterogen | Pembagian beban: Gemini Lite (Router), Gemini Flash (SQL), Groq (Viz) | `IMPLEMENTED` | `backend/agents/llm_helper.py`<br>`credentials/api_keys.json` | Konfigurasi dapat diganti secara hot-swap via Admin Dashboard. |
| **Automated Benchmarking** | Evaluasi akurasi otomatis | Skrip Python mandiri membandingkan hasil 5 kueri analitik kompleks | `PARTIALLY IMPLEMENTED` | `backend/tes_kompleks.py` | Belum terintegrasi ke framework benchmark baku (RAGAS/BIRD). |
| **User Feedback Loop** | Rating kepuasan jawaban pengguna | Hanya tersedia telemetri performa sistem; belum ada tombol feedback di UI | `NOT FOUND` | `frontend/.../ChatMessage.vue` | Belum ada tombol thumbs up/down atau penyimpanan feedback user. |

---

# 16. CONFLICTS AND UNCERTAINTIES

Berikut adalah daftar ketidaksesuaian (*conflicts*) dan ketidakpastian yang ditemukan saat audit kode:

1. **[CONFLICT 1] Label UI "Self-Healing Active" vs Logika Nyata Fail-Fast:**
   - *Sumber 1 (Frontend):* [`frontend/src/components/ChatMessage.vue:L31-L33`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/frontend/src/components/ChatMessage.vue#L31-L33) menampilkan badge teks statis: `<span ...>Self-Healing Active</span>`.
   - *Sumber 2 (Backend):* [`backend/agents/graph.py:L38-L55`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/graph.py#L38-L55) dan [`backend/agents/execute.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/execute.py) secara tegas menerapkan alur linier **Fail-Fast Single-Pass (0 Retry)** dan telah menghapus fungsi self-healing loop.
   - *Verifikasi:* Badge UI tersebut merupakan teks *hardcoded* peninggalan versi lama yang belum diperbarui menjadi "Fail-Fast Active".
2. **[CONFLICT 2] Berkas CSV di `data/raw/csv/` vs Berkas Excel di `data/raw/*.xlsx`:**
   - *Sumber 1:* Terdapat subfolder `data/raw/csv/` berisi berkas CSV per-sheet.
   - *Sumber 2:* Script [`backend/etl/main_etl.py:L65-L72`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/etl/main_etl.py#L65-L72) membaca langsung dari berkas Excel `.xlsx` menggunakan `pd.read_excel`.
   - *Verifikasi:* Folder `data/raw/csv/` adalah artefak cadangan lama; pipeline ETL aktif bekerja langsung pada file `.xlsx`.
3. **[UNCERTAINTY 1] Dukungan Provider Ollama (Local LLM):**
   - *Kondisi:* Terpasang di `requirements.txt:L10` (`langchain-ollama`) dan ada pada dropdown menu Admin, namun dalam berkas `credentials/api_keys.json`, konfigurasi aktif seluruh step hanya menggunakan provider Google Gemini dan Groq Cloud.
   - *Status:* `PLANNED / PARTIALLY IMPLEMENTED`.
4. **[UNCERTAINTY 2] Anomali Dimensi Tahun pada Tabel Vessel Service:**
   - *Kondisi:* Pada tabel `fakta_vessel_service`, kueri `min/max` menemukan nilai `year = 0.0` dan `year = 2099.0` akibat baris kosong berformula pada lembar kerja Excel asal.
   - *Verifikasi:* Perlu ditambahkan filter `WHERE year BETWEEN 2020 AND 2026` saat analisis time-series untuk tabel ini.

---

# 17. THESIS-RELEVANT FACTS (FAKTA KUNCI UNTUK BAB 3)

Daftar 25 fakta teknis konkret dan terverifikasi untuk dituliskan pada BAB 3 Metodologi:

1. Sistem menggunakan basis data analitik lokal berbasis kolom (**DuckDB OLAP**) yang menyimpan 9 tabel fakta dengan total akumulasi ~32.054 baris data relasional.
2. Sumber data sistem berasal dari 9 berkas spreadsheet Microsoft Excel (`.xlsx`) operasional riil PT Terminal Petikemas Surabaya, bukan benchmark publik.
3. Pipeline pemrosesan data menerapkan pola **Medallion Architecture (Bronze ➔ Silver ➔ Gold)** di modul `backend/etl/main_etl.py`.
4. Tahap Bronze mengekstrak data mentah langsung dari seluruh sheet berkas Excel as-is ke dalam memori DataFrame dan arsip CSV.
5. Tahap Silver melakukan pembersihan kolom kosong `Unnamed`, penanganan missing value, standardisasi nama operator `lop`, dan pemaksaan numerik `paksa_angka()`.
6. Tahap Gold melakukan unpivot otomatis pada format pivot tabel Market Share, standardisasi penamaan kolom SQL snake_case, dan konsolidasi multi-sheet.
7. Seluruh tabel analitik akhir disimpan secara fisik pada berkas lokal persisten `data/processed/tps_komersial.duckdb`.
8. Orkestrasi sistem AI diatur menggunakan **LangGraph StateGraph** yang terdiri dari 5 node fungsional: `router`, `sql_gen`, `sanitizer`, `execute_sql`, dan `viz_gen`.
9. Sistem menerapkan paradigma **Asymmetric Multi-LLM Tiering**, memisahkan beban kerja ke 2 provider cloud komputasi dan 3 model AI yang berbeda.
10. Node Router (STEP 1) menggunakan model ringan **`gemini-3.1-flash-lite`** untuk efisiensi biaya dan latensi klasifikasi tabel.
11. Node SQL Generator (STEP 2) menggunakan model penalaran standar **`gemini-3.6-flash`** untuk akurasi sintesis logika kueri DuckDB SQL.
12. Node Viz Analyst (STEP 5) menggunakan model berkecepatan tinggi **`openai/gpt-oss-20b` via Groq Cloud** untuk menghasilkan narasi bisnis eksekutif dan konfigurasi Apache ECharts.
13. Pemilihan model bersifat *Dynamic Runtime Configurable* melalui Admin Dashboard tanpa memerlukan restart server backend.
14. Sistem menerapkan mekanisme **Pre-Flight Query Specificity Guard** di layer FastAPI untuk menolak pertanyaan ambigu tanpa metrik (0 Token LLM).
15. Sistem menerapkan teknik **Schema Pruning**: Router hanya meloloskan 1–2 tabel relevan sehingga memangkas 80% skema database yang tidak diperlukan dari prompt SQL Generator.
16. Sistem menerapkan teknik **SQL-Only History Injection**: Pada obrolan multi-turn, prompt hanya menyertakan kueri SQL sebelumnya, membuang teks narasi panjang 1.000 kata untuk menghemat token konteks.
17. Sistem menerapkan teknik **Smart Row Sampling**: Data hasil kueri dipotong maksimal hanya **15 baris sampel teratas** sebelum dikirim ke LLM visualisasi naratif.
18. Node Sanitizer (STEP 3) bekerja secara deterministik tanpa LLM (0 Token) untuk memblokir kueri titik koma (`;`), komentar SQL, dan kata kunci DDL/DML terlarang.
19. Koneksi DuckDB saat runtime AI dikunci pada mode **`read_only=True`** oleh connection pool terpusat (`backend/db.py`).
20. Sistem mengadopsi prinsip **Zero Data Leakage**: Berkas Excel mentah dan seluruh database operasional tidak pernah dikirim ke pihak penyedia LLM cloud.
21. Sistem menerapkan paradigma **Fail-Fast Error Handling Single-Pass**: Mekanisme Self-Healing (retry loop hingga 3 kali) telah dihapuskan untuk menghemat token dan latensi.
22. Jika terjadi kegagalan (Sanitizer Blocked, Syntax Error, atau Data Empty), proses langsung dialihkan ke node visualisasi untuk memberikan respons *Graceful Degradation*.
23. Memori riwayat percakapan dikelola secara dual-layer: **Redis RAM** untuk akses real-time (<1ms) dengan sliding window 3 percakapan terakhir (`[-6:]`), dan **Berkas JSON Disk** untuk persistensi permanen.
24. Sistem telah diuji menggunakan **9 Unit Tests Pytest** otomatis pada modul ETL, Router, dan Sanitizer dengan tingkat kelulusan 100% (`9 passed in 0.69s`).
25. Sistem observabilitas mencatat latensi milidetik dan konsumsi token LLM secara asinkron ke database terpisah `data/processed/telemetry.duckdb` pada tabel `log_audit_token`.

---

# 18. DO NOT CLAIM (HAL-HAL YANG DILARANG DIKLAIM DI SKRIPSI)

Untuk menjaga integritas dan kejujuran akademik penulisan Tugas Akhir, **JANGAN MENULISKAN hal-hal berikut sebagai klaim implementasi**:

1. ❌ **Jangan mengklaim sistem masih menggunakan mekanisme Self-Healing Loop atau perbaikan kueri berulang kali.**  
   *Fakta:* Mekanisme Self-Healing telah resmi dibongkar dan diganti dengan alur linier **Fail-Fast Single-Pass (0 Retry)**.
2. ❌ **Jangan mengklaim sistem menggunakan teknologi streaming real-time atau Delta Lake CDC.**  
   *Fakta:* Pipeline Medallion diimplementasikan secara **Lightweight In-Memory Batch Script** menggunakan Pandas dan DuckDB fisik.
3. ❌ **Jangan mengklaim sistem telah diuji melalui User Acceptance Testing (UAT) resmi dengan kuesioner baku (SUS/TAM) kepada staf direksi PT TPS.**  
   *Fakta:* Pengujian saat ini berada pada tahap pengujian internal fungsi dan akurasi oleh pengembang (*Developer Alpha Testing*).
4. ❌ **Jangan mengklaim sistem memiliki antarmuka Feedback Rating pengguna (Thumbs Up/Down).**  
   *Fakta:* Antarmuka UI chat belum memiliki tombol umpan balik pengguna; yang tersedia baru logging telemetri mesin di `telemetry.duckdb`.
5. ❌ **Jangan mengklaim sistem menggunakan model open-source lokal via Ollama dalam operasional defaultnya.**  
   *Fakta:* Walaupun library terpasang, sistem saat ini beroperasi 100% menggunakan Cloud API (Google Gemini dan Groq).
6. ❌ **Jangan mengklaim sistem menerapkan Few-Shot Prompting dinamis pada perakitan SQL.**  
   *Fakta:* Node SQL Generator murni bekerja secara **Zero-Shot** berbasis glosarium aturan domain dan skema kolom.
7. ❌ **Jangan mengklaim sistem menggunakan database server eksternal mandiri (seperti PostgreSQL / MySQL) untuk penyimpanan analitik.**  
   *Fakta:* Database analitik 100% disimpan dan dieksekusi secara lokal menggunakan mesin kolumnar **DuckDB**.
8. ❌ **Jangan mengklaim seluruh data tabel DuckDB dikirimkan ke LLM untuk membuat narasi.**  
   *Fakta:* Pengiriman data ke LLM narasi dibatasi secara ketat maksimal hanya **15 baris sampel teratas** (*Smart Row Sampling*).
