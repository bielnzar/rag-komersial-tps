# 📘 Handover & Blueprint Sistem: TPS Enterprise AI Data Agent

**Tanggal:** Agustus 2026  
**Status Proyek:** Stable / Production-Ready  
**Konteks Dokumen:** Dokumen ini bertindak sebagai Peta Arsitektur dan Panduan Komprehensif (Ground Truth) bagi LLM atau Pengembang Baru untuk memahami keseluruhan sistem, mulai dari Data Engineering, Multi-Agent AI (LangGraph), hingga integrasi UI. Sama sekali tidak ada halusinasi dalam dokumen ini; semua berdasarkan struktur kode dan implementasi aktual.

---

## 🎯 1. Gambaran Umum Sistem (Executive Summary)

Aplikasi ini adalah **AI Data Agent** berstandar Enterprise yang dirancang khusus untuk menganalisis data finansial dan operasional **PT Terminal Petikemas Surabaya (TPS)**. 

Alih-alih sekadar menjadi *chatbot* teks, agen ini mampu secara otomatis menerjemahkan pertanyaan bisnis (Natural Language) menjadi bahasa pemrograman database murni (SQL), mengeksekusinya ke dalam database lokal berkecepatan tinggi, lalu mengubah hasilnya menjadi narasi bisnis dan grafik interaktif (Apache ECharts).

Sistem ini didesain dengan memprioritaskan:
1. **Zero Data Leakage:** Database operasional tidak pernah dikirim ke pihak LLM eksternal. LLM hanya menerima Skema (Nama Kolom) dan bertugas merakit sintaks query saja.
2. **Cost-Efficiency & Low Latency:** Menggunakan arsitektur "Hybrid LLM" yang memisahkan beban otak logis (Gemini) dan perakit struktur JSON cepat (Groq).
3. **Ketahanan / Fault-Tolerance:** Menggunakan mekanisme *Execution-Guided Self-Healing* dan *Multi-Key Pool Rotator*.

---

## 🏗️ 2. Tumpukan Teknologi Utama (Tech Stack)

### A. Backend Layer
- **Framework:** `FastAPI` (Python 3.11+)
- **Analytical Database (OLAP):** `DuckDB` (Digunakan untuk querying triliunan baris data secara instan).
- **In-Memory Cache:** `Redis` (Disematkan dalam modul `semantic_cache.py` untuk mengamankan riwayat sesi dan menahan laju request yang sama berulang kali).
- **Authentication:** `JWT (JSON Web Tokens)` & Algoritma Hashing `PBKDF2`.

### B. AI & Orchestration Layer
- **Orkestrator Utama:** `LangGraph` (Mendefinisikan aliran kerja sebagai *State Machine* antar sekumpulan Agen AI).
- **LLM Provider (Layer 1 - Logic):** `Google Gemini 3.6 Flash` via `langchain-google-genai` (Dengan *fallback* ke Gemini 3.5 Flash).
- **LLM Provider (Layer 2 - JSON/Viz):** `Groq Cloud (GPT-OSS-20b)` via `langchain-groq` (Dioptimalkan untuk kecepatan cetak karakter tertinggi).

### C. Frontend Layer
- **Framework:** `Vue 3` (Composition API) berjalan di atas ekosistem `Vite`.
- **Styling:** `Tailwind CSS` (Menggunakan desain estetik ala *Glassmorphism* dan palet *Dark Mode* elegan).
- **Visualisasi Data:** `Apache ECharts` (Via komponen khusus `v-chart`).

---

## 🧬 3. Alur Data & Medallion Architecture (ETL)

Sistem memastikan data akuntansi aman melalui tahapan *Cleansing* berstandar Medallion (`backend/etl/`). File awal berupa lembaran Microsoft Excel (`.xlsx`) yang disinkronisasi dari Google Drive.

1. **Bronze Layer (`backend/etl/bronze.py`):** Menggunakan *Pandas* untuk mengonsumsi data mentah dari `.xlsx` as-is.
2. **Silver Layer (`backend/etl/transformers.py`):** Membersihkan kolom kosong ("kolom hantu"), menormalisasi penamaan, melakukan fungsi Unpivot untuk matriks berantakan, serta memastikan tipe data nominal benar (memaksa tipe *float/int*).
3. **Gold Layer (`backend/etl/gold.py`):** Mentransformasi data bersih menjadi *Star Schema* / Data Mart dan menginjeksinya (menyimpan) secara persisten ke dalam `data/processed/tps_komersial.duckdb`.

> **Catatan Semantic Layer:** Di tahap `transformers.py` (khususnya untuk tabel `DATA KOMERSIAL` dan `TREND KOMERSIAL`), kolom pendapatan dipisahkan menjadi dua: `total_all_revenue` dan `total_revenue`. *Knowledge* ini secara ketat disuntikkan ke dalam Prompt AI agar selalu memanggil klausa `COALESCE(total_all_revenue, total_revenue)` saat menganalisis pendapatan.

---

## 🤖 4. Multi-Agent AI Workflow (LangGraph)

Saat pengguna mengirimkan pertanyaan lewat portal obrolan, *request* tidak diselesaikan oleh satu agen AI, melainkan didelegasikan ke "tim spesialis" di `backend/agents/`:

1. **Router Node (`router.py`)**: 
   Bertindak sebagai Resepsionis. Ia mengevaluasi pertanyaan dan mencocokkannya dengan *Glosarium Database* (Katalog Tabel DuckDB) untuk memutuskan tabel mana yang relevan.
   
2. **SQL Generator Node (`sql_gen.py`)**: 
   Agen paling krusial. Memakai model dengan nalar tertinggi (**Gemini 3.6 Flash**, `temperature=0.0`). Ia membaca skema hasil dari Router, dan menerjemahkannya murni ke DuckDB SQL. *Prompt* pada agen ini membawa injeksi "Semantic Layer" (misal: "Domestik" = "DOMESTIC", `COALESCE` kolom revenue).

3. **Sanitizer Node (`sanitizer.py`)**: 
   Bukan LLM, melainkan kode skrip Python statis (*Hard Rules*). Mengamankan SQL dari potensi injeksi berbahya (memblokir DROP, DELETE, INSERT), membatasi `LIMIT 500` secara otomatis, dan memastikan format *Date Interval* sejalan dengan standar khusus mesin DuckDB.

4. **Execute Node (`execute.py`)**: 
   Mengeksekusi SQL di database nyata. Jika muncul `Error` (misal kolom tidak ditemukan), alur akan dibelokkan **kembali ke SQL Generator** (Mekanisme *Execution-Guided Self-Healing*). Proses retur (coba ulang) dibatasi maksimal 3 kali. Jika berhasil, data ditangkap ke dalam variabel `query_result`.

5. **Visualization Node (`viz_gen.py` & `chart_gen.py`)**: 
   Bertugas merangkai narasi *Summary* bagi Direksi, sekaligus merakit struktur JSON `echarts_config` yang ketat. Menggunakan model kilat (**Groq Llama 3 / GPT-OSS**) karena tidak membutuhkan nalar rumit, hanya formatting cepat dari data tabular menjadi format *ECharts*.

---

## 🔑 5. Infrastruktur Enterprise (Keamanan & Telemetri)

### A. Sistem Otentikasi (JWT + PBKDF2)
- Terdapat dua role utama: `staff` dan `executive`/`admin`. 
- Sistem *History* (Riwayat Percakapan) dipisahkan secara eksklusif menggunakan JWT *Subject* (`user_id`). Cache tidak akan tercampur antar-pengguna.

### B. Multi-Key API Rotator & Fallback
Berada di pusat *brain* LLM (`backend/agents/llm_helper.py` dan `api_keys_manager.py`).
- **Masalah umum:** LLM di *Cloud* sering kali mengembalikan *HTTP 429 Resource Exhausted / Rate Limit*.
- **Solusi kami:** Kami menyimpan pool berisi **5 API Key Gemini** dan **5 API Key Groq** (diatur dari halaman Frontend Admin). 
- Jika eksekusi gagal akibat limit (429), sistem otomatis memberi label `COOLDOWN` 60 detik pada kunci tersebut, dan menggeser *request* ke Kunci API berikutnya tanpa disadari oleh pengguna. Jika satu tingkat model hancur total, ia memiliki fallback struktural (`gemini-3.6-flash` -> `gemini-3.5-flash`).

### C. Telemetri Token & Latensi RAG (Audit Trail)
Kita harus tahu ke mana uang perusahaan pergi (Audit Konsumsi Token). 
- Setiap invocasi LLM ditangkap metrik penggunaannya (`input_tokens`, `output_tokens`, `latency_ms`, dan `status`).
- Data tersebut dicatat secara *Asynchronous Threading* ke dalam DuckDB terpisah, yakni tabel **`log_audit_token`** (`telemetry.duckdb`). Penggunaan database terpisah ini menghindari bentrokan status **Write-Lock** dengan database analitik `tps_komersial.duckdb` (yang selalu terbuka dalam mode *read-only* bagi sesi pengguna).

---

## 🎨 6. Integrasi Frontend Admin (Vue 3)

Antarmuka dibangun dengan mengutamakan UX berkelas eksekutif:
- Komponen chat responsif yang cerdas dalam menahan konteks (`App.vue`, `SidebarHistory.vue`).
- Memiliki fitur pembersihan Cache / Sesi.
- **Admin Portal (`AdminDashboard.vue`)**:
  Dapat diakses hanya oleh akun bertipe `admin` atau `executive` via tombol (⚙️) di Navbar atas. Portal ini mengekspos API Endpoint khusus dari `main.py` yang memberikan kekuatan pada admin untuk:
  1. Memantau kesehatan RAG, metrik Latensi LLM rata-rata, persentase keberhasilan (*success rate*), dan pemakaian Token harian.
  2. Melihat ukuran dan jumlah baris data faktual pada mesin analitik DuckDB.
  3. Memasukkan/memperbarui secara instan Multi-Key Rotator (Gemini/Groq) untuk sistem ketahanan beban tanpa harus merestart server.

---
**-- Akhir dari Blueprint Milestone --**
*(Dokumen ini dibuat dan divalidasi oleh AI Architect berdasarkan pemeriksaan struktural kode secara mendalam).*
