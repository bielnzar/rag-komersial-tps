# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN C
## AUDIT MEDALLION ARCHITECTURE (BRONZE → SILVER → GOLD)

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Code Walkthrough, Pipeline Tracing, & Data Artifact Verification (`backend/etl/`)

---

### ⚖️ Kesimpulan Awal Auditor (Status Penerapan Medallion)
* **Status Implementasi:** `IMPLEMENTED (Lightweight Batch Medallion Pattern)`
* **Penilaian Objektif:** Proyek ini **benar-benar mengimplementasikan prinsip pemisahan kualitas data Medallion Architecture (Bronze → Silver → Gold)** dalam pipeline ETL-nya (`backend/etl/main_etl.py`).
* **Karakteristik Implementasi:** Berbeda dengan arsitektur enterprise besar berbasis Databricks/Delta Lake yang menggunakan 3 tabel database terpisah untuk tiap layer, sistem ini menerapkan **Lightweight In-Memory Data Transformation Pipeline**:
  - **Bronze & Silver:** Berwujud *In-Memory Pandas DataFrames* dengan *Persistent CSV Checkpoints* di disk untuk auditabilitas.
  - **Gold:** Berwujud *Consolidated DataFrames*, *CSV Checkpoints*, dan **Tabel Database Fisik di DuckDB** (`fakta_*`) yang menjadi single source of truth untuk query analitik.

---

### 1. Apa yang Dianggap sebagai Bronze?
* **Definisi:** Data mentah tabular hasil ekstraksi langsung dari lembar kerja Microsoft Excel (`.xlsx`) apa adanya (*as-is*), tanpa manipulasi struktur, tanpa pembersihan tipe data, dan tanpa penghapusan missing values.
* **Karakteristik Data:** Masih mengandung kolom sisa format Excel (`Unnamed`), baris kosong, header ganda, nilai angka berformat string dengan pemisah ribuan koma, dan format matriks menyamping (*pivot*).

---

### 2. Di Mana Bronze Disimpan?
Bronze disimpan dalam dua bentuk:
1. **Penyimpanan Utama (Runtime):** *In-Memory Dictionary of DataFrames* (`semua_sheet = pd.read_excel(path_file, sheet_name=None)`).
2. **Penyimpanan File Fisik (Audit/Debug Checkpoint):** Folder `data/bronze/` dalam format CSV mentah dengan penamaan `bronze_{nama_file}_{nama_sheet}.csv`.
* **Bukti Kode:**
  ```python
  # backend/etl/main_etl.py:L72-L80
  semua_sheet = pd.read_excel(path_file, sheet_name=None)
  for nama_sheet, df_mentah in semua_sheet.items():
      simpan_debug_csv(df_mentah, str(BASE_DIR / "data/bronze"), f"bronze_{nama_file}_{nama_sheet}.csv", DEBUG_MODE)
  ```

---

### 3. Apa Proses pada Bronze?
Proses pada tahap Bronze adalah **Raw Extraction & Ingestion**:
- Pembacaan seluruh berkas Excel dari `data/raw/*.xlsx`.
- Iterasi otomatis ke seluruh sheet di dalam masing-masing file tanpa hardcoding nama sheet.
- Pembacaan representasi tabel Excel menjadi objek DataFrame tabular tanpa filterisasi.
- Penyimpanan salinan mentah ke folder `data/bronze/` untuk kebutuhan replikasi dan *data lineage audit*.

---

### 4. Apa yang Dilakukan pada Silver?
Tahap Silver adalah **Cleansing, Type Casting, & Semantic Standardization**:
1. **Pembersihan Kolom Hantu (`hapus_kolom_hantu`):**
   - Menghapus kolom sisa formula Excel bernama `Unnamed` menggunakan regex `^Unnamed`.
   - Menghapus baris dan kolom yang bernilai 100% kosong (`dropna(axis=1, how='all').dropna(axis=0, how='all')`).
2. **Standardisasi Semantik Awal:**
   - Menyeragamkan nama operator kapal menjadi kolom tunggal `lop` (*Line Operating Partner*) jika sebelumnya bernama `VESSEL OPERATOR` atau `OPERATOR`.
   - Resolusi ambiguitas maritim: membedakan kolom `TEUS` milik volume boks menjadi `boxes_teus` dan milik gerakan crane menjadi `moves_teus`.
   - Mengubah kolom simbol `%` menjadi kata `persentase`.
3. **Pemaksaan Tipe Data Numerik (`paksa_angka`):**
   - Menghapus karakter pemisah ribuan koma (`,`) dan spasi pada kolom numerik.
   - Mengonversi data numerik string menjadi float via `pd.to_numeric(errors='coerce')` dan mengganti error/kosong menjadi `0`.
4. **Penyimpanan Checkpoint:**
   - Hasil disimpan di memori sebagai `df_silver` dan dicetak ke disk `data/silver/silver_{nama_file}_{nama_sheet}.csv`.

---

### 5. Apa yang Dilakukan pada Gold?
Tahap Gold adalah **Data Mart Modeling, Reshaping, & Database Readiness**:
1. **Standardisasi Identifier SQL:**
   - Mengubah seluruh nama kolom menjadi huruf kecil (*lowercase*) dan mengganti seluruh spasi serta karakter non-alfanumerik menjadi garis bawah (*underscore*) via regex: `df_gold.columns.str.lower().str.replace(r'[^a-z0-9_]', '_')`.
2. **Penambahan Dimensi Konteks Bisnis:**
   - Menambahkan kolom `kategori_layanan` bernilai standar internasional (`INTERNATIONAL` atau `DOMESTIC`) dari nama sheet.
   - Menambahkan kolom `sumber_sheet` untuk melacak asal sheet transaksi.
3. **Restrukturisasi Matriks (Unpivoting / Melting):**
   - Pada tabel persaingan pasar (`proses_market_share`), sistem mendeteksi kolom tahun horizontal (seperti `2022 (TEUS)`, `2023 (TEUS)`) dan melakukan unpivot otomatis menggunakan `pd.melt()` menjadi baris vertikal granular: `tahun_kategori` dan `total_teus`.
4. **Konsolidasi Multi-Sheet (Union/Concatenation):**
   - Seluruh dataframe sheet yang setipe digabungkan menjadi satu tabel utuh menggunakan `pd.concat(daftar_df, ignore_index=True)`.
5. **Penanganan Schema Inference DuckDB:**
   - Memastikan kolom bertipe campuran (*object/datetime*) dikonversi menjadi string eksplisit untuk mencegah kegagalan inferensi skema DuckDB.

---

### 6. Di Mana Gold Disimpan?
Gold disimpan dalam dua media:
1. **Checkpoint File CSV:** Folder `data/gold/` dengan format `gold_{nama_file}_{nama_sheet}.csv`.
2. **Penyimpanan Permanen (Analytical Data Warehouse):** Di dalam file database analitik kolumnar DuckDB: **`data/processed/tps_komersial.duckdb`**.

---

### 7. Bagaimana Gold Terhubung ke Database Analitik?
Koneksi dan pemuatan Gold DataFrame ke DuckDB dilakukan secara langsung dalam memori melalui **DuckDB Python In-Process Engine**:
* **Mekanisme Pemuatan (In-Memory Registration):**
  DataFrame Pandas akhir (`df_final`) didaftarkan sementara ke engine DuckDB sebagai virtual view (`conn.register('temp_df', df_final)`).
* **Eksekusi Materialisasi SQL:**
  DuckDB mengeksekusi DDL SQL otomatis untuk membuat tabel fisik persisten:
  ```python
  # backend/etl/main_etl.py:L114-L116
  conn.register('temp_df', df_final)
  conn.execute(f"CREATE OR REPLACE TABLE {nama_tabel} AS SELECT * FROM temp_df")
  conn.unregister('temp_df')
  ```
* **Hasil Akhir:** Terbentuk 9 tabel relasional fisik di DuckDB dengan prefiks `fakta_*` yang dapat diakses langsung oleh Router dan SQL Generator Agent saat runtime.

---

### 8. Bentuk Artefak Masing-Masing Layer (File / DataFrame / Table)

| Layer Medallion | Bentuk Komputasi (Runtime) | Bentuk Penyimpanan (Storage) | Lokasi Path di Project |
| :--- | :--- | :--- | :--- |
| **BRONZE** | `pandas.DataFrame` (Mentah) | File CSV Mentah | `data/bronze/bronze_*.csv` |
| **SILVER** | `pandas.DataFrame` (Bersih) | File CSV Bersih | `data/silver/silver_*.csv` |
| **GOLD** | `pandas.DataFrame` (Konsolidasi) | File CSV Model + **Tabel Database DuckDB** | `data/gold/gold_*.csv`<br>`data/processed/tps_komersial.duckdb` |

---

### 9. Pemetaan Kode: File, Fungsi, dan Class Implementasi

| Layer | Nama File | Fungsi / Logika Pengendali | Bukti Potongan Kode |
| :--- | :--- | :--- | :--- |
| **Orchestrator** | `backend/etl/main_etl.py` | `jalankan_etl()` | Mengontrol alur dari loop `RAW_DIR`, memicu transformer, hingga menyimpan ke DuckDB. |
| **Bronze Layer** | `backend/etl/main_etl.py` | `pd.read_excel()` & `simpan_debug_csv()` | `semua_sheet = pd.read_excel(path_file, sheet_name=None)`<br>`simpan_debug_csv(df_mentah, ..., 'bronze_...')` |
| **Silver Layer** | `backend/etl/utils.py` | `hapus_kolom_hantu()`<br>`paksa_angka()`<br>`pastikan_kolom_unik()` | `df_bersih = df.loc[:, ~df.columns.str.contains('^Unnamed')]`<br>`df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)` |
| **Silver & Gold Transformers** | `backend/etl/transformers.py` | `proses_throughput()`<br>`proses_komersial_dashboard()`<br>`proses_market_share()`<br>`proses_vessel()`<br>`proses_vessel_service()`<br>`proses_realisasi_uc()`<br>`proses_overview_box()`<br>`proses_transhipment()`<br>`proses_rest_n_disc()` | Setiap fungsi mengembalikan tuple 3 elemen:<br>`return df_silver, pastikan_kolom_unik(df_gold), "nama_tabel_fakta"` |
| **Gold Load to DB** | `backend/etl/main_etl.py` | `conn.execute("CREATE OR REPLACE TABLE ...")` | `df_final = pd.concat(daftar_df, ignore_index=True)`<br>`conn.execute(f"CREATE OR REPLACE TABLE {nama_tabel} AS SELECT * FROM temp_df")` |

---

### 🔍 10. Catatan Kritis Auditor: Perbedaan dengan Enterprise Delta Lake Medallion
Untuk keperluan pelaporan akademik BAB 3 Skripsi yang jujur dan dapat dipertanggungjawabkan:
1. **Bukan Streaming / CDC:** Pipeline ini adalah **Batch Ingestion**, bukan streaming berkelanjutan (*continuous streaming*) seperti pada Apache Kafka / Delta Live Tables.
2. **Idempoten via Table Overwrite:** Pembaruan data ke DuckDB menggunakan klausa `CREATE OR REPLACE TABLE`, yang berarti data lama ditimpa secara utuh (*full refresh overwrite*), bukan *merge/upsert incremental*.
3. **Penyimpanan Bronze/Silver Tidak di DuckDB:** Database DuckDB **hanya menyimpan layer Gold**. Bronze dan Silver disimpan sebagai file CSV dan objek DataFrame di memori demi efisiensi ukuran file database lokal.
