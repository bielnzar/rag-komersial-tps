# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN B
## SUMBER DAN STRUKTUR DATA: MEDALLION DATA ARCHITECTURE

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Static File Inspection, ETL Pipeline Tracing, & DuckDB Catalog Verification

---

### 1. Sumber dan Lokasi Pembacaan File Excel
* **Path Penyimpanan:** `data/raw/*.xlsx`
* **Asal Sumber:** File spreadsheet operasional internal PT TPS yang disinkronisasi dari Cloud Storage perusahaan (terkonfirmasi dari jejak arsip `data/raw/OneDrive_1_8-25-2026.zip`).
* **Bukti Kode:**
  ```python
  # backend/etl/main_etl.py:L27-L33
  BASE_DIR = Path(__file__).resolve().parent.parent.parent
  RAW_DIR = str(BASE_DIR / "data/raw")
  ```

---

### 2. Jumlah File Excel yang Digunakan
Sistem saat ini menggunakan **tepat 9 file Microsoft Excel (.xlsx)** yang dipetakan secara terpusat dalam `FILE_ROUTER` pada `backend/etl/main_etl.py`:

| No | Nama File Excel Mentah | Ukuran File | Modul Transformer Pemroses |
| :-: | :--- | :-: | :--- |
| 1 | `Container Throughput.xlsx` | ~18.5 KB | `proses_throughput` |
| 2 | `Komersial Dashboard.xlsx` | ~186.1 KB | `proses_komersial_dashboard` |
| 3 | `Market Share.xlsx` | ~466.6 KB | `proses_market_share` |
| 4 | `OVERVIEW BOX.xlsx` | ~72.5 KB | `proses_overview_box` |
| 5 | `OVERVIEW VESSEL.xlsx` | ~119.0 KB | `proses_vessel` |
| 6 | `Realisasi UC.xlsx` | ~269.0 KB | `proses_realisasi_uc` |
| 7 | `RestNDisc.xlsx` | ~15.4 KB | `proses_rest_n_disc` |
| 8 | `Transhipment.xlsx` | ~1.46 MB | `proses_transhipment` |
| 9 | `VESSEL SERVICE.xlsx` | ~471.2 KB | `proses_vessel_service` |

---

### 3. Mekanisme Pembacaan: Langsung vs Pra-Konversi
* **Status:** `IMPLEMENTED (Direct Ingestion)`
* **Penjelasan:** Seluruh 9 file Excel dibaca **secara langsung dari format aslinya (`.xlsx`)** menggunakan library `pandas` dengan engine `openpyxl`. Script membaca seluruh lembar kerja (*multi-sheet*) secara dinamis ke dalam memori:
  ```python
  # backend/etl/main_etl.py:L72
  semua_sheet = pd.read_excel(path_file, sheet_name=None)
  ```
  *(Catatan: Terdapat subfolder `data/raw/csv/` di repository yang merupakan artefak backup konversi per sheet, namun proses ETL utama sistem mengonsumsi file Excel `.xlsx` secara langsung).*

---

### 4. Transformasi Format Data (Pipeline Transition)

Sistem menerapkan siklus perubahan format data mengikuti tahapan **Medallion Architecture**:

```text
[SOURCE: .xlsx Files]
        │
        ▼ (pd.read_excel)
[BRONZE LAYER: In-Memory Pandas DataFrames & Debug CSVs in data/bronze/]
        │
        ▼ (transformers.py: Cleaning, Type Casting, Normalization)
[SILVER LAYER: Cleaned DataFrames & Debug CSVs in data/silver/]
        │
        ▼ (transformers.py: Unpivot, Concat Multi-Sheet, Column Standardization)
[GOLD LAYER: Consolidated DataFrames & Debug CSVs in data/gold/]
        │
        ▼ (conn.execute: CREATE OR REPLACE TABLE ... AS SELECT * FROM df)
[OUTPUT / WAREHOUSE: Relational OLAP Database in data/processed/tps_komersial.duckdb]
```

1. **Tahap 1 (Bronze):** In-Memory `pandas.DataFrame` mentah per sheet + file arsip `CSV` lokal di `data/bronze/`.
2. **Tahap 2 (Silver):** In-Memory `pandas.DataFrame` terbersihkan + file checkpoint `CSV` di `data/silver/`.
3. **Tahap 3 (Gold):** In-Memory `pandas.DataFrame` konsolidasi + file checkpoint `CSV` di `data/gold/`.
4. **Tahap 4 (Output Akhir):** **DuckDB Database Tables** yang tersimpan secara persisten pada file biner `data/processed/tps_komersial.duckdb`.

---

### 5. Proses Pengolahan & Transformasi Data (Data Cleansing)

Berdasarkan audit fungsi pada `backend/etl/utils.py` dan `backend/etl/transformers.py`, seluruh perlakuan data diidentifikasi sebagai berikut:

* **A. Data Cleaning:** `IMPLEMENTED`  
  - Penghapusan baris dan kolom yang 100% bernilai kosong (NaN) via `dropna(how='all')`.
  - Penghapusan kolom tidak bernama / kolom sisa format Excel (`Unnamed`) via regex `^Unnamed` di fungsi `hapus_kolom_hantu()`.
* **B. Standardisasi Nama Kolom:** `IMPLEMENTED`  
  - Seluruh nama kolom dikonversi ke huruf kecil (*lowercase*) dan spasi/simbol diganti menjadi *underscore* (`df.columns.str.lower().str.replace(r'[^a-z0-9_]', '_')`).
  - Kolom `%` diubah menjadi `persentase`.
  - Kolom nama operator (*Vessel Operator*, *Operator*) dinormalisasi menjadi `lop` (*Line Operating Partner*).
  - Resolusi kolom ganda kontekstual pelabuhan: membedakan `TEUS` milik *Boxes* menjadi `boxes_teus` dan `TEUS` milik *Moves* menjadi `moves_teus`.
* **C. Perubahan Tipe Data (Type Casting):** `IMPLEMENTED`  
  - Fungsi `paksa_angka()` mengonversi data nominal dan volume string menjadi float/numeric dengan menghapus simbol string ribuan, titik desimal, dan tanda kurung negatif.
  - Penyeragaman tipe data teks/tanggal menjadi `string` sebelum injeksi ke DuckDB untuk menghindari *DuckDB Schema Inference Type Mismatch*.
* **D. Handling Missing Value:** `IMPLEMENTED`  
  - Nilai numerik kosong diisi `0` atau `NaN` numerik. Nilai string kosong distandarisasikan menjadi `None` (SQL NULL).
* **E. Filtering:** `IMPLEMENTED`  
  - Mengabaikan baris ringkasan/catatan kaki (*footnotes*) yang tidak memiliki atribut tanggal/tahun.
* **F. Deduplication:** `PARTIALLY IMPLEMENTED`  
  - Fungsi `pastikan_kolom_unik()` menangani kolom bernama sama dengan memberikan suffix numerik (`_1`, `_2`). Deduplikasi baris data belum menerapkan hashing baris transaksi, melainkan mengandalkan partisi sheet yang unik dari file sumber.
* **G. Join / Merge / Concat:** `IMPLEMENTED`  
  - Melakukan konkatenasi multi-sheet setipe menggunakan `pd.concat(daftar_df, ignore_index=True)` sebelum dimuat ke DuckDB (misalnya sheet *Domestik* dan *Internasional* digabung menjadi satu tabel fakta dengan atribut `kategori_layanan`).
* **H. Reshaping / Unpivot (Melt):** `IMPLEMENTED`  
  - Pada `proses_market_share()`, kolom tahun menyamping berformat Pivot Excel (seperti `2022 (TEUS)`, `2023 (TEUS)`) secara otomatis di-unpivot (*melt*) menjadi baris data granular: `tahun_kategori` dan `total_teus`.
* **I. Agregasi saat ETL:** `NOT FOUND (By Design)`  
  - Data dipertahankan pada tingkat granulasi terendah (bulanan/transaksional). Proses agregasi (*SUM, AVG, GROUP BY*) sengaja didelegasikan ke DuckDB SQL engine pada saat runtime query oleh AI Agent.

---

### 6. Katalog Dataset & Skema Database DuckDB

Database `data/processed/tps_komersial.duckdb` menampung **9 Tabel Fakta Utama** dengan total akumulasi **~32.054 baris data analitik**:

| Nama Tabel di DuckDB | Total Baris | Jumlah Kolom | Sumber File Excel Mentah |
| :--- | :-: | :-: | :--- |
| `fakta_throughput` | 94 | 8 | `Container Throughput.xlsx` |
| `fakta_komersial_dashboard` | 910 | 26 | `Komersial Dashboard.xlsx` |
| `fakta_market_share` | 7.657 | 54 | `Market Share.xlsx` |
| `fakta_realisasi_uc` | 1.686 | 19 | `Realisasi UC.xlsx` |
| `fakta_rest_n_disc` | 5 | 11 | `RestNDisc.xlsx` |
| `fakta_vessel` | 940 | 10 | `OVERVIEW VESSEL.xlsx` |
| `fakta_vessel_service` | 2.410 | 26 | `VESSEL SERVICE.xlsx` |
| `fakta_transhipment` | 17.626 | 33 | `Transhipment.xlsx` |
| `fakta_overview_box` | 726 | 9 | `OVERVIEW BOX.xlsx` |

---

### 7. Rincian Metadata & Fungsi Masing-Masing Tabel

#### 1. `fakta_throughput`
* **Fungsi:** Menyimpan Key Performance Indicator (KPI) arus petikemas pelabuhan (target vs realisasi).
* **Jumlah Kolom:** 8 kolom
* **Kolom Utama & Tipe Data:** `year` (BIGINT), `month` (VARCHAR), `description` (VARCHAR), `unit` (VARCHAR), `actual` (DOUBLE), `budget` (DOUBLE), `actual_vs_budget` (DOUBLE), `kategori_layanan` (VARCHAR).
* **Relasi:** Berelasi logis dengan `fakta_overview_box` dan `fakta_vessel` melalui `year`, `month`, dan `kategori_layanan`.

#### 2. `fakta_komersial_dashboard`
* **Fungsi:** Ringkasan kinerja finansial dan pendapatan komersial per operator/pelanggan pelayaran.
* **Jumlah Kolom:** 26 kolom
* **Kolom Utama & Tipe Data:** `tahun` (DOUBLE), `bulan` (VARCHAR), `lop` (VARCHAR), `total_all_revenue` (DOUBLE), `total_revenue` (DOUBLE), `mooring_revenue` (DOUBLE), `repayment_day` (VARCHAR), `top_policy_day` (VARCHAR).
* **Relasi:** Berelasi logis dengan seluruh tabel berbasis operator via kolom `lop`.

#### 3. `fakta_market_share`
* **Fungsi:** Analisis persaingan pangsa pasar, volume kontainer TEUs, dan persentase pangsa per operator kapal.
* **Jumlah Kolom:** 54 kolom
* **Kolom Utama & Tipe Data:** `year` (DOUBLE), `month` (BIGINT), `lop` (VARCHAR), `teus` (DOUBLE), `persentase` (DOUBLE), `total_teus` (DOUBLE), `tahun_kategori` (VARCHAR), `sumber_sheet` (VARCHAR).
* **Relasi:** Berelasi logis via `lop` dan `year`.

#### 4. `fakta_realisasi_uc` (Uncontainerized Cargo)
* **Fungsi:** Realisasi penanganan kargo curah / non-kontainer (Unit Cargo / Breakbulk / Project Cargo).
* **Jumlah Kolom:** 19 kolom
* **Kolom Utama & Tipe Data:** `tahun` (BIGINT), `bulan` (VARCHAR), `status` (VARCHAR - Import/Export), `20` (DOUBLE), `40` (BIGINT), `45` (BIGINT), `total_box` (DOUBLE), `total_teus` (BIGINT).
* **Relasi:** Berelasi logis dengan `fakta_throughput` via dimensi waktu `tahun` dan `bulan`.

#### 5. `fakta_rest_n_disc` (Restitusi & Diskon)
* **Fungsi:** Pencatatan permohonan keringanan biaya, diskon komersial, dan restitusi jasa kepelabuhanan.
* **Jumlah Kolom:** 11 kolom
* **Kolom Utama & Tipe Data:** `nama_perusahaan` (VARCHAR), `status` (VARCHAR - Diterima/Ditolak), `aktivitas` (VARCHAR), `tanggal_surat_jawaban_tps` (VARCHAR), `nomor_jasa_kepelabuhan` (BIGINT), `nominal_persetujuan_keringanan` (DOUBLE).
* **Relasi:** Berelasi logis dengan `fakta_komersial_dashboard` melalui nama pelanggan / perusahaan.

#### 6. `fakta_vessel`
* **Fungsi:** Evaluasi produktivitas operasional tambatan kapal dan crane pelabuhan.
* **Jumlah Kolom:** 10 kolom
* **Kolom Utama & Tipe Data:** `year` (BIGINT), `month` (VARCHAR), `lop` (VARCHAR), `teus` (DOUBLE), `boxes` (DOUBLE), `bch` (DOUBLE - Box per Crane per Hour), `bsh` (DOUBLE - Box per Ship per Hour), `kategori_layanan` (VARCHAR).
* **Relasi:** Berelasi logis via `lop`, `year`, dan `kategori_layanan`.

#### 7. `fakta_vessel_service`
* **Fungsi:** Monitoring rute pelayaran, service loop, frekuensi kunjungan (call kapal), dan kecepatan operasional (BMPH/GMPH).
* **Jumlah Kolom:** 26 kolom
* **Kolom Utama & Tipe Data:** `year` (DOUBLE), `month` (DOUBLE), `lop` (VARCHAR), `service` (VARCHAR), `routes` (VARCHAR), `service_mode` (VARCHAR), `total_call` (DOUBLE), `average_bmph` (DOUBLE), `average_gmph` (DOUBLE).
* **Relasi:** Berelasi logis via `lop`, `service`, dan `year`.

#### 8. `fakta_transhipment`
* **Fungsi:** Pencatatan aktivitas alih muat (*transhipment*) kontainer antar kapal serta pendapatan penumpukan (*yard revenue*).
* **Jumlah Kolom:** 33 kolom
* **Kolom Utama & Tipe Data:** `lop` (VARCHAR), `date` (VARCHAR), `bulan` (VARCHAR), `kategori` (VARCHAR), `d20`, `d40`, `d45`, `l20`, `l40`, `l45` (DOUBLE), `yard_revenue` (DOUBLE).
* **Relasi:** Berelasi logis via `lop` dan dimensi tanggal.

#### 9. `fakta_overview_box`
* **Fungsi:** Rekapitulasi perbandingan volume boks fisik (*Boxes*) terhadap kapasitas standar (*TEUs*).
* **Jumlah Kolom:** 9 kolom
* **Kolom Utama & Tipe Data:** `year` (DOUBLE), `month` (VARCHAR), `lop` (VARCHAR), `teus` (DOUBLE), `boxes` (DOUBLE), `kategori_layanan` (VARCHAR).
* **Relasi:** Berelasi logis via `lop` dan `kategori_layanan`.

---

### 8. Relasi Data, Primary Key, dan Foreign Key

* **Arsitektur Model Data:** **Denormalized Star/Datamart Schema (OLAP Optimized)**.
* **Primary Key Fisik:** `NOT ENFORCED (By Design in DuckDB)` — DuckDB memprioritaskan performa kueri analitik kolumnar berkecepatan tinggi tanpa beban *PK/FK constraint validation overhead*.
* **Foreign Key Logis (Semantic Connectors):**
  1. **`lop` (Line Operator / Pelanggan / Shipping Line):**  
     Menghubungkan entitas operator di 7 tabel fakta: `fakta_komersial_dashboard`, `fakta_market_share`, `fakta_vessel`, `fakta_vessel_service`, `fakta_transhipment`, `fakta_overview_box`, dan `fakta_rest_n_disc`.
  2. **`year` / `tahun` & `month` / `bulan`:**  
     Dimensi waktu umum untuk seluruh analisis tren agregat antar tabel.
  3. **`kategori_layanan`:**  
     Memisahkan segmentasi arus kargo (`INTERNATIONAL` vs `DOMESTIC`).

---

### 9. Periode Waktu Data

Berdasarkan audit kueri nilai minimum dan maksimum (`SELECT MIN(year), MAX(year)`) pada database DuckDB:
* **Rentang Waktu Historis Keseluruhan:** Tahun **2021 hingga awal 2026**.
* **Fokus Periode Analitik Utama:** Data terpadat dan terlengkap berada pada tahun **2023, 2024, dan 2025**.
* *(Catatan Validitas: Terdapat anomali data `year = 0.0` dan `year = 2099.0` pada sebagian baris mentah `fakta_vessel_service` akibat baris rumus kosong di Excel asal).*

---

### 10. Otentisitas Data (Bukan Kaggle / Benchmark Publik)

* **Hasil Audit:** **100% DATA RIIL OPERASIONAL PERUSAHAAN (PT TERMINAL PETIKEMAS SURABAYA).**
* **Bukti Teknis:**
  1. **Nomenklatur Operator Kapal Nyata:** Mengandung nama-nama konsorsium pelayaran internasional dan domestik nyata (misal: *CMA CGM*, *Samudera Shipping Line / SSL*, *Maersk Line / MSK*, *Mediterranean Shipping Company / MSC*, *Evergreen / EMC*, *Meratus*, *SPIL*).
  2. **Metrik Khusus Terminal Petikemas:** Kolom berisikan terminologi maritim resmi yang tidak ada pada dataset umum Kaggle: *BCH* (*Box per Crane per Hour*), *BSH* (*Box per Ship per Hour*), *BMPH/GMPH* (*Berth/Gross Moves per Hour*), *Mooring Revenue*, *Yard Revenue*, dan *Restitusi Jasa Kepelabuhanan*.
  3. **Metadata Berkas:** Nama file, jejak sheet, dan nomor surat persetujuan keringanan pada `RestNDisc.xlsx` mencantumkan identitas resmi divisi komersial PT TPS.

---

### 🔄 Ringkasan Pipeline: SOURCE → PROCESSING → OUTPUT

```text
[SOURCE: 9 File Excel Mentah (.xlsx)]
  ├── Container Throughput.xlsx
  ├── Komersial Dashboard.xlsx
  ├── Market Share.xlsx
  ├── OVERVIEW BOX.xlsx
  ├── OVERVIEW VESSEL.xlsx
  ├── Realisasi UC.xlsx
  ├── RestNDisc.xlsx
  ├── Transhipment.xlsx
  └── VESSEL SERVICE.xlsx
            │
            ▼
[PROCESSING: Medallion Architecture di backend/etl/]
  ├── BRONZE LAYER  : Ingestion multi-sheet otomatis (openpyxl + pandas)
  ├── SILVER LAYER  : Hapus kolom hantu (Unnamed), normalisasi 'lop', paksa_angka()
  └── GOLD LAYER    : Concat multi-sheet setipe, unpivot (melt) matriks, casting string
            │
            ▼
[OUTPUT: Data Warehouse OLAP di data/processed/tps_komersial.duckdb]
  └── 9 Star Schema Fact Tables (~32.054 baris data relasional siap query Text-to-SQL)
```
