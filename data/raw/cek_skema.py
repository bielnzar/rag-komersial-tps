import os
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
CSV_OUT_DIR = RAW_DIR / "csv"

os.makedirs(CSV_OUT_DIR, exist_ok=True)

SISA_FILES = [
    "Transhipment.xlsx",
    "VESSEL SERVICE.xlsx",
    "Komersial Dashboard.xlsx",
    "Realisasi UC.xlsx",
    "OVERVIEW BOX.xlsx",
    "RestNDisc.xlsx"
]

print("==================================================")
print("   INSPEKSI SKEMA & KONVERSI 6 FILE EXCEL SISA    ")
print("==================================================")

for file_name in SISA_FILES:
    file_path = RAW_DIR / file_name
    if not file_path.exists():
        print(f"⚠️ File tidak ditemukan: {file_name}")
        continue

    print(f"\n📂 MEMBEDAH FILE: {file_name}")
    try:
        excel_file = pd.read_excel(file_path, sheet_name=None)
        for sheet_name, df in excel_file.items():
            clean_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_', '-')).strip()
            out_csv_name = f"{file_name.replace('.xlsx', '')}_{clean_sheet_name}.csv"
            out_csv_path = CSV_OUT_DIR / out_csv_name
            
            # Simpan 100 baris pertama sebagai CSV preview agar cepat dan mudah dibaca
            df.head(100).to_csv(out_csv_path, index=False)
            
            print(f"  📄 Sheet: '{sheet_name}' | Ukuran: {df.shape[0]} baris x {df.shape[1]} kolom")
            print(f"     Sub-kolom: {list(df.columns[:8])}{'...' if len(df.columns) > 8 else ''}")
            print(f"     💾 Preview CSV tersimpan di: data/raw/csv/{out_csv_name}")

    except Exception as e:
        print(f"  ❌ Error membaca {file_name}: {e}")

print("\n==================================================")
print("🎉 INSPEKSI SELESAI! CSV Preview tersimpan di data/raw/csv/")
print("==================================================")