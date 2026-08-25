import pandas as pd

# Ganti dengan nama file Excel kamu
path_data = "csv" 
pen_namaan = "Market Share"
nama_file_excel = f"{pen_namaan}.xlsx" 
nama_file_csv = f"{path_data}/{pen_namaan}.csv"

try:
    print(f"⏳ Sedang membaca {nama_file_excel}...")
    semua_sheet = pd.read_excel(nama_file_excel, sheet_name=None)
    
    daftar_skema = []
    
    # Looping ke semua sheet untuk mengambil metadata
    for nama_sheet, df in semua_sheet.items():
        for kolom, tipe in df.dtypes.items():
            daftar_skema.append({
                "Nama Sheet": nama_sheet,
                "Nama Kolom": kolom,
                "Tipe Data": str(tipe)
            })
            
    # Simpan hasil ekstraksi ke CSV
    df_skema = pd.DataFrame(daftar_skema)
    df_skema.to_csv(nama_file_csv, index=False)
    
    print(f"✅ Berhasil! Skema telah diekspor ke '{nama_file_csv}'")

except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")