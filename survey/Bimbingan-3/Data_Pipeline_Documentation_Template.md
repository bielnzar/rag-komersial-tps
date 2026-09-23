# DATA PIPELINE DOCUMENTATION
## Pemetaan Data Raw → Bronze → Silver → Gold → DuckDB

**Proyek:** Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ  
**Status:** Master Documentation / Living Document  
**Tujuan:** Dokumentasi teknis dan akademik proses pengolahan data dari data mentah hingga data siap analitik.

> **Catatan penting mengenai kerahasiaan data**
>
> Pada tahap dokumentasi ini, seluruh data digunakan sebagaimana kondisi aktual untuk kebutuhan pengembangan dan eksperimen. Identitas perusahaan ditulis sebagai **PT XYZ**. Belum ada keputusan final mengenai masking terhadap atribut sensitif lainnya; batas penggunaan dan publikasi data masih menunggu konfirmasi pihak yang berwenang. Jangan mengubah nilai data hanya untuk keperluan dokumentasi sebelum batas masking tersebut ditetapkan.

---

# 1. Tujuan Dokumentasi

Dokumentasi ini dibuat untuk menjelaskan secara terstruktur perjalanan data dari sumber mentah hingga menjadi data matang yang digunakan sebagai sumber analitik bagi sistem Multi-Agent Text-to-SQL.

Dokumentasi harus menjawab pertanyaan berikut:

1. Dari mana data berasal?
2. Bagaimana karakteristik data mentah?
3. Apa yang terjadi pada data pada setiap layer Medallion?
4. Transformasi apa saja yang dilakukan?
5. Mengapa setiap transformasi diperlukan?
6. Seperti apa bentuk data sebelum dan sesudah transformasi?
7. Bagaimana data Gold dimaterialisasikan ke DuckDB?
8. Bagaimana data tersebut digunakan oleh asisten analitik?
9. Informasi apa yang berpotensi sensitif dan bagaimana status penanganannya?

---

# 2. Lingkup Dokumentasi

Dokumentasi mencakup:

- Data mentah (Raw)
- Bronze Layer
- Silver Layer
- Gold Layer
- Materialisasi dan penyimpanan pada DuckDB
- Transformasi data yang benar-benar diimplementasikan
- Contoh Before–After
- Pemetaan tabel Gold/DuckDB
- Keterkaitan data dengan Multi-Agent Text-to-SQL
- Status kerahasiaan data
- Artefak dan bukti implementasi

Dokumentasi **tidak** boleh mengklaim fitur, proses, atau transformasi yang tidak ditemukan pada implementasi aktual.

---

# 3. Ringkasan Arsitektur Data

## 3.1 Data Lineage

> **RAW → BRONZE → SILVER → GOLD → DUCKDB → MULTI-AGENT TEXT-TO-SQL**

[ANTIGRAVITY: buat/isi diagram atau deskripsi data lineage berdasarkan implementasi aktual.]

## 3.2 Ringkasan Setiap Layer

| Layer | Input | Proses Utama | Output | Bukti Implementasi |
|---|---|---|---|---|
| Raw | [isi] | [isi] | [isi] | [isi] |
| Bronze | [isi] | [isi] | [isi] | [isi] |
| Silver | [isi] | [isi] | [isi] | [isi] |
| Gold | [isi] | [isi] | [isi] | [isi] |
| DuckDB | [isi] | [isi] | [isi] | [isi] |

---

# 4. Audit Data Mentah (Raw Data)

## 4.1 Sumber Data Mentah

[ANTIGRAVITY: inventarisasi seluruh sumber data mentah yang benar-benar digunakan. Sertakan format, lokasi, jumlah file/sheet bila relevan, tetapi bedakan antara kondisi aktual saat audit dan angka yang menjadi bagian tetap dari metodologi.]

| No. | Sumber/File | Format | Sheet/Tabel | Lokasi | Status Verifikasi |
|---:|---|---|---|---|---|
| 1 | [isi] | [isi] | [isi] | [isi] | [VERIFIED/...] |

## 4.2 Karakteristik Struktur Data Mentah

[ANTIGRAVITY: jelaskan bentuk data mentah berdasarkan pemeriksaan aktual. Sertakan contoh struktur/kolom, heterogenitas, format wide/long, master data yang menyatu dengan transaksi, form response, atau karakteristik lain yang benar-benar ditemukan.]

## 4.3 Permasalahan Data Mentah yang Terverifikasi

| No. | Permasalahan | Contoh Aktual | Dampak terhadap Pengolahan | Bukti File/Code |
|---:|---|---|---|---|
| 1 | [isi] | [isi] | [isi] | [isi] |

> Hanya masukkan permasalahan yang benar-benar ditemukan pada data/source code.

---

# 5. Pemetaan RAW → BRONZE

## 5.1 Input

[ANTIGRAVITY: jelaskan file/sumber yang dibaca.]

## 5.2 Proses

[ANTIGRAVITY: jelaskan proses ingest/extraction, termasuk library/function yang digunakan.]

## 5.3 Perlakuan terhadap Data

[ANTIGRAVITY: jelaskan apakah nilai data diubah, dibuang, atau dipertahankan apa adanya pada tahap ini.]

## 5.4 Output

[ANTIGRAVITY: jelaskan bentuk output in-memory dan/atau checkpoint fisik.]

## 5.5 Bukti Implementasi

| Komponen | Bukti |
|---|---|
| Script/File | [isi] |
| Function | [isi] |
| Artefak Output | [isi] |

---

# 6. Pemetaan BRONZE → SILVER

## 6.1 Input

[ANTIGRAVITY: isi.]

## 6.2 Transformasi

[ANTIGRAVITY: dokumentasikan seluruh cleaning dan standardisasi yang benar-benar dilakukan.]

| No. | Transformasi | Before | After | Alasan | Bukti Code |
|---:|---|---|---|---|---|
| 1 | [isi] | [isi] | [isi] | [isi] | [isi] |

## 6.3 Output

[ANTIGRAVITY: isi struktur/output Silver.]

---

# 7. Pemetaan SILVER → GOLD

## 7.1 Input

[ANTIGRAVITY: isi.]

## 7.2 Transformasi

[ANTIGRAVITY: dokumentasikan restrukturisasi, filtering, standardisasi kategori, snake_case, metadata tagging, dan transformasi lain yang benar-benar ada.]

| No. | Transformasi | Before | After | Alasan | Bukti Code |
|---:|---|---|---|---|---|
| 1 | [isi] | [isi] | [isi] | [isi] | [isi] |

## 7.3 Output

[ANTIGRAVITY: isi bentuk output Gold.]

---

# 8. Pemetaan GOLD → DUCKDB

## 8.1 Konsolidasi Data

[ANTIGRAVITY: jelaskan proses penggabungan dataframe, penentuan tabel target, dan transformasi tambahan setelah Gold sebelum materialisasi fisik.]

## 8.2 Pembuatan Tabel DuckDB

[ANTIGRAVITY: jelaskan proses materialisasi tabel fisik dan konfigurasi read-only yang digunakan sistem analitik jika memang terverifikasi.]

## 8.3 Post-Processing DuckDB

| No. | Post-Processing | Tujuan | Bukti Code |
|---:|---|---|---|
| 1 | [isi] | [isi] | [isi] |

---

# 9. Katalog Transformasi Data Terverifikasi

Bagian ini menjadi katalog utama transformasi. Setiap item harus mempunyai bukti implementasi.

| ID | Transformasi | Layer | File/Sheet | Before | After | Dampak Analitik | Code Reference | Verification |
|---|---|---|---|---|---|---|---|---|
| T01 | [isi] | [isi] | [isi] | [isi] | [isi] | [isi] | [isi] | VERIFIED |

## 9.1 Contoh 1 — Transformasi Paling Representatif

[ANTIGRAVITY: pilih satu kasus yang paling representatif untuk bimbingan, lalu dokumentasikan lengkap dari Raw/Bronze sampai Gold/DuckDB.]

### Before

[Isi screenshot/tabel/contoh struktur.]

### Proses

[Isi transformasi secara berurutan.]

### After

[Isi screenshot/tabel/contoh struktur.]

### Alasan Transformasi

[Isi alasan teknis/analitik berdasarkan implementasi aktual.]

---

# 10. Contoh Before–After

## 10.1 Contoh A — [Nama Transformasi]

**Sumber:** [isi]  
**Layer:** [isi]

### Before

```text
[isi]
```

### After

```text
[isi]
```

### Penjelasan

[isi]

## 10.2 Contoh B — [Nama Transformasi]

[isi]

## 10.3 Contoh C — [Nama Transformasi]

[isi]

> Jangan tampilkan nilai sensitif perusahaan pada bagian ini sebelum batas publikasinya disetujui. Gunakan struktur/placeholder bila diperlukan.

---

# 11. Spesifikasi Data Gold dan DuckDB

## 11.1 Ringkasan Tabel

| No. | Nama Tabel | Fungsi Bisnis | Baris | Kolom | Kolom Utama |
|---:|---|---|---:|---:|---|
| 1 | [isi] | [isi] | [isi] | [isi] | [isi] |

## 11.2 Data Dictionary Ringkas

| Tabel | Kolom | Tipe Data | Makna/Definisi | Dimensi/Metrik | Sensitivitas | Catatan |
|---|---|---|---|---|---|---|
| [isi] | [isi] | [isi] | [isi] | [isi] | [isi] | [isi] |

[ANTIGRAVITY: isi hanya berdasarkan struktur DuckDB/metadata aktual. Jangan mengarang definisi bisnis yang tidak ditemukan.]

---

# 12. Keterkaitan Data Gold dengan Multi-Agent Text-to-SQL

## 12.1 Router

[ANTIGRAVITY: jelaskan bagaimana katalog/tabel Gold digunakan Router untuk memilih data yang relevan, berdasarkan implementasi aktual.]

## 12.2 Schema Linking / Schema Pruning

[ANTIGRAVITY: jelaskan bagaimana tabel/kolom yang relevan dipilih sebelum SQL Generator.]

## 12.3 SQL Generator

[ANTIGRAVITY: jelaskan bagaimana schema Gold/DuckDB diberikan ke SQL Generator.]

## 12.4 Execution

[ANTIGRAVITY: jelaskan bagaimana SQL dieksekusi pada DuckDB.]

---

# 13. Analisis Kerahasiaan Data

> **Status saat ini:** Batas penggunaan/publikasi data selain anonimisasi nama perusahaan belum difinalkan.

## 13.1 Atribut yang Berpotensi Sensitif

| Kategori | Atribut/File/Tabel | Potensi Risiko | Status Saat Ini | Tindakan Final |
|---|---|---|---|---|
| [isi] | [isi] | [isi] | BELUM DIFINALKAN | Menunggu konfirmasi |

## 13.2 Perlakuan Saat Ini

Saat ini:

- Nama perusahaan ditulis sebagai **PT XYZ**.
- Nilai dan atribut data lainnya **belum diubah** hanya untuk kebutuhan anonimisasi.
- Keputusan masking tambahan menunggu konfirmasi pihak yang berwenang.

## 13.3 Hal yang Tidak Boleh Masuk Dokumentasi Publik Sebelum Disetujui

[ANTIGRAVITY: identifikasi atribut yang terdeteksi sensitif, tetapi jangan menyalin nilai rahasianya.]

---

# 14. Artefak dan Bukti Implementasi

## 14.1 Artefak yang Tersedia

| Artefak | Lokasi | Status | Kegunaan untuk Bimbingan |
|---|---|---|---|
| Data Raw | [isi] | [isi] | [isi] |
| Bronze Checkpoint | [isi] | [isi] | [isi] |
| Silver Checkpoint | [isi] | [isi] | [isi] |
| Gold Checkpoint | [isi] | [isi] | [isi] |
| DuckDB | [isi] | [isi] | [isi] |
| Source Code ETL | [isi] | [isi] | [isi] |
| Log ETL | [isi] | [isi] | [isi] |

## 14.2 Artefak yang Belum Tersedia

| Artefak | Status | Prioritas | Tindak Lanjut |
|---|---|---|---|
| Data Dictionary Terpadu | [isi] | [isi] | [isi] |
| Diagram Data Lineage | [isi] | [isi] | [isi] |
| Sampel Side-by-Side Raw→Gold | [isi] | [isi] | [isi] |
| Script/Prosedur Masking Publikasi | [isi] | [isi] | [isi] |

---

# 15. Paket Bahan untuk Bimbingan Dosen

## 15.1 Bahan Utama yang Ditampilkan

1. Contoh data mentah.
2. Contoh Bronze.
3. Contoh Silver.
4. Contoh Gold.
5. Contoh tabel DuckDB.
6. Satu contoh lengkap Before–After transformasi.
7. Diagram Raw → Bronze → Silver → Gold → DuckDB.
8. Catatan mengenai status kerahasiaan data.

## 15.2 Contoh Kasus Utama

[ANTIGRAVITY: pilih contoh yang paling informatif dan paling aman ditampilkan untuk bimbingan.]

**Kasus:** [isi]

**Alasan dipilih:** [isi]

## 15.3 Pertanyaan yang Perlu Dikonfirmasi kepada Dosen / Pihak Berwenang

1. Apakah anonimisasi **PT XYZ** sudah cukup untuk penyebutan perusahaan dalam dokumen akademik?
2. Atribut apa saja yang wajib dimasking atau dianonimkan sebelum dimasukkan ke skripsi/lampiran?
3. Apakah contoh data operasional boleh ditampilkan dalam bentuk nilai asli, atau harus disamarkan?
4. Apakah data hasil transformasi Gold/DuckDB boleh ditampilkan dalam skripsi?
5. Apakah terdapat batasan terhadap publikasi nama pelanggan/operator, nominal, nomor dokumen, atau atribut lain?

---

# 16. Matriks Verifikasi Akhir

| Komponen | Status | Bukti | Catatan |
|---|---|---|---|
| Sumber Raw teridentifikasi | [VERIFIED/...] | [isi] | [isi] |
| Bronze terverifikasi | [VERIFIED/...] | [isi] | [isi] |
| Silver terverifikasi | [VERIFIED/...] | [isi] | [isi] |
| Gold terverifikasi | [VERIFIED/...] | [isi] | [isi] |
| DuckDB terverifikasi | [VERIFIED/...] | [isi] | [isi] |
| Transformasi teridentifikasi | [VERIFIED/...] | [isi] | [isi] |
| Before–After tersedia | [VERIFIED/...] | [isi] | [isi] |
| Status kerahasiaan teridentifikasi | [VERIFIED/...] | [isi] | [isi] |
| Artefak bimbingan tersedia | [VERIFIED/...] | [isi] | [isi] |

---

# 17. Catatan Audit

## 17.1 Temuan Terverifikasi

[ANTIGRAVITY: isi fakta yang benar-benar diverifikasi dari source code dan artefak.]

## 17.2 Temuan yang Belum Dapat Diverifikasi

[ANTIGRAVITY: isi.]

## 17.3 Asumsi / Interpretasi

[ANTIGRAVITY: isi hanya jika memang diperlukan, dan tandai jelas sebagai interpretasi.]

---

# 18. Riwayat Perubahan Dokumen

| Versi | Tanggal | Perubahan | Sumber |
|---|---|---|---|
| 0.1 | [tanggal] | Template dibuat | Tim penelitian |
| 0.2 | [tanggal] | [isi] | [isi] |

---

# Lampiran A — Pemetaan File/Sumber ke Tabel Gold

[ANTIGRAVITY: buat tabel lineage source → sheet → transformer → Gold → DuckDB table.]

| Source File | Sheet | Transformer/Process | Gold Artifact | DuckDB Table |
|---|---|---|---|---|
| [isi] | [isi] | [isi] | [isi] | [isi] |

# Lampiran B — Referensi Code

[ANTIGRAVITY: daftar file/function/class penting yang terkait dengan ETL.]

| File | Function/Class | Peran |
|---|---|---|
| [isi] | [isi] | [isi] |

# Lampiran C — Sampel Struktur Data

> Gunakan contoh struktur atau data yang sudah disetujui untuk ditampilkan. Jangan memasukkan kredensial atau nilai sensitif yang belum mendapat izin publikasi.

[ANTIGRAVITY: isi seperlunya.]
