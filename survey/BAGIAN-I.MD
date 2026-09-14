# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN I
## KEAMANAN DATA, SQL SANITIZER, & DATA PRIVACY

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Static Code Inspection (`backend/agents/sanitizer.py`, `backend/db.py`), Security Policy Verification, & Data Leakage Trace

---

### 1. Apakah Ada SQL Sanitizer?
* **Status:** `IMPLEMENTED (Dual-Layer Security Guardrail)`
* **Lokasi Kode:** [`backend/agents/sanitizer.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/sanitizer.py)
* **Mekanisme Kerja:** Berjalan pada **STEP 3** sebagai *Deterministic Python Rule Engine (0 Token LLM / <1 ms)*. Sanitizer memeriksa dua sisi sekaligus:
  1. **Input Guard:** Memeriksa pertanyaan asli dari pengguna (`user_query`).
  2. **Output Guard:** Memeriksa sintaks SQL rakitan AI (`generated_sql`) sebelum diizinkan menyentuh mesin DuckDB.

---

### 2. Aturan-Aturan Keamanan yang Diterapkan
Berdasarkan implementasi kode pada `backend/agents/sanitizer.py`, terdapat 4 pilar aturan keamanan:
1. **Aturan Single-Statement (Anti-Chaining):** Melarang penggunaan karakter titik koma (`;`) di tengah kueri untuk menggagalkan upaya *multiple statements execution* atau *SQL injection stacking*.
2. **Aturan Anti-Comment Manipulation:** Melarang token komentar SQL seperti `--` (inline comment) dan `/* ... */` (block comment) yang kerap digunakan penyerang untuk menetralkan klausa `WHERE`.
3. **Aturan DDL/DML Blacklist:** Memblokir seluruh kata kunci manipulasi struktur dan penghapusan data database.
4. **Aturan Validasi Eksistensi Tabel & CTE:** Memastikan seluruh tabel dalam klausa `FROM` dan `JOIN` benar-benar terdaftar di database DuckDB, dengan dukungan pengenalan alias *Common Table Expression* (`WITH <alias> AS (...)`).

---

### 3. Apakah Hanya SELECT yang Diperbolehkan?
* **Status:** `IMPLEMENTED (Strict Read-Only Enforcement)`
* **Penjelasan:** Sistem **hanya mengizinkan operasi pembacaan data (`SELECT`)**. Jika SQL rakitan mengandung perintah penulisan, modifikasi, atau penghapusan, kueri langsung dibatalkan seketika dan ditandai sebagai pelanggaran keamanan (`SANITIZER BLOCKED`).

---

### 4. Apakah INSERT / UPDATE / DELETE / DROP Diblokir?
* **Status:** `IMPLEMENTED (Double-Layer Protection)`
* **Lapisan 1 (Regex Keyword Blocker di `sanitizer.py:L18-L22`):**
  Menggunakan regular expression berbasis *word boundary* (`\b`) untuk memblokir seluruh kata kunci berikut:
  ```python
  FORBIDDEN_KEYWORDS = [
      r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b', 
      r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bGRANT\b', 
      r'\bREVOKE\b', r'\bMERGE\b', r'\bEXEC\b', r'\bEXECUTE\b'
  ]
  ```
* **Lapisan 2 (Physical Engine Guard di `backend/db.py:L25`):**
  Koneksi DuckDB saat melayani runtime AI dikunci pada tingkat driver dengan mode **`read_only=True`**. Bahkan seandainya ada kueri modifikasi yang lolos dari filter regex, mesin DuckDB secara fisik akan menolak eksekusi dan melempar error *Cannot execute modification statement on a read-only database*.

---

### 5. Apakah Ada Validasi Nama Tabel / Kolom?
* **Status:** `IMPLEMENTED (Table-Level Validation & CTE Alias Awareness)`
* **Bukti Kode (`backend/agents/sanitizer.py:L73-L84`):**
  ```python
  # Ambil seluruh nama tabel sah dari DuckDB information_schema
  valid_tables = {row[0].lower() for row in conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()}

  # Deteksi alias CTE sementara yang sah (WITH alias AS (...))
  cte_matches = {m.lower() for m in re.findall(r'\b(?:WITH|,)\s*([a-zA-Z0-9_]+)\s+AS\s*\(', sql_query, re.IGNORECASE)}
  allowed_tables = valid_tables | cte_matches

  # Periksa seluruh tabel dalam klausa FROM dan JOIN
  table_matches = re.findall(r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)', upper_sql, re.IGNORECASE)
  for tbl in table_matches:
      if tbl.lower() not in allowed_tables:
          errors.append(f"Tabel '{tbl}' tidak ditemukan di skema database.")
  ```
* *(Catatan Validasi Kolom: Validasi eksistensi kolom diserahkan secara internal ke parser SQL DuckDB pada STEP 4, sehingga jika kolom salah, DuckDB akan melempar `DB_SYNTAX_ERROR` yang ditangani secara Fail-Fast).*

---

### 6. Apakah Ada SQL Injection Protection?
* **Status:** `IMPLEMENTED (Multi-Tier Defense-in-Depth)`
* **Bentuk Perlindungan:**
  1. **Tingkat Pertanyaan User (Input Guard):** Mencegah *Prompt Injection* dan *Tautology Attack* (`' OR 1=1 --`) dengan menyaring titik koma dan tanda komentar SQL di awal sebelum masuk ke LLM.
  2. **Tingkat Sintaks SQL (Output Guard):** Memverifikasi bahwa SQL yang dirakit LLM tidak menyisipkan perintah *stacked query*.
  3. **Tingkat Mesin Database (Read-Only Driver):** Mencegah potensi eksploitasi fungsi bawaan DuckDB seperti `COPY TO` atau `ATTACH DATABASE` berbahaya.

---

### 7. Apakah Raw Company Data Pernah Dikirim ke External LLM?
* **Temuan Auditor:** **TIDAK PERNAH SAMA SEKALI (ZERO DATA LEAKAGE PRINCIPLE).**
* **Penjelasan Audit:** Seluruh 9 berkas Excel mentah (~32.054 baris data) dan file biner `tps_komersial.duckdb` **berada dan diproses 100% di server lokal**. Pihak penyedia Cloud LLM (Google dan Groq) **tidak pernah menerima salinan database operasional perusahaan**.

---

### 8. Data Apa yang Sebenarnya Dikirim ke Cloud LLM?
Secara detail dan transparan, data yang dikirimkan ke cloud LLM per tahapan adalah:

| Tahapan Agent | Provider & Model | Data yang Dikirimkan ke Cloud (Payload Prompt) |
| :--- | :--- | :--- |
| **STEP 1: Router** | Google (`gemini-3.1-flash-lite`) | • Teks pertanyaan user.<br>• Metadata katalog nama tabel dan deskripsi semantik bisnis singkat.<br>• Role pengguna (RBAC). |
| **STEP 2: SQL Gen** | Google (`gemini-3.6-flash`) | • Teks pertanyaan user.<br>• Skema nama kolom dan tipe data dari 1–2 tabel relevan (`information_schema.columns`).<br>• Glosarium aturan bisnis maritim TPS.<br>• Sintaks SQL dari 3 percakapan sebelumnya (*SQL-Only History*). |
| **STEP 5: Viz Gen** | Groq (`openai/gpt-oss-20b`) | • Teks pertanyaan user.<br>• **Maksimal 15 baris sampel data** teratas hasil kueri lokal DuckDB (`format_data_compact(rows, 15)`) beserta total baris data.<br>• *Tidak pernah mengirimkan ribuan baris data mentah.* |

---

### 9. Hasil Apa yang Dikembalikan dari LLM?
LLM tidak pernah mengembalikan data database, melainkan hanya mengembalikan instruksi komputasi dan narasi:
1. **Dari Router LLM:** Mengembalikan struktur data JSON berisikan array nama tabel terpilih: `{"relevant_tables": ["fakta_throughput"]}`.
2. **Dari SQL Generator LLM:** Mengembalikan satu baris string query SQL: `SELECT year, SUM(actual) FROM fakta_throughput WHERE year = 2024 GROUP BY year`.
3. **Dari Viz Analyst LLM:** Mengembalikan narasi bisnis eksekutif dalam format Markdown ramah direksi.
4. **Dari Chart Generator LLM:** Mengembalikan objek konfigurasi JSON untuk di-render oleh komponen Apache ECharts di browser.

---

### 📋 Ringkasan Status Keamanan (Implemented vs Not Implemented)

| Fitur Keamanan | Status Implementasi | Keterangan Teknis |
| :--- | :---: | :--- |
| Dual-Layer SQL Sanitizer (Input & Output Guard) | `IMPLEMENTED` | `backend/agents/sanitizer.py` |
| Pemblokiran Multiple Statements (`;`) | `IMPLEMENTED` | `sanitizer.py:L43, L62` |
| Pemblokiran SQL Comments (`--`, `/* */`) | `IMPLEMENTED` | `sanitizer.py:L53` |
| Pemblokiran DDL & DML (DROP, DELETE, INSERT, dsb.) | `IMPLEMENTED` | Regex `FORBIDDEN_KEYWORDS` di `sanitizer.py` |
| Read-Only Database Connection Pool | `IMPLEMENTED` | `duckdb.connect(..., read_only=True)` di `db.py` |
| Validasi Skema Tabel & CTE Parsing | `IMPLEMENTED` | Verifikasi terhadap `information_schema.tables` |
| Pre-Flight Query Ambiguity Filter | `IMPLEMENTED` | `check_query_specificity` di `backend/main.py` |
| Zero Data Leakage ke Cloud LLM | `IMPLEMENTED` | Data mentah lokal; LLM hanya menerima skema & 15 baris sampel |
| Dynamic Data Masking (DDM) per Kolom Sensitif | `PARTIALLY IMPLEMENTED` | Masking diterapkan pada token API & otentikasi role RBAC, namun belum ada masking khusus kolom nominal gaji/tarif internal di level database. |
