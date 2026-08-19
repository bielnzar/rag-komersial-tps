# 🏛️ Blueprint Arsitektur Sistem: AI Data Agent (Enterprise Edition)

**Rencana Judul Tugas Akhir:** Pengembangan AI Data Agent Berbasis Multi-Agent Text-to-SQL dan Arsitektur Medallion untuk Analitik Komersial pada PT XYZ

**Studi Kasus:** PT Terminal Petikemas Surabaya (TPS)

**Fokus Arsitektur:** Full Dataset (Non-Streaming), Deterministic Mapping, Multi-Agent LLM & Self-Healing

---

## 👨‍🎓 Identitas Penulis

- **Nama Lengkap:** Nabiel Nizar Anwari
- **NIM / NPM:** 5027231087
- **Program Studi:** Teknologi Informasi
- **Universitas / Institusi:** Institut Teknologi Sepuluh Nopember
- **GitHub / Email:** bielnzar / biel.nizar79@gmail.com

---

## 1. Pendekatan Utama (Core Philosophy)

- **Akurasi Numerik Tinggi:** LLM (_Large Language Model_) tidak digunakan untuk melakukan komputasi numerik secara langsung, melainkan difokuskan untuk menerjemahkan bahasa alami menjadi _query_ `SQL`. Eksekusi komputasi sepenuhnya ditangani oleh DuckDB untuk menjamin determinisme dan akurasi data.
- **Efisiensi Biaya dan Waktu:** Optimalisasi melalui proses _Unpivot_ dan penyederhanaan skema _database_ dilakukan untuk menekan jumlah token yang diproses oleh LLM, sehingga memungkinkan waktu respons yang mendekati _real-time_.
- **Keamanan dan Kontrol Akses (RBAC):** Privasi data perusahaan dijaga dengan memproses _dataset_ secara lokal (tidak dikirim ke layanan _cloud_ publik). Selain itu, sistem menerapkan _Role-Based Access Control_ (RBAC) pada setiap instruksi _query_ untuk mencegah akses silang antar divisi yang tidak sah.
- **Keandalan Sistem (Resiliency):** Sistem mengadopsi validasi struktur data (_Data Contract_) serta mekanisme perbaikan _query_ otomatis (_Self-Healing_) oleh agen AI untuk meminimalisasi kegagalan sistem akibat _query_ yang tidak valid.

---

## 2. Alur Pemrosesan Data: Data Engineering & ETL (Medallion Architecture)

_Proses ETL (Extract, Transform, Load) berjalan secara asinkron di latar belakang dengan penanganan error untuk meminimalisasi interupsi layanan._

1. **Pemicu (Trigger & Debouncing):** Sistem memantau perubahan pada _file_ `.xlsx` di _server_ lokal menggunakan modul `watchdog` atau `APScheduler`. Pemrosesan data hanya akan dieksekusi setelah pengguna menyelesaikan pembaruan pada _file_ guna menghindari pemrosesan data parsial.
2. **Bronze Layer (Data Ingestion):** Tahap awal untuk membaca berbagai _file_ mentah berbasis Excel (`.xlsx`) menggunakan **Pandas** tanpa melakukan modifikasi.
3. **Silver Layer (Pembersihan, Validasi, & Pemetaan):**
   - **Validasi Data Contract:** Implementasi Pydantic/Pandera untuk memastikan konsistensi struktur kolom pada sumber data Excel, meminimalisasi error sistem jika terjadi modifikasi pada nama atau tipe kolom.
   - **Pembersihan Data:** Eliminasi baris atau kolom yang tidak memiliki nilai (NaN/Null).
   - **Pemetaan Data:** Penggabungan _sheet_ yang memiliki skema identik menggunakan aturan deterministik.
4. **Gold Layer (Unpivot & Konsolidasi):**
   - Penggunaan fungsi `pandas.melt()` untuk melakukan normalisasi tabel dari bentuk _Pivot_ menjadi _Flat Table_ (Unpivot).
   - Proses peleburan berbagai _sheet_ menjadi beberapa **Tabel Inti** menggunakan desain _Star Schema_.
5. **Database & Auto-Cataloging (DuckDB Persistent):**
   - Seluruh Tabel Inti disimpan secara lokal pada _file_ `tps_data.duckdb` untuk menjaga persistensi data saat sistem _restart_, namun proses _query_ dieksekusi secara _In-Memory_ untuk memastikan _latency_ yang rendah.
   - Sistem secara otomatis akan membaca _Information Schema_ untuk menghasilkan **Katalog Data** yang digunakan oleh agen AI.

---

## 3. Alur Logika AI: Orkestrasi Multi-Agen (Two-Pass LLM)

_Arsitektur yang mengandalkan beberapa agen LLM spesifik dengan mitigasi halusinasi dan batasan panjang konteks yang ketat._

1. **Verifikasi Keamanan dan Sistem Cache:**
   - **Penerapan RBAC:** Memeriksa otoritas akses pengguna sebelum permintaan diteruskan ke agen AI. Pertanyaan di luar cakupan otorisasi akan secara proaktif diblokir.
   - **Redis Caching:** Memanfaatkan _semantic cache_ untuk merespons pertanyaan berulang dengan _latency_ minimal tanpa perlu melakukan pemanggilan API tambahan ke LLM.
2. **Agen 1 (Router / Pemilah Konteks):**
   - **Input:** _Query_ Pengguna + Katalog Data + Konteks Otorisasi Pengguna.
   - **Fungsi:** Mengidentifikasi tabel maupun skema data yang paling relevan dengan _intent_ pengguna.
3. **Agen 2 (Specialist / Text-to-SQL):**
   - **Input:** _Query_ Pengguna + Detail Skema Tabel.
   - **Fungsi:** Bertugas mengubah _query_ berbahasa alami menjadi sintaks `SQL` fungsional.
   - **Pembatasan Data:** Agen ini diinstruksikan untuk menambahkan klausul `LIMIT` pada _query_ yang menghasilkan data mentah non-agregat guna mencegah kelebihan beban pada memori sistem (OOM).
4. **Siklus Eksekusi dan Koreksi Otomatis (Self-Healing Loop):**
   - Sistem aplikasi mengeksekusi _query_ `SQL` melalui DuckDB.
   - **Koreksi Otomatis:** Apabila eksekusi menghasilkan error seperti _Syntax Error_, sistem akan meneruskan pesan error tersebut kembali ke Agen 2 untuk diperbaiki secara iteratif (dibatasi maksimal 3 siklus koreksi) tanpa memunculkan interupsi pada _User Interface_ (UI) pengguna.
5. **Agen 3 (Generator Data & Visualizer):**
   - **Input:** _Intent_ Awal Pengguna + Hasil _Query_ Aktual dari DuckDB.
   - **Fungsi:** Menganalisis hasil _query_ untuk disusun menjadi narasi penjelasan analisis (_Natural Language Generation_/NLG), sekaligus menyusun data menjadi format `JSON` yang siap dirender menjadi elemen visualisasi.

---

## 4. Spesifikasi Teknologi (Tech Stack)

### A. Pemrosesan Data dan Backend

- **Framework:** FastAPI (Python) — _Berkinerja tinggi dengan dukungan Asynchronous._
- **Data Engineering:** Pandas — _Utilitas untuk memanipulasi data dan proses Unpivot dalam Medallion Architecture._
- **Data Validation:** Pandera / Pydantic — _Memastikan konsistensi struktur Data Contract dari sumber data eksternal._
- **OLAP Database:** DuckDB (Persistent Mode) — _Database analitik berskala lokal dengan kinerja query tingkat In-Memory._
- **Task Scheduler:** APScheduler / Watchdog — _Menangani mekanisme pemantauan otomatisasi ETL._

### B. Orkestrasi AI dan Caching

- **Orchestrator:** LangGraph — _Mengembangkan workflow State Machine untuk orkestrasi Multi-Agen dan mekanisme Self-Healing._
- **Model Bahasa (LLM):** Google Gemini 1.5 Flash (via API) — _Model AI yang efisien untuk latency rendah pada sistem agen logis._
- **Sistem Cache:** Redis — _Penyimpanan riwayat sesi pengguna dan implementasi Semantic Caching._

### C. Frontend dan Visualisasi Data

- **UI Framework:** Vue.js 3 — _Pengembangan UI berbasis komponen yang reaktif._
- **Styling:** Tailwind CSS — _Membangun UI modern yang responsif dan konsisten._
- **Visualisasi Data:** Apache ECharts — _Mengolah objek JSON hasil analisis menjadi grafik interaktif untuk pengguna._
