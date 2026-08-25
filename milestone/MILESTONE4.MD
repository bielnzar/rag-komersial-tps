# Milestone 4: Analitik & Visualisasi Data ECharts

Di Milestone 1 sampai 3, sistem kita sudah cerdas luar biasa. Data mengalir bersih, AI tahu semua tentang pelabuhan, dan ia bisa memperbaiki kesalahannya sendiri. Namun, dari segi *Output* (hasil akhir), ia masih punya satu kelemahan: ia hanya merespons menggunakan **kata-kata** (teks narasi murni). 

Di dunia nyata, jajaran manajerial pelabuhan membutuhkan grafik untuk melihat tren! **Milestone 4** didedikasikan untuk menyuntikkan jiwa "Seniman Visual" (Frontend Engineer) ke dalam AI kita.

---

## 1. Tantangan: AI vs Format Grafik
Kita ingin agar aplikasi *Dashboard* nanti bisa merender grafik cantik menggunakan pustaka (library) **Apache ECharts**. Syarat utamanya: ECharts butuh pengaturan (*config*) dalam format **JSON yang sangat ketat**.

Masalahnya, LLM (Gemini) punya kebiasaan ngobrol bebas (contoh: *"Ini adalah json-nya ya kak: ```json ... ```"*). Jika teks sapaan bebas ini dikirim ke *Dashboard*, aplikasi kita pasti *crash* karena format JSON-nya rusak/tercampur.

---

## 2. Solusi: Membungkam AI dengan Pydantic Structured Output
Untuk menyelesaikan masalah tersebut, kita memaksa Agen Visualisasi (`viz_gen.py`) untuk mematuhi satu hukum mutlak menggunakan teknologi **Pydantic Structured Output** dari LangChain.

AI tidak lagi diizinkan merespons dengan teks bebas. Kita membuatkan cetakan pakem (skema `VizOutput`):
```python
class VizOutput(BaseModel):
    answer: str
    echarts_config: dict
```

AI (Gemini 3.6 Flash) dipaksa untuk "mengisi formulir" JSON ini. 
1. Jika pengguna bertanya soal perbandingan per bulan, AI akan mengisi kolom `echarts_config` dengan kode pembuat *Bar Chart* murni.
2. Jika pengguna hanya bertanya soal satu angka tunggal yang mustahil dijadikan grafik, AI dengan pintar akan membiarkan kolom `echarts_config` tersebut KOSONG (`{}`).

---

## 3. Eksekusi API di main.py
Hasil akhir racikan AI tersebut dilempar keluar lewat `main.py` sehingga *response* aplikasi berubah dari yang awalnya polos, menjadi seperti ini:

```json
{
  "status": "success",
  "answer": "Berdasarkan data, capaian Januari adalah...",
  "chart_config": {
      "xAxis": { "data": ["Januari", "Februari"] },
      "series": [ { "type": "bar", "data": [1000, 2000] } ]
  },
  "sql_executed": "SELECT ..."
}
```

**Kesimpulan Milestone 4**: 
*Backend* kita kini resmi bukan hanya menyajikan kalimat analisis, tapi juga menyediakan kerangka diagram yang siap pakai (*plug-and-play*). Ini menjadi karpet merah yang sempurna bagi developer Frontend untuk merender *dashboard* super interaktif di **Milestone 5**.
