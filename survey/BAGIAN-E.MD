# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN E
## ARSITEKTUR MULTI-AGENT & EKOSISTEM KOMPUTASI AI

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Static Code Walkthrough (`backend/agents/`), LangGraph Graph Compilation Tracing (`graph.py`), & Dynamic LLM Configuration Review (`llm_helper.py`, `api_keys.json`)

---

### 1. Berapa Agent / Node yang Benar-Benar Ada?
Berdasarkan kompilasi graf LangGraph pada [`backend/agents/graph.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/graph.py#L29-L36), terdapat **5 Node Utama di dalam Graph State Machine**, ditambah **1 Pre-Flight Guard Gate** di layer FastAPI dan **1 Sub-Module Generator**:

* **Node di dalam Graf LangGraph (5 Node):**
  1. `router` (Router Agent)
  2. `sql_gen` (Text-to-SQL Generator Agent)
  3. `sanitizer` (Security Sanitizer Guardrail Node)
  4. `execute_sql` (DuckDB Execution Engine Node)
  5. `viz_gen` (Visualization & Narrative Analyst Agent)
* **Node Pendukung Eksternal Graf (2 Modul):**
  6. `pre_flight_guard` (Pre-Flight Specificity Validator di `backend/main.py`)
  7. `chart_gen` (Sub-generator visualisasi Apache ECharts di `backend/agents/chart_gen.py`)

---

### 2. Nama, Role, dan Tanggung Jawab Masing-Masing Entitas

| No | Nama Node / Modul | Role Teknis | Klasifikasi Entitas |
| :-: | :--- | :--- | :--- |
| 0 | `pre_flight_guard` | **Gatekeeper Anti-Ambigu** | *Deterministic Rule Engine* (0 Token LLM) |
| 1 | `router` | **Semantic Dispatcher & Access Controller** | **Cognitive LLM Agent** |
| 2 | `sql_gen` | **Data Engineer & SQL Synthesizer** | **Cognitive LLM Agent** |
| 3 | `sanitizer` | **Security Firewall & Query Inspector** | *Deterministic Rule Engine* (0 Token LLM) |
| 4 | `execute_sql` | **Database Query Runner & Fast-Fail Detector** | *Deterministic Execution Tool* (0 Token LLM) |
| 5 | `viz_gen` | **Executive Business Analyst & Communicator** | **Cognitive LLM Agent** |
| - | `chart_gen` | **Visual Analytics Architect** | **Cognitive LLM Sub-Agent** |

---

### 3. Fungsi Masing-Masing Entitas
1. **`pre_flight_guard` (`backend/main.py`):** Menyaring pertanyaan di gerbang awal sebelum menyentuh LLM; menolak pertanyaan tanpa metrik bisnis (misal: *"berapa total 2025"* atau *"kalau 2024"*).
2. **`router` (`backend/agents/router.py`):** Menganalisis pertanyaan bisnis pengguna dan menentukan 1–2 tabel DuckDB yang paling relevan dari katalog 9 tabel serta memfilter hak akses peran (*Role-Based Access Control*).
3. **`sql_gen` (`backend/agents/sql_gen.py`):** Mengambil skema kolom dari tabel yang dipilih Router, menerapkan glosarium analitik PT TPS, dan merakit kueri SQL DuckDB murni yang presisi.
4. **`sanitizer` (`backend/agents/sanitizer.py`):** Memvalidasi keamanan sintaks SQL (mencegah SQL Injection, pemblokiran DDL perusak seperti DROP/DELETE, dan validasi CTE table).
5. **`execute_sql` (`backend/agents/execute.py`):** Menjalankan SQL ke DuckDB, mensterilkan anomali angka float (`NaN/Infinity` ➔ `null`), dan mendeteksi data kosong (*Fail-Fast Empty Detection*).
6. **`viz_gen` (`backend/agents/viz_gen.py`):** Menerjemahkan angka mentah menjadi narasi bisnis eksekutif (format TEUs/Rp, penomoran rapi) dan memberikan panduan ramah jika data kosong (*Graceful Degradation*).
7. **`chart_gen` (`backend/agents/chart_gen.py`):** Merakit konfigurasi JSON Apache ECharts jika pengguna secara eksplisit meminta grafik atau tren visual.

---

### 4 & 5. Matriks Input dan Output Masing-Masing Entitas

| Node / Modul | Input Data | Output Data |
| :--- | :--- | :--- |
| **`pre_flight_guard`** | `request.query` (String pertanyaan asli) | `is_specific` (Boolean) & `guidance_msg` (String panduan) |
| **`router`** | `user_query`, `role`, `chat_history[-6:]`, Katalog 9 Tabel DuckDB | `relevant_tables` (List nama tabel, contoh: `['fakta_throughput']`) |
| **`sql_gen`** | `user_query`, `relevant_tables`, Skema Kolom (`PRAGMA table_info`), Glosarium Bisnis TPS | `generated_sql` (String SQL DuckDB murni) |
| **`sanitizer`** | `user_query`, `generated_sql`, Daftar tabel valid di database | `sql_error` (`None` jika lolos, atau string alasan blokir keamanan) |
| **`execute_sql`** | `generated_sql`, Koneksi `DuckDBPool` | `query_result` (List of dicts data baris) atau `DATA_EMPTY` |
| **`viz_gen`** | `user_query`, `query_result` (maks 15 baris sampel), `sql_error` | `final_answer` (Narasi teks berformat eksekutif resmi) |
| **`chart_gen`** | `user_query`, `query_result` mentah | `echarts_config` (Struktur JSON valid Apache ECharts) |

---

### 6 & 7. Penggunaan LLM dan Model yang Digunakan
Sistem menerapkan prinsip **Multi-LLM Tiering & Specialization** (Model berbeda sesuai beban kognitif tugas):

| Node / Komponen | Menggunakan LLM? | Model AI yang Digunakan (Aktif) | Provider AI | Alasan Pemilihan Model |
| :--- | :---: | :--- | :--- | :--- |
| `pre_flight_guard` | **TIDAK (0 Token)** | *None (Regex / Python Rule)* | Local Native | Eksekusi instan 0 ms tanpa biaya token. |
| **`router` (STEP 1)** | **YA** | **`gemini-3.1-flash-lite`** | Google GenAI | Model teringan dan paling murah; ideal untuk klasifikasi teks cepat. |
| **`sql_gen` (STEP 2)** | **YA** | **`gemini-3.6-flash`** | Google GenAI | Presisi reasoning logika tinggi untuk sintaks analitik SQL kompleks. |
| `sanitizer` (STEP 3) | **TIDAK (0 Token)** | *None (Regex / AST Parser)* | Local Native | Menjamin deterministik 100% tanpa celah halusinasi keamanan. |
| `execute_sql` (STEP 4)| **TIDAK (0 Token)** | *None (DuckDB Engine)* | Local Native | Eksekusi database lokal berkecepatan tinggi (<50 ms). |
| **`viz_gen` (STEP 5)** | **YA** | **`openai/gpt-oss-20b`** | Groq Cloud | Latensi cetak token super cepat (*high TPS*), kuota API terpisah dari Gemini. |
| `chart_gen` (Sub) | **YA** | **`openai/gpt-oss-20b`** | Groq Cloud | Output terstruktur JSON handal untuk visualisasi ECharts. |

---

### 8. Apakah Ada Agent yang Menggunakan Model Berbeda?
* **Jawaban:** **YA, BENAR.**  
* **Pola Arsitektur:** Sistem sengaja menggunakan **Arsitektur Hibrida Multi-Provider (Google Gemini + Groq Cloud)**:
  - **Google Gemini** dialokasikan untuk fase **Logika & Pemrosesan Data** (`Router` dan `SQL Gen`) karena keunggulannya dalam penalaran struktural SQL dan kapasitas konteks.
  - **Groq Cloud** dialokasikan untuk fase **Sintesis Narasi & Visualisasi** (`Viz Gen` dan `Chart Gen`) karena kecepatan komputasi LPU Groq yang menghasilkan teks eksekutif dan format JSON dalam hitungan sepersekian detik tanpa menghabiskan kuota token Google Gemini.
* **Manajemen API Key Independen:** Masing-masing step memiliki slot kunci API terisolasi di `credentials/api_keys.json` yang dapat dirotasi dan diganti modelnya secara dinamis melalui Admin Dashboard.

---

### 9. Klasifikasi Nyata: Mana yang "Agent" vs "Deterministic Function/Tool"?

Untuk keperluan pelaporan metodologi BAB 3 Skripsi yang presisi:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   KLASIFIKASI KOMPONEN SISTEM                          │
├──────────────────────────────────┬─────────────────────────────────────┤
│   COGNITIVE AI AGENTS (LLM)      │   DETERMINISTIC TOOLS (NON-LLM)     │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 1. Router Agent (router.py)      │ 1. Pre-Flight Guard (main.py)       │
│    - Menggunakan LLM Gemini-Lite │    - Regex & Rule Keyword Matching   │
│    - Keputusan klasifikasi tabel │                                     │
│                                  │ 2. Schema Linking Tool (sql_gen.py) │
│ 2. SQL Gen Agent (sql_gen.py)    │    - Ekstraksi PRAGMA table_info     │
│    - Menggunakan LLM Gemini-Flash│                                     │
│    - Sintesis kode SQL dari teks │ 3. Security Sanitizer (sanitizer.py)│
│                                  │    - Regex DDL/DML & AST CTE parser │
│ 3. Viz Gen Agent (viz_gen.py)    │                                     │
│    - Menggunakan LLM Groq        │ 4. Execution Tool (execute.py)      │
│    - Perumusan narasi eksekutif  │    - DuckDB Driver Query Execution  │
│                                  │                                     │
│ 4. Chart Gen Agent (chart_gen.py)│ 5. Session Caching (cache.py)       │
│    - Menggunakan LLM Groq        │    - Redis Key-Value Operations     │
│    - Sintesis JSON ECharts       │                                     │
└──────────────────────────────────┴─────────────────────────────────────┘
```

---

### 10. Perbandingan Struktur Konseptual vs Struktur Aktual Project

Pengguna mengusulkan struktur konseptual:
> *User → Router → Schema Linking / Schema Pruning → SQL Generator → Sanitizer / Validator → Execute → Viz Analyst → Output*

#### ✅ Hasil Evaluasi Auditor terhadap Struktur Aktual:
Struktur aktual proyek **SANGAT MENDEKATI** alur konseptual tersebut, dengan **dua penyempurnaan nyata pada kode produksi**:

1. **Penambahan Pre-Flight Guard di Pintu Masuk:** Sebelum masuk ke Router, terdapat filter berbasis aturan untuk menolak kueri ambigu secara instan tanpa membebani LLM (0 Token).
2. **Schema Linking Berada di Dalam Node SQL Generator:** Schema linking tidak dibuat sebagai node LangGraph mandiri yang terpisah, melainkan dieksekusi sebagai *internal programmatic function* di awal `sql_gen_node` untuk menarik kolom tabel terpilih.
3. **Penerapan Conditional Edge Fail-Fast pada Sanitizer:** Jika Sanitizer memblokir kueri, alur **melompati (bypass)** node `execute_sql` dan langsung meloncat ke `viz_gen` untuk menyajikan notifikasi keamanan secara ramah (*Fail-Safe*).

#### 🗺️ Diagram Alur Aktual di Kode (`backend/agents/graph.py` & `main.py`):

```text
[User Prompt]
      │
      ▼
[Pre-Flight Specificity Guard] ──(Ambigu)──► [Direct 0-Token Guidance Output]
      │ (Spesifik)
      ▼
[Semantic Cache Check (Redis)] ──(Hit)─────► [Instant 0-Token Cached Output]
      │ (Miss)
      ▼
[ROUTER NODE (LLM Gemini 3.1)] 
      │ (Menghasilkan: relevant_tables -> Schema Pruning)
      ▼
[Schema Linking Tool: PRAGMA table_info()]
      │
      ▼
[SQL GENERATOR NODE (LLM Gemini 3.6)]
      │ (Menghasilkan: generated_sql)
      ▼
[SANITIZER NODE (Deterministic Rule)]
      │
      ├─── (Lolos) ──► [EXECUTE SQL NODE (DuckDB Engine)]
      │                         │
      │                         ▼
      │                  (query_result)
      │                         │
      └─── (Blokir) ────────────┼───────────────────────────┐
                                │                           │
                                ▼                           ▼
                      [VIZ GEN NODE (LLM Groq)] ◄───────────┘
                                │
                                ▼
                       [Executive Output]
```
