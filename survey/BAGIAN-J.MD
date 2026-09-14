# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN J
## MEKANISME FAIL-FAST & PENANGANAN KEGAGALAN SISTEM

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Exception Tracing, State Graph Routing Inspection (`graph.py`), & Graceful Degradation Handler Audit (`viz_gen.py`)

---

### 1. Kondisi Apa yang Menyebabkan Proses Berhenti / Berbelok?
Terdapat **5 kondisi kegagalan teridentifikasi** yang langsung menghentikan atau membelokkan alur eksekusi tanpa perulangan:

1. **Kondisi 1: Kueri Ambigu / Tanpa Metrik Bisnis (Pre-Flight Guard):**  
   Pengguna menanyakan hal yang terlalu umum (misal: *"berapa total 2025"* atau *"kalau 2024"*). Berhenti langsung di level FastAPI (0 Token LLM).
2. **Kondisi 2: Pelanggaran Kuota / Rate Limit:**  
   Pengguna mengirim lebih dari 30 request dalam 1 menit. Berhenti di FastAPI dengan HTTP status 429.
3. **Kondisi 3: Pelanggaran Keamanan SQL (Sanitizer Blocked):**  
   Kueri terdeteksi mengandung titik koma (`;`), komentar SQL (`--`), keyword DDL/DML (`DROP`, `DELETE`), atau tabel tidak dikenal.
4. **Kondisi 4: Kesalahan Sintaks Database (`DB_SYNTAX_ERROR`):**  
   Kueri SQL yang dirakit LLM gagal diparse atau dieksekusi oleh mesin DuckDB (misal: nama kolom keliru atau ketidakcocokan tipe data).
5. **Kondisi 5: Hasil Kueri Kosong (`DATA_EMPTY`):**  
   Kueri SQL valid dan berhasil dieksekusi, namun mengembalikan 0 baris data atau 1 baris bernilai `NULL` secara agregat.

---

### 2. Apa yang Terjadi Ketika SQL Invalid?
* **Mekanisme:** DuckDB melempar runtime exception (misal: `Parser Error` atau `Binder Error`).
* **Penanganan Teknis di [`backend/agents/execute.py:L73-L78`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/execute.py#L73-L78):**  
  Exception ditangkap oleh blok `try-except` Python lokal. Sistem menyetel:
  ```python
  "query_result": None,
  "sql_error": f"DB_SYNTAX_ERROR: {str(e)}"
  ```
* **Alur Selanjutnya:** Proses SQL dihentikan seketika. Tidak ada re-prompting ke LLM. State langsung dilempar ke `viz_gen_node` untuk menghasilkan saran perbaikan kata kunci bagi pengguna.

---

### 3. Apa yang Terjadi Ketika Tabel atau Kolom Tidak Ditemukan?
Sistem menangani kasus ini pada dua pos pemeriksaan yang berbeda:

* **A. Jika Nama Tabel Tidak Ditemukan (Terdeteksi di STEP 3 - Sanitizer):**  
  Sanitizer mencocokkan klausa `FROM` dan `JOIN` terhadap `information_schema.tables` DuckDB. Jika tabel tidak sah, disetel `sql_error = "SANITIZER BLOCKED: Tabel '...' tidak ditemukan"`. Graph melompati (*skips*) node eksekusi database dan langsung menuju `viz_gen`.
* **B. Jika Nama Kolom Tidak Ditemukan (Terdeteksi di STEP 4 - DuckDB Engine):**  
  Mesin DuckDB menolak eksekusi dan melempar *Binder Error: Referenced column not found*. Error ini ditangkap sebagai `DB_SYNTAX_ERROR` dan dialihkan ke `viz_gen` tanpa retry.

---

### 4. Apa yang Terjadi Jika Query Gagal Dijalankan?
* **Tindakan Sistem:**
  1. Eksekusi database dihentikan seketika.
  2. Flag status error (`sql_error`) dicatat ke memori state graf.
  3. Alur dialihkan ke agen visualisasi (`viz_gen`) untuk merumuskan respons penanganan kegagalan yang ramah (*Graceful Degradation*).
  4. Pengguna tidak pernah melihat layar error mentah (*raw crash traceback*), melainkan penjelasan bahasa manusia yang santun.

---

### 5 & 6. Apakah Sistem Melakukan Retry atau Self-Correction?
* **Status Audit:** **TIDAK ADA RETRY & TIDAK ADA SELF-CORRECTION (0 KALI).**
* **Penjelasan Arsitektur:** Sistem menerapkan paradigma **Fail-Fast (Single-Pass Execution)**. Mekanisme *Self-Healing Loop* yang sebelumnya mencoba memperbaiki kueri berulang kali hingga 3 kali **telah dihapuskan sepenuhnya**.
* **Rasionalisasi Desain:** Jika kueri gagal karena data memang tidak tersedia atau kata kunci salah, perulangan perbaikan kueri oleh LLM hanya membuang kuota token dan menambah latensi pengguna hingga 10–15 detik tanpa hasil yang pasti.

---

### 7. Apakah Proses Langsung Dihentikan?
* **Jawaban:** **YA, ALUR KOMPUTASI SQL LANGSUNG DIHENTIKAN.**
* **Penjelasan:** Komputasi analitik database langsung dihentikan dan diarahkan secara linier ke terminal output node (`viz_gen ➔ END`).

---

### 8. Bagaimana Respons / Error Dikembalikan ke Pengguna? (Graceful Degradation)
Sistem tidak mengembalikan pesan galat teknis yang membingungkan. Agen visualisasi di [`backend/agents/viz_gen.py:L68-L86`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/viz_gen.py#L68-L86) mengubah setiap kategori kegagalan menjadi pesan eksekutif:

1. **Respons untuk Sanitizer Blocked:**
   > 🛑 **Permintaan Ditolak oleh Sistem Keamanan Sanitizer PT TPS**  
   > *Sistem mengidentifikasi adanya klausa/simbol yang tidak diizinkan demi menjaga integritas database pelabuhan. Harap ajukan pertanyaan analisis data secara normal.*
2. **Respons untuk Data Kosong (Data Empty):**
   > ⚠️ *Maaf, data yang Anda cari tidak ditemukan atau bernilai kosong pada database PT TPS untuk kriteria atau periode waktu yang diminta.*  
   > **Saran:**  
   > - Pastikan penulisan nama operator/layanan sudah sesuai (misal: *CMA*, *SSL*, *MSK*, *Internasional*, atau *Domestik*).  
   > - Coba perjelas atau sesuaikan parameter rentang tahun/bulan yang ingin dianalisis.
3. **Respons untuk Error Sintaks (DB Syntax Error):**
   > ⚠️ *Maaf, sistem tidak dapat memproses kueri untuk pertanyaan tersebut secara langsung.*  
   > **Saran:** *Mohon ajukan kembali pertanyaan dengan kata kunci atau parameter yang lebih spesifik.*

---

### 9. File dan Fungsi Pengendali Error Handling

| File | Fungsi / Komponen | Peran dalam Mekanisme Fail-Fast |
| :--- | :--- | :--- |
| **`backend/main.py`** | `check_query_specificity()` | Memblokir pertanyaan ambigu di gerbang pertama (0 Token LLM). |
| **`backend/agents/sanitizer.py`** | `sanitizer_node()` | Memeriksa input/output query dan menyetel flag `SANITIZER BLOCKED`. |
| **`backend/agents/graph.py`** | `should_continue_sanitizer()` | Conditional router yang melompati node DuckDB jika Sanitizer terblokir. |
| **`backend/agents/execute.py`** | `execute_sql_node()` | Menangkap exception DuckDB (`DB_SYNTAX_ERROR`) dan mendeteksi ketiadaan baris data (`DATA_EMPTY`). |
| **`backend/agents/viz_gen.py`** | `viz_gen_node()` | Merumuskan pesan *Graceful Degradation* ramah pengguna berdasarkan flag `sql_error`. |

---

### 🗺️ Decision Flow: Mekanisme Fail-Fast & Graceful Degradation

```text
               [User Query]
                    │
                    ▼
     [Pre-Flight Specificity Check]
          ├── (Ambigu) ──────────────► [Tolak di Awal (0 Token) & Beri Contoh Pertanyaan]
          │
          └── (Spesifik)
                    │
                    ▼
            [Router Agent (STEP 1)]
                    │
                    ▼
          [SQL Generator (STEP 2)]
                    │
                    ▼
        [Security Sanitizer (STEP 3)]
          ├── (Melanggar / Tabel Tidak Sah) ──────────────┐
          │                                                │
          └── (Lolos Keamanan)                             │ (Bypass Execute)
                    │                                      │
                    ▼                                      │
        [DuckDB Execution (STEP 4)]                        │
          ├── (Syntax Error: DB_SYNTAX_ERROR) ─────┐       │
          │                                        │       │
          ├── (Data Kosong: DATA_EMPTY) ───────────┼───────┤
          │                                        │       │
          └── (Berhasil Ada Data)                  │       │
                    │                              │       │
                    ▼                              ▼       ▼
    [Viz & Narrative Analyst (STEP 5)] ◄───────────────────┘
          │
          ├───► Jika Sukses      : Narasi Eksekutif Lengkap + ECharts Config
          │
          └───► Jika Ada Error   : Respons "Graceful Degradation" Ramah User
```
