# 🔍 Deep Dive: Proyek RAG Komersial TPS

Analisis komprehensif seluruh proyek **AI Data Agent** untuk PT Terminal Petikemas Surabaya.

---

## 1. Visi & Tujuan Proyek

Proyek ini adalah **Tugas Akhir** oleh Nabiel Nizar Anwari (NIM 5027231087, ITS) yang membangun **AI Data Agent** berbasis:
- **Multi-Agent Text-to-SQL** — LLM menerjemahkan bahasa natural → SQL DuckDB
- **Medallion Architecture** — ETL pipeline tiga lapis (Bronze → Silver → Gold)
- **Self-Healing Loop** — Koreksi mandiri SQL hingga 3 kali percobaan

**Studi kasus:** Divisi Komersial PT TPS, mengolah data operasional pelabuhan petikemas (vessel, throughput, market share, transhipment, dll).

---

## 2. Arsitektur Sistem (High-Level)

```mermaid
flowchart LR
    subgraph DATA["📊 Data Engineering (ETL)"]
        A["Excel .xlsx\n(data/raw/)"] -->|Bronze| B["Pandas Read"]
        B -->|Silver| C["Cleaning +\nSkema Standar"]
        C -->|Gold| D["Unpivot/Melt +\nDuckDB Load"]
    end

    subgraph AI["🤖 AI Orchestration (LangGraph)"]
        E["User Query"] --> F["sql_gen\n(Gemini 3.6 Flash)"]
        F --> G["execute_sql\n(DuckDB)"]
        G -->|Error / Empty| F
        G -->|Success| H["viz_gen\n(Groq GPT-OSS-20B)"]
    end

    subgraph API["🌐 FastAPI"]
        I["POST /api/v1/chat"]
        J["GET /api/v1/data/status"]
    end

    D --> G
    H --> I
```

---

## 3. Struktur Direktori Proyek

```
rag-komersial-tps/
├── README.md                    # Blueprint arsitektur (judul TA)
├── SYSTEM_CONTEXT.md            # Technical blueprint & system prompt reference
├── requirements.txt             # Dependencies Python
├── test_db.py                   # Skrip tes koneksi DuckDB
├── test_viz.py                  # Skrip tes VizGen node
│
├── backend/
│   ├── .env                     # API keys (Gemini, Groq)
│   ├── BACKEND.MD               # Dokumentasi developer backend
│   ├── main.py                  # Entry point FastAPI
│   ├── agents/                  # Orkestrasi AI (LangGraph)
│   │   ├── state.py             # AgentState TypedDict
│   │   ├── graph.py             # StateGraph builder + conditional router
│   │   ├── sql_gen.py           # Node: Text-to-SQL (Gemini)
│   │   ├── execute.py           # Node: Eksekusi SQL + deteksi empty
│   │   └── viz_gen.py           # Node: NLG + ECharts JSON (Groq)
│   └── etl/                     # Pipeline Medallion
│       ├── main_etl.py          # Orchestrator ETL (router per file)
│       ├── transformers.py      # Fungsi transformasi per dataset
│       └── utils.py             # Helpers: cleaning, logging, debug CSV
│
├── data/
│   ├── raw/                     # 9 file Excel sumber (.xlsx)
│   ├── bronze/                  # 17 CSV checkpoint (data mentah)
│   ├── silver/                  # 17 CSV checkpoint (data bersih)
│   ├── gold/                    # 17 CSV checkpoint (data matang)
│   └── processed/
│       └── tps_komersial.duckdb # Database persisten (~2.1 MB)
│
├── milestone/                   # Dokumentasi per fase
│   ├── MILESTONE1.MD            # ETL Pipeline ✅
│   ├── MILESTONE2.MD            # Text-to-SQL Core ✅
│   ├── MILESTONE3.MD            # Self-Healing + Semantic Layer ✅
│   └── MILESTONE4.MD            # Visualisasi ECharts ✅
│
└── logs/                        # ETL system logs (RotatingFileHandler)
```

---

## 4. Pipeline ETL (Medallion Architecture)

### 4.1 Sumber Data (9 File Excel)

| File Excel | Ukuran | Deskripsi |
|---|---|---|
| `Container Throughput.xlsx` | 18 KB | KPI throughput container (Domestik + Internasional) |
| `Komersial Dashboard.xlsx` | 186 KB | Dashboard agregat komersial |
| `Market Share.xlsx` | 467 KB | Data pangsa pasar per operator |
| `OVERVIEW BOX.xlsx` | 72 KB | Ringkasan operasi box/container |
| `OVERVIEW VESSEL.xlsx` | 119 KB | Operasional kapal per bulan |
| `Realisasi UC.xlsx` | 269 KB | Realisasi Unit Cost |
| `RestNDisc.xlsx` | 15 KB | Restitusi & Diskon |
| `Transhipment.xlsx` | 1.4 MB | Data transhipment (terbesar) |
| `VESSEL SERVICE.xlsx` | 471 KB | Layanan kapal detail |

> **PENTING:**
> Saat ini hanya **3 file** yang di-route oleh ETL (`FILE_ROUTER` di `main_etl.py`):
> - `OVERVIEW VESSEL.xlsx` → `proses_vessel` → tabel `fakta_vessel`
> - `Container Throughput.xlsx` → `proses_throughput` → tabel `fakta_throughput`
> - `Market Share.xlsx` → `proses_market_share` → tabel `fakta_market_share`
>
> **6 file lainnya** (Komersial Dashboard, Realisasi UC, RestNDisc, Transhipment, VESSEL SERVICE, OVERVIEW BOX) **belum memiliki transformer** dan belum diproses ke DuckDB.

### 4.2 Alur Transformasi

```mermaid
flowchart TD
    A["Excel .xlsx<br/>(pd.read_excel sheet_name=None)"] -->|"BRONZE"| B["CSV Mentah<br/>(checkpoint debug)"]
    B -->|"SILVER"| C["hapus_kolom_hantu()<br/>paksa_angka()<br/>Standarisasi Skema"]
    C -->|"GOLD"| D["Unpivot (pd.melt)<br/>Label kategori_layanan<br/>Standarisasi kolom snake_case"]
    D -->|"LOAD"| E["pd.concat per tabel fakta<br/>→ DuckDB CREATE OR REPLACE TABLE"]
```

### 4.3 Fungsi Utilitas Kunci (`utils.py`)

| Fungsi | Tujuan |
|---|---|
| `hapus_kolom_hantu` | Hapus kolom Unnamed, baris/kolom NaN, replace dash "-" → 0, rename "%" → "persentase", disambiguasi kolom TEUS duplikat |
| `paksa_angka` | Konversi string ke numerik (hapus koma ribuan, coerce errors → 0) |
| `pastikan_kolom_unik` | Cegah error concat akibat kolom duplikat |
| `simpan_debug_csv` | Simpan checkpoint CSV per layer jika `DEBUG_MODE=True` |

---

## 5. Database DuckDB — Skema & Data

File: `data/processed/tps_komersial.duckdb` (~2.1 MB)

### 5.1 Tabel Inti (Fakta) — Hasil ETL Konsolidasi

Berdasarkan `FILE_ROUTER`, dihasilkan **3 tabel fakta utama**:

#### Tabel `fakta_vessel`
Sumber: `OVERVIEW VESSEL.xlsx` (sheet Domestic + International digabung)
| Kolom | Deskripsi |
|---|---|
| `date`, `year`, `month_code`, `month` | Dimensi waktu |
| `lop` | Line Operator (EMC, SSL, CNC, MSC, SPI, TIL, dll) |
| `teus`, `boxes`, `bch`, `bsh` | Metrik operasional kapal |
| `kategori_layanan` | 'DOMESTIC' atau 'INTERNATIONAL' |

#### Tabel `fakta_throughput`
Sumber: `Container Throughput.xlsx` (sheet Domestik + International)
| Kolom | Deskripsi |
|---|---|
| `year`, `month`, `description`, `unit` | Dimensi & deskripsi |
| `actual`, `budget`, `actual_vs_budget` | KPI throughput vs target |
| `kategori_layanan` | 'DOMESTIK' atau 'INTERNATIONAL' |

#### Tabel `fakta_market_share`
Sumber: `Market Share.xlsx` (multi-sheet, termasuk Unpivot kolom tahun)
| Kolom | Deskripsi |
|---|---|
| `lop` | Line Operator |
| `teus`, `persentase` | Volume & pangsa pasar |
| `tahun_kategori`, `total_teus` | Hasil Unpivot kolom tahun |
| `sumber_sheet` | Asal sheet (SL DOM, SL INT, B.OPR DOM, dll) |

### 5.2 Tabel Sheet Individu (Gold Layer CSVs)

Selain 3 tabel konsolidasi, gold layer juga menghasilkan 17 CSV terpisah yang merepresentasikan tiap sheet individual. Data-data ini semuanya dimuat ke DuckDB (masing-masing jadi tabel tersendiri karena proses `pd.concat` per `nama_tabel`).

> **CATATAN:**
> Karena semua sheet dari `Market Share.xlsx` di-route ke `proses_market_share` yang mengembalikan `nama_tabel = "fakta_market_share"`, semua sheet-nya akan digabung (concat) ke satu tabel. Demikian juga untuk vessel dan throughput.

---

## 6. Orkestrasi AI (LangGraph Multi-Agent)

### 6.1 State Machine

Didefinisikan di `state.py`:

```python
class AgentState(TypedDict):
    user_query: str                  # Pertanyaan user
    generated_sql: Optional[str]     # SQL rakitan LLM
    sql_error: Optional[str]         # Error message (trigger self-healing)
    correction_attempts: int         # Counter percobaan (max 3)
    query_result: Optional[List[dict]]  # Hasil DuckDB
    final_answer: Optional[str]      # Narasi jawaban
    echarts_config: Optional[dict]   # JSON konfigurasi grafik
```

### 6.2 Graf Eksekusi (`graph.py`)

```mermaid
stateDiagram-v2
    [*] --> sql_gen
    sql_gen --> execute_sql
    execute_sql --> sql_gen : Error & attempts < 3\n(Self-Healing)
    execute_sql --> viz_gen : Success / Max Attempts
    viz_gen --> [*]
```

Fungsi `should_continue` menentukan apakah lanjut ke `viz_gen` atau putar balik ke `sql_gen`.

### 6.3 Node 1: SQL Generator (`sql_gen.py`)

- **LLM:** `gemini-3.6-flash` via `langchain-google-genai`
- **Dynamic Schema Injection:** Query `information_schema.columns` real-time dari DuckDB
- **Semantic Layer (Glosarium Bisnis):**
  - "Domestik" → `DOMESTIC` / `DOM`
  - "Internasional" → `INTERNATIONAL` / `INT`
  - Kolom "Unit" = `TEUs`, bukan `BOXES`
  - Wajib `ILIKE` untuk case-insensitive
- **Self-Healing Input:** Menerima `sql_error` dari percobaan sebelumnya dalam prompt

### 6.4 Node 2: SQL Executor (`execute.py`)

- Eksekusi SQL di DuckDB (read-only mode)
- **Deteksi data kosong:**
  - 0 baris → empty
  - 1 baris, semua value `None`/`NaN` → empty (aggregasi null)
- Increment `correction_attempts` untuk trigger self-healing
- Convert datetime columns ke string untuk serialisasi JSON

### 6.5 Node 3: Visualization Generator (`viz_gen.py`)

- **LLM:** `openai/gpt-oss-20b` via `langchain-groq` (Groq inference)
- **Pydantic Structured Output** (`VizOutput`) memaksa output terstruktur:
  - `answer`: Narasi teks profesional
  - `echarts_config`: JSON Apache ECharts (bar/line/pie) atau dict kosong

> **CATATAN:**
> sql_gen menggunakan **Gemini** (Google), sedangkan viz_gen menggunakan **Groq** — dua provider LLM berbeda. Ini menarik karena SQL generation dianggap membutuhkan reasoning yang lebih kuat (Gemini 3.6 Flash), sedangkan NLG + chart formatting menggunakan Groq yang sangat cepat.

---

## 7. API Layer (`main.py`)

### Endpoints

| Method | Path | Fungsi |
|---|---|---|
| `POST` | `/api/v1/chat` | Terima query → jalankan LangGraph → return answer + chart |
| `GET` | `/api/v1/data/status` | Cek status ETL (saat ini di-mock) |

### Request/Response Model

```python
# Request
class ChatRequest(BaseModel):
    query: str
    user_id: str = "guest"
    role: str = "commercial"

# Response
class ChatResponse(BaseModel):
    status: str              # "success" | "error"
    answer: str              # Narasi jawaban
    chart_config: dict | None  # ECharts JSON
    sql_executed: str | None   # SQL yang dieksekusi
    error: str | None          # Pesan error (jika ada)
    data: list | None          # Raw query result
```

> **PERINGATAN:**
> CORS dikonfigurasi `allow_origins=["*"]` — ini aman untuk prototyping tapi **HARUS diubah** untuk production.

---

## 8. Progress Milestone

| Milestone | Status | Deliverable |
|---|---|---|
| **M1** — Data Engineering ETL | ✅ Selesai | Pipeline Medallion, 3 tabel fakta di DuckDB |
| **M2** — AI Text-to-SQL Core | ✅ Selesai | FastAPI + LangGraph linear (sql_gen → execute) |
| **M3** — Advanced Orchestration | ✅ Selesai | Semantic Layer, Self-Healing Loop (max 3 retry) |
| **M4** — Visualisasi ECharts | ✅ Selesai | Pydantic Structured Output, echarts_config JSON |
| **M5** — Frontend UI/UX | ✅ Selesai | Vue.js 3 + Tailwind CSS + Apache ECharts + Glassmorphism |

---

## 9. Gap Analysis & Temuan Penting

### 🔴 Isu Kritis

1. **6 dari 9 file Excel belum diproses ETL**
   - `Komersial Dashboard.xlsx`, `Realisasi UC.xlsx`, `RestNDisc.xlsx`, `Transhipment.xlsx` (1.4 MB, file terbesar!), `VESSEL SERVICE.xlsx`, `OVERVIEW BOX.xlsx` — semua belum punya transformer
   - Artinya LLM hanya bisa menjawab pertanyaan seputar vessel, throughput, dan market share

2. **Belum ada Router Agent (Agen 1)**
   - Berdasarkan `SYSTEM_CONTEXT.md`, seharusnya ada `RouterNode` untuk memilih tabel relevan sebelum SQL gen
   - Saat ini SQL gen langsung menerima **seluruh skema** — boros token dan rawan salah pilih tabel

3. **Belum ada RBAC (Role-Based Access Control)**
   - `user_id` dan `role` diterima di request tapi **tidak digunakan** di LangGraph
   - Tidak ada `RBACNode` atau `CheckCacheNode` yang di-mention di blueprint

4. **Belum ada Redis Semantic Cache**
   - Disebutkan di arsitektur tapi belum diimplementasi

5. **Hard Rules Sanitizer belum ada**
   - Seharusnya ada node validasi SQL (hanya 1 SELECT, tabel valid, format DuckDB) sebelum eksekusi

### 🟡 Isu Sedang

6. **Inkonsistensi `kategori_layanan`** pada tabel fakta_throughput
   - Sheet "Domestik" menghasilkan `kategori_layanan = 'DOMESTIK'` (bahasa Indonesia)
   - Sheet lain menggunakan `'DOMESTIC'` (bahasa Inggris)
   - Ini bisa membingungkan LLM meski sudah ada Glosarium

7. **`DUCKDB_PATH` di .env** mengarah ke `../data/processed/tps_komersial.duckdb`
   - Ini adalah relative path dari `backend/` yang bekerja saat menjalankan dari `backend/`
   - Tapi `BASE_DIR` di kode sudah resolve ke absolute path — bisa terjadi konflik

8. **Tidak ada unit test formal** — hanya ada `test_db.py` dan `test_viz.py` sebagai skrip ad-hoc

9. **Belum ada frontend sama sekali** — Milestone 5 belum dimulai

### 🟢 Hal Positif

10. **ETL sangat rapi** — Logging dengan RotatingFileHandler, debug CSV checkpoint, modular transformers
11. **Self-Healing bekerja baik** — Deteksi syntax error + empty result + pesan teguran kontekstual
12. **Dual-LLM strategy** cerdas — Gemini untuk code-gen, Groq untuk narasi (menghindari bottleneck satu provider)
13. **Pydantic Structured Output** di viz_gen — mencegah LLM menghasilkan JSON yang rusak
14. **Dokumentasi sangat baik** — Setiap milestone didokumentasikan dengan jelas dan naratif

---

## 10. Tech Stack Aktual vs Rencana

| Komponen | Rencana (README) | Implementasi Aktual |
|---|---|---|
| Backend | FastAPI | ✅ FastAPI |
| Database | DuckDB Persistent | ✅ DuckDB |
| ETL | Pandas + Medallion | ✅ Pandas |
| Orchestrator | LangGraph | ✅ LangGraph |
| LLM (SQL) | Gemini 1.5 Flash | ⚠️ `gemini-3.6-flash` (lebih baru) |
| LLM (Viz) | Gemini | ⚠️ Groq `gpt-oss-20b` (provider berbeda) |
| Validasi Data | Pandera/Pydantic | ❌ Belum ada (manual cleaning saja) |
| Cache | Redis Semantic | ❌ Belum ada |
| Scheduler | APScheduler/Watchdog | ❌ Belum ada (ETL manual) |
| Frontend | Vue.js 3 + Tailwind + ECharts | ❌ Belum ada (Milestone 5) |

---

## 11. Peta Jalan: Apa yang Perlu Dikerjakan Selanjutnya

Berdasarkan analisis di atas, urutan prioritas pengembangan:

### Milestone 5 — Frontend UI/UX (Prioritas Utama)
- [x] Inisialisasi Vue.js 3 project di folder `frontend/`
- [x] Integrasi Tailwind CSS & Custom Glassmorphism System
- [x] Komponen chatbot (input, message history, pipeline loading states)
- [x] Render Apache ECharts dari `echarts_config` JSON
- [x] Responsive design & maritime aesthetic polish

### Backend Enhancements (Bisa Paralel)
- [ ] Tambah transformer untuk 6 file Excel yang belum diproses
- [x] Implementasi Router Agent (pilih tabel relevan)
- [x] Implementasi Hard Rules Sanitizer
- [ ] Implementasi RBAC (filter berdasarkan role)
- [ ] Setup Redis Semantic Cache
- [ ] Validasi Data Contract (Pandera/Pydantic)
- [x] Fix inkonsistensi `DOMESTIK` vs `DOMESTIC`

---

> **TIP:**
> **Untuk developer baru:** Jika AI mulai keliru, hal pertama yang harus diperiksa adalah **Glosarium di `sql_gen.py`**. Tambahkan fakta bisnis baru ke dalam prompt untuk "mendidik" AI.
