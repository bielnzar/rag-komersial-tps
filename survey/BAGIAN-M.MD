# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN M
## EVALUASI, PENGUJIAN (TESTING), & OBSERVABILITAS SISTEM

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Test Suite Execution (`pytest`), Telemetry Database Inspection (`telemetry.duckdb`), & Benchmark Script Walkthrough

---

### 📊 Matriks Status Evaluasi dan Pengujian (Available vs Not Available)

| No | Komponen Pengujian / Evaluasi | Status Implementasi | Bukti File / Lokasi Kode | Keterangan Teknis |
| :-: | :--- | :---: | :--- | :--- |
| 1 | **Unit Test** | `IMPLEMENTED` | `backend/tests/test_*.py` | 9 Unit test otomatis menggunakan Pytest (`9 passed in 0.69s`). |
| 2 | **Integration Test** | `PARTIALLY IMPLEMENTED` | `backend/tes_jawaban.py`<br>`backend/tes_kompleks.py` | Pengujian integrasi pipeline end-to-end melalui skrip simulasi kueri dan HTTP requests. |
| 3 | **Test Query** | `IMPLEMENTED` | `backend/tes_kompleks.py`<br>`milestone/WALKTHROUGH.md` | Himpunan kueri uji bisnis (Throughput, LOP Revenue, UC Cargo, Restitusi, Market Share). |
| 4 | **Test Dataset** | `IMPLEMENTED` | `data/processed/tps_komersial.duckdb` | Database lokal berisi 9 tabel fakta (~32.054 baris data riil pelabuhan). |
| 5 | **Logging** | `IMPLEMENTED` | `logs/etl_system.log`<br>`backend/agents/pipeline_logger.py` | Dual logging: Rotating file log untuk ETL dan konsol terstruktur untuk state LangGraph. |
| 6 | **Latency Measurement** | `IMPLEMENTED` | `backend/agents/llm_helper.py:L133` | Pengukuran durasi milidetik (`latency_ms`) per-panggilan LLM dan disimpan ke database. |
| 7 | **Token Counting** | `IMPLEMENTED` | `backend/agents/llm_helper.py:L130`<br>`backend/db.py:L46` | Perhitungan token input/output yang disimpan ke DuckDB `log_audit_token`. |
| 8 | **Accuracy Measurement** | `PARTIALLY IMPLEMENTED` | `backend/tes_kompleks.py` | Diuji secara *Execution Accuracy* terhadap 5 kasus analitik kompleks; belum memakai automated framework (RAGAS). |
| 9 | **SQL Comparison** | `PARTIALLY IMPLEMENTED` | `backend/tes_kompleks.py` | Pencocokan manual hasil query terhadap SQL Ground Truth; belum ada *AST SQL Diff Parser*. |
| 10 | **User Testing (UAT)** | `PARTIALLY IMPLEMENTED` | Lingkungan Lokal Pengembang | Pengujian kualitatif fungsi oleh peneliti/pengembang; belum ada pengujian formal kuisioner SUS/CSAT ke staf eksekutif. |
| 11 | **Feedback Mechanism** | `PARTIALLY IMPLEMENTED` | `data/processed/telemetry.duckdb` | *Machine telemetry feedback* sudah aktif; *User feedback UI* (thumbs up/down) belum ada. |

---

### 1. Unit Testing Otomatis
* **Framework:** `pytest` (v9.1.1)
* **Lokasi Berkas:** [`backend/tests/`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/tests)
* **Cakupan Pengujian:**
  1. `test_etl.py` (3 test cases):
     - `test_normalisasi_kategori`: Memvalidasi translasi `'DOMESTIK'` ➔ `'DOMESTIC'` dan `'INTERNASIONAL'` ➔ `'INTERNATIONAL'`.
     - `test_paksa_angka`: Menguji pembersihan tanda koma ribuan dan konversi teks menjadi float.
     - `test_hapus_kolom_hantu`: Memverifikasi penghapusan kolom `Unnamed` dan baris NaN.
  2. `test_router.py` (1 test case):
     - `test_get_table_catalog`: Memverifikasi ketersediaan dan kekayaan deskripsi semantik 9 tabel DuckDB.
  3. `test_sanitizer.py` (5 test cases):
     - `test_sanitizer_valid_select`: Memastikan kueri SELECT normal diizinkan.
     - `test_sanitizer_multiple_statements`: Memastikan titik koma (`;`) diblokir.
     - `test_sanitizer_forbidden_keywords`: Memastikan keyword DROP/DELETE/UPDATE diblokir.
     - `test_sanitizer_invalid_table`: Memastikan tabel di luar DuckDB ditolak.
     - `test_sanitizer_prompt_injection_input`: Memastikan injeksi komentar (`--`, `/*`) pada pertanyaan user dicegat di awal.
* **Hasil Eksekusi:** `9 passed in 0.69s` (100% Lulus Sempurna).

---

### 2. Integration Testing
* **Metode:** Skrip Python mandiri yang mengeksekusi request HTTP REST API lengkap menggunakan library `requests`:
  - Mengirim payload ke `http://127.0.0.1:8000/api/v1/chat` dengan Bearer JWT token.
  - Memverifikasi status HTTP (200 OK), pembentukan SQL, dan narasi akhir.
  - Menguji kasus negatif: Kueri kosong, kueri ambigu, kueri data kosong tahun 1980, dan injeksi DROP TABLE.

---

### 3. Test Query & Benchmark Ground Truth
Sistem telah diuji menggunakan himpunan kueri benchmark bisnis pada [`backend/tes_kompleks.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/tes_kompleks.py):
1. *Ranking Pasar:* "Top 3 LOP Market Share tahun 2023" (Target: SSL, MSK, EMC).
2. *Realisasi vs Anggaran:* "Throughput Actual vs Budget International tahun 2023" (Target: 1.375.929 TEUs vs 1.488.384 TEUs).
3. *Operasional Tambatan:* "Top 5 Operator rata-rata BMPH layanan kapal".
4. *Biaya Unit (UC):* "Realisasi Unit Cost status FULL tahun 2024".
5. *Alih Muat (Transhipment):* "Total yard revenue dan boks 20ft kegiatan Discharge tahun 2024".

---

### 4. Test Dataset
* **Media:** Berkas biner database lokal `data/processed/tps_komersial.duckdb`.
* **Karakteristik:** Dataset uji bukan data dummy tiruan atau benchmark publik (seperti Spider atau BIRD-SQL), melainkan data riil operasional 9 tabel fakta PT TPS (~32.054 baris data relasional) yang merefleksikan kondisi lapangan sesungguhnya.

---

### 5. Logging & Observabilitas
* **Sistem ETL Logging:** Menggunakan `RotatingFileHandler` di [`backend/etl/utils.py:L25-L33`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/etl/utils.py#L25-L33) yang menulis ke `logs/etl_system.log` (maksimal 5 MB per berkas, rotasi hingga 5 berkas cadangan / total 25 MB).
* **Pipeline Logger:** Menggunakan modul [`backend/agents/pipeline_logger.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/pipeline_logger.py) yang mencetak transisi state LangGraph dengan emoji indikator visual (`STEP 1: ROUTER_START`, `STEP 2: SQL_GEN_DONE`, `STEP 4: DUCKDB_SUCCESS`) ke terminal stdout.

---

### 6 & 7. Pengukuran Latensi & Perhitungan Token (Telemetry Engine)
* **Mekanisme Pengukuran di [`backend/agents/llm_helper.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/llm_helper.py#L79-L138):**
  - **Latensi:** Dihitung tepat sebelum dan sesudah pemanggilan LLM:  
    `latency_ms = (time.time() - start_time) * 1000`.
  - **Token Input:** Dihitung dari estimasi panjang teks karakter prompt (`len(str) // 4`) dan disinkronkan dengan metadata resmi provider (`response_metadata["token_usage"]`).
  - **Token Output:** Diambil dari jumlah token jawaban yang dihasilkan LLM.
* **Penyimpanan Telemetri:** Disimpan secara asinkron (*fire-and-forget daemon thread*) ke dalam file database terpisah **`data/processed/telemetry.duckdb`** pada tabel **`log_audit_token`**.
* **Visualisasi Telemetri:** Data telemetri kuota dan frekuensi penggunaan kunci API ditampilkan secara live di panel **Admin Dashboard** (`/administrator`).

---

### 8 & 9. Evaluasi Akurasi & Perbandingan SQL (Ground Truth)
* **Yang Sudah Ada:** Pengujian dilakukan dengan membandingkan **Hasil Eksekusi (Execution Accuracy)** antara kueri AI dengan kueri SQL manual yang disusun oleh analis data internal. Jika hasil angka nominal atau volume TEUs cocok 100%, kueri dinyatakan lulus.
* **Yang Belum Ada:** Sistem belum memiliki *Automated Semantic Evaluator* berbasis AST (*Abstract Syntax Tree Parser*) yang membandingkan struktur klausa SQL secara otomatis tanpa mengeksekusi database.

---

### 10 & 11. Pengujian Pengguna (User Testing) & Mekanisme Feedback
* **User Testing (UAT):** Saat ini berada pada tahap **Pengujian Internal Pengembang (Alpha Testing)**. Belum dilakukan pengujian penerimaan pengguna formal (*User Acceptance Testing*) yang melibatkan staf operasional/direksi menggunakan kuesioner baku seperti *System Usability Scale (SUS)* atau *Technology Acceptance Model (TAM)*.
* **Feedback Mechanism:**
  - **System Feedback:** Telah terimplementasi penuh melalui audit telemetri kegagalan dan penanganan *Graceful Degradation*.
  - **User Feedback di UI:** Belum menyediakan tombol interaktif penilaian (*Thumbs Up / Thumbs Down*) atau formulir koreksi jawaban di antarmuka obrolan `ChatMessage.vue`.
