# System Context & Technical Blueprint: AI Data Agent PT TPS

Dokumen ini berisi detail teknis dan rancangan arsitektur untuk proyek **Pengembangan AI Data Agent Berbasis Multi-Agent Text-to-SQL dan Arsitektur Medallion**. Dokumen ini dirancang untuk menjadi acuan utama (*system context*) bagi pengembangan (*prompting*) selanjutnya.

## Pilar Arsitektur Utama (State-of-the-Art)
Sistem ini WAJIB mengadopsi 3 pilar arsitektur utama untuk menjamin akurasi, performa, dan ketahanan sistem (berdasarkan literatur IEEE/ACM):
1. **Injeksi Lapisan Semantik (Semantic Layer Integration):** Sebelum LLM memproses teks ke SQL, sistem wajib menyertakan Glosarium Metadata Bisnis (menerjemahkan istilah operasional logistik pelabuhan), Pemetaan Relasi Skema, dan Definisi Metrik Kurasi (rumus agregasi baku). Ini mencegah halusinasi skema pada LLM.
2. **LangGraph Orchestration & Hard Rules Sanitizer:** Setiap kueri SQL dari LLM wajib dilewatkan ke *node sanitizer* yang menegakkan aturan ketat (contoh: hanya mengizinkan satu blok `SELECT`, tabel/view wajib valid, dan format interval mematuhi sintaks DuckDB) sebelum dieksekusi.
3. **Execution-Guided Self-Healing Loop:** Menerapkan dekomposisi berulang. Jika eksekusi SQL gagal (*syntax error*) atau mengembalikan hasil kosong (*empty result set*), tangkap pesan error dan kembalikan ke agen untuk koreksi mandiri (maksimal 3 kali *retry*).

## 1. Arsitektur Integrasi Data (Google Drive ke Medallion)
Mengingat data sumber (.xlsx) diasumsikan berada di Google Drive (berfungsi layaknya SharePoint untuk kolaborasi), alur ingestinya adalah sebagai berikut:
- **Sinkronisasi (Google Drive -> Lokal):** 
  - **Opsi A (API):** Menggunakan Google Drive API (Service Account) untuk secara berkala mengunduh file `.xlsx` dari folder spesifik di Drive ke direktori lokal *server* (misal: `data/raw/`).
  - **Opsi B (Sync App):** Jika berjalan di server/PC lokal dengan Google Drive for Desktop terpasang, folder tersebut sudah otomatis tersinkronisasi. Sistem hanya perlu memantau folder lokal tersebut.
- **Event Trigger (Watchdog / APScheduler):**
  - Direktori `data/raw/` akan dipantau oleh modul `watchdog`.
  - Saat ada file baru atau perubahan file `.xlsx`, mekanisme *debouncing* (menunggu beberapa detik/menit setelah modifikasi terakhir) akan aktif guna memastikan file tidak diakses saat proses sinkronisasi/unduhan masih berjalan, mencegah *data corruption*.

## 2. Rancangan Struktur Direktori Proyek
Proyek akan dibagi menjadi *Backend* (Python) dan *Frontend* (Vue.js). Untuk Backend, disarankan menggunakan arsitektur modular berikut:

```text
rag-komersial-tps/
├── data/
│   ├── raw/             # File .xlsx mentah tersinkronisasi dari GDrive (Bronze Layer)
│   ├── processed/       # File temporary hasil cleansing (Silver Layer - opsional)
│   └── tps_data.duckdb  # Database persisten DuckDB (Gold Layer)
├── backend/
│   ├── api/             # FastAPI routers, endpoints, dan controllers
│   ├── core/            # Konfigurasi environment, keamanan, RBAC
│   ├── etl/             # Pipeline Data Engineering (Medallion)
│   │   ├── ingest.py    # Script integrasi GDrive & event listener (Watchdog)
│   │   ├── bronze.py    # Membaca mentah via Pandas
│   │   ├── silver.py    # Validasi Pandera/Pydantic & data cleansing
│   │   └── gold.py      # Proses Unpivot, Star Schema, Load ke DuckDB
│   ├── agents/          # Logika Orkestrasi AI LangGraph
│   │   ├── state.py     # Definisi State/Konteks graph
│   │   ├── router.py    # Agen 1: Pemilah Konteks & Intent
│   │   ├── sql_gen.py   # Agen 2: Text-to-SQL & Mekanisme Self-healing
│   │   └── viz_gen.py   # Agen 3: Generator narasi (NLG) & JSON ECharts
│   ├── services/        # Business logic & helper (Eksekusi SQL, Redis Cache)
│   └── main.py          # Entry point aplikasi FastAPI
├── frontend/            # Vue.js 3 + TailwindCSS + ECharts (inisialisasi terpisah)
├── requirements.txt
├── .env                 # API keys (Gemini, GDrive, dll)
└── README.md
```

## 3. Detail Implementasi Orkestrasi LangGraph (Multi-Agent State Machine)
Proses interaksi *chatbot* akan diorkestrasi menggunakan **LangGraph**. Graph *State* akan menyimpan variabel konteks selama siklus berjalan:

**Definisi Graph State:**
- `user_query`: Pertanyaan asli pengguna.
- `user_role`: Peran/Divisi pengguna (untuk filter RBAC).
- `relevant_tables`: Daftar tabel dan skema DuckDB hasil analisis Agen 1.
- `generated_sql`: Query SQL yang dirakit oleh Agen 2.
- `sql_error`: Pesan error (jika ada) saat eksekusi SQL di DuckDB, untuk memicu *Self-Healing*.
- `correction_attempts`: Penghitung jumlah percobaan koreksi error SQL (dibatasi maks. 3 kali).
- `query_result`: Hasil eksekusi data tabular dari DuckDB.
- `final_answer`: Narasi teks bahasa natural (jawaban akhir).
- `echarts_config`: Konfigurasi JSON yang siap di-render menjadi grafik.

**Alur Logika Node pada LangGraph:**
1. **`CheckCacheNode`**: Mengecek *Semantic Cache* (Redis). Jika ada kecocokan -> Langsung return hasil.
2. **`RBACNode`**: Memverifikasi otoritas. Jika pertanyaan di luar *role* pengguna -> Block & return pesan peringatan.
3. **`RouterNode` (Agen 1)**: Menganalisis `user_query` terhadap Katalog Data DuckDB. **Wajib menginjeksi Lapisan Semantik** (Glosarium Bisnis, Relasi, Metrik Kurasi) agar LLM memahami konteks logistik pelabuhan secara tepat sebelum memilih tabel.
4. **`SQLGenNode` (Agen 2)**: Menghasilkan *syntax* DuckDB SQL dengan aturan ketat (wajib menggunakan `LIMIT` bila tidak agregasi).
5. **`SanitizerNode`**: Mengeksekusi *Hard Rules Sanitizer* pada SQL dari agen. Memastikan hanya ada satu blok `SELECT`, merujuk pada view/tabel yang diizinkan, dan sesuai format DuckDB.
6. **`ExecuteSQLNode`**: Menjalankan SQL di DuckDB. 
   - *Kondisi A:* Jika eksekusi gagal (*Syntax Error*) atau data kosong (*Empty Result Set*), dan `correction_attempts` < 3 -> Teruskan error tersebut kembali ke `SQLGenNode` untuk diperbaiki (*Self-Healing*).
   - *Kondisi B:* Jika eksekusi berhasil dan menghasilkan data (*Success*) -> Lanjut ke `VizGenNode`.
6. **`VizGenNode` (Agen 3)**: Menganalisis `query_result` dari DuckDB dan menghasilkan narasi (`final_answer`) serta visualisasi ECharts (`echarts_config`).

## 4. Spesifikasi Integrasi Frontend & Backend (API Contracts)
Backend FastAPI akan mengekspos endpoint RESTful untuk dikonsumsi Vue.js Frontend:
- **`POST /api/v1/chat`**
  - **Fungsi:** Mengirim pertanyaan pengguna dan memicu eksekusi LangGraph.
  - **Payload (Request):** `{ "query": "Tampilkan perbandingan throughput bulan ini dan lalu", "user_id": "usr-001", "role": "commercial_manager" }`
  - **Response:** `{ "status": "success", "answer": "Berikut adalah perbandingan throughput...", "chart": { "type": "bar", "options": { ...echarts_json... } } }`
- **`GET /api/v1/data/status`**
  - **Fungsi:** Memeriksa status pipeline ETL (kapan terakhir sinkronisasi GDrive sukses, jumlah baris ter-update).

## 5. Rencana Fase Pengembangan (Roadmap Magang)
Agar sistematis, pengembangan dapat dilakukan dalam tahapan (*milestones*) berikut:
1. **Milestone 1 - Data Engineering (ETL Pipeline):** Setup *mock-up* integrasi GDrive (bisa menggunakan folder statis lokal dulu), kembangkan *script* Pandas untuk memproses *file* Excel dari tahap Bronze hingga Gold (unpivot), dan pastikan data tersimpan sempurna di DuckDB secara presisten.
2. **Milestone 2 - AI Text-to-SQL Core:** Bangun API dengan FastAPI yang langsung terkoneksi ke Gemini 1.5 Flash. Kembangkan *prompt* khusus untuk DuckDB SQL. Mulai integrasikan LangGraph sederhana tanpa *self-healing*.
3. **Milestone 3 - Advanced AI Orkestrasi:** Tambahkan agen *Router*, fitur *Self-Healing* (koreksi error iteratif), RBAC, dan *Redis Semantic Cache*.
4. **Milestone 4 - Analitik & Visualisasi Data:** Kembangkan *VizGenNode* agar *output* LLM tidak hanya teks naratif tapi juga menghasilkan struktur JSON yang dikenali oleh *library* Apache ECharts.
5. **Milestone 5 - Frontend UI/UX:** Bangun UI modern interaktif dengan Vue.js 3 dan Tailwind CSS. Pastikan transisi percakapan *chatbot* dan animasi *chart* terasa mulus dan profesional.

---
*Gunakan file ini sebagai rujukan atau prompt awal pada setiap sesi pengembangan komponen yang spesifik (misal: "Berdasarkan arsitektur ETL di SYSTEM_CONTEXT.md, mari kita kembangkan file silver.py").*
