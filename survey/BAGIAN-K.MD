# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN K
## OUTPUT ANALITIK, VISUALISASI DATA, & TELEMETRI

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Frontend UI Component Inspection (`ChatMessage.vue`, `EChartsViewer.vue`), Agent Code Review (`viz_gen.py`, `chart_gen.py`), & Telemetry Database Audit

---

### 1. Bentuk Penyajian Output Analitik
* **Bentuk Output:** **KOMBINASI MULTI-MODAL TERPADU (Narrative + Interactive Chart + Raw Table Modal + SQL Inspector).**
* **Elemen-Elemen Output yang Diterima Pengguna:**
  1. **Executive Narrative (Teks Narasi Resmi):** Disajikan langsung sebagai jawaban utama di chat panel dengan penomoran rapi (`1. `, `2. `), cetak tebal nama entitas, satuan standar pelabuhan (*TEUs*, *Boxes*), dan pemisah ribuan titik pada mata uang Rupiah (*Rp*).
  2. **Interactive Chart (Apache ECharts):** Grafik dinamis yang dapat di-hover, di-zoom, dan memiliki tooltip serta label angka presisi.
  3. **Data Table Modal (Tabel Data Mentah):** Pengguna dapat mengklik tombol *"Lihat Data Tabel"* untuk memeriksa seluruh baris data tabular hasil kueri DuckDB melalui komponen modal [`DataTableModal.vue`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/frontend/src/components/DataTableModal.vue).
  4. **SQL Accordion (Transparansi Kueri):** Komponen *collapsible* [`SqlAccordion.vue`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/frontend/src/components/SqlAccordion.vue) yang memungkinkan auditor atau manajemen melihat kueri DuckDB SQL yang dieksekusi.

---

### 2. Bagaimana Sistem Menentukan Jenis Visualisasi?
Penentuan jenis grafik dipandu oleh aturan semantik di dalam prompt [`backend/agents/chart_gen.py:L46-L51`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/chart_gen.py#L46-L51):
* **Bar Chart (`type: 'bar'`):** Dipilih untuk data kategori, perbandingan antar operator/layanan, atau ranking (misal: *Top 5 LOP Revenue* atau *Realisasi Throughput Domestik vs Internasional*).
* **Line Chart (`type: 'line'`):** Dipilih untuk data deret waktu (*time-series*), tren pergerakan bulanan, atau perbandingan pertumbuhan antar tahun (*year-on-year growth*).
* **Pie / Donut Chart (`type: 'pie'`):** Dipilih untuk data proporsi persentase atau pangsa pasar (*Market Share*).
* **Fitur On-Demand Charting:** Jika pengguna tidak meminta grafik di awal, sistem menampilkan tombol *"📊 Visualisasikan Grafik"* di bawah pesan, memungkinkan pengguna meminta visualisasi secara *on-demand*.

---

### 3. Apakah Ada Agent Khusus untuk Visualisasi?
* **Status:** `IMPLEMENTED (STEP 5 & Chart Generator Sub-Module)`
* **Implementasi:**
  1. **Node LangGraph:** `viz_gen_node` di [`backend/agents/viz_gen.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/viz_gen.py) bertanggung jawab atas orkestrasi narasi bisnis dan penanganan *graceful degradation*.
  2. **Dedicated Generator:** `generate_chart_config()` di [`backend/agents/chart_gen.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/chart_gen.py) bertindak sebagai spesialis sintesis format JSON Apache ECharts.

---

### 4. Apakah LLM Digunakan untuk Narasi?
* **Jawaban:** **YA, MENGGUNAKAN MODEL DEDIKASI TINGGI.**
* **Model yang Digunakan:** **`openai/gpt-oss-20b` via Groq Cloud LPU**.
* **Alasan:** Menghasilkan bahasa Indonesia yang santun, formal, dan berstruktur eksekutif tanpa menghabiskan kuota token Google Gemini yang digunakan oleh SQL Generator.

---

### 5. Data Apa yang Dikirim ke LLM untuk Membuat Narasi?
Data yang dikirimkan ke prompt LLM adalah:
1. **`question`:** Teks pertanyaan asli pengguna.
2. **`data`:** Kumpulan data tabular hasil eksekusi DuckDB yang telah diformat menjadi **Compact CSV String** (baris nilai dipisahkan koma, titik koma untuk sanitasi string internal) untuk menghemat ukuran token hingga 50% dibanding JSON biasa.

---

### 6. Apakah Ada Pembatasan Jumlah Record Sebelum Dikirim ke LLM?
* **Status:** `IMPLEMENTED (Smart Row Sampling 15 Baris)`
* **Batasan Konkret:** Dibatasi secara ketat **maksimal 15 baris data teratas** melalui fungsi `format_data_compact()` di [`backend/agents/viz_gen.py:L11-L31`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/viz_gen.py#L11-L31).
* **Mekanisme Indikator Agregat:** Jika hasil kueri memiliki lebih dari 15 baris (misal 500 baris), sistem memotongnya pada baris ke-15 dan menambahkan informasi footer penutup:
  ```text
  ... (dan 485 baris data lainnya. Total keseluruhan baris: 500)
  ```
* **Dampak:** Memangkas ~80% konsumsi token payload data dan mencegah pembengkakan biaya API LLM pada kueri tabel besar.

---

### 7, 8, & 9. Evaluasi Feedback Mechanism (User vs System Feedback)

Untuk keperluan pelaporan akademik yang objektif, audit membedakan antara **User Feedback** dan **System Telemetry**:

| Kategori Feedback | Status Implementasi | Deskripsi & Lokasi Penyimpanan |
| :--- | :---: | :--- |
| **User Explicit Feedback** (Thumbs Up / Down / Rating Bintang) | `NOT FOUND (Belum Diimplementasikan)` | Saat ini belum ditemukan tombol rating kepuasan pengguna (*thumbs up / thumbs down*) ataupun formulir koreksi jawaban di antarmuka obrolan `ChatMessage.vue`. |
| **Machine Telemetry Audit** (System Performance Feedback) | `IMPLEMENTED` | Sistem secara otomatis mencatat telemetri performa AI ke dalam database terpisah: **`data/processed/telemetry.duckdb`** pada tabel **`log_audit_token`**. |

* **Skema Data Telemetri yang Disimpan di `telemetry.duckdb`:**
  ```sql
  CREATE TABLE log_audit_token (
      id VARCHAR PRIMARY KEY,
      timestamp TIMESTAMP,
      agent_name VARCHAR,    -- router / sql_gen / viz_gen
      provider VARCHAR,      -- google / groq
      model_name VARCHAR,    -- gemini-3.6-flash, gpt-oss-20b, dsb.
      input_tokens INTEGER,  -- perkiraan token prompt masuk
      output_tokens INTEGER, -- token jawaban keluar
      total_tokens INTEGER,
      latency_ms DOUBLE,     -- durasi eksekusi dalam milidetik
      status VARCHAR         -- success / error
  );
  ```
* **Mekanisme Penyimpanan Asinkron:** Pencatatan log telemetri dijalankan secara *fire-and-forget* menggunakan background daemon thread (`_async_log_telemetry` di `backend/agents/llm_helper.py:L26-L44`) sehingga proses pencatatan log tidak memperlambat respon jawaban ke pengguna.
