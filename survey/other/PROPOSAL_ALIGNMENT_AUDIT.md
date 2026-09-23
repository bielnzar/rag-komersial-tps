# ⚖️ PROPOSAL ALIGNMENT AUDIT: ANALISIS KESELARASAN PROPOSAL VS PROYEK AKTUAL
## Evaluasi Komparatif Rancangan Akademis (BAB 3) terhadap Implementasi Nyata Sistem

**Dasar Dokumen Komparasi:**
1. **Rancangan Teoretis / Proposal:** [`PROPOSAL_RESEARCH_ALIGNMENT.md`](../PROPOSAL_RESEARCH_ALIGNMENT.md)
2. **Kondisi Faktual Sistem / Audit Nyata:** [`TECHNICAL_MASTER_BRIEF.md`](../TECHNICAL_MASTER_BRIEF.md)

**Prinsip Penilaian:**  
Objektif, berbasis bukti kode (*Evidence-Based*), tanpa pemaksaan teori ke kode atau sebaliknya, dan membedakan secara tegas antara sistem yang sudah terpasang (*Implemented*) dengan rencana masa depan (*Future Work*).

---

# 1. OVERALL ALIGNMENT SUMMARY

Berdasarkan audit komparatif terhadap 26 aspek penelitian (A s/d Z):

| Kategori Penilaian | Jumlah Aspek | Persentase | Rincian Aspek |
| :--- | :---: | :---: | :--- |
| **SESUAI (Fully Aligned)** | **16 Aspek** | **61.5%** | Studi Kasus (A), Divisi Komersial (B), Microsoft Excel (C), DuckDB (F), Router (H), Schema Pruning (J), SQL Generator (K), Sanitizer (L), Execute (M), Viz Analyst (N), LangGraph (O), Model Routing (P), Fail-Fast (Q), Visualization (R), Narrative (S), Syntactic Validity (W). |
| **SEBAGIAN SESUAI (Partially Aligned)** | **6 Aspek** | **23.1%** | Medallion Architecture (E), Multi-Agent System (G), Schema Linking (I), Feedback (T), Execution Accuracy (U), Token Reduction Ratio (Y). |
| **BELUM ADA (Not Available / Planned)** | **3 Aspek** | **11.5%** | Exact Match (V), User Acceptance Testing (Z), Feedback Rating UI Pengguna (T.2). |
| **BERBEDA (Divergent / Contextual Difference)** | **1 Aspek** | **3.8%** | Microsoft Power BI (D) — Berada sebagai *Problem Background / External Baseline*, bukan komponen kode perangkat lunak di repositori. |

---

# 2. DETAILED ALIGNMENT AUDIT (KOMPONEN A – Z)

### A. Studi Kasus (PT XYZ / PT TPS)
* **Status:** `SESUAI`
* **Evaluasi:** Repositori menggunakan data operasional riil dari **PT Terminal Petikemas Surabaya (PT TPS)** yang dianonimkan menjadi **PT XYZ** dalam penulisan judul dan naskah publikasi skripsi demi kerahasiaan korporasi.

### B. Divisi Komersial
* **Status:** `SESUAI`
* **Evaluasi:** Seluruh 9 berkas data mencakup metrik inti Divisi Komersial: *Commercial Revenue Dashboard, Container Throughput, Market Share Pelayaran (LOP), Vessel Service (BMPH), Realisasi Unit Cost (UC), Restitusi & Diskon, Alih Muat (Transhipment),* dan *Overview Box*.

### C. Sumber Data Microsoft Excel
* **Status:** `SESUAI`
* **Evaluasi:** Sistem membaca 9 berkas spreadsheet `.xlsx` dari direktori `data/raw/` menggunakan engine `openpyxl` dan library `pandas`.

### D. Sistem Eksisting Microsoft Power BI
* **Status:** `BERBEDA (KONTEKSTUAL MASALAH)`
* **Evaluasi:** Power BI merupakan sistem eksisting di perusahaan yang melatarbelakangi masalah penelitian (kebutuhan kueri ad-hoc berbasis bahasa alami). Di repositori tidak ada berkas `.pbix` atau integrasi API Power BI, karena asisten AI ini dibangun sebagai sistem mandiri pengganti/pendamping dashboard statis tersebut.

### E. Medallion Architecture (Bronze ➔ Silver ➔ Gold)
* **Status:** `SEBAGIAN SESUAI`
* **Evaluasi:**
  - *Sisi Sesuai:* Alur logis pembersihan 3 tahap diterapkan nyata di `backend/etl/main_etl.py` (Bronze = raw data, Silver = clean data & typed, Gold = unpivot, snake_case & DuckDB physical tables).
  - *Sisi Deviasi:* Dijalankan menggunakan pola **Lightweight In-Memory Batch Pandas**, bukan teknologi streaming data lake enterprise seperti Databricks Delta Lake atau Apache Spark.

### F. Analytic Database (DuckDB)
* **Status:** `SESUAI`
* **Evaluasi:** DuckDB v1.1+ terpasang nyata sebagai *in-process columnar database engine* lokal di `data/processed/tps_komersial.duckdb`, menyimpan 9 tabel fisik secara permanen (~32.054 baris data relasional) dengan akses thread-safe connection pool (`read_only=True`).

### G. Multi-Agent System
* **Status:** `SEBAGIAN SESUAI`
* **Evaluasi:**
  - *Sisi Sesuai:* Sistem menggunakan pembagian tugas multi-komponen yang diorkestrasikan oleh LangGraph.
  - *Sisi Perlu Diperjelas:* Di level kode, hanya 3 komponen yang merupakan **Cognitive AI Agent berbasis LLM** (`router`, `sql_gen`, `viz_gen`), sedangkan komponen lain (`pre_flight_guard`, `sanitizer`, `execute_sql`) adalah **Deterministic Tools / Rule Engine**. Di skripsi tidak boleh mengklaim seluruh node sebagai AI agent.

### H. Router Agent
* **Status:** `SESUAI`
* **Evaluasi:** Terimplementasi di `backend/agents/router.py` menggunakan LLM `gemini-3.1-flash-lite` untuk memetakan teks kueri pengguna ke katalog 9 tabel dan memfilter otorisasi RBAC.

### I. Schema Linking
* **Status:** `SEBAGIAN SESUAI`
* **Evaluasi:**
  - *Sisi Sesuai:* Pemetaan skema kolom dilakukan secara dinamis melalui kueri `PRAGMA table_info` di fungsi `get_duckdb_schema()` pada `backend/agents/sql_gen.py`.
  - *Sisi Deviasi:* Tidak menggunakan *Semantic Vector Schema Linking* (misal embeddings kueri vs kolom), melainkan ekstraksi skema tabel terpilih berbasis SQL Information Schema lookup.

### J. Schema Pruning
* **Status:** `SESUAI`
* **Evaluasi:** Router Agent secara nyata memangkas tabel yang tidak relevan (hanya meloloskan 1–2 tabel dari total 9 tabel), sehingga memangkas ~80% definisi skema yang tidak diperlukan dari prompt generator.

### K. SQL Generator Agent
* **Status:** `SESUAI`
* **Evaluasi:** Terimplementasi di `backend/agents/sql_gen.py` menggunakan LLM `gemini-3.6-flash`. Menghasilkan DuckDB SQL murni berbasis glosarium maritim TPS (aturan throughput, COALESCE revenue, ILIKE).

### L. Security Sanitizer
* **Status:** `SESUAI`
* **Evaluasi:** Terimplementasi di `backend/agents/sanitizer.py` sebagai *Deterministic Rule Engine* (0 Token LLM). Memblokir titik koma (`;`), komentar SQL (`--`), kata kunci DDL/DML (DROP, DELETE, dsb.), dan memvalidasi eksistensi tabel/CTE.

### M. Execute Node
* **Status:** `SESUAI`
* **Evaluasi:** Terimplementasi di `backend/agents/execute.py`. Mengeksekusi kueri read-only ke DuckDB, mensterilkan anomali angka float `NaN/Infinity` ke `null`, dan menangkap kegagalan sintaks secara terisolasi.

### N. Viz Analyst Agent
* **Status:** `SESUAI`
* **Evaluasi:** Terimplementasi di `backend/agents/viz_gen.py` menggunakan LLM `openai/gpt-oss-20b` via Groq Cloud untuk merumuskan narasi bisnis eksekutif berstandar formal dan menangani pesan *Graceful Degradation*.

### O. LangGraph State Machine
* **Status:** `SESUAI`
* **Evaluasi:** Terimplementasi di `backend/agents/graph.py` menggunakan objek `StateGraph(AgentState)` dengan 5 node terdaftar dan 1 conditional edge bypass sanitizer.

### P. Model Routing (Asymmetric LLM Tiering)
* **Status:** `SESUAI`
* **Evaluasi:** Terimplementasi nyata membagi model secara heterogen: `gemini-3.1-flash-lite` (Router), `gemini-3.6-flash` (SQL Gen), dan `openai/gpt-oss-20b` (Viz Gen). Konfigurasi dapat diubah dinamis melalui Admin Dashboard.

### Q. Fail-Fast Mechanism
* **Status:** `SESUAI`
* **Evaluasi:** Sistem menghentikan alur seketika saat kueri ambigu (Pre-flight), terblokir Sanitizer, error database, atau data kosong, langsung menuju `viz_gen` untuk menyajikan respons *Graceful Degradation* (0 Retry, tanpa perulangan self-healing).

### R. Visualization (Apache ECharts)
* **Status:** `SESUAI`
* **Evaluasi:** Terimplementasi di `backend/agents/chart_gen.py` (sintesis JSON config ECharts) dan frontend `EChartsViewer.vue` (merender Bar, Line, atau Pie chart interaktif).

### S. Executive Narrative
* **Status:** `SESUAI`
* **Evaluasi:** Terimplementasi dengan aturan prompt ketat: pemisah ribuan titik pada mata uang Rupiah (*Rp*), penomoran standar (`1. `, `2. `), dan satuan volume *TEUs/Boxes*.

### T. Feedback Mechanism
* **Status:** `SEBAGIAN SESUAI`
* **Evaluasi:**
  - *Machine Feedback (Audit Telemetri):* `SESUAI`. Tercatat otomatis ke `data/processed/telemetry.duckdb` pada tabel `log_audit_token` (mencatat latensi ms, token masuk/keluar, status kueri).
  - *User Feedback UI (Rating):* `BELUM ADA`. Belum ada tombol jempol *thumbs up/down* atau input formulir koreksi di UI `ChatMessage.vue`.

### U. Execution Accuracy (EA)
* **Status:** `SEBAGIAN SESUAI`
* **Evaluasi:** Pengujian akurasi hasil eksekusi telah diuji secara manual terhadap 5 kasus analitik kompleks di `backend/tes_kompleks.py` dengan hasil identik 100%, namun belum diformalkan ke dalam pengujian batch otomatis terhadap puluhan kueri uji.

### V. Exact Match (EM)
* **Status:** `BELUM ADA`
* **Evaluasi:** Belum ada skrip otomatis untuk membandingkan kesamaan string SQL sintaksis (*AST Match*) terhadap Gold SQL.

### W. Syntactic Validity (SV)
* **Status:** `SESUAI`
* **Evaluasi:** Validitas sintaks divalidasi oleh AST regex Sanitizer dan 9 unit test Pytest (`test_sanitizer.py`), di mana kueri yang lolos terbukti dieksekusi oleh parser DuckDB tanpa runtime error sintaks.

### X. End-to-End Latency ($L_{\text{E2E}}$)
* **Status:** `SESUAI`
* **Evaluasi:** Diukur secara presisi di `backend/agents/llm_helper.py` menggunakan selisih waktu (`time.time()`) dan disimpan permanen pada tabel `log_audit_token` di `telemetry.duckdb` (rata-rata 500–1200 ms).

### Y. Token Reduction Ratio (TRR)
* **Status:** `SEBAGIAN SESUAI`
* **Evaluasi:** Secara konsep dan kode, sistem telah menerapkan pemangkasan skema (hanya menyuntikkan 1–2 tabel dari 9 tabel), namun formula formal $TRR = \frac{T_{\text{full}} - T_{\text{pruned}}}{T_{\text{full}}} \times 100\%$ belum dihitung secara kuantitatif dalam bentuk tabel benchmark eksperimen di kode.

### Z. User Acceptance Testing (UAT)
* **Status:** `BELUM ADA`
* **Evaluasi:** Belum dilaksanakan pengujian formal ke staf pengguna di Divisi Komersial PT TPS menggunakan kuesioner baku (SUS/TAM). Sistem saat ini baru melalui tahap Alpha Testing oleh pengembang internal.

---

# 3. BAB 3 WRITING MAP (PANDUAN PENULISAN METODOLOGI SKRIPSI)

Berikut adalah panduan pemetaan penulisan sub-bab metodologi BAB 3:

| Komponen Metodologi | Fakta Nyata yang BOLEH Ditulis di BAB 3 | Sumber Berkas Implementasi | Bagian Proposal yang Didukung | Bagian yang BELUM BISA Ditulis / Batasan | Hal yang Perlu Dikonfirmasi Mahasiswa |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sumber & Karakteristik Data** | Menggunakan 9 file Excel operasional PT TPS (~32.054 baris), Denormalized Star Schema, relasi utama via kolom `lop` dan dimensi tahun/bulan. | `data/raw/*.xlsx`<br>`survey/BAGIAN-B.MD` | Sub-bab Desain Data & Studi Kasus | Jangan mengklaim jumlah file Excel dikunci permanen (karena dapat ditambah). | Validasi izin pengutipan nama PT TPS vs anonimasi menjadi "PT XYZ". |
| **Prapemrosesan Medallion** | Transformasi 3 tahap: Bronze (ekstraksi mentah), Silver (pembersihan kolom hantu & casting angka), Gold (unpivot pivot table & persistensi ke DuckDB). | `backend/etl/main_etl.py`<br>`backend/etl/transformers.py` | Sub-bab Rekayasa Data & Pipeline ETL | Jangan mengklaim menggunakan Apache Spark streaming atau Delta Lake. | Konfirmasi frekuensi pembaruan data (apakah harian, bulanan, atau batch per semester). |
| **Database Analitik** | DuckDB lokal in-process, format penyimpanan kolumnar fisik, akses read-only thread-safe connection pool. | `backend/db.py`<br>`data/processed/*.duckdb` | Sub-bab Penyimpanan Data Analitik | Jangan mengklaim menggunakan database server eksternal cloud (PostgreSQL/MySQL). | - |
| **Orkestrasi Multi-Agent** | LangGraph StateGraph linier 5 node (`router`, `sql_gen`, `sanitizer`, `execute_sql`, `viz_gen`), 11 keys memori `AgentState`, bypass conditional edge. | `backend/agents/graph.py`<br>`backend/agents/state.py` | Sub-bab Perancangan Arsitektur Sistem | Jangan menyebut `sanitizer` dan `execute_sql` sebagai AI Agent (mereka adalah deterministic tools). | - |
| **Text-to-SQL & Asymmetric LLM** | Pembagian model heterogen: Gemini 3.1 Flash-Lite (Router), Gemini 3.6 Flash (SQL Gen), Groq GPT-OSS-20B (Viz Gen). | `backend/agents/llm_helper.py`<br>`credentials/api_keys.json` | Sub-bab Model Kognitif & Reasoning | Jangan mengklaim menggunakan model lokal Ollama dalam operasional default. | Pastikan model yang tercatat di skripsi adalah model yang aktif saat pengujian evaluasi. |
| **Keamanan & Guardrails** | Dual-layer sanitizer (input guard + output guard), pemblokiran titik koma, komentar SQL, keyword DDL/DML, mode read-only DuckDB, Zero Data Leakage. | `backend/agents/sanitizer.py`<br>`backend/main.py:L150-L223` | Sub-bab Keamanan Sistem & Sanitasi Data | - | - |
| **Fail-Fast & Penanganan Error** | Pemutusan alur linier saat error sintaks atau data kosong, tanpa retry loop (0 retry), dialihkan ke viz_gen untuk respons *Graceful Degradation*. | `backend/agents/execute.py`<br>`backend/agents/viz_gen.py` | Sub-bab Error Handling & Keandalan Sistem | **DILARANG MENGKLAIM MASIH ADA SELF-HEALING LOOP.** | Ubah teks badge hardcoded di UI "Self-Healing Active" agar selaras dengan narasi skripsi. |
| **Evaluasi Teknis (5 Metrik)** | Formulasi kuantitatif EA, EM, SV, Latensi E2E, dan TRR. Hasil latensi rata-rata 500–1200 ms dari `telemetry.duckdb`. | `backend/agents/llm_helper.py`<br>`backend/tes_kompleks.py` | Sub-bab Rencana Evaluasi & Pengujian | Angka persentase final EA, EM, SV, dan TRR belum bisa diklaim sebelum seluruh benchmark dijalankan. | Mahasiswa harus menjalankan skrip pengujian benchmark komprehensif untuk mendapatkan tabel angka pengujian. |
| **UAT (User Acceptance)** | Metodologi rencana pengujian pengguna pada Divisi Komersial PT XYZ menggunakan kuesioner kualitatif/kuantitatif (misal TAM/SUS). | Rencana Konseptual Proposal | Sub-bab Pengujian Penerimaan Pengguna | Skor nilai kepuasan UAT belum bisa ditulis karena pengujian lapangan belum terlaksana. | Tentukan jumlah responden staf komersial PT TPS yang akan diwawancarai/diberi kuesioner. |

---

# 4. PROBLEMATIC CLAIMS (KLAIM PROPOSAL YANG BERMASALAH)

Berdasarkan audit sistem aktual, berikut adalah klaim yang berpotensi menjadi temuan kesalahan fatal jika ditulis apa adanya dalam skripsi:

1. ⚠️ **Klaim "Sistem Memiliki Kemampuan Self-Healing Berulang":**  
   *Permasalahan:* Di proposal mungkin direncanakan adanya koreksi kueri mandiri (self-correction retry loop).  
   *Fakta Aktual:* Mekanisme retry loop telah **resmi dibongkar dan dihapus** di kode karena memboroskan token dan menambah latensi. Sistem kini murni mengadopsi **Single-Pass Fail-Fast**.  
   *Tindakan Koreksi:* Tuliskan secara jujur di BAB 3 bahwa sistem memilih pendekatan *Fail-Fast Single-Pass* demi efisiensi biaya komputasi dan determinisme waktu respon.

2. ⚠️ **Klaim "Semua Node di LangGraph adalah AI Agent":**  
   *Permasalahan:* Menyebut sistem memiliki 5 atau 6 AI Agent.  
   *Fakta Aktual:* Hanya ada **3 AI Agent berbasis LLM** (`router`, `sql_gen`, `viz_gen`), sedangkan `sanitizer` dan `execute_sql` adalah fungsi terprogram deterministik non-AI.  
   *Tindakan Koreksi:* Gunakan terminologi *Hibrida Multi-Agent dan Deterministic Tool Nodes*.

3. ⚠️ **Klaim "Sistem Menerapkan Few-Shot Prompting":**  
   *Permasalahan:* Berasumsi sistem menggunakan banyak contoh pasangan pertanyaan-kueri SQL di prompt.  
   *Fakta Aktual:* Node SQL Generator murni bekerja secara **Zero-Shot Prompting** berbasis skema kolom dan glosarium domain pelabuhan.

4. ⚠️ **Klaim "Sistem Telah Teruji Secara UAT oleh Pengguna Komersial":**  
   *Permasalahan:* Mengklaim tingkat kepuasan pengguna komersial sudah terbukti tinggi di bab metodologi.  
   *Fakta Aktual:* Pengujian formal ke staf pengguna di lapangan **belum dilaksanakan** (baru sebatas developer testing).

5. ⚠️ **Klaim "Sistem Menggunakan Delta Lake / Streaming CDC":**  
   *Permasalahan:* Menggunakan istilah industri besar tanpa melihat implementasi repositori.  
   *Fakta Aktual:* Medallion Architecture diimplementasikan secara batch lokal menggunakan Pandas dan DuckDB fisik.

---

# 5. REQUIRED ACTIONS (TINDAKAN YANG HARUS DILAKUKAN)

### A. MUST FIX BEFORE WRITING BAB 3 (Wajib Dibereskan Segera)
1. **Perbaiki Badge Frontend di `ChatMessage.vue`:**  
   Ganti teks label statis `<span ...>Self-Healing Active</span>` pada baris 32 menjadi `<span ...>Fail-Fast Active</span>` atau hapus badge tersebut agar penguji skripsi tidak menemukan kontradiksi antara tampilan UI dengan laporan tulisan.
2. **Definisikan Rumusan Ground Truth Resmi:**  
   Susun daftar tabel minimal 20–30 pertanyaan acuan bisnis, Gold SQL, dan Gold Result yang disetujui untuk menjadi tolok ukur pengujian metrik EA, EM, dan SV pada BAB 4.
3. **Formalisasi Definisi TRR pada Skripsi:**  
   Tegaskan di metodologi bahwa *Token Reduction Ratio (TRR)* dihitung spesifik pada **skema database yang diumpankan ke SQL Generator**, membandingkan 9 tabel lengkap terhadap 1–2 tabel hasil seleksi Router.

### B. SHOULD FIX (Sangat Disarankan untuk Memperkuat Skripsi)
1. **Buat Script Otomatis Penghitung 5 Metrik Evaluasi:**  
   Bangun satu skrip Python evaluasi (misal: `evaluasi_benchmark.py`) yang membaca daftar ground truth, mengeksekusi pipeline chat, menghitung skor EA, EM, SV, Latensi E2E, serta TRR secara otomatis, dan mengekspornya langsung menjadi tabel LaTeX/Markdown untuk bab hasil.
2. **Tambahkan Tombol Feedback Sederhana di UI:**  
   Tambahkan tombol jempol *Like / Dislike* sederhana di `ChatMessage.vue` yang menyimpan respons kepuasan pengguna ke `telemetry.duckdb` agar klaim *User Feedback Mechanism* menjadi berstatus `IMPLEMENTED`.

### C. CAN BE DESCRIBED AS FUTURE WORK (Dapat Ditulis Sebagai Saran Pengembangan)
1. Integrasi otomatisasi evaluasi kueri berbasis framework *RAGAS* atau *DeepEval*.
2. Implementasi semantic vector schema linking menggunakan vector embedding.
3. Pelaksanaan *User Acceptance Testing (UAT)* berskala luas dengan puluhan pemangku kepentingan lintas divisi operasional pelabuhan.
4. Dukungan penuh untuk model open-source lokal murni (Ollama/vLLM) secara *on-premise air-gapped*.

---

# 6. FINAL SYSTEM DESCRIPTION (DESKRIPSI RESMI SISTEM AKTUAL)

> **"Sistem yang dikembangkan dalam penelitian ini adalah asisten analitik data percakapan hibrida yang mengintegrasikan arsitektur data kolumnar Medallion-DuckDB dengan orkestrasi penalaran kognitif Multi-Agent berbasis LangGraph linier. Sistem memproses data operasional riil PT Terminal Petikemas Surabaya dari berkas spreadsheet Microsoft Excel melalui pembersihan bertahap (Bronze mentah, Silver bersih, dan Gold konsolidasi) ke dalam 9 tabel fakta fisik terdenormalisasi pada mesin DuckDB lokal.**  
>  
> **Pada lapisan penalaran, sistem menerapkan paradigma Asymmetric Multi-LLM Tiering yang memisahkan beban kerja kognitif ke model heterogen: Google Gemini 3.1 Flash-Lite dialokasikan pada Router Agent untuk klasifikasi tabel dan pemangkasan skema (Schema Pruning), Google Gemini 3.6 Flash dialokasikan pada SQL Generator Agent untuk sintesis Text-to-SQL analitik Zero-Shot berbasis aturan bisnis pelabuhan, dan OpenAI GPT-OSS-20B via Groq Cloud dialokasikan pada Viz Analyst Agent untuk penyusunan narasi bisnis eksekutif serta konfigurasi visualisasi Apache ECharts.**  
>  
> **Keamanan dan integritas data dijamin melalui prinsip Zero Data Leakage ke cloud, penguncian koneksi fisik database read-only, Pre-Flight Specificity Guard pada layer API, serta node Sanitizer deterministik non-LLM yang memblokir instruksi DDL/DML berbahaya. Seluruh siklus eksekusi diatur secara linier dengan mekanisme Fail-Fast Single-Pass (0 Retry) yang secara instan mengalihkan kegagalan kueri atau kekosongan data menuju respons penanganan ramah (Graceful Degradation) guna menjamin determinisme waktu respons dan efisiensi biaya token."**
