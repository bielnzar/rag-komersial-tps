# Dokumentasi Backend: TPS AI Data Agent

Dokumen ini ditulis khusus untuk *developer* selanjutnya yang bakal memelihara (*maintain*) atau mengembangkan *backend* dari project RAG Komersial PT TPS. 

Intinya, *backend* ini bukan sekadar API CRUD biasa. Ini adalah mesin orkestrasi AI berbasis *Large Language Model* (LLM) yang bisa menerjemahkan bahasa natural manusia menjadi *query* database, mengeksekusinya secara lokal, lalu mengembalikan hasil analisis naratif beserta konfigurasi grafik secara otomatis.

---

## 1. Konsep Utama (Big Picture)

Stack teknologi yang kita pakai di *backend* ini cukup *straightforward* tapi *powerful*:
- **FastAPI**: Fondasi utama untuk melayani API *endpoint*. Ringan, cepat, dan modern.
- **DuckDB**: Berperan sebagai *analytical database* (OLAP) lokal. Datanya bersumber dari ekstraksi file Excel divisi komersial. Kita pakai DuckDB karena eksekusi agregasi data tabularnya super ngebut dan tidak butuh server database terpisah.
- **LangGraph**: Otak dari *workflow* agen AI kita. Alih-alih membuat *chain* linear yang kaku, kita pakai *state machine* dari LangGraph agar agen AI bisa melakukan siklus putar balik (*self-healing*) ketika melakukan kesalahan *query*.
- **Gemini (Google GenAI)**: LLM utama yang diandalkan untuk merakit SQL (*code generation*) dan merancang visualisasi JSON terstruktur.

---

## 2. Peta Direktori

Berikut adalah struktur folder di dalam direktori `backend/` yang wajib dipahami:

- **`agents/`**: Ini adalah sentral orkestrasi AI.
  - `state.py`: Mendefinisikan memori (`AgentState`) yang dilempar-lempar ke setiap node (seperti `user_query`, `sql_error`, `echarts_config`).
  - `sql_gen.py`: Node agen pertama. Tugas spesifiknya mengonversi teks *user* menjadi *query* SQL yang valid. Di dalamnya terdapat injeksi skema dinamis dan **Glosarium Bisnis** (Lapisan Semantik).
  - `execute.py`: Node eksekutor. Tugasnya murni untuk menghajar *database* DuckDB dengan SQL dari node sebelumnya. Di sinilah letak sensor "Data Kosong" untuk memicu *self-healing*.
  - `viz_gen.py`: Node agen terakhir. Bertugas merangkum hasil *query* menjadi bahasa manusia (`answer`), sekaligus merakit JSON konfigurasi grafik Apache ECharts (`echarts_config`) menggunakan Pydantic *Structured Output*.
  - `graph.py`: Tempat merangkai semua node di atas menjadi satu alur kerja, termasuk fungsi *conditional router* (kapan harus maju, kapan harus putar balik).

- **`etl/`**: Pipeline Data Engineering (konsep *Medallion Architecture*).
  - `main_etl.py`: *Script* utama untuk mengekstrak data dari Excel mentah dan menyuntikkannya ke DuckDB.
  - `transformers.py`: Berisi fungsi-fungsi spesifik untuk membersihkan tiap bentuk *sheet* Excel (contoh: *unpivot*, penyeragaman nama kolom).
  - `utils.py`: Berisi *helper* modular (hapus kolom hantu, pemaksaan tipe data, sistem *logging* otomatis).

- **`main.py`**: *Entry point* FastAPI. Semua rute API (termasuk `/api/v1/chat`) hidup di sini.

---

## 3. Alur Kerja ETL (Extract, Transform, Load)

Sebelum AI bisa diandalkan, data mentah harus dimasak dulu melalui *script* ETL ini. Cara kerjanya mengadopsi struktur *Medallion*:

1. **Bronze**: Data ditarik mentah-mentah dari *file* `.xlsx` menggunakan Pandas, dipecah berdasarkan *sheet*.
2. **Silver**: Data dibersihkan. Kolom tak bernama dihapus, dan kolom target dipaksa menjadi numerik agar tidak ada teks "nyelip" yang berpotensi bikin DuckDB *crash*. Di sini juga ada **Standarisasi Skema** (misal: menyamakan kolom `Vessel Operator` dan `LOP` menjadi satu nama baku agar LLM tidak kebingungan).
3. **Gold**: Data yang sudah solid kemudian dilipat (*melt*/*unpivot*) ke format baris memanjang, lalu dibenamkan secara permanen ke *file* `tps_komersial.duckdb`.

**Cara eksekusi ETL:** 
(Biasanya hanya perlu dijalankan ulang ketika ada *file* Excel terbaru dari divisi komersial)
```bash
python backend/etl/main_etl.py
```

---

## 4. Alur Kerja LangGraph (Text-to-SQL + Self Healing)

Ini adalah keunggulan utama dari sistem yang telah kita bangun. Alurnya tidak hanya berjalan maju, tapi memiliki otak untuk mengoreksi diri.

1. **User Nanya**: Pertanyaan masuk via *endpoint* API di `main.py`.
2. **SQL Gen**: LLM akan mengintip struktur aktual DuckDB. LLM juga akan membaca instruksi **Glosarium Semantik** di dalam *prompt*-nya (misal: pengingat bahwa "jalur domestik" itu tertulis sebagai 'DOMESTIC', bukan 'domestik'). Setelah berfikir, LLM memuntahkan satu blok SQL murni.
3. **Execute SQL**: Sistem menjajal SQL tersebut di DuckDB.
   - Kalau **Gagal (Syntax Error)**: Sistem menangkap pesannya.
   - Kalau **Data Kosong** (0 baris atau agregasi `null`): Sistem mendeteksinya dan menciptakan pesan error teguran buatan sendiri.
4. **Conditional Router**: Sistem mengevaluasi, apakah ada error?
   - Jika **ADA ERROR** (dan percobaan koreksi masih < 3 kali): Sistem membanting setir (putar balik) ke node `SQL Gen`. Intinya sistem berkata, *"Eh query lu ngawur nih, cepet benerin berdasarkan error ini!"*. Proses inilah yang kita sebut **Self-Healing**.
   - Jika **SUKSES** (data riil didapatkan): Alur berlanjut ke tahap visualisasi.
5. **Viz Gen**: Dengan berbekal data matang, LLM merangkai narasi sekaligus memformulasikan kerangka JSON untuk diagram ECharts. Hasil ini kemudian dilempar kembali ke pengguna via API.

---

## 5. Menjalankan Server API (Development)

Untuk menghidupkan *server backend* di mode *development*:
```bash
uvicorn main:app --reload
```
API dapat diakses sekaligus diuji coba melalui dokumentasi interaktif (Swagger UI) di `http://localhost:8000/docs`.

---

> **Catatan Krusial untuk Developer Selanjutnya:**
> Jika suatu saat Anda menemukan AI mulai keliru dalam mengambil data atau merakit logika filter yang salah, hal **pertama** yang wajib Anda periksa adalah **Glosarium di `sql_gen.py`**. Sering kali LLM hanya butuh sedikit *hint* (konteks tambahan) mengenai kebiasaan bisnis atau istilah khusus yang dipakai oleh tim PT TPS. Tambahkan saja fakta bisnis tersebut ke dalam *prompt*, dan AI akan kembali pintar. Selamat *coding*!
