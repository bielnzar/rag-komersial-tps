# Milestone 1: Data Engineering (Pipeline ETL Medallion)

Dokumen ini membedah apa saja yang sudah kita bangun di **Milestone 1**. Intinya, di fase ini kita menyiapkan fondasi data yang kuat sebelum AI diizinkan untuk "berpikir". Tanpa data yang rapi, AI terpintar sekalipun cuma bakal menghasilkan jawaban ngawur (*Garbage In, Garbage Out*).

---

## 1. Konsep Dasar: Apa itu ETL? (Penjelasan untuk Orang Awam)
Buat yang belum familiar, ETL itu singkatan dari **Extract, Transform, Load**.
Bayangkan tim komersial PT TPS punya banyak file Excel (laporan bulanan, operasional kapal, *market share*). File-file ini formatnya macam-macam, ada yang judul kolomnya pakai bahasa Indonesia, ada yang bahasa Inggris, ada yang datanya menyamping, ada yang datanya kosong.

Kalau file Excel mentah ini langsung dikasih ke AI, AI-nya bakal kebingungan.
Nah, Pipeline ETL adalah **"Pabrik Pengolahan"** otomatis:
- **Extract (Tarik)**: Mengambil paksa data dari file Excel mentah.
- **Transform (Bersihkan & Permak)**: Merapikan data. Kolom yang namanya beda disamakan, angka yang nyangkut jadi teks dipaksa jadi angka murni, dan baris yang kosong dibuang.
- **Load (Simpan)**: Menyimpan data yang sudah "glowing" (bersih) ke dalam sebuah brankas data (*database*) khusus agar bisa ditarik super cepat oleh aplikasi.

---

## 2. Arsitektur Medallion (Cara Kita Memilah Data)
Di proyek ini, kita menggunakan standar industri data modern yang disebut **Medallion Architecture**. Datanya disaring lewat tiga tahap (seperti medali):

### 🥉 Bronze Layer (Data Mentah)
Ini adalah data asli yang ditarik dari Excel menggunakan pustaka Python bernama **Pandas**. Bentuknya masih berantakan persis seperti aslinya. Kita menyimpannya ke format `.csv` murni untuk *backup* dan *checkpoint*. 
- *Analogi: Biji kopi yang baru dipetik dari pohon, masih ada ranting dan kotoran.*

### 🥈 Silver Layer (Data Bersih)
Di tahap ini, *script* `utils.py` dan `transformers.py` mulai bekerja keras. 
- Kita hapus "kolom hantu" (*unnamed columns* yang tidak ada gunanya).
- Kita paksa kolom berbau angka menjadi angka mutlak (`numeric`), agar huruf seperti "NaN" atau "-" tidak merusak sistem perhitungan.
- **Standarisasi Skema**: Kita menyatukan nama kolom yang maknanya sama tapi tulisannya beda. (Misal: `Vessel Operator` diubah paksa jadi `LOP` agar seragam dengan *sheet* lain).
- *Analogi: Biji kopi yang sudah dicuci bersih dan dikupas.*

### 🥇 Gold Layer (Data Matang Siap Konsumsi)
Ini adalah tahap final. Data yang sudah seragam dan bersih kemudian digabung (*concat*) menjadi satu tabel raksasa. 
- Jika ada data yang bentuk laporannya "melebar ke samping" (format *Pivot*, di mana tiap bulan/tahun jadi kolom tersendiri), kita "lipat" ke bawah menggunakan teknik *Unpivot/Melt*. Ini sangat penting karena *Database* dan AI jauh lebih mudah membaca data yang memanjang ke bawah daripada menyamping.
- Data emas ini kemudian disuntikkan ke **DuckDB**.
- *Analogi: Kopi bubuk saset kualitas premium yang tinggal diseduh oleh AI.*

---

## 3. Kenapa Pakai DuckDB? (Untuk Developer)
Di proyek ini kita memakai `tps_komersial.duckdb`. Kenapa nggak pakai MySQL atau PostgreSQL?
1. **Serverless & File-based**: Nggak butuh *install server database* yang berat. Semuanya tersimpan di dalam satu *file* `.duckdb` di dalam folder `data/processed/`. Sangat mudah dipindah-pindah.
2. **Kecepatan Analitik (OLAP)**: DuckDB dirancang spesifik untuk membaca jutaan baris data untuk keperluan analisis (seperti `SUM`, `AVG`, `GROUP BY`) dengan sangat cepat dibandingkan SQLite biasa.
3. **Kompatibilitas Pandas**: DuckDB bisa langsung membaca *DataFrame* Pandas tanpa perlu perantara yang rumit. 

---

## 4. Bedah Kode (Di Balik Layar)
Pekerjaan utama di Milestone 1 terpusat di folder `backend/etl/`:
- **`main_etl.py`**: Ini bosnya. Dia yang membaca semua *file* di folder `data/raw/`. Dia menggunakan sistem *Router* (`FILE_ROUTER`) untuk mengarahkan: *"Oh, ini file Throughput, kirim ke fungsi proses_throughput!"*
- **`transformers.py`**: Berisi tiga fungsi utama (`proses_vessel`, `proses_throughput`, `proses_market_share`). Di sinilah logika *Unpivot* dan penyisipan kategori ("Domestik"/"Internasional") berdasarkan nama *sheet* Excel dilakukan.
- **`utils.py`**: Berisi fungsi-fungsi utilitas generik seperti `paksa_angka()` untuk *cleaning* dan setup *Logging* sistem.

**Hasil Akhir Milestone 1**: 
Tiga buah tabel emas raksasa (`fakta_throughput`, `fakta_vessel`, `fakta_market_share`) yang tertanam kokoh di DuckDB, siap menampung kueri SQL paling brutal sekalipun dari AI kita.
