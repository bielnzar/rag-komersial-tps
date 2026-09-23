# MULTI-AGENT TASK MAPPING

## Pemetaan Komponen, Task, Input dan Output

**Proyek:** Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ  
**Tujuan:** Menetapkan pemetaan teknis komponen Multi-Agent, alur LangGraph, dan task masing-masing sebelum revisi proposal diserahkan.

---

## 1. Pemetaan Komponen Sistem Aktual

Berdasarkan _source code_ aktual pada modul [backend/agents/](../backend/agents/), arsitektur sistem terdiri atas **5 Node LangGraph fisik**: **3 AI Agent berbasis LLM** dan **2 Node Deterministik**, yang dihubungkan dengan pola kendali **Fail-Fast (Single-Pass)**.

### 1.1 Komponen AI Agent Berbasis LLM

| Agent                   | Task Utama                                                                                                          | Input Utama                                                                        | Output Utama                                                               | Peran Akademik                       |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------ |
| **Router Agent**        | Menentukan tabel data yang relevan terhadap pertanyaan pengguna berdasarkan katalog semantik                        | Pertanyaan pengguna + Katalog metadata tabel + Riwayat obrolan (Multi-turn)        | Daftar nama tabel yang relevan (`relevant_tables`)                         | Klasifikasi Intent & Pemilihan Skema |
| **SQL Generator Agent** | Melakukan _schema pruning_ dan merakit kueri ANSI SQL dialek DuckDB menggunakan _Dynamic Few-Shot_                  | Pertanyaan + Skema kolom terpilih + Glosarium bisnis + _Dynamic Few-Shot Examples_ | Kueri SQL rakitan (`generated_sql`)                                        | Pembentukan Kueri Deterministik      |
| **Viz Analyst Agent**   | Menganalisis data hasil kueri, menyusun narasi bisnis eksekutif, dan merakit konfigurasi JSON grafik Apache ECharts | Pertanyaan + Hasil eksekusi database (Format CSV Ringkas)                          | Narasi eksekutif (`final_answer`) + Konfigurasi ECharts (`echarts_config`) | Sintesis Wawasan & Presentasi Visual |

### 1.2 Komponen Deterministik Pendukung

| Komponen (Node)         | Task Utama                                                                                                                                                               | Input                                   | Output                                                        | Peran Teknis                                      |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------- |
| **Sanitizer Node**      | Validasi keamanan dual-layer: memeriksa SQL Injection/command chaining pada pertanyaan (_input guard_) dan memblokir keyword DDL/DML terlarang pada SQL (_output guard_) | Pertanyaan pengguna + Kueri SQL rakitan | Status validasi (`sql_error = None` atau `SANITIZER BLOCKED`) | Pengawal Keamanan Basis Data (_Rule-Based Regex_) |
| **Execute Engine Node** | Mengeksekusi SQL terhadap engine DuckDB melalui _Connection Pool Read-Only_ dan mendeteksi kondisi ketiadaan data                                                        | SQL yang lolos validasi                 | Dataset tabular (List of Dicts) atau status `DATA_EMPTY`      | Eksekusi Fisik Basis Data (_OLAP Engine_)         |

### 1.3 Posisi Konseptual Fail-Fast & LangGraph

> [!IMPORTANT]
> **Pembedaan Krusial untuk Proposal:**
>
> - **LangGraph** adalah **Framework Orkestrator Alur Kerja (_Workflow Orchestrator_)**, bukan sebuah agent.
> - **Fail-Fast** adalah **Pola Desain Arsitektur / Strategi Percabangan (_Architectural Pattern / Conditional Routing_)**, bukan sebuah node atau agent terpisah.  
>   Pola Fail-Fast diimplementasikan melalui percabangan bersyarat (_conditional edges_) yang langsung memutus alur tanpa memicu _retry loop_ yang boros token.

---

## 2. Task Decomposition End-to-End

Berikut adalah diagram alur state machine aktual yang diatur oleh LangGraph ([backend/agents/graph.py](../backend/agents/graph.py)):

```text
                  Pertanyaan Pengguna (Natural Language)
                                   |
                                   v
                   +-------------------------------+
                   |       1. ROUTER AGENT         | (LLM Node)
                   |  Memilih tabel data relevan   |
                   +-------------------------------+
                                   |
                                   v [relevant_tables]
                   +-------------------------------+
                   |    2. SQL GENERATOR AGENT     | (LLM Node)
                   |  - Schema Pruning Kolom Lebar |
                   |  - Dynamic Few-Shot Examples  |
                   +-------------------------------+
                                   |
                                   v [generated_sql]
                   +-------------------------------+
                   |         3. SANITIZER          | (Deterministic Node)
                   |  Dual-Layer Regex & DDL Guard |
                   +-------------------------------+
                                   |
              [Percabangan Bersyarat / Pola Fail-Fast]
                                   |
                 +-----------------+-----------------+
                 |                                   |
         Lolos Validasi                         Terblokir
                 |                                   |
                 v                                   |
    +-------------------------+                      |
    |    4. EXECUTE ENGINE    | (Deterministic Node) |
    | Eksekusi DuckDB Pool    |                      |
    +-------------------------+                      |
                 |                                   |
        +--------+--------+                          |
        |                 |                          |
    Data Ada          Data Kosong                    |
        |                 |                          |
        | [query_result]  | [DATA_EMPTY]             | [SANITIZER BLOCKED]
        v                 v                          v
    +-------------------------------------------------------+
    |                  5. VIZ ANALYST AGENT                 | (LLM Node)
    | - Input: CSV Compact (Sampling cerdas maks 15 baris)  |
    | - Output Paralel: Narasi Eksekutif + ECharts Config   |
    | - Graceful Handling: Penolakan Aman / Saran Pertanyaan|
    +-------------------------------------------------------+
                                   |
                                   v
             Tabel Data + Grafik Interaktif + Narasi Analisis
```

---

## 3. Penjelasan Task Rinci Masing-Masing Komponen

### 3.1 Router Agent ([backend/agents/router.py](../backend/agents/router.py))

- **Tujuan Task:** Mengidentifikasi intensi analitik pengguna dan menyaring tabel DuckDB mana saja yang relevan untuk menjawab pertanyaan.
- **Input:**
  1. `user_query` (string pertanyaan asli dari pengguna);
  2. `catalog` (deskripsi semantik 10 tabel yang dimuat dari database);
  3. `history` (konteks 3 percakapan terakhir dari Redis untuk pertanyaan lanjutan berantai);
  4. `role` (peran pengguna untuk pencatatan hak akses RBAC).
- **Output:** `relevant_tables` (list of string nama tabel yang valid di DuckDB, misal: `['fakta_throughput']`).
- **Tanggung Jawab:**
  - Memetakan kebutuhan pengguna ke tabel data spesifik;
  - Mengabaikan tabel yang tidak relevan agar context window pada tahap berikutnya tetap ringkas;
  - Menangani pertanyaan rujukan (_contextual follow-up_, misal: _"bagaimana dengan tahun 2023?"_).
- **Batas Tanggung Jawab:**
  - **TIDAK** merakit query SQL;
  - **TIDAK** melakukan _schema pruning_ tingkat kolom (kolom dipangkas di SQL Generator);
  - **TIDAK** menyentuh engine database.

---

### 3.2 SQL Generator Agent ([backend/agents/sql_gen.py](../backend/agents/sql_gen.py))

- **Tujuan Task:** Menerjemahkan kebutuhan analisis menjadi kueri ANSI SQL yang presisi dan kompatibel dengan dialek DuckDB.
- **Input:**
  1. `user_query` (pertanyaan pengguna);
  2. Skema kolom dari `relevant_tables`;
  3. Glosarium aturan bisnis (misal: penanganan `COALESCE(total_all_revenue, total_revenue)`);
  4. `few_shot` (contoh kueri terpilih via `get_few_shot_examples()`).
- **Output:** `generated_sql` (string kueri SQL murni tanpa format markdown pembungkus).
- **Fitur & Tanggung Jawab Khusus:**
  - **Column-Level Schema Pruning (`prune_columns`):** Memangkas tabel lebar (>20 kolom seperti `fakta_market_share` yang memiliki 54 kolom) menjadi hanya kolom dimensi waktu, operator, dan kolom yang cocok dengan kata kunci kueri, menghemat 300–500 token.
  - **Dynamic Selective Few-Shot:** Hanya menyuntikkan 1–2 contoh kueri yang relevan dengan tabel terpilih, bukan membubuhkan seluruh contoh tabel lain.
- **Batas Tanggung Jawab:**
  - **TIDAK** mengeksekusi SQL ke database;
  - **TIDAK** melakukan validasi keamanan (tugas Sanitizer);
  - **TIDAK** membuat asumsi visualisasi.

---

### 3.3 Sanitizer Node ([backend/agents/sanitizer.py](../backend/agents/sanitizer.py))

- **Tujuan Task:** Komponen pertahanan deterministik (_gatekeeper_) untuk mencegah ancaman manipulasi data dan kebocoran sistem.
- **Klasifikasi:** **Komponen Deterministik (Rule-Based Regex & Schema Validator)** — Bukan Agent LLM.
- **Input:** `user_query` dan `generated_sql`.
- **Output:** `sql_error` (`None` jika lolos, atau string `"SANITIZER BLOCKED: ..."` jika terdeteksi pelanggaran).
- **Mekanisme Dual-Layer Guard:**
  1. _Input Guard:_ Memeriksa karakter titik koma (`;`) berantai, komentar SQL (`--`, `/*`), serta kata kunci DDL/DML pada teks pertanyaan user.
  2. _Output Guard:_ Memeriksa kueri SQL rakitan dari kata kunci modifikasi (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`), memastikan kueri hanya berupa single-statement `SELECT`, serta memverifikasi bahwa tabel yang diakses terdaftar resmi di basis data DuckDB.
- **Batas Tanggung Jawab:**
  - **TIDAK** memperbaiki kueri secara otomatis;
  - **TIDAK** mengeksekusi data.

---

### 3.4 Execute Engine Node ([backend/agents/execute.py](../backend/agents/execute.py))

- **Tujuan Task:** Mengeksekusi SQL yang telah lolos verifikasi keamanan secara langsung pada basis data DuckDB.
- **Klasifikasi:** **Komponen Deterministik (Database OLAP Engine)** — Bukan Agent LLM.
- **Input:** `generated_sql` tervalidasi.
- **Output:** `query_result` (list of dictionary records) atau pesan `sql_error` (`DATA_EMPTY` / `DB_SYNTAX_ERROR`).
- **Fitur Khusus:**
  - Terhubung via _Centralized Read-Only Connection Pool_ ([backend/db.py](../backend/db.py)) untuk mencegah file lock;
  - Sanitasi nilai numerik non-standar (`NaN` / `inf` dipaksa menjadi `None`/`null` agar tidak memicu _JSON decode error_ pada API);
  - Sensor _Fail-Fast Data Empty_: Mendeteksi hasil 0 baris atau hasil agregasi berisi nilai `None` tunggal.
- **Batas Tanggung Jawab:**
  - **TIDAK** bernalar terhadap data;
  - **TIDAK** memformat narasi untuk user.

---

### 3.5 Viz Analyst Agent ([backend/agents/viz_gen.py](../backend/agents/viz_gen.py) & [chart_gen.py](../backend/agents/chart_gen.py))

- **Tujuan Task:** Menganalisis hasil tabular dan mentransformasikannya menjadi informasi analitik yang komunikatif bagi pengambil keputusan.
- **Input:**
  1. `user_query` (pertanyaan pengguna);
  2. `query_result` (data tabular hasil eksekusi DuckDB);
  3. `sql_error` (status kegagalan dari node sebelumnya jika ada);
  4. `force_chart` / deteksi kata kunci grafik.
- **Output:**
  1. `final_answer` (ringkasan narasi eksekutif berformat Markdown dengan pemisah ribuan standar Indonesia);
  2. `echarts_config` (objek JSON konfigurasi visualisasi Apache ECharts);
  3. `suggestions` (rekomendasi 3 pertanyaan interaktif jika data kosong).
- **Fitur Khusus:**
  - **Smart Row Sampling (`format_data_compact`):** Mengonversi data JSON ke format CSV ringkas (maksimal 15 baris untuk dataset besar, atau seluruhnya jika $\le 30$ baris) guna menghemat token hingga 80%.
  - **Parallel Execution (`ThreadPoolExecutor`):** Menjalankan perakitan narasi bisnis dan perakitan konfigurasi grafik ECharts secara paralel di dua thread terpisah.
  - **Graceful Degradation:** Jika menerima sinyal error dari Sanitizer atau DuckDB, agen tidak mengalami _crash_, melainkan memberikan edukasi penolakan yang ramah atau opsi saran pertanyaan.
- **Batas Tanggung Jawab:**
  - **Bukan sumber kebenaran numerik;** seluruh fakta angka wajib disadur langsung dari CSV hasil DuckDB (tidak mengarang angka);
  - **TIDAK** merakit query SQL baru.

---

## 4. Hubungan dengan Schema Linking dan Schema Pruning

Dalam proposal, pemisahan konsep ini harus dijelaskan secara runtut agar tidak menimbulkan kerancuan:

1. **Schema Linking:** Proses pemetaan istilah bahasa alami pengguna ke entitas skema database (dikerjakan bersama oleh **Router Agent** untuk level tabel dan **SQL Generator Agent** untuk level kolom).
2. **Schema Pruning:** Teknik optimasi token di mana skema tabel berukuran lebar (>20 kolom) dipangkas secara deterministik oleh fungsi `prune_columns()` di dalam modul `sql_gen.py` sebelum dikirimkan ke model bahasa.
3. **Dynamic Few-Shot:** Teknik pembelajaran dalam konteks (_In-Context Learning_) di mana model diberikan 1–2 contoh kueri SQL spesifik tabel terpilih untuk memandu dialek agregasi DuckDB yang tepat.

---

## 5. Implementasi Source Code

Menjawab bagian audit teknis sebelumnya, berikut adalah bukti faktual langsung dari berkas kode sumber:

|  No.  | Aspek Pertanyaan                 | Hasil Audit Kode Aktual                                                                                                                          | Bukti Implementasi Source Code                                                                                                                                                               |
| :---: | :------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | **Metode SQL Generator**         | **100% Menggunakan Dynamic Selective Few-Shot** (Bukan Zero-Shot murni).                                                                         | Kamus `FEW_SHOT_EXAMPLES` & fungsi `get_few_shot_examples()` pada [backend/agents/sql_gen.py (L165-L225)](../backend/agents/sql_gen.py#L165-L225).                                           |
| **2** | **Tugas Router & Letak Pruning** | Router memilih tabel & mencatat peran RBAC. Schema Pruning dijalankan oleh SQL Gen via `prune_columns()`.                                        | Modul [backend/agents/router.py](../backend/agents/router.py) dan [backend/agents/sql_gen.py (L56-L120)](../backend/agents/sql_gen.py#L56-L120).                                             |
| **3** | **Input & Output Viz Analyst**   | Menerima data dalam format CSV Compact (maks 15 baris / full jika $\le 30$ baris) dan menghasilkan JSON Apache ECharts lengkap.                  | Fungsi `format_data_compact()` & `generate_chart_config()` pada [backend/agents/viz_gen.py](../backend/agents/viz_gen.py) dan [backend/agents/chart_gen.py](../backend/agents/chart_gen.py). |
| **4** | **Mekanisme Fail-Fast**          | Menggunakan arsitektur _Single-Pass_. Jika Sanitizer memblokir kueri, alur melompati (_skip_) eksekusi database dan langsung menuju Viz Analyst. | Fungsi `should_continue_sanitizer` pada [backend/agents/graph.py (L12-L23)](../backend/agents/graph.py#L12-L23).                                                                             |

---

## 6. Format Tabel Rekomendasi untuk BAB 3 Proposal

Tabel berikut dirancang khusus untuk disematkan pada Sub-bab **Perancangan Sistem Multi-Agent** di proposal skripsi:

**Tabel Pemetaan Komponen dan Pembagian Tugas Sistem Multi-Agent Text-to-SQL**

| Komponen                | Klasifikasi Komponen                 | Task Utama                                                                                                   | Input                                                                | Output                                             |
| ----------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- | -------------------------------------------------- |
| **Router Agent**        | AI Agent (LLM)                       | Mengklasifikasikan intent dan menentukan tabel data yang relevan                                             | Pertanyaan bahasa alami + Katalog metadata tabel                     | Daftar tabel terpilih (`relevant_tables`)          |
| **SQL Generator Agent** | AI Agent (LLM)                       | Menjalankan _schema pruning_ dan merakit kueri ANSI SQL dialek DuckDB via _Dynamic Few-Shot_                 | Pertanyaan + Skema terpilih + Glosarium bisnis + _Few-Shot Examples_ | Kueri SQL terstruktur (`generated_sql`)            |
| **Sanitizer**           | Deterministik (_Rule-Based Regex_)   | Memvalidasi sintaks keamanan (_input guard_) dan membatasi perintah modifikasi data DDL/DML (_output guard_) | Pertanyaan pengguna + Kueri SQL rakitan                              | Status validasi keamanan (`PASSED` / `BLOCKED`)    |
| **Execute Engine**      | Deterministik (_OLAP Database Pool_) | Mengeksekusi SQL terhadap engine DuckDB dan mendeteksi kondisi ketiadaan data (_Data Empty_)                 | Kueri SQL lolos validasi                                             | Dataset tabular (_List of Dicts_) atau Error State |
| **Viz Analyst Agent**   | AI Agent (LLM)                       | Menyusun narasi analitik eksekutif dan menghasilkan konfigurasi grafik Apache ECharts secara paralel         | Pertanyaan pengguna + Dataset hasil eksekusi (Format CSV Ringkas)    | Narasi eksekutif + Konfigurasi JSON Apache ECharts |

> **Catatan Tambahan untuk Narasi Proposal:**  
> _"Kelima komponen di atas dirangkai menggunakan state machine **LangGraph** dengan menerapkan strategi orkestrasi **Fail-Fast (Single-Pass)**. Mekanisme ini memastikan bahwa kueri yang tidak aman akan langsung digagalkan sebelum menyentuh engine database, serta mengeliminasi latensi akibat perulangan perbaikan kueri (retry loop) yang berlebihan."_

---

## 7. Panduan Menjawab Pertanyaan Dosen Pembimbing Saat Bimbingan

Berikut adalah argumen akademik yang siap Anda gunakan jika dosen mengajukan pertanyaan:

1. **“Mengapa jumlah AI Agent hanya 3, bukan 5 atau 6?”**  
   _Jawaban:_ Sesuai prinsip rekayasa perangkat lunak dan efisiensi komputasi, agent berbasis LLM hanya digunakan untuk tugas-tugas yang membutuhkan penalaran bahasa alami dan fleksibilitas pemetaan semantik (Router, SQL Generator, Viz Analyst). Untuk tugas validasi keamanan (Sanitizer) dan eksekusi query (Execute), penggunaan komponen deterministik (Regex & Database Engine) jauh lebih unggul karena memiliki kepastian matematis 100%, berlatensi 0 ms, dan bebas dari risiko halusinasi AI.

2. **“Apakah sistem ini menggunakan Zero-Shot atau Few-Shot?”**  
   _Jawaban:_ Pada tahap Router digunakan Zero-Shot karena katalog tabel bersifat umum. Namun pada tahap **SQL Generator**, sistem menerapkan **Dynamic Selective Few-Shot Prompting**, di mana sistem menyuntikkan contoh kueri referensi khusus untuk tabel yang sedang ditanyakan guna memastikan kueri SQL mematuhi dialek DuckDB dan konvensi penamaan kolom pelabuhan.

3. **“Mengapa memilih arsitektur Fail-Fast dibanding Self-Correction Loop?”**  
   _Jawaban:_ Berdasarkan karakteristik data komersial pelabuhan, jika data memang tidak ada pada periode tersebut (misal data 2027), melakukan _retry loop_ berulang kali hanya akan memboroskan token dan menambah latensi tanpa mengubah fakta bahwa data di database kosong. Pendekatan Fail-Fast memberikan respon cepat (<2 detik) dan langsung menawarkan 3 pertanyaan rekomendasi alternatif yang dijamin memiliki data.
