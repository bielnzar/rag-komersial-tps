# 📑 PROPOSAL RESEARCH ALIGNMENT
## Konteks Teoretis, Desain Metodologis, & Baseline Penelitian Skripsi

**Dokumen Acuan:** Kerangka Konseptual Usulan Penelitian Tugas Akhir  
**Peran Dokumen:** Baseline resmi penelitian yang digunakan sebagai acuan komparasi antara rancangan proposal akademis dengan kondisi aktual sistem pada [`TECHNICAL_MASTER_BRIEF.md`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/TECHNICAL_MASTER_BRIEF.md).  
**Sifat Dokumen:** Normatif & Konseptual (Bukan laporan audit kode).

---

# 1. JUDUL PENELITIAN

> **“Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ”**

---

# 2. KONTEKS & BATASAN PENELITIAN

* **Studi Kasus:** PT XYZ (Perusahaan penyedia jasa terminal petikemas).
* **Lingkup Unit Kerja:** Divisi Komersial (*Commercial & Business Development*).
* **Karakteristik Data:**
  - Menggunakan **data operasional riil perusahaan** (*Genuine Corporate Data*).
  - Data **BUKAN** dataset sintetis, bukan data tiruan, dan **BUKAN** dataset publik/akademik terbuka (seperti Kaggle, Spider Benchmark, atau BIRD-SQL).
* **Sumber Data Utama:** Berkas spreadsheet Microsoft Excel (`.xlsx`).
* **Sistem Analitik Eksisting:** Microsoft Power BI (Dashboard statis yang memerlukan intervensi kueri manual atau pembuatan report berulang oleh analis data).
* **Kebijakan Volume Data:** Jumlah berkas Excel **TIDAK DIKUNCI** pada angka tertentu, melainkan bersifat dinamis mengikuti ketersediaan dan kebutuhan bisnis Divisi Komersial yang dapat berkembang seiring waktu.

---

# 3. ARSITEKTUR PENELITIAN YANG DIRENCANAKAN

### A. Konsep Aliran Data Utama
Penelitian merancang alur pemrosesan data hibrida yang memadukan rekayasa data (*Data Engineering*) dan penalaran bahasa alami (*Natural Language Reasoning*):

```text
Data Perusahaan (Excel)
  │
  ▼
Medallion Architecture (Bronze ➔ Silver ➔ Gold)
  │
  ▼
Analytical In-Process Database (DuckDB OLAP)
  │
  ▼
Multi-Agent Text-to-SQL Orchestration
  │
  ▼
Analytic Output (Narasi Eksekutif, Visualisasi Grafik, & Tabel Data)
```

### B. Komponen Sistem yang Direncanakan
Sistem analitik konseptual membagi alur penalaran ke dalam fungsi-fungsi modular berikut:

1. **Router:** Menganalisis intensi pertanyaan dan memilih domain data yang tepat.
2. **Schema Linking:** Memetakan entitas/istilah bisnis pada pertanyaan ke kolom spesifik di database.
3. **Schema Pruning:** Memangkas tabel/kolom yang tidak relevan agar tidak membebani konteks LLM.
4. **SQL Generator:** Merakit sintaks kueri SQL analitik berdasarkan skema ter-pruning.
5. **Sanitizer:** Memeriksa dan memvalidasi keamanan kueri SQL dari instruksi destruktif.
6. **Execute:** Menjalankan kueri SQL ke mesin database analitik lokal.
7. **Viz Analyst:** Menyintesis hasil angka menjadi narasi bisnis dan konfigurasi visualisasi grafik.
8. **Feedback:** Mengakomodasi mekanisme umpan balik untuk penjaminan kualitas dan evaluasi performa.

> [!IMPORTANT]
> **Klasifikasi Entitas:** Tidak semua komponen di atas harus berupa *Cognitive AI Agent*. Peneliti membedakan secara tegas antara **Agent** (berbasis LLM reasoning), **Node** (titik alur state machine), **Tool** (alat pemanggil fungsi), **Function** (blok kode terprogram), dan **Deterministic Process** (algoritma/aturan berbasis pola pasti non-LLM).

---

# 4. PARADIGMA PENGGUNAAN MODEL LLM (ASYMMETRIC TIERING)

* Penelitian mengadopsi pendekatan **pembagian model berbasis fungsi tugas (*Task-Specialized Asymmetric LLM*)**.
* **Prinsip Beban Kognitif:** Tugas berintensitas penalaran ringan (seperti klasifikasi dan perutean) diarahkan menggunakan model komputasi hemat/cepat, sedangkan tugas sintesis logika struktural SQL menggunakan model dengan kemampuan penalaran tinggi.
* **Prinsip Verifikasi Objektif:** Peneliti dilarang mengasumsikan atau mengklaim penggunaan model AI tertentu dalam proposal/bab metodologi sebelum diverifikasi secara faktual pada kode sistem aktual.

---

# 5. MEKANISME FAIL-FAST & PENANGANAN KEGAGALAN

* **Definisi Fail-Fast:** Mekanisme penghentian proses secara cepat dan terarah seketika terjadi kegagalan validasi keamanan, kesalahan sintaks analitik, atau kueri yang tidak dapat dieksekusi, tanpa membiarkan sistem mengalami *crash* atau perulangan tanpa ujung.
* **Perlakuan terhadap Hasil Kosong (*Empty Result*):**
  - Hasil kueri bernilai kosong (0 baris) **TIDAK OTOMATIS DIANGGAP SEBAGAI ERROR SISTEM**.
  - Suatu kueri yang mengembalikan 0 baris bisa jadi merupakan respons yang **benar dan valid** apabila pada data historis memang tidak terdapat transaksi untuk parameter tersebut (misal: mencari kargo tertentu pada tahun yang belum berjalan).
  - Kebenaran status *empty result* wajib dievaluasi melalui perbandingan terhadap **Ground Truth**.
* **Penghindaran Asumsi Retry:** Penelitian tidak mengasumsikan keberadaan mekanisme *Self-Healing* atau perulangan *Retry Loop* apabila pada implementasi teknis nyata sistem memilih strategi *Single-Pass Execution*.

---

# 6. EVALUASI TEKNIS: 5 METRIK UTAMA

Kinerja teknis dari sistem Text-to-SQL dievaluasi menggunakan 5 metrik baku kuantitatif:

### 1. Execution Accuracy (EA)
* **Makna:** Mengukur kebenaran hasil eksekusi analitik yang dihasilkan kueri SQL AI dibandingkan dengan hasil eksekusi kueri acuan (*Gold Result*).
* **Formulasi:**
  $$\text{EA} = \frac{N_{\text{correct}}}{N_{\text{total}}} \times 100\%$$
  *(di mana $N_{\text{correct}}$ adalah jumlah kueri dengan hasil eksekusi yang identik terhadap Gold Result, dan $N_{\text{total}}$ adalah total kueri uji).*

### 2. Exact Match (EM)
* **Makna:** Mengukur tingkat kesesuaian struktural dan sintaksis antara string SQL yang dirakit AI dengan SQL acuan (*Gold SQL*) berdasarkan aturan perbandingan/normalisasi yang ditentukan (misal: pengabaian *casing* atau urutan klausa non-kritis).
* **Formulasi:**
  $$\text{EM} = \frac{N_{\text{exact}}}{N_{\text{total}}} \times 100\%$$

### 3. Syntactic Validity (SV)
* **Makna:** Mengukur rasio sintaks SQL yang valid dan dapat dipahami secara gramatikal oleh mesin database (DuckDB) tanpa melempar kesalahan sintaks (*Parser/Binder Error*).
* **Formulasi:**
  $$\text{SV} = \frac{N_{\text{valid}}}{N_{\text{total}}} \times 100\%$$

### 4. End-to-End Latency ($L_{\text{E2E}}$)
* **Makna:** Durasi waktu total yang dibutuhkan sistem sejak permintaan pertanyaan pengguna diterima oleh sistem hingga jawaban akhir (narasi & visualisasi) siap dikembalikan ke pengguna.
* **Formulasi:**
  $$L_{\text{E2E}} = t_{\text{response}} - t_{\text{request}}$$

### 5. Token Reduction Ratio (TRR)
* **Makna:** Rasio efisiensi pemangkasan token pada konteks skema database yang dikirimkan ke prompt SQL Generator sebagai hasil dari mekanisme *Schema Pruning*.
* **Formulasi:**
  $$\text{TRR} = \frac{T_{\text{full}} - T_{\text{pruned}}}{T_{\text{full}}} \times 100\%$$
* **Batasan Perhitungan:**
  > [!IMPORTANT]
  > TRR secara spesifik menghitung **token pada konteks skema (schema context)** yang disuntikkan kepada SQL Generator (membandingkan ukuran token seluruh skema katalog database $T_{\text{full}}$ terhadap ukuran token skema ter-pruning $T_{\text{pruned}}$), bukan ukuran keseluruhan prompt percakapan, kecuali implementasi teknis menetapkan cakupan lain.

---

# 7. USER ACCEPTANCE TESTING (UAT)

* **Tujuan:** Mengevaluasi tingkat penerimaan, kemudahan penggunaan, dan kesesuaian fungsional asisten analitik di mata pengguna akhir (*End-User Usability*).
* **Partisipan UAT:** Pengguna pada lingkungan operasional **Divisi Komersial PT XYZ**.
* **Distingsi Konseptual:** UAT **bukan metrik Text-to-SQL**, melainkan metode evaluasi sistem informasi pada tingkat persepsi manusia (*Human-Centric Evaluation*).
* **Parameter Terbuka:** Jumlah responden/pengguna serta rincian skenario pengujian UAT bersifat fleksibel dan belum dikunci, disesuaikan dengan ketersediaan pemangku kepentingan di perusahaan.

---

# 8. DATASET GROUND TRUTH

Evaluasi teknis memerlukan dataset pembanding (*Ground Truth Benchmark*) yang disusun berdasarkan kebutuhan analitik riil Divisi Komersial:
* **Komponen Ground Truth:**
  1. **User Question:** Teks pertanyaan bahasa alami yang mencerminkan variasi analitik (Throughput, Revenue, Market Share, Vessel Service, dsb.).
  2. **Gold SQL:** Kueri SQL terstandar yang disusun secara cermat dan divalidasi oleh analis data internal perusahaan sebagai jawaban kueri paling benar.
  3. **Gold Result:** Tabel data atau nilai agregat eksak hasil eksekusi Gold SQL pada database DuckDB.
* **Implementasi Detail:** Komposisi kuantitatif pertanyaan dan rincian skenario benchmark akan diformalkan pada BAB 3 Metodologi Penelitian.

---

# 9. PRINSIP KOMPARASI AUDIT DENGAN SISTEM AKTUAL

Saat membandingkan baseline usulan penelitian pada dokumen ini dengan kondisi teknis riil di proyek (`TECHNICAL_MASTER_BRIEF.md`):

1. **Anti-Pemaksaan Teori ke Proyek:** Jangan memaksakan kode sistem agar terlihat persis dengan teori/istilah umum jika implementasi nyatanya berbeda.
2. **Anti-Pemaksaan Proyek ke Teori:** Jangan memaksakan teori proposal akademis agar menyesuaikan kelemahan atau jalan pintas kode yang belum teruji.
3. **Eksplisit terhadap Ketidaksesuaian:** Ungkapkan setiap deviasi, anomali, atau perbedaan arsitektur secara transparan dan berimbang.
4. **Taksonomi Penilaian Empat Tingkat:**
   - `SESUAI (Fully Aligned)`: Konsep proposal dan implementasi kode berjalan identik 100%.
   - `SEBAGIAN SESUAI (Partially Aligned)`: Konsep diterapkan, namun memiliki batasan atau bentuk implementasi yang disederhanakan.
   - `BELUM TERSEDIA (Not Available / Planned)`: Tercantum dalam rencana proposal, namun belum ada wujud kodenya.
   - `BERBEDA (Divergent / Alternative Implementation)`: Masalah yang diangkat diselesaikan menggunakan pendekatan arsitektur yang berbeda dari rancangan awal.
5. **Kejujuran Rekayasa (*Engineering Honesty*):** Jangan mengarang fungsi yang tidak ada hanya demi melengkapi tabel komparasi.
