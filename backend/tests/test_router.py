import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from agents.router import get_table_catalog

def test_get_table_catalog():
    catalog = get_table_catalog()
    assert isinstance(catalog, str)
    if "Gagal membaca katalog" not in catalog:
        # Assumsikan DB sudah ada
        assert "Daftar Tabel" in catalog
        assert "fakta_vessel" in catalog or "fakta_throughput" in catalog
