# 15. Paket Bahan untuk Bimbingan Dosen

## 15.1 Bahan Utama yang Ditampilkan

1. **Contoh Data Mentah:** File `Market Share.xlsx` sheet `B.OPR INT` (menunjukkan bentuk laporan horizontal wide).
2. **Contoh Bronze:** Berkas `bronze_Market Share.xlsx_B.OPR INT.csv` (kondisi data mentah saat diekstrak ke CSV).
3. **Contoh Silver:** Berkas `silver_Market Share.xlsx_B.OPR INT.csv` (kondisi data pasca-pembersihan spasi dan simbol).
4. **Contoh Gold:** Berkas `gold_Market Share.xlsx_B.OPR INT.csv` (hasil unpivot menjadi 2.935 baris long data).
5. **Contoh Tabel DuckDB:** Hasil kueri SQL pada tabel `fakta_market_share` di terminal atau Admin Dashboard.
6. **Satu Contoh Lengkap Before–After:** Kasus unpivot data pangsa pasar dan pemulihan tahun rusak pada kapal.
7. **Diagram Alur Medallion:** Diagram alur data dari Raw $\rightarrow$ Bronze $\rightarrow$ Silver $\rightarrow$ Gold $\rightarrow$ DuckDB.
8. **Catatan Kerahasiaan Data:** Usulan rencana masking data sensitif untuk publikasi skripsi.

## 15.2 Contoh Kasus Utama

- **Kasus Dipilih:** Transformasi Sheet `B.OPR INT` (`Market Share.xlsx`) via teknik _Unpivot Data (pd.melt)_.
- **Alasan Dipilih:** Kasus ini paling representatif secara akademik karena mendemonstrasikan bagaimana data laporan horizontal non-standar (yang sulit diproses oleh database relasional dan LLM) berhasil ditransformasikan secara elegan menjadi struktur data relasional normal (_tidy data_) sehingga dapat dikueri secara efisien oleh query Text-to-SQL.

## 15.3 Pertanyaan yang Perlu Dikonfirmasi kepada Dosen / Pihak Berwenang

1. Apakah penyebutan identitas perusahaan sebagai **PT XYZ** sudah memadai untuk seluruh dokumen skripsi dan artikel ilmiah?
2. Apakah nama operator pelayaran internasional (seperti CMA, Maersk, Evergreen) boleh ditampilkan secara terbuka, atau wajib disamarkan menjadi Operator L1, L2, dst.?
3. Bagaimana mekanisme masking yang disetujui untuk data pendapatan finansial (apakah diperbolehkan menggunakan metode _scaling factor_ / faktor pengali acak agar korelasi data tetap valid)?
4. Apakah tabel restitusi dan diskon (`fakta_rest_n_disc`) diperkenankan masuk ke dalam naskah skripsi setelah seluruh nama perusahaan dan nomor suratnya dianonimkan?
5. Apakah artefak checkpoint CSV pada layer Bronze, Silver, dan Gold perlu disertakan sebagai lampiran digital (_Google Drive repository_) skripsi?

---
