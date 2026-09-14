# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN H
## MEKANISME TEXT-TO-SQL & PENANGANAN KEGAGALAN (FAIL-FAST)

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Deep Code Inspection (`backend/agents/sql_gen.py`, `sanitizer.py`, `execute.py`, `viz_gen.py`, `graph.py`)

---

### 1. Lokasi Prompt SQL Generator
* **File:** [`backend/agents/sql_gen.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/sql_gen.py#L49-L66)
* **Variabel:** Konstanta `SQL_SYSTEM_PROMPT` yang dirangkai ke objek LangChain `ChatPromptTemplate.from_messages()`.

---

### 2. Komponen Input yang Diberikan ke SQL Generator
Node SQL Generator (`sql_gen_node`) menerima 5 elemen input utama ke dalam prompt-nya:
1. **`user_query` (Pertanyaan Pengguna):** String pertanyaan asli dari user.
2. **`relevant_tables` (Tabel Terpilih):** Output dari Router Agent (STEP 1) yang membatasi tabel analitik yang boleh digunakan.
3. **`schema` (Skema Tabel Dinamis):** Daftar nama kolom dan tipe data DuckDB hasil kueri `information_schema.columns` hanya untuk tabel terpilih (Schema Pruning).
4. **`history` (Konteks Percakapan Terdekat):** Ringkasan riwayat 3 obrolan terakhir yang diformat padat (hanya memuat teks pertanyaan user dan sintaks SQL yang pernah dieksekusi sebelumnya).
5. **`Glosarium & Semantik PT TPS`:** Aturan khusus istilah bisnis maritim pelabuhan.

---

### 3. Apakah User Question Diberikan?
* **Jawaban:** **YA, DIBERIKAN SECARA EKSPLISIT.**
* **Bukti Kode:**
  ```python
  # backend/agents/sql_gen.py:L95-L100
  user_message = f"Pertanyaan: {user_query}"
  prompt = ChatPromptTemplate.from_messages([
      ("system", SQL_SYSTEM_PROMPT),
      ("human", user_message)
  ])
  ```

---

### 4. Apakah Schema Diberikan?
* **Jawaban:** **YA, DINAMIS DAN TER-PRUNING.**
* **Bukti Kode:** Fungsi `get_duckdb_schema(relevant_tables)` mengekstrak kolom dan tipe data dari DuckDB via `information_schema.columns`, memfilternya hanya untuk tabel yang dipilih Router, dan menyuntikkannya ke placeholder `{schema}`:
  ```text
  Table fakta_throughput:
  - year (BIGINT)
  - month (VARCHAR)
  - actual (DOUBLE)
  - budget (DOUBLE)
  - kategori_layanan (VARCHAR)
  ```

---

### 5. Apakah Contoh SQL Diberikan (Few-Shot Prompting)?
* **Status:** `NOT FOUND (Zero-Shot Text-to-SQL Pattern)`
* **Penjelasan:** Di dalam `SQL_SYSTEM_PROMPT`, **tidak ada pasangan contoh pertanyaan-jawaban SQL (Few-Shot Pairs)**. Sistem bekerja secara *Zero-Shot* murni dengan mengandalkan deskripsi kolom, glosarium aturan semantik pelabuhan, dan kemampuan inferensi dasar model `gemini-3.6-flash`.

---

### 6. Apakah Ada System Prompt Khusus?
* **Jawaban:** **YA, SANGAT SPESIFIK PADA DOMAIN PELABUHAN PT TPS.**
* **Isi Aturan Khusus dalam `SQL_SYSTEM_PROMPT`:**
  - **Aturan Segmentasi:** *Domestik* ➔ `'DOMESTIC'`/`'DOM'`, *Internasional* ➔ `'INTERNATIONAL'`/`'INT'`.
  - **Aturan Throughput:** Pada tabel `fakta_throughput`, seluruh baris sudah merupakan data petikemas (TEUs); dilarang keras memfilter kata redundan `'peti kemas'` atau `'container'`.
  - **Aturan Pendapatan:** Pada `fakta_komersial_dashboard`, **wajib** menggabungkan `COALESCE(total_all_revenue, total_revenue) AS total_revenue` karena data pendapatan terpecah pada dua kolom tersebut.
  - **Aturan Pencarian String:** Wajib menggunakan operator *case-insensitive* `ILIKE`.
  - **Aturan Format:** Mengharuskan output hanya berupa string SQL murni tanpa backticks (` ```sql `) dan tanpa narasi penjelas.

---

### 7. Apakah Hasil SQL Divalidasi?
* **Status:** `IMPLEMENTED (STEP 3: Security Sanitizer Node)`
* **Penjelasan:** Validasi dilakukan secara otomatis oleh modul [`backend/agents/sanitizer.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/sanitizer.py) menggunakan *Deterministic Python Rule Engine (0 Token LLM)*:
  1. **Deteksi Multiple Statement:** Memeriksa karakter titik koma (`;`) untuk mencegah injeksi multi-kueri.
  2. **Deteksi Komentar SQL:** Memeriksa token komentar (`--`, `/*`, `*/`).
  3. **Pencegahan Perusakan Database (DDL/DML Blacklist):** Memblokir kata kunci `DROP`, `DELETE`, `UPDATE`, `INSERT`, `TRUNCATE`, `ALTER`, `ATTACH`, `COPY`.
  4. **Validasi Eksistensi Tabel:** Mengekstrak nama tabel menggunakan regex klausa `FROM` / `JOIN` dan memverifikasi bahwa tabel tersebut ada di DuckDB (termasuk mendukung alias CTE `WITH <alias> AS (...)`).

---

### 8, 9, 10, 11, & 12. Penanganan Kegagalan, Retry, dan Self-Healing Loop

#### A. Apakah Ada Retry atau Self-Healing / Correction Loop?
* **Status:** **TIDAK ADA (REMOVED / DEPRECATED).**
* **Jumlah Retry:** **0 Kali (Strictly Single-Pass).**
* **Latar Belakang Keputusan Arsitektur:** Pada versi pengembangan awal, sistem sempat memiliki perulangan *Self-Healing* (mencoba membetulkan SQL hingga 3 kali jika terjadi error sintaks). Namun, fitur ini **secara resmi telah dihapuskan** karena dinilai memboroskan token LLM secara signifikan dan memperlama latensi hingga 10–15 detik, terutama pada kasus data yang memang tidak ada di database.

#### B. Bagaimana Kegagalan Ditangani? (Fail-Fast Mechanism & Graceful Degradation)
Sistem saat ini menerapkan **Fail-Fast Error Handling** yang linier:

```text
[Sanitizer Terblokir]  ──┐
                         ├──► [LangGraph Langsung Loncat ke STEP 5 (viz_gen)]
[DB Syntax Error]      ──┤
                         │    └── Mengembalikan Pesan "Graceful Degradation"
[Data Kosong (0 Baris)]──┘        (Saran koreksi kata kunci/parameter ke User)
```

1. **Kasus 1: Terblokir Sanitizer Keamanan**
   - Node `sanitizer` menyetel `sql_error = "SANITIZER BLOCKED: ..."`.
   - Conditional edge pada `backend/agents/graph.py` mendeteksi flag ini dan **seketika membatalkan eksekusi DuckDB**, langsung mengalihkan state ke `viz_gen`.
   - Respon ke User: Notifikasi penolakan ramah bahwa permintaan mengandung klausa terlarang demi integritas data pelabuhan.
2. **Kasus 2: Error Sintaks Database (`DB_SYNTAX_ERROR`)**
   - Ditangkap pada blok exception di `backend/agents/execute.py`.
   - Disimpan pada state sebagai `sql_error = f"DB_SYNTAX_ERROR: {str(e)}"`.
   - LangGraph tetap melaju ke `viz_gen` tanpa looping coba-ulang.
   - Respon ke User: Saran untuk menyederhanakan struktur pertanyaan atau memeriksa parameter yang diminta.
3. **Kasus 3: Data Kosong / Tidak Ditemukan (`DATA_EMPTY`)**
   - Jika query menghasilkan 0 baris data atau 1 baris bernilai null semua (hasil agregat kosong), `execute.py` menyetel `sql_error = "DATA_EMPTY: ..."`.
   - LangGraph meneruskannya ke `viz_gen`.
   - Respon ke User: AI menjawab sopan bahwa data tidak ditemukan untuk periode/kriteria tersebut, disertai rekomendasi pengecekan nama operator (misal: *CMA*, *SSL*, *MSK*) atau rentang tahun.
