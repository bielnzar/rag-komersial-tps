import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
from etl.transformers import _normalisasi_nama_sheet, proses_throughput
from etl.utils import hapus_kolom_hantu, paksa_angka

def test_normalisasi_kategori():
    assert _normalisasi_nama_sheet("Domestik") == "DOMESTIC"
    assert _normalisasi_nama_sheet("DOMESTIK") == "DOMESTIC"
    assert _normalisasi_nama_sheet("Internasional") == "INTERNATIONAL"
    assert _normalisasi_nama_sheet("INTERNATIONAL") == "INTERNATIONAL"
    assert _normalisasi_nama_sheet("RandomSheet") == "RANDOMSHEET"

def test_paksa_angka():
    df = pd.DataFrame({"TEUS": ["1,000.5", "2,000", "-", "abc", 500]})
    df_clean = paksa_angka(df, ["TEUS"])
    
    assert df_clean["TEUS"].iloc[0] == 1000.5
    assert df_clean["TEUS"].iloc[1] == 2000.0
    assert df_clean["TEUS"].iloc[2] == 0.0 # - becomes 0
    assert df_clean["TEUS"].iloc[3] == 0.0 # error coerced to 0
    assert df_clean["TEUS"].iloc[4] == 500.0

def test_hapus_kolom_hantu():
    df = pd.DataFrame({
        "Unnamed: 0": [1, 2, 3],
        "ValidCol": [4, 5, 6],
        "EmptyCol": [None, None, None]
    })
    df_clean = hapus_kolom_hantu(df)
    
    assert "Unnamed: 0" not in df_clean.columns
    assert "EmptyCol" not in df_clean.columns
    assert "ValidCol" in df_clean.columns
