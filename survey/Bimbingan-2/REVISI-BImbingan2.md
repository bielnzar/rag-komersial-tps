# 📄 Laporan Audit Data & Arsitektur Medallion ETL (Revisi Bimbingan TA #2)

**Judul Tugas Akhir:** Pengembangan AI Data Agent Berbasis Multi-Agent Text-to-SQL dan Arsitektur Medallion untuk Analitik Komersial pada PT XYZ  
**Studi Kasus:** PT Terminal Petikemas Surabaya (TPS)  
**Penulis:** Nabiel Nizar Anwari (NIM: 5027231087) — Teknologi Informasi, Institut Teknologi Sepuluh Nopember  
**Tanggal Audit:** 14 September 2026  
**Status Audit:** Terverifikasi 100% Berdasarkan Implementasi Source Code, File Fisik Excel, Checkpoint CSV, dan Database DuckDB  

---

## DAFTAR ISI
1. [Fokus 1: Audit Data Mentah (Raw Data)](#1-audit-data-mentah-raw-data)
2. [Fokus 2: Pemetaan Pipeline Medallion (Raw → Bronze → Silver → Gold → DuckDB)](#2-pemetaan-pipeline-medallion)
3. [Fokus 3: Rincian Transformasi Data (Dilengkapi Bukti Before & After)](#3-rincian-transformasi-data)
4. [Fokus 4: Spesifikasi Data Gold (Basis Data DuckDB Aktual)](#4-spesifikasi-data-gold)
5. [Fokus 5: Analisis Kredensial & Kerahasiaan Data (Data Privacy & Compliance)](#5-analisis-kredensial--kerahasiaan-data)
6. [Fokus 6: Ketersediaan Artefak untuk Bimbingan Dosen](#6-ketersediaan-artefak-untuk-bimbingan-dosen)
7. [Fokus 7: Matriks Hasil Audit & Rekomendasi Tindak Lanjut](#7-matriks-hasil-audit--rekomendasi-tindak-lanjut)

---

# 1. AUDIT DATA MENTAH (RAW DATA)

### 1.1 Sumber Data Mentah Aktual
Sistem analitik ini tidak terhubung langsung via koneksi live streaming ke sistem ERP/TOS pelabuhan, melainkan menggunakan **9 file spreadsheet Microsoft Excel (`.xlsx`)** yang ditempatkan pada direktori `data/raw/`. 

Berikut adalah rincian inventarisasi fisik ke-9 file tersebut:

| No | Nama File Mentah | Ukuran Fisik | Jumlah Sheet | Daftar Nama Sheet Aktual |
|:---:|:---|:---:|:---:|:---|
| 1 | `Container Throughput.xlsx` | 18.08 KB | 2 | `Domestik`, `International` |
| 2 | `Komersial Dashboard.xlsx` | 181.74 KB | 3 | `DATA KOMERSIAL`, `TREND KOMERSIAL`, `Sheet3` |
| 3 | `Market Share.xlsx` | 455.65 KB | 13 | `SL INT`, `BOX. OPR PIVOT`, `CONT THROUGHPUT`, `C.THR. DOM`, `V.OPR INT`, `V.OPR DOM`, `B.OPR INT`, `B.OPR DOM`, `TOP SERVICES`, `SL DOM`, `Sheet12`, `BAR INT`, `BAR DOM` |
| 4 | `OVERVIEW BOX.xlsx` | 70.80 KB | 2 | `DOMESTIK`, `INTERNATIONAL` |
| 5 | `OVERVIEW VESSEL.xlsx` | 116.21 KB | 2 | `DOMESTIC`, `INTERNATIONAL` |
| 6 | `Realisasi UC.xlsx` | 262.69 KB | 3 | `SUMMARY`, `TREND UC`, `OH OW OL` |
| 7 | `RestNDisc.xlsx` | 15.08 KB | 1 | `Form Responses 1` |
| 8 | `Transhipment.xlsx` | 1.433,12 KB | 18 | `new vr`, `Transhipment `, `YR Disc Real New`, `YR Load Real`, `YR Load Cancel New`, `YR Load Cancel`, `YR Disc Cancel`, `YR Disc Real`, `VR`, `YR Disc Real 10%`, `YR Disc Real 50%`, `YR Disc Can 10%`, `YR Disc Can 50%`, `YR Load Real 10%`, `YR Load Real 50%`, `YR Load Can 50%`, `VR 10%`, `VR 50%` |
| 9 | `VESSEL SERVICE.xlsx` | 460.11 KB | 4 | `New`, `Sheet4`, `Pivot Table 1`, `Sheet3` |
| **Total** | **9 File Excel** | **~2.99 MB** | **48 Sheet** | **48 Sheet Terbaca Otomatis oleh ETL** |

### 1.2 Karakteristik & Struktur Data Awal
Data mentah spreadsheet memiliki karakteristik heterogen dan tidak terstandarisasi dalam bentuk relasional (non-3NF):
1. **Format Transaksional Harian/Bulanan:** Memiliki penanda tanggal, kode operator, dan volume boks/TEUs. Contoh:
   * `OVERVIEW VESSEL.xlsx`: `['DATE', 'YEAR', 'MONTH_CODE', 'MONTH', 'LOP', 'TEUS ', 'Boxes', 'BCH', 'BSH']`
   * `Container Throughput.xlsx`: `['YEAR', 'MONTH', 'DESCRIPTION', 'UNIT', 'ACTUAL', 'BUDGET', 'ACTUAL VS BUDGET']`
2. **Format Laporan Horizontal (Wide Pivot Report):** Kolom tahun menyebar secara horizontal ke kanan, bukan memanjang ke bawah (*tidy data*). Contoh:
   * `Market Share.xlsx` (sheet `B.OPR INT`): `['DATE', 'YEAR', 'MONTH', 'LOP', '2022 (TEUS)', '2023 (TEUS)', '2024 (TEUS)', '2025 (TEUS)', '2026 (TEUS)', '%']`
3. **Penyatuan Kamus Master ke dalam File Transaksi:**
   * `Komersial Dashboard.xlsx` (sheet `Sheet3`): Hanya berisi 23 baris daftar nama perusahaan operator pelayaran dan singkatannya (`Full Name`, `Code`), namun disatukan di dalam file transaksi pendapatan komersial bulanan.
4. **Data Formulir Ekspor Google Form:**
   * `RestNDisc.xlsx`: Format form respons dengan header panjang dan tautan aktif lampiran berkas dokumen bukti pengajuan.

### 1.3 Permasalahan Nyata Data Mentah yang Terverifikasi
Berdasarkan hasil inspeksi langsung baris demi baris, ditemukan permasalahan konkret berikut:
* **Kolom Artefak Format Excel (`Unnamed: x`):** Terbentuk akibat sisa formatting atau rumus kosong yang melebar ke samping. Ditemukan pada `Market Share.xlsx` (sheet `C.THR. DOM`, `Sheet12`), `Transhipment.xlsx` (sheet `Transhipment `), `Realisasi UC.xlsx` (sheet `TREND UC`), dan `VESSEL SERVICE.xlsx` (sheet `Sheet4`).
* **Inkonsistensi Nomenklatur Kolom:**
  * Entitas Pelayaran: tertulis sebagai `'VESSEL OPERATOR'`, `'OPERATOR'`, `'Vessel Operator'`, dan `'LOP'`.
  * Waktu: tertulis `'Tahun'`, `'TAHUN'`, `'YEAR'`, `'Year'` serta `'BULAN'`, `'Bulan'`, `'MONTH'`, `'Month'`.
  * Typo Fatal Header: Kolom bulan di `OVERVIEW BOX.xlsx` sheet `INTERNATIONAL` tertulis **`'MONT H'`** (ada spasi di tengah kata).
  * Spasi Tak Terlihat (*Trailing Whitespace*): Kolom TEUS tertulis sebagai `'TEUS '` (dengan spasi di akhir) pada `OVERVIEW BOX.xlsx`, `OVERVIEW VESSEL.xlsx`, `BAR INT`, dan `BAR DOM`.
  * Karakter Simbolik: Kolom persentase tertulis `'%'`, dimensi boks tertulis `"20'"`, `"40'"`, `"45'"`, dan typo tanda kurung `'TOP POLICY DAY)'`.
* **Karakter Non-Numerik pada Kolom Metrik:**
  * Penggunaan tanda hubung/dash `"-"` untuk merepresentasikan angka nol (0).
  * Angka ribuan menggunakan tanda koma dalam bentuk string teks (contoh: `"1,500"`).
* **Anomali Nilai Formula Excel:**
  * Formula `=YEAR()` di `VESSEL SERVICE.xlsx` sheet `New` menghasilkan tahun korup **`1905`** dan **`2099`** pada **159 baris**.
  * Formula `=IFS()` di `OVERVIEW BOX.xlsx` menghasilkan teks `"Invalid Month"` pada ratusan baris karena sel acuan `MONTH_CODE` bernilai kosong.
* **Kerusakan Salinan Data Manual (Human Error Copy-Paste):**
  * `OVERVIEW BOX.xlsx` sheet `INTERNATIONAL` terpotong menjadi 517 baris dengan tanggal yang tertukar akibat salin-tempel manual yang salah dari `OVERVIEW VESSEL.xlsx`.
  * Di sheet `DOMESTIK` pada `OVERVIEW BOX.xlsx`, baris 138–209 kolom LOP dan TEUS kosong (`NaN`), padahal di `OVERVIEW VESSEL.xlsx` terisi lengkap.

---

# 2. PEMETAAN PIPELINE MEDALLION

Arsitektur data mengadopsi pola **Medallion Data Architecture (Bronze → Silver → Gold)** yang terotomatisasi secara end-to-end melalui script Python [backend/etl/main_etl.py](../backend/etl/main_etl.py).

```
+---------------------------------------------------------------------------------------+
|                                     1. RAW LAYER                                      |
| 9 File Excel Fisik (.xlsx) di direktori data/raw/ (~2.99 MB, 48 sheet)               |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v (pd.read_excel sheet_name=None)
+---------------------------------------------------------------------------------------+
|                                    2. BRONZE LAYER                                    |
| - Ekstraksi in-memory dictionary per sheet: {nama_sheet: DataFrame_mentah}           |
| - Artefak Checkpoint Fisik: data/bronze/bronze_{nama_file}_{nama_sheet}.csv (65 file) |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v (sanitasi_skema_awal + paksa_angka)
+---------------------------------------------------------------------------------------+
|                                    3. SILVER LAYER                                    |
| - Hapus kolom artefak 'Unnamed' & baris/kolom 100% NaN                                |
| - Standarisasi nama LOP, perbaikan simbol %, trailing whitespace trim                 |
| - Pembersihan karakter '-' -> 0 dan konversi koma ribuan -> float numerik             |
| - Pemulihan tahun korup (1905/2099 -> recovered from 'tahun')                         |
| - Artefak Checkpoint Fisik: data/silver/silver_{nama_file}_{nama_sheet}.csv (65 file) |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v (pd.melt + filter tahun + regex snake_case)
+---------------------------------------------------------------------------------------+
|                                     4. GOLD LAYER                                     |
| - Unpivot (Melt) sheet pivot horizontal (B.OPR INT & B.OPR DOM) -> Format Long        |
| - Filter rentang tahun valid operasional (2020 <= YEAR <= 2030)                       |
| - Tagging metadata asal: 'sumber_sheet' & 'kategori_layanan'                          |
| - Transformasi nama kolom ke standar SQL Snake_Case: lowercase + underscore regex    |
| - Artefak Checkpoint Fisik: data/gold/gold_{nama_file}_{nama_sheet}.csv (65 file)     |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v (pd.concat + DuckDB CREATE OR REPLACE + Post-Process)
+---------------------------------------------------------------------------------------+
|                              5. DUCKDB STORAGE & ANALYTICS                            |
| - pd.concat() seluruh sheet setipe menjadi tabel fakta terkonsolidasi                 |
| - Sanitasi tanggal ISO (YYYY-MM-DD) & pemotongan residu string ' 00:00:00'            |
| - Post-Processing:                                                                    |
|   1. Ekstraksi master sheet3 -> tabel dimensi fisik 'dim_vessel_operator'             |
|   2. Relasi UPDATE enrich nama lengkap operator pelayaran                             |
|   3. Penyelarasan fakta_overview_box dari master data valid fakta_vessel (940 baris)  |
|   4. Casting fisik kolom bilangan bulat diskrit -> BIGINT                             |
| - Basis Data Fisik: data/processed/tps_komersial.duckdb (10 Tabel, 7.51 MB)           |
+---------------------------------------------------------------------------------------+
```

### Rincian Per Tahap:

#### A. RAW → BRONZE
* **Input:** 9 file spreadsheet `.xlsx` di `data/raw/`.
* **Proses / Transformasi:**
  * Pembacaan otomatis seluruh sheet menggunakan `pd.read_excel(path_file, sheet_name=None)` di [main_etl.py line 72](../backend/etl/main_etl.py#L72).
  * Tidak ada pembuangan data atau perubahan nilai sel pada tahap ini. Data disimpan murni apa adanya ke memori.
  * Pencatatan checkpoint fisik berupa file CSV ke direktori `data/bronze/` via fungsi `simpan_debug_csv()`.
* **Output:** Objek Dictionary DataFrame mentah dalam memori dan **65 file CSV Bronze**.
* **Script Pemroses:** [main_etl.py line 71-81](../backend/etl/main_etl.py#L71-L81).

#### B. BRONZE → SILVER
* **Input:** DataFrame mentah layer Bronze.
* **Proses / Transformasi:**
  * `sanitasi_skema_awal()`: Menghapus kolom artefak `^Unnamed`, memotong spasi ujung nama kolom (`str.strip()`), me-rename `'%'` menjadi `'persentase'`, membedakan `'boxes_teus'` dan `'moves_teus'`.
  * `paksa_angka()`: Mengubah dash `"-"` menjadi `0`, membuang koma ribuan string, dan melakukan type coercion dengan `pd.to_numeric(errors='coerce').fillna(0)`.
  * Standarisasi nama entitas: me-rename `'VESSEL OPERATOR'` / `'OPERATOR'` menjadi `'LOP'`.
  * Pemulihan anomali tahun formula: baris dengan tahun `1905` dan `2099` pada `VESSEL SERVICE.xlsx` dipulihkan nilainya dari kolom `'tahun'`.
* **Output:** Objek `df_silver` dan **65 file CSV Silver**.
* **Script Pemroses:** [utils.py line 41-93](../backend/etl/utils.py#L41-L93) dan [transformers.py line 1-203](../backend/etl/transformers.py#L1-L203).

#### C. SILVER → GOLD
* **Input:** Objek `df_silver`.
* **Proses / Transformasi:**
  * Unpivot / Normalisasi Bentuk Data: Lembar pivot `B.OPR INT` dan `B.OPR DOM` di-unpivot menggunakan `pd.melt()` sehingga kolom tahun horizontal berubah menjadi dimensi baris `tahun_kategori` dan metrik `total_teus`.
  * Filtering Data Valid: Menyeleksi data operasional pada rentang tahun valid `2020 <= YEAR <= 2030`.
  * Normalisasi Kategori Layanan: Standarisasi nilai bahasa Indonesia ke bahasa Inggris (`'Domestik'` $\rightarrow$ `'DOMESTIC'`, `'Internasional'` $\rightarrow$ `'INTERNATIONAL'`).
  * Konversi Snake_Case: Menjalankan pembersihan nama kolom dengan `.str.lower().str.replace(r'[^a-z0-9_]', '_').str.strip('_')`.
* **Output:** Objek `df_gold`, penentuan nama target tabel, dan **65 file CSV Gold**.
* **Script Pemroses:** [transformers.py](../backend/etl/transformers.py) (9 fungsi transformer).

#### D. GOLD → DUCKDB
* **Input:** Kumpulan dataframe `df_gold` yang dikelompokkan berdasarkan nama tabel target.
* **Proses / Transformasi:**
  * Konsolidasi vertikal seluruh sheet setipe menggunakan `pd.concat(daftar_df, ignore_index=True)`.
  * Format string tanggal datetime menjadi format tanggal bersih `YYYY-MM-DD`.
  * Registrasi tabel fisik DuckDB via `CREATE OR REPLACE TABLE {nama_tabel} AS SELECT * FROM temp_df`.
  * Pasca-proses SQL:
    1. Pemisahan data master `SHEET3` menjadi tabel dimensi fisik `dim_vessel_operator` (23 baris).
    2. Eksekusi query UPDATE JOIN untuk mengisi nama lengkap operator pelayaran (`full_name`) di `fakta_komersial_dashboard`.
    3. Penyelarasan tabel `fakta_overview_box` langsung dari master data valid `fakta_vessel` (940 baris akurat).
    4. Pembersihan residu teks `' 00:00:00'` pada seluruh kolom tanggal di 6 tabel fakta.
    5. Konversi tipe data diskrit (*discrete integer casting*) dari `DOUBLE` ke `BIGINT` murni.
* **Output:** File basis data OLAP tunggal `data/processed/tps_komersial.duckdb`.
* **Script Pemroses:** [main_etl.py line 100-250](../backend/etl/main_etl.py#L100-L250).

---

# 3. RINCIAN TRANSFORMASI DATA

Berikut adalah katalog transformasi yang benar-benar diimplementasikan dalam kode program beserta bukti data konkretnya:

### 3.1 Restrukturisasi Unpivot Data (Wide to Long)
* **Lokasi Kode:** [transformers.py line 68-76](../backend/etl/transformers.py#L68-L76)
* **Deskripsi:** Sheet `B.OPR INT` di `Market Share.xlsx` memiliki format matriks tahun horizontal (`2022 (TEUS)`, `2023 (TEUS)`, `2024 (TEUS)`, `2025 (TEUS)`). Struktur ini diubah menjadi format relasional panjang (*long format*).
* **Bukti Riil:**
  * **BEFORE (Bronze CSV: `bronze_Market Share.xlsx_B.OPR INT.csv`):**  
    Ukuran: 587 baris $\times$ 10 kolom.  
    Kolom: `['DATE', 'YEAR', 'MONTH', 'LOP', '2022 (TEUS)', '2023 (TEUS)', '2024 (TEUS)', '2025 (TEUS)', '2026 (TEUS)', '%']`  
    *Sampel Baris 0:* `DATE=2024-01-01, LOP=CMA, 2022 (TEUS)=12085, 2023 (TEUS)=14158.0, 2024 (TEUS)=10480.0`
  * **AFTER (Gold CSV: `gold_Market Share.xlsx_B.OPR INT.csv`):**  
    Ukuran: 2.935 baris $\times$ 8 kolom (587 baris $\times$ 5 tahun).  
    Kolom: `['date', 'year', 'month', 'lop', 'persentase', 'tahun_kategori', 'total_teus', 'sumber_sheet']`  
    *Sampel Baris 0:* `date=2024-01-01, lop=CMA, tahun_kategori=2022, total_teus=12085.0`  
    *Sampel Baris 1:* `date=2024-01-01, lop=CMA, tahun_kategori=2023, total_teus=14158.0`

### 3.2 Pemulihan Tahun Formula Rusak (Year Recovery)
* **Lokasi Kode:** [transformers.py line 113-120](../backend/etl/transformers.py#L113-L120)
* **Deskripsi:** Di `VESSEL SERVICE.xlsx` sheet `New`, formula `=YEAR(A...)` menghasilkan tahun `1905` dan `2099` pada 159 baris data karena membaca format serial tanggal Excel yang tidak sesuai. Sistem memulihkan tahun valid dari kolom teks `'tahun'`.
* **Bukti Riil:**
  * **BEFORE (Bronze CSV: `bronze_VESSEL SERVICE.xlsx_New.csv`):**  
    *Baris 0:* `NO=1, tahun=2022, YEAR=2099, MONTH=7.0, VESSEL OPERATOR=COS`  
    *Baris 1:* `NO=2, tahun=2022, YEAR=1905, MONTH=7.0, VESSEL OPERATOR=COS`  
    *(Total 159 baris bernilai 1905 atau 2099).*
  * **AFTER (Gold CSV: `gold_VESSEL SERVICE.xlsx_New.csv`):**  
    *Baris 0:* `no=1, tahun=2022, year=2022, month=7, lop=COS`  
    *Baris 1:* `no=2, tahun=2022, year=2022, month=7, lop=COS`  
    *(Tahun berhasil dipulihkan menjadi 2022).*

### 3.3 Pembersihan Karakter Dash `"-"` & Konversi Numerik
* **Lokasi Kode:** [utils.py line 73, 85-87](../backend/etl/utils.py#L73)
* **Deskripsi:** Tanda hubung `"-"` yang dipakai Excel untuk merepresentasikan nol dibersihkan menjadi angka `0`, dan teks angka berformat ribuan diubah menjadi numerik murni.
* **Bukti Riil:**
  * **BEFORE (Raw/Bronze):** Baris 142 pada `OVERVIEW VESSEL.xlsx` (sheet `DOMESTIC`): Kolom `TEUS = "-"` dan `Boxes = "-"`.
  * **AFTER (Silver/Gold):** Kolom `teus = 0.0` dan `boxes = 0`.

### 3.4 Sanitasi Format Tanggal ISO & Pemangkasan Residu Waktu
* **Lokasi Kode:** [main_etl.py line 110-116, 225](../backend/etl/main_etl.py#L110-L116)
* **Deskripsi:** Karena data komersial TPS adalah rekapitulasi harian/bulanan tanpa informasi jam, objek `Timestamp` yang secara default menghasilkan `"00:00:00"` dipangkas menjadi tanggal bersih ISO.
* **Bukti Riil:**
  * **BEFORE:** Nilai tanggal tersimpan sebagai string `"2023-01-01 00:00:00"`.
  * **AFTER:** Nilai tanggal tersimpan rapi sebagai string tanggal ISO `"2023-01-01"`.

### 3.5 Standarisasi Penamaan Kolom ke Snake_Case
* **Lokasi Kode:** [transformers.py line 30, 47, 79, 99, 132, 149, 165, 187, 201](../backend/etl/transformers.py#L30)
* **Deskripsi:** Menyeragamkan seluruh header kolom menjadi huruf kecil dengan pemisah garis bawah menggunakan regex.
* **Bukti Riil:**
  * `'TOTAL ALL REVENUE'` $\rightarrow$ `total_all_revenue`
  * `'ACTUAL VS BUDGET'` $\rightarrow$ `actual_vs_budget`
  * `'REPAYMENT (DAY)'` $\rightarrow$ `repayment_day`
  * `'2022 (TEUS)'` $\rightarrow$ `2022_teus`
  * `"20'"` $\rightarrow$ `20`

### 3.6 Konsolidasi Multi-Sheet (Concatenation)
* **Lokasi Kode:** [main_etl.py line 107](../backend/etl/main_etl.py#L107)
* **Deskripsi:** Menggabungkan seluruh sheet dari file yang sama menjadi satu tabel fakta tunggal.
* **Bukti Riil:**
  * **BEFORE:** File `Transhipment.xlsx` memiliki 18 sheet terpisah.
  * **AFTER:** Seluruh 18 sheet digabung menjadi satu tabel fisik **`fakta_transhipment`** dengan total **17.625 baris dan 33 kolom**.

### 3.7 Type Casting Fisik Diskrit ke BIGINT
* **Lokasi Kode:** [main_etl.py line 246](../backend/etl/main_etl.py#L246)
* **Deskripsi:** Kolom kuantitas cacah diskrit (`total_box`, `moves`, `boxes`, `year`, `month`) yang sebelumnya bertipe `DOUBLE` (contoh: `1500.0`) dikonversi ke **`BIGINT`** murni menggunakan perintah DDL DuckDB:  
  `ALTER TABLE "{tbl}" ALTER COLUMN "{col}" TYPE BIGINT USING ROUND(TRY_CAST("{col}" AS DOUBLE))::BIGINT;`

---

# 4. SPESIFIKASI DATA GOLD

Basis data analitik akhir berlokasi di `data/processed/tps_komersial.duckdb` (ukuran file: **7.51 MB**). Terdiri dari **10 tabel operasional** yang siap dikueri:

| No | Nama Tabel di DuckDB | Total Baris | Total Kolom | Fungsi Bisnis Tabel | Kolom Utama (Dimensi & Metrik) |
|:---:|:---|:---:|:---:|:---|:---|
| 1 | **`dim_vessel_operator`** | 23 | 2 | Master data kamus resmi operator kapal/pelayaran (shipping line) di TPS. | `code` (PK), `full_name` |
| 2 | **`fakta_throughput`** | 94 | 8 | Pencatatan KPI throughput peti kemas bulanan (realisasi aktual vs target budget RKAP) kategori Domestik & Internasional. | `year`, `month`, `kategori_layanan`, `actual`, `budget`, `actual_vs_budget` |
| 3 | **`fakta_komersial_dashboard`** | 887 | 26 | Rekapitulasi pendapatan komersial (*revenue*), pendapatan tambat, termin pembayaran (TOP), dan kuantitas boks per operator per bulan. | `tahun`, `bulan`, `lop`, `full_name`, `total_all_revenue`, `mooring_revenue`, `total_box`, `total_teus` |
| 4 | **`fakta_market_share`** | 7.657 | 54 | Analisis pangsa pasar (*market share*), persentase volume TEUs per operator pelayaran, dan rute layanan kapal. | `year`, `month`, `lop`, `teus`, `persentase`, `tahun_kategori`, `total_teus`, `service` |
| 5 | **`fakta_vessel`** | 940 | 10 | Metrik performa operasional kapal, produktivitas bongkar muat (*Box Crane per Hour / BCH* dan *Box Ship per Hour / BSH*). | `date`, `year`, `month`, `lop`, `teus`, `boxes`, `bch`, `bsh`, `kategori_layanan` |
| 6 | **`fakta_overview_box`** | 940 | 8 | Ringkasan perbandingan volume boks fisik (*Boxes*) terhadap kapasitas standar (*TEUs*) kategori Domestik & Internasional. | `date`, `year`, `month`, `lop`, `teus`, `boxes`, `kategori_layanan` |
| 7 | **`fakta_vessel_service`** | 2.407 | 26 | Data performa rute pelayaran, *service mode*, total kunjungan kapal (*total call*), dan produktivitas crane (*BMPH/GMPH*). | `year`, `month`, `lop`, `service`, `routes`, `service_mode`, `total_call`, `moves` |
| 8 | **`fakta_transhipment`** | 17.625 | 33 | Transaksi alih muat kontainer antar-kapal (*transhipment*), ukuran boks (20ft, 40ft, 45ft), pendapatan dermaga (*vessel*) dan penumpukan (*yard*). | `year`, `month`, `lop`, `size`, `direct_or_cy_trans`, `vessel_revenue`, `yard_revenue`, `loading_terminal` |
| 9 | **`fakta_realisasi_uc`** | 1.686 | 19 | Pencatatan kegiatan kargo non-kontainer / *uncontainerized* (UC) meliputi tonase, volume, diskon, dan tarif. | `tahun`, `bulan`, `status`, `total_box`, `total_teus`, `total`, `total_discount`, `kegiatan` |
| 10 | **`fakta_rest_n_disc`** | 5 | 11 | Rekam permohonan restitusi dan diskon komersial yang diajukan oleh pelanggan korporat ke manajemen TPS. | `nama_perusahaan`, `nomor_surat_jawaban_tps`, `status`, `nominal_persetujuan_keringanan` |
| **Total** | **10 Tabel DuckDB** | **32.264 Baris** | - | **Dataset Analitik Terpadu Siap Kueri Text-to-SQL** | - |

### Integrasi dengan Multi-Agent Text-to-SQL:
* **Router Agent ([router.py](../backend/agents/router.py)):** Menggunakan katalog semantik 10 tabel di atas untuk mendeteksi intent pengguna dan memilih tabel relevan berdasarkan *Role-Based Access Control (RBAC)*.
* **SQL Generator Agent ([sql_gen.py](../backend/agents/sql_gen.py)):** Menerapkan *Column-Level Schema Pruning* untuk memangkas tabel lebar (seperti `fakta_market_share` 54 kolom) menjadi hanya kolom dimensi dan metrik yang relevan sebelum diserahkan ke model bahasa (LLM).
* **Execution Engine ([execute.py](../backend/agents/execute.py)):** Menjalankan SQL secara deterministik di DuckDB melalui *shared read-only connection pool* ([db.py](../backend/db.py)).

---

# 5. ANALISIS KREDENSIAL & KERAHASIAAN DATA

Audit kerahasiaan data menemukan bahwa file dataset komersial TPS **mengandung informasi sensitif bisnis tingkat tinggi (*Highly Confidential Enterprise Data*)**:

| Kategori Data Sensitif | Ditemukan Pada Tabel / File | Contoh Nilai Riil di Code/Database | Tingkat Risiko |
|:---|:---|:---|:---:|
| **Identitas Klien Korporat** | `fakta_rest_n_disc` | Nama perseroan nyata: `PT Antam`, `PT Unilever`, `PT United Tractors`, `PT Paragon`, `PT Wings`. | 🔴 TINGGI |
| **Nominal Diskon / Keringanan Biaya** | `fakta_rest_n_disc` | Angka rupiah kesepakatan keringanan: `Rp 65.000.000`, `Rp 10.000.000`, `Rp 35.000.000`. | 🔴 TINGGI |
| **Nomor Dokumen Legal & Surat Resmi** | `fakta_rest_n_disc` | Nomor Master Pelanggan (`83826`), Nomor Surat Jawaban TPS (`73858`), Nomor Jasa Kepelabuhan (`72851`). | 🔴 TINGGI |
| **Tautan Dokumen Bukti (Nota Internal)** | `fakta_rest_n_disc` | Tautan aktif Google Drive nota permohonan keringanan biaya: `https://drive.google.com/open?id=1HmkLyLKDajFQpw...` | 🔴 SANGAT TINGGI |
| **Pendapatan Riil Perusahaan (*Revenue*)** | `fakta_komersial_dashboard` & `fakta_transhipment` | Pendapatan miliaran rupiah per shipping line (contoh: CMA Rp 16,57 Miliar, COSCO Rp 9,72 Miliar, Tambat Kapal Rp 789 Juta). | 🔴 TINGGI |
| **Perjanjian Termin Pembayaran (*TOP*)** | `fakta_komersial_dashboard` | Hari jatuh tempo piutang pelanggan (`repayment_day`, `top_policy_day`). | 🟡 SEDANG |
| **Kredensial Akun Pengguna** | `credentials/users.json` | Hash password PBKDF2-HMAC-SHA256 dan salt untuk akun internal (`admin`, `user`). | 🔴 SANGAT TINGGI |

---

### Jawaban Khusus Terkait Penulisan Skripsi / Publikasi Tugas Akhir:

#### A. Data yang Secara Struktur Aman Ditampilkan dalam Skripsi
1. **Struktur Skema DDL:** Nama tabel (`fakta_vessel`, `fakta_throughput`), nama kolom (`year`, `teus`, `bch`, `bsh`), dan tipe data (`BIGINT`, `DOUBLE`, `VARCHAR`).
2. **Arsitektur Model Data & Pipeline:** Diagram alur Medallion, diagram Star Schema, dan logika query Text-to-SQL.
3. **Data Agregat Relatif / Persentase:** Rasio pertumbuhan throughput (% YoY), perbandingan performa BCH/BSH, rasio TEUs terhadap Boxes, dan waktu respon latensi sistem LLM.

#### B. Data yang WAJIB Di-mask / Dianonimkan Terlebih Dahulu
1. Seluruh kolom **`nama_perusahaan`** pada permohonan diskon dan restitusi.
2. Seluruh nominal rupiah riil pada **`nominal_persetujuan_keringanan`**, **`total_all_revenue`**, **`mooring_revenue`**, **`vessel_revenue`**, dan **`yard_revenue`**.
3. Seluruh **`nomor_surat_jawaban_tps`**, **`nomor_master_pelanggan_tps`**, dan tautan URL **`supporting_document`** (URL Google Drive harus dihilangkan).
4. File **`.env`** dan **`credentials/users.json`** wajib masuk dalam `.gitignore` dan tidak boleh dilampirkan dalam lampiran kode skripsi.

#### C. Apakah Cukup Hanya Mengganti Nama Perusahaan Menjadi PT XYZ?
**TIDAK CUKUP.**  
Mengganti nama perusahaan saja tidak mencukupi standar kepatuhan privasi data karena:
* Nomor surat jawaban dan nomor master pelanggan dapat dilacak ke arsip internal Pelindo/TPS.
* Tautan URL Google Drive langsung membuka dokumen surat resmi asli.
* Nominal rupiah yang spesifik (misal `Rp 16.571.830.000`) dapat dicocokkan dengan laporan keuangan audit tahunan pelabuhan.

#### D. Strategi Masking yang Aman Tanpa Merusak Karakteristik Analitik
1. **Entitas Klien / Pelayaran:** Ubah menggunakan pseudonim konsisten:
   * `PT Antam` $\rightarrow$ `Klien Korporat A`
   * `CMA CGM GROUP` $\rightarrow$ `Operator Line L1`
   * `EVERGREEN LINE` $\rightarrow$ `Operator Line L2`  
   *(Pertahankan konsistensi kode agar query JOIN antara tabel fakta dan dimensi master tetap menghasilkan relasi yang valid).*
2. **Nilai Moneter / Rupiah (Scaling Factor):** Kalikan seluruh kolom finansial dengan faktor pengali rahasia (misal $k = 0.732$ atau normalisasi indeks $0.0 - 1.0$).  
   *Manfaat:* Karakteristik analitik (korelasi, ranking top-5 operator, tren bulanan, dan agregasi SUM) **tetap 100% utuh**, namun nominal rupiah asli perusahaan terlindungi secara matematis.
3. **Nomor Dokumen Legal:** Ganti dengan pola dummy (contoh: `TPS/REG/2025/XXXX`) dan kolom `supporting_document` diisi string dummy `https://internal.tps.co.id/doc/sample_XXXX`.

---

# 6. KETERSEDIAAN ARTEFAK UNTUK BIMBINGAN DOSEN

Berikut adalah inventarisasi status artefak di repositori proyek:

### A. Artefak yang SUDAH TERSEDIA di Repositori Proyek
* [x] **File Data Mentah Asli:** 9 file Excel lengkap di folder `data/raw/`.
* [x] **Data Checkpoint Bronze (CSV):** 65 file CSV data mentah per sheet di folder `data/bronze/`.
* [x] **Data Checkpoint Silver (CSV):** 65 file CSV data bersih per sheet di folder `data/silver/`.
* [x] **Data Checkpoint Gold (CSV):** 65 file CSV data terstandarisasi per sheet di folder `data/gold/`.
* [x] **Basis Data DuckDB Fisik:** File `data/processed/tps_komersial.duckdb` (10 tabel, 32.264 baris).
* [x] **Log Eksekusi Pipeline Riil:** File `logs/etl_system.log` (merekam seluruh tahapan eksekusi per sheet).
* [x] **Source Code ETL:** Script [main_etl.py](../backend/etl/main_etl.py), [transformers.py](../backend/etl/transformers.py), dan [utils.py](../backend/etl/utils.py).
* [x] **Data Explorer Interaktif (Admin Dashboard):** Fitur *"Intip Data"* di dashboard admin web UI untuk melihat 25 baris sampel setiap tabel.

### B. Artefak yang BELUM TERSEDIA di Repositori Proyek
* [ ] **Dokumen Data Dictionary Terpadu:** Belum ada satu berkas dokumen PDF/Markdown resmi yang merangkum definisi bisnis, rumus, dan tipe data setiap kolom dalam 1 tabel terpadu.
* [ ] **Diagram Visual Relasi Data (ERD / Star Schema Diagram):** Belum ada file diagram relasi visual resmi (PNG/SVG) yang siap disisipkan langsung ke naskah skripsi Bab 3.
* [ ] **Script Ekspor Sampel Ringkas untuk Dosen:** Belum ada script otomatis untuk mengambil 5 baris pertama dari Raw $\rightarrow$ Bronze $\rightarrow$ Silver $\rightarrow$ Gold secara berdampingan (*side-by-side comparison*) dalam satu berkas cetak siap bimbingan.
* [ ] **Automated Data Masking Script:** Script ETL saat ini memproses data riil secara langsung tanpa tahapan anonimisasi otomatis jika data diekspor untuk publikasi publik.

---

# 7. MATRIKS HASIL AUDIT & REKOMENDASI TINDAK LANJUT

### Matriks Pemetaan End-to-End Pipeline

| Tahap | Input | Proses | Output | Bukti di Code / File Fisik |
|:---|:---|:---|:---|:---|
| **Raw** | File spreadsheet operasional dari divisi komersial TPS. | Pengarsipan file mentah apa adanya di storage internal. | 9 File `.xlsx` (total ~2.99 MB, 48 sheets). | Direktori [data/raw/](../data/raw) |
| **Bronze** | 9 file Excel di `data/raw/`. | Ekstraksi otomatis per sheet dengan `pd.read_excel(..., sheet_name=None)`. | In-memory DataFrames + 65 file CSV mentah. | [main_etl.py: L71-L81](../backend/etl/main_etl.py#L71-L81) & folder [data/bronze/](../data/bronze) |
| **Silver** | DataFrame Bronze per sheet. | Hapus kolom Unnamed, trimming string header, standarisasi nama LOP & %, replace dash `"-"` $\rightarrow$ 0, pemaksaan numerik (`pd.to_numeric`). | In-memory DataFrames bersih + 65 file CSV bersih. | [utils.py: L41-L93](../backend/etl/utils.py#L41-L93) & folder [data/silver/](../data/silver) |
| **Gold** | DataFrame Silver per sheet. | Unpivot (*melt*) sheet pivot horizontal, filter tahun operasional valid (`2020 <= year <= 2030`), snake_case regex, tagging metadata. | In-memory DataFrames terstandarisasi + 65 file CSV. | [transformers.py: L1-L203](../backend/etl/transformers.py#L1-L203) & folder [data/gold/](../data/gold) |
| **DuckDB** | Koleksi DataFrame Gold per kategori tabel. | `pd.concat()`, penanaman tabel fisik (`CREATE OR REPLACE TABLE`), ekstraksi `dim_vessel_operator`, pemangkasan string `' 00:00:00'`, casting diskrit ke `BIGINT`. | 10 Tabel Basis Data OLAP (`tps_komersial.duckdb`, ukuran 7.51 MB). | [main_etl.py: L102-L250](../backend/etl/main_etl.py#L102-L250) & [tps_komersial.duckdb](../data/processed/tps_komersial.duckdb) |

---

### A. Temuan yang Sudah Terverifikasi (Fakta Aktual)
1. Arsitektur data telah menerapkan **Arsitektur Medallion lengkap** yang berjalan 100% otomatis dari file Excel mentah hingga basis data DuckDB via script `backend/etl/main_etl.py` dan endpoint `/api/v1/admin/re_etl`.
2. Pipeline terbukti menghasilkan artefak fisik riil berupa **65 file CSV Bronze, 65 file CSV Silver, dan 65 file CSV Gold** di folder `data/` yang dapat ditunjukkan langsung ke dosen pembimbing.
3. Transformasi kompleks seperti **Unpivot (*pd.melt*)** pada data pangsa pasar dan **Pemulihan Tahun Rusak (*recovery logic*)** pada data kapal benar-benar ada dan berjalan aktif di *source code*.
4. Basis data DuckDB memiliki **10 tabel operasional** yang terindeks dan terhubung langsung ke multi-agent system (Router, SQL Gen, dan Visualization Generator).

### B. Hal yang Belum Dapat Diverifikasi
1. **Siklus Pembaruan File Mentah Otomatis:** Saat ini penambahan file Excel di `data/raw/` masih bersifat statis/manual (belum terhubung ke cronjob download otomatis dari server intranet TPS / SAP / TOS).
2. **Metadata Pembuat File Excel Asli:** Identitas staf atau unit kerja penyusun file spreadsheet mentah di TPS tidak tercatat dalam metadata file Excel (hanya label sheet dan formula sel).

### C. Data / Artefak yang Perlu Disiapkan untuk Bimbingan Berikutnya
1. **Printout / Screenshot Sampel 4 Tahap (Raw, Bronze, Silver, Gold):**
   Ambil 1 kasus nyata yang paling menarik, yaitu sheet **`B.OPR INT`** (menunjukkan data awal pivot horizontal di Excel, masuk ke Bronze, dibersihkan di Silver, hingga di-unpivot rapi di Gold).
2. **Tabel Rekapitulasi 10 Tabel DuckDB:**
   Bawa tabel rekapitulasi jumlah baris dan kolom yang ada di Fokus 4 laporan ini untuk membuktikan volume data Tugas Akhir Anda mencapai **>32.000 baris data analitik**.
3. **Dokumen Kebijakan Anonimisasi Data:**
   Bawa draft rencana masking (Fokus 5 laporan ini) untuk meminta persetujuan dosen pembimbing terkait batas-batas data yang boleh ditampilkan pada naskah skripsi yang akan dipublikasikan di perpustakaan kampus.

### D. Rekomendasi Dokumentasi Raw → Gold yang Sebaiknya Dibuat
1. **Buat Diagram Alur Data (Data Lineage Diagram) per Tabel Utama:**
   Gambarkan perjalanan data dari sheet Excel asal hingga menjadi tabel DuckDB untuk Bab 3 Skripsi.
2. **Sediakan Cuplikan Before-After Script:**
   Dokumentasikan fungsi `sanitasi_skema_awal`, `paksa_angka`, dan logika `pd.melt` sebagai inovasi *data preprocessing* pada Bab 4 Skripsi.
