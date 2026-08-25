# Milestone 2: AI Text-to-SQL Core & Integrasi API

Setelah data kita terorganisir rapi di DuckDB (hasil dari Milestone 1), sekarang saatnya memasang "otak" di sistem kita. **Milestone 2** berfokus pada bagaimana mengajari AI agar bisa menerjemahkan bahasa manusia menjadi bahasa *database* (SQL), lalu menyajikannya lewat sebuah gerbang API.

---

## 1. Konsep Dasar: Apa itu Text-to-SQL? (Penjelasan untuk Orang Awam)
Kalau dulu, tiap kali Manajer Komersial ingin melihat data (misal: "Berapa banyak jumlah kapal domestik bulan lalu?"), dia harus menelepon divisi IT atau Data Analyst untuk menarik datanya. Divisi IT kemudian mengetik kode rumit (SQL) di komputer mereka.

Di Milestone 2 ini, kita membunuh proses birokrasi tersebut. 
Kita membangun jembatan bernama **Text-to-SQL**. Jembatan ini menggunakan kecerdasan buatan (Gemini AI) yang bisa "mendengarkan" pertanyaan bahasa Indonesia sehari-hari, lalu secara instan (dalam hitungan detik) menerjemahkannya sendiri menjadi kode SQL yang rumit, menjalankannya, dan memberikan jawabannya langsung. 

*Analogi: AI kita kini bertindak sebagai Asisten IT pribadi yang tidak pernah tidur.*

---

## 2. Fondasi Mesin: FastAPI & LangChain
Agar aplikasi *Frontend* (atau aplikasi lain) bisa mengobrol dengan AI kita, kita membangun gerbang komunikasi menggunakan **FastAPI**.
- **FastAPI** adalah *framework* Python super cepat. Dialah yang menyediakan *endpoint* (alamat URL) seperti `/api/v1/chat` untuk menerima kiriman JSON pertanyaan dari luar.
- **LangChain & LangGraph** adalah kerangka kerja (*framework*) khusus AI. Ketimbang memanggil Gemini secara manual yang berisiko berantakan, kita menggunakan LangGraph untuk menyusun alur kerja AI agar terstruktur langkah demi langkah (terima pertanyaan -> bikin SQL -> eksekusi database -> rangkum teks). Di fase awal (Milestone 2) ini, alurnya masih berjalan satu arah (linear).

---

## 3. "Menyuntikkan" Mata ke AI (Dynamic Schema Injection)
Ini adalah masalah klasik di dunia AI: *Bagaimana caranya Gemini tahu nama-nama tabel dan kolom di database kita?* Kalau dia nebak-nebak sendiri (halusinasi), SQL-nya pasti *error*.

**Solusinya (Untuk Developer):**
Di dalam file `backend/agents/sql_gen.py`, sebelum kita menyuruh AI membuat SQL, kita secara otomatis *query* ke DuckDB untuk mengambil strukturnya.
```sql
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema='main';
```
Hasil dari *query* struktur ini (berupa daftar tabel dan kolomnya) kita masukkan ke dalam *Prompt* utama (system prompt) LLM. 
Jadi, AI benar-benar "melihat" peta data kita secara *real-time* dan tahu persis bahwa kolomnya bernama `year`, `month`, dan `actual`. Ia tidak akan sembarangan menciptakan nama kolom gaib.

---

## 4. Dua Agen Pertama Kita
Di fase ini, kita sudah berhasil menghidupkan 2 Agen (Node) utama di `backend/agents/`:
1. **Node SQL Gen (`sql_gen.py`)**: Agen pertama yang kerjanya fokus membaca pertanyaan, melihat skema *database*, lalu merakit teks SQL murni tanpa *error* pengetikan. Kita menyuruhnya bertindak sebagai "Senior Data Engineer".
2. **Node Execute (`execute.py`)**: Agen kedua (bukan AI, melainkan fungsi Python biasa) yang bertugas mengeksekusi kode SQL buatan agen pertama secara langsung ke dalam perut DuckDB, lalu mengembalikan hasilnya berupa wujud data tabular nyata.

**Kesimpulan Milestone 2**:
Pada tahap ini, sistem sudah bisa diajak mengobrol dan bisa menjawab data secara akurat. Namun, ia masih punya kelemahan: kalau AI *typo* sedikit saja atau salah mengerti ejaan kata (misal mencari "jalur domestik" pakai filter `kategori = 'domestik'` alih-alih `DOMESTIC`), sistem akan langsung *crash* atau menampilkan data kosong tanpa tahu cara memperbaikinya.

Kelemahan inilah yang menjadi alasan kita maju merombak total otak AI-nya di **Milestone 3**.
