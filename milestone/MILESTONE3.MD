# Milestone 3: Advanced AI Orchestration (Semantic Layer & Self-Healing)

Di akhir Milestone 2, kita mendapati sistem yang cukup pintar tapi "naif". Dia tahu cara nulis SQL, tapi kalau dia salah nebak (misal mencari huruf kecil `domestik` padahal di database huruf besar `DOMESTIC`), dia bakal memuntahkan jawaban: *"Maaf, data tidak ditemukan."* 

Di **Milestone 3** inilah sistem kita di-*upgrade* menjadi aplikasi AI setara *Enterprise*. Kita memberinya otak untuk memahami makna bisnis pelabuhan dan kemampuan untuk sadar akan kesalahannya sendiri.

---

## 1. Solusi Pertama: Semantic Layer (Glosarium Bisnis)
Apa masalah terbesar LLM ketika dihubungkan ke *database* perusahaan? **Dia nggak ngerti bahasa gaul atau singkatan internal perusahaan Anda.** 

Kalau ada *user* bertanya *"Berapa banyak boxes jalur domestik?"*, Gemini mungkin mengira ia harus mencari kata "boxes" di kolom `unit`, padahal di database TPS, satuan yang dipakai adalah `TEUs`.

**Bagaimana Kita Mengatasinya (Untuk Developer):**
Di dalam *Prompt* utama AI (`sql_gen.py`), kita menyuntikkan apa yang disebut **Lapisan Semantik (Semantic Layer)**. Ini pada dasarnya adalah "Kamus Rahasia" PT TPS yang diselipkan diam-aim ke otak AI setiap kali ia mau berpikir.
Di dalamnya tertulis:
> - "Jalur Domestik" itu nama aslinya 'DOMESTIC' atau 'DOM'.
> - Kata "boxes" itu tidak ada di kolom unit, abaikan saja, gunakan 'TEUs'.
> - Tolong gunakan `ILIKE` agar huruf besar/kecil tidak jadi masalah.

Dengan disuntikkannya kamus ini, AI langsung berhenti berhalusinasi dan bisa mencocokkan niat (*intent*) pengguna dengan realita *database*.

---

## 2. Solusi Kedua: Execution-Guided Self-Healing (Perbaikan Mandiri)
Di sistem biasa, alur kerjanya hanya berjalan lurus. Kalau SQL gagal dijalankan atau hasil tabelnya *kosong (0 baris)*, sistem akan langsung nyerah dan minta maaf ke *user*. Ini sangat menjengkelkan.

Di Milestone 3, kita memanfaatkan arsitektur **LangGraph** untuk membuat sirkuit melingkar (*looping*). Sistem kita ubah dari "Anak Buah yang Mudah Nyerah" menjadi "Problem Solver yang Ngulik".

**Bagaimana Alurnya Bekerja?**
1. Saat fungsi `execute.py` mencoba menjalankan kueri SQL, dia sekaligus berperan sebagai **Mandor**.
2. Kalau SQL-nya salah tulis (*Syntax Error*), si Mandor tidak mengembalikan *error* itu ke pengguna.
3. Kalau SQL-nya berhasil dijalankan tapi hasil tabelnya KOSONG, si Mandor juga curiga: *"Jangan-jangan AI-nya salah ngetik filter kategori?"*
4. Si Mandor lalu meneriaki Agen AI: *"Woi, SQL lu ngasilin data kosong nih! Coba periksa lagi ejaan Glosarium lo, jangan nyerah!"*
5. Melalui fungsi `should_continue` di `graph.py`, arah eksekusi akan dipaksa **PUTAR BALIK** ke node `sql_gen`. AI akan melihat teguran Mandor, menyadari kesalahannya, dan memperbaiki *query*-nya (misal mengubah `LIKE '%domestik%'` menjadi `ILIKE '%DOM%'`).
6. AI diberi kesempatan memperbaiki diri maksimal 3 kali sebelum akhirnya benar-benar menyerah.

**Kesimpulan Milestone 3**: 
Sekarang, jika AI gagal di percobaan pertama, pengguna tidak akan pernah tahu. AI akan memutar otak dan mengoreksi dirinya sendiri dalam hitungan detik di belakang layar, lalu menyajikan data yang benar. Inilah yang membedakan *backend* kita dengan *chatbot* LLM biasa!
