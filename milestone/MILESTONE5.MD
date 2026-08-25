# Milestone 5: Frontend UI/UX (Vue 3 & ECharts)

Milestone ini merupakan mahkota (puncak) dari proyek kita. Di sinilah tempat di mana teknologi AI *backend* yang luar biasa rumit dibalut menjadi antarmuka yang sangat elegan, interaktif, dan mudah digunakan oleh eksekutif bisnis sekalipun.

---

## 1. Tantangan: Infrastruktur Tertutup (Closed Environment)
Di lingkungan korporat/Enterprise tingkat tinggi (seperti sistem *sandbox* internal tempat *server* kita beroperasi), akses internet ke repositori global seperti NPM (`registry.npmjs.org`) seringkali diblokir demi keamanan. 

Hal ini mengakibatkan pendekatan "instalasi normal" (`npm install vue tailwindcss`) gagal total.

**Solusinya:** Kita mem- *bypass* batasan *server* ini dengan memanfaatkan teknologi **CDN (Content Delivery Network)** murni pada arsitektur HTML Statis. Semua pustaka akan diunduh secara *on-the-fly* oleh peramban pengguna (browser eksekutif), bukan oleh mesin server kita.

---

## 2. Arsitektur Komponen (Tanpa Build System)
Kita menggunakan **Vue 3 Global Build (Composition API)** tanpa memerlukan kompilasi Node.js (seperti Vite/Webpack). Semuanya hidup bahagia di dalam dua file utama:

### 📄 `index.html` (Kerangka Visual)
- Mengimpor skrip sakti dari CDN (Vue, Axios, Tailwind, ECharts, Marked).
- Disuntik dengan *Tailwind Configuration* khusus. Warna yang digunakan merupakan perpaduan **Midnight Blue** (`#0A192F`) khas *dashboard* analitik tingkat dewa, dipadu aksen **TPS Cyan** (`#64FFDA`) untuk memberikan kesan elegan nan presisi.
- Mengandung struktur DOM (*chat container*, pesan masuk, dan *text area*). 

### 📄 `app.js` (Otak Interaksi)
- **State Management**: Menyimpan memori obrolan (`messages`) dan status (*loading/typing*).
- **Pemanggilan API (Axios)**: Bertugas berteriak (menembak POST *request*) ke pelabuhan *backend* kita di `http://127.0.0.1:8000/api/v1/chat`.
- **ECharts Engine**: Ini adalah bagian paling memukau. Setiap kali AI merespons dengan JSON `chart_config`, `app.js` akan mencegat JSON tersebut, menyuntikkan *background* transparan agar grafiknya terlihat menyatu, lalu me- *render* animasi grafik (Bar, Pie, atau Line chart) tepat di bawah teks jawaban AI.

---

## 3. Sistem Jembatan: CORS Middleware
Agar gerbang FastAPI di *backend* (`main.py`) mau menerima surat dari HTML *frontend* ini, kita harus menambahkan "paspor" yang dinamakan **CORS (Cross-Origin Resource Sharing)**.

Tanpa *middleware* ini, peramban (Chrome/Edge) akan menolak menghubungkan *Frontend* (Port 3000) ke *Backend* (Port 8000) karena dianggap sebagai "serangan peretas dari domain asing". Kita membukakan pintunya dengan aturan `allow_origins=["*"]` agar aliran datanya lancar.

**Kesimpulan Akhir Proyek (Milestone 1-5)**: 
Kini kita memiliki sistem RAG (Retrieval-Augmented Generation) berbasis *Text-to-SQL* yang sepenuhnya otonom. Ia membersihkan datanya sendiri (ETL), memahami glosarium perusahaannya sendiri, memperbaiki kesalahannya sendiri, melukis grafiknya sendiri, dan menyajikannya dalam balutan antarmuka kelas dunia. Sempurna!
