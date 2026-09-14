# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN D
## DATABASE ANALITIK (DUCKDB OLAP ENGINE)

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Code Inspection (`backend/db.py`, `backend/agents/execute.py`), Database Schema Verification, & Security Trace

---

### 1. Apakah DuckDB Benar-Benar Digunakan?
* **Status:** `IMPLEMENTED (100% Aktif & Digunakan Nyata)`
* **Bukti Teknis:** Proyek ini **sepenuhnya menggunakan DuckDB** sebagai mesin database analitik kolumnar utama (*In-Process OLAP Database Engine*). Seluruh proses querying kueri SQL hasil rakitan AI dieksekusi langsung ke berkas biner DuckDB lokal: `data/processed/tps_komersial.duckdb`. Tidak ada database eksternal lain (seperti PostgreSQL atau MySQL) yang digunakan untuk data analitik.

---

### 2. Di File Mana Koneksi DuckDB Dibuat?
Koneksi DuckDB dikelola di dua tempat terpisah berdasarkan perannya:

1. **Koneksi Analitik Runtime (Read-Only Pool):**
   - **File:** [`backend/db.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/db.py#L12-L31)
   - **Implementasi:** Class `DuckDBPool` mengimplementasikan pola *Singleton Shared Connection* dengan mode `read_only=True` agar aman dari perubahan data saat melayani request AI:
     ```python
     # backend/db.py:L21-L30
     @classmethod
     def get_connection(cls, db_path: str = None) -> duckdb.DuckDBPyConnection:
         target_path = db_path or DB_PATH
         if cls._instance is None:
             cls._instance = duckdb.connect(target_path, read_only=True)
         return cls._instance
     ```
2. **Koneksi ETL Data Pipeline (Read-Write Mode):**
   - **File:** [`backend/etl/main_etl.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/etl/main_etl.py#L57)
   - **Implementasi:** Digunakan secara eksklusif oleh batch script saat fase migrasi data Excel ke DuckDB:
     ```python
     # backend/etl/main_etl.py:L57
     conn = duckdb.connect(DB_PATH)  # Default read_write
     ```
3. **Koneksi Telemetri Audit Token (Read-Write Mode):**
   - **File:** [`backend/db.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/db.py#L33-L63)
   - **Implementasi:** Mengelola file terpisah `data/processed/telemetry.duckdb` untuk mencatat konsumsi token LLM dan latensi tanpa mengganggu lock database analitik utama.

---

### 3. Bagaimana Data Dimasukkan ke DuckDB?
Data dimasukkan melalui mekanisme **In-Memory Arrow/Pandas Zero-Copy Registration** pada tahap akhir ETL Medallion (`Gold Layer`):
1. Seluruh lembar kerja Excel yang telah dibersihkan dan distandarisasi dikonsolidasikan ke objek `pandas.DataFrame` (`df_final`).
2. DataFrame didaftarkan sementara ke sesi koneksi DuckDB menggunakan metode virtual view:
   `conn.register('temp_df', df_final)`
3. DuckDB mengeksekusi perintah DDL Create Table As Select (CTAS):
   `conn.execute(f"CREATE OR REPLACE TABLE {nama_tabel} AS SELECT * FROM temp_df")`
4. View sementara dilepas dari memori:
   `conn.unregister('temp_df')`
* **Keunggulan:** Transfer data dari memori Python ke penyimpanan disk DuckDB berlangsung instan tanpa perlu ekspor-impor file perantara.

---

### 4. Apakah Data Disimpan sebagai Tabel atau View?
* **Status:** `PHYSICAL TABLES (Tabel Fisik Materialized)`
* **Penjelasan:** Seluruh 9 dataset analitik disimpan sebagai **Tabel Fisik Persisten** di dalam file biner DuckDB, bukan sekadar Virtual View. Hal ini dibuktikan dari klausa DDL `CREATE OR REPLACE TABLE` saat ETL dan ketersediaan data permanen bahkan saat aplikasi dimatikan.

---

### 5. Daftar Tabel yang Dibuat di DuckDB
Terdapat **9 Tabel Fakta Utama** di dalam file `data/processed/tps_komersial.duckdb`:

| Nama Tabel Fisik | Fungsi Bisnis Utama | Volume Baris | Dimensi Utama |
| :--- | :--- | :-: | :--- |
| `fakta_throughput` | KPI realisasi & anggaran arus petikemas pelabuhan | 94 | `year`, `month`, `kategori_layanan` |
| `fakta_komersial_dashboard` | Pendapatan komersial & revenue per operator kapal | 910 | `tahun`, `bulan`, `lop` |
| `fakta_market_share` | Pangsa pasar & persentase volume TEUs operator | 7.657 | `year`, `month`, `lop` |
| `fakta_realisasi_uc` | Realisasi penanganan kargo non-petikemas (*Uncontainerized*) | 1.686 | `tahun`, `bulan`, `status` |
| `fakta_rest_n_disc` | Permohonan restitusi, diskon komersial, & keringanan biaya | 5 | `nama_perusahaan`, `status` |
| `fakta_vessel` | Performa produktivitas tambatan dan crane kapal (BCH/BSH) | 940 | `year`, `month`, `lop` |
| `fakta_vessel_service` | Monitoring rute kapal, loop service, dan kunjungan (call) | 2.410 | `year`, `lop`, `service` |
| `fakta_transhipment` | Transaksi alih muat kontainer & pendapatan lapangan (yard) | 17.626 | `date`, `bulan`, `lop` |
| `fakta_overview_box` | Rasio perbandingan volume boks fisik terhadap kapasitas TEUs | 726 | `year`, `month`, `lop` |

---

### 6. Bagaimana Query SQL Dieksekusi?
Eksekusi kueri SQL dilakukan secara terprogram pada **STEP 4 (Execution Node)** di file [`backend/agents/execute.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/execute.py):

1. **Pemeriksaan Status Sanitizer:** Sebelum menyentuh database, sistem memverifikasi bahwa kueri tidak diblokir oleh Sanitizer Guardrail (`if sql_error and "SANITIZER BLOCKED" in sql_error: return {"query_result": None}`).
2. **Pengambilan Koneksi Pool:** Memanggil `conn = get_db()` dari `DuckDBPool` (mode read-only).
3. **Eksekusi SQL Kolumnar:** Menjalankan kueri dan mengonversi hasil tabel DuckDB ke Pandas DataFrame:  
   `result_df = conn.execute(sql_query).df()`
4. **Sanitasi Nilai Numerik JSON:** Mengonversi nilai numerik anomali (`NaN`, `Infinity`) menjadi `None` (JSON `null`) agar browser tidak crash:  
   `result_df = result_df.where(pd.notnull(result_df), None)`
5. **Serialisasi Dictionary:** Mengubah DataFrame menjadi format *list of dictionaries*:  
   `result_dict = result_df.to_dict(orient='records')`
6. **Deteksi Fail-Fast:** Jika hasil kueri menghasilkan 0 baris atau nilai all-null, ditandai sebagai `DATA_EMPTY` untuk diteruskan ke agen visualisasi tanpa memicu perulangan.

---

### 7. Apakah Database Berjalan Secara Lokal?
* **Status:** `YA, 100% LOKAL (In-Process Embedded OLAP)`
* **Penjelasan:** DuckDB adalah database *serverless in-process* (serupa dengan SQLite, namun berorientasi kolumnar untuk OLAP). DuckDB berjalan langsung di dalam proses memori Python tanpa memerlukan service daemon database eksternal terpisah dan tanpa membuka port jaringan database ke luar.

---

### 8. Hak Akses Data LLM: Raw Excel vs Skema Terbatas (Data Governance)
* **Temuan Auditor:** **LLM SAMA SEKALI TIDAK MEMILIKI AKSES KE FILE EXCEL MENTAH MAUPUN SELURUH DATABASE DUCKDB.**
* **Tingkat Akses Informasi LLM per Step:**
  1. **STEP 1 (Router):** LLM hanya menerima daftar **Nama Tabel + Deskripsi Semantik Bisnis** (kurang dari 500 kata).
  2. **STEP 2 (SQL Generator):** LLM hanya menerima **Nama Kolom & Tipe Data Kolom** dari 1–2 tabel relevan yang telah disaring (`PRAGMA table_info(...)`). LLM tidak melihat satu barispun isi data perusahaan pada tahap perakitan SQL.
  3. **STEP 3 (Sanitizer):** Tidak melibatkan LLM (0 Token). Pemeriksaan keamanan dilakukan murni oleh regex Python.
  4. **STEP 4 (Execute):** Tidak melibatkan LLM. SQL dieksekusi secara lokal oleh mesin DuckDB.
  5. **STEP 5 (Narrative & Viz):** LLM hanya menerima **Maksimal 15 Baris Sampel Data Teratas** (`format_data_compact(rows, 15)`) dari hasil kueri yang sudah difilter oleh SQL, semata-mata untuk merangkum gaya bahasa narasi eksekutif.

---

### 🔄 Rekapitulasi Alur Konkret Data Pipeline

```text
[DATA SOURCE]
9 Berkas Excel Mentah (.xlsx) di folder data/raw/
        │
        ▼
[TRANSFORMATION: backend/etl/]
Pembersihan 'Unnamed', standardisasi operator 'lop', normalisasi numerik paksa_angka(),
unpivoting matriks pivot, dan penyeragaman identifier snake_case.
        │
        ▼
[DUCKDB STORAGE: backend/db.py]
Materialisasi fisik 9 Star Schema Fact Tables di data/processed/tps_komersial.duckdb
melalui DuckDB zero-copy registration (CREATE OR REPLACE TABLE ... AS SELECT).
        │
        ▼
[SQL EXECUTION: backend/agents/execute.py]
Eksekusi read-only via DuckDBPool, sanitasi tipe numerik NaN/inf ke JSON null,
dan deteksi fail-fast data kosong (DATA_EMPTY).
        │
        ▼
[RESULT / CONSUMPTION: backend/agents/viz_gen.py & Frontend]
Pengambilan maksimal 15 baris sampel untuk narasi bisnis AI (Groq), perakitan
grafik interaktif Apache ECharts, dan visualisasi tabel lengkap di antarmuka Vue 3.
```
