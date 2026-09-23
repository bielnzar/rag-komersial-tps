import sys
import os
import re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from main import check_query_specificity

def is_followup_query(query: str, session_history: list) -> bool:
    """Helper fungsi yang merefleksikan logika deteksi follow-up di chat_endpoint."""
    q_lower = query.lower().strip()
    has_history = bool(session_history and len(session_history) > 0)
    
    has_year = bool(re.search(r'\b20[2-3][0-9]\b', q_lower))
    has_followup_kw = any(kw in q_lower for kw in [
        "bagaimana", "kalau", "siapa", "berapa", "apa", "mana", "coba", "tampilkan", "lihat",
        "tahun", "bulan", "lalu", "sekarang", "kemudian", "berikutnya", "sebelumnya", "tadi",
        "tersebut", "itu", "ini", "yang", "nya", "selain", "lagi",
        "top", "terbesar", "terkecil", "terbanyak", "terendah", "tertinggi", "urutkan", "ranking", "peringkat", "grafik", "chart",
        "domestik", "internasional", "domestic", "international", "export", "import",
        "cma", "ssl", "msk", "msc", "one", "meratus", "spil", "cosco", "evergreen", "oocl", "samudera"
    ])
    
    return has_history and (has_followup_kw or has_year)


def test_specificity_guard_standalone_queries():
    """Menguji pertanyaan mandiri (Turn 1 tanpa riwayat)."""
    # Pertanyaan spesifik harus lolos
    ok, _ = check_query_specificity("Berapa total throughput internasional tahun 2024?")
    assert ok is True

    ok, _ = check_query_specificity("Tampilkan total revenue komersial tahun 2023")
    assert ok is True

    ok, _ = check_query_specificity("Siapa operator dengan market share terbesar?")
    assert ok is True

    # Pertanyaan ambigu tanpa konteks harus ditolak
    ok, guidance = check_query_specificity("kalau 2025?")
    assert ok is False
    assert "Pertanyaan Kurang Spesifik" in guidance

    ok, guidance = check_query_specificity("bagaimana dengan tahun lalu?")
    assert ok is False
    assert "Pertanyaan Kurang Spesifik" in guidance


def test_followup_detection_with_session_history():
    """Menguji pertanyaan lanjutan (Turn 2+ dengan riwayat percakapan aktif)."""
    mock_history = [
        {"role": "user", "content": "Berapa throughput internasional 2024?"},
        {"role": "assistant", "content": "Total throughput 1.500.000 TEUs", "sql": "SELECT SUM(actual) FROM fakta_throughput WHERE year=2024"}
    ]

    # Pertanyaan follow-up harus terdeteksi sebagai follow-up
    assert is_followup_query("bagaimana dengan 2025?", mock_history) is True
    assert is_followup_query("kalau 2023?", mock_history) is True
    assert is_followup_query("siapa nomor 1 nya?", mock_history) is True
    assert is_followup_query("2025", mock_history) is True
    assert is_followup_query("tampilkan grafiknya", mock_history) is True
    assert is_followup_query("urutkan dari yang terbesar", mock_history) is True

    # Greeting / sapaan tidak boleh dianggap sebagai follow-up data
    assert is_followup_query("halo", mock_history) is False
    assert is_followup_query("selamat pagi", mock_history) is False


def test_row_sampling_limit_15():
    """Menguji Smart Row Sampling tepat maksimal 15 baris sampel (Tugas 1.2)."""
    from agents.viz_gen import format_data_compact as viz_format
    from agents.chart_gen import format_data_compact as chart_format

    # Buat dataset simulasi 50 baris
    mock_data = [{"id": i, "operator": f"OP_{i}", "teus": i * 100} for i in range(1, 51)]

    res_viz = viz_format(mock_data)
    lines_viz = res_viz.strip().split("\n")

    # Header + 15 baris data + 1 baris notice = 17 baris
    assert len(lines_viz) == 17
    assert "id,operator,teus" in lines_viz[0]
    assert "1,OP_1,100" in lines_viz[1]
    assert "15,OP_15,1500" in lines_viz[15]
    assert "... (dan 35 baris data lainnya. Total keseluruhan baris: 50)" in lines_viz[16]

    res_chart = chart_format(mock_data)
    lines_chart = res_chart.strip().split("\n")
    # chart_format tidak memiliki notice baris tambahan, hanya header + 15 baris = 16 baris
    assert len(lines_chart) == 16
    assert "15,OP_15,1500" in lines_chart[15]


def test_dynamic_few_shot_prompting():
    """Menguji Dynamic Few-Shot Prompting pada SQL Generator (Tugas 2.2)."""
    from agents.sql_gen import get_few_shot_examples, FEW_SHOT_EXAMPLES

    # 1. Tanpa tabel terpilih -> string kosong (0 token overhead)
    assert get_few_shot_examples(None) == ""
    assert get_few_shot_examples([]) == ""

    # 2. Tabel throughput terpilih -> hanya mengembalikan contoh throughput
    fs_throughput = get_few_shot_examples(["fakta_throughput"])
    assert "fakta_throughput" in fs_throughput
    assert "Contoh Kueri Referensi yang Benar:" in fs_throughput
    assert "fakta_komersial_dashboard" not in fs_throughput
    assert "fakta_market_share" not in fs_throughput

    # 3. Multi-tabel terpilih -> mengembalikan kedua contoh
    fs_multi = get_few_shot_examples(["fakta_throughput", "fakta_komersial_dashboard"])
    assert "fakta_throughput" in fs_multi
    assert "fakta_komersial_dashboard" in fs_multi
    assert "COALESCE(total_all_revenue, total_revenue)" in fs_multi
    assert "fakta_market_share" not in fs_multi

    # 4. Tabel tidak dikenal -> aman tanpa error
    assert get_few_shot_examples(["tabel_tidak_ada"]) == ""


def test_parallel_viz_and_chart_execution(monkeypatch):
    """Menguji Paralelisasi ThreadPoolExecutor untuk Narasi dan ECharts (Tugas 2.1)."""
    import time
    import threading
    from agents.viz_gen import viz_gen_node

    thread_ids = []

    def mock_generate_chart(query, result):
        thread_ids.append(("chart", threading.get_ident()))
        time.sleep(0.1)
        return {"echarts_config": {"title": {"text": "Chart Uji Coba"}}}

    class MockResponse:
        content = "Ini adalah narasi analitis hasil uji coba."

    def mock_invoke_chain(*args, **kwargs):
        thread_ids.append(("narrative", threading.get_ident()))
        time.sleep(0.1)
        return MockResponse()

    monkeypatch.setattr("agents.viz_gen.generate_chart_config", mock_generate_chart)
    monkeypatch.setattr("agents.viz_gen.invoke_chain_with_fallback", mock_invoke_chain)

    state = {
        "user_query": "Tampilkan tren throughput 2024 beserta grafiknya",
        "query_result": [{"tahun": 2024, "teus": 1000}],
        "sql_error": None,
        "force_chart": False
    }

    start_time = time.time()
    result = viz_gen_node(state)
    elapsed = time.time() - start_time

    # Keduanya tidur 0.1 detik. Jika sekuensial: >= 0.2s. Karena paralel ThreadPool: < 0.18s
    assert elapsed < 0.18, f"Waktu eksekusi {elapsed:.3f}s melebihi batas paralel (<0.18s)"
    assert result["echarts_config"] is not None
    assert "Chart Uji Coba" in str(result["echarts_config"])
    assert "Ini adalah narasi analitis" in result["final_answer"]

    # Pastikan thread yang mengeksekusi chart dan narasi keduanya terpanggil
    agent_names = [t[0] for t in thread_ids]
    assert "chart" in agent_names
    assert "narrative" in agent_names


@pytest.mark.anyio
async def test_user_feedback_submission_and_admin_metrics():
    """Menguji Pengiriman Feedback Pengguna dan Rekapitulasi Kepuasan Pengguna di Admin (Tugas 2.3)."""
    from main import submit_feedback, admin_get_feedbacks, FeedbackRequest
    import uuid

    test_session = f"test_session_{uuid.uuid4().hex[:8]}"

    # 1. Kirim feedback THUMBS_UP
    req1 = FeedbackRequest(
        session_id=test_session,
        query="Berapa throughput internasional 2024?",
        sql_executed="SELECT SUM(actual) FROM fakta_throughput WHERE year=2024",
        rating="THUMBS_UP",
        feedback_note=None
    )
    res1 = await submit_feedback(req1, authorization=None)
    assert res1["status"] == "success"

    # 2. Kirim feedback THUMBS_DOWN dengan catatan
    req2 = FeedbackRequest(
        session_id=test_session,
        query="Berapa tarif transhipment?",
        sql_executed="SELECT * FROM fakta_transhipment",
        rating="THUMBS_DOWN",
        feedback_note="Kueri transhipment salah kolom"
    )
    res2 = await submit_feedback(req2, authorization=None)
    assert res2["status"] == "success"

    # 3. Ambil data feedback via mock admin token
    from auth import create_jwt_token
    admin_token = create_jwt_token({"sub": "admin_test", "role": "admin", "name": "Admin Tester"})
    auth_header = f"Bearer {admin_token}"

    res_admin = await admin_get_feedbacks(authorization=auth_header)
    assert res_admin["status"] == "success"
    summary = res_admin["summary"]
    assert summary["total_feedback"] >= 2
    assert summary["thumbs_up"] >= 1
    assert summary["thumbs_down"] >= 1
    assert summary["satisfaction_rate"] > 0

    # Pastikan data yang baru saja dikirim ada di riwayat
    recent_queries = [fb["query"] for fb in res_admin["feedbacks"]]
    assert "Berapa throughput internasional 2024?" in recent_queries
    assert "Berapa tarif transhipment?" in recent_queries


def test_context_aware_suggestions_on_data_empty():
    """Menguji Context-Aware Local Suggestions saat DATA_EMPTY (Tugas 2.4)."""
    from agents.viz_gen import get_context_suggestions, viz_gen_node

    # 1. Deteksi domain Throughput
    sug_tp = get_context_suggestions("Berapa throughput tahun 2018?", ["fakta_throughput"])
    assert len(sug_tp) == 3
    assert any("throughput" in s.lower() for s in sug_tp)

    # 2. Deteksi domain Revenue / Komersial
    sug_rev = get_context_suggestions("Berapa pendapatan PT XYZ tahun 2019?", ["fakta_komersial_dashboard"])
    assert len(sug_rev) == 3
    assert any("pendapatan" in s.lower() or "revenue" in s.lower() for s in sug_rev)

    # 3. Deteksi domain Market Share
    sug_ms = get_context_suggestions("Siapa market share operator anu?", ["fakta_market_share"])
    assert len(sug_ms) == 3
    assert any("market share" in s.lower() for s in sug_ms)

    # 4. Deteksi domain Kapal / Vessel
    sug_vessel = get_context_suggestions("Berapa call kapal kemarin?", ["fakta_vessel"])
    assert len(sug_vessel) == 3
    assert any("kapal" in s.lower() for s in sug_vessel)

    # 5. Uji viz_gen_node saat DATA_EMPTY: harus menyertakan suggestions (0 Token LLM)
    state = {
        "user_query": "Berapa throughput kontainer tahun 2017?",
        "relevant_tables": ["fakta_throughput"],
        "query_result": [],
        "sql_error": "DATA_EMPTY: Kueri DuckDB tidak mengembalikan baris data.",
        "force_chart": False
    }
    result = viz_gen_node(state)
    assert result["echarts_config"] is None
    assert "suggestions" in result
    assert len(result["suggestions"]) == 3
    assert any("throughput" in s.lower() for s in result["suggestions"])


def test_true_semantic_canonical_caching():
    """Menguji True Semantic Caching via Canonical Query Hashing (Tugas 3.1)."""
    from cache import semantic_cache, extract_canonical_descriptor

    # 1. Pasangan variasi kalimat semantik yang harus identik (100% Cache Hit)
    pairs = [
        ("Berapa throughput internasional tahun 2024?", "Throughput internasional di tahun 2024 berapa?"),
        ("Berapa throughput internasional tahun 2024?", "Tolong tampilkan total throughput international untuk tahun 2024 dong"),
        ("Berapa total pendapatan komersial tahun 2023?", "Total revenue komersial 2023 berapa ya?"),
        ("Siapa 5 operator dengan revenue terbesar tahun 2024?", "Top 5 operator revenue tahun 2024"),
        ("Tampilkan tren throughput 2024 beserta grafiknya", "Grafik tren throughput 2024"),
        ("Berapa market share operator CMA tahun 2023?", "Pangsa pasar CMA 2023 berapa?")
    ]

    for q1, q2 in pairs:
        desc1 = extract_canonical_descriptor(q1)
        desc2 = extract_canonical_descriptor(q2)
        key1 = semantic_cache._normalize_key(q1)
        key2 = semantic_cache._normalize_key(q2)
        assert desc1 == desc2, f"Deskriptor tidak cocok: '{q1}' ({desc1}) vs '{q2}' ({desc2})"
        assert key1 == key2, f"Key hash tidak cocok: '{q1}' vs '{q2}'"

    # 2. Uji End-to-End Set dan Get Cache antar variasi kalimat (Gunakan tahun 2099 agar tidak menimpa data riil)
    mock_payload = {
        "status": "success",
        "answer": "Total throughput internasional 2099 adalah 9.999.999 TEUs.",
        "sql_executed": "SELECT SUM(actual) FROM fakta_throughput WHERE year=2099 AND kategori_layanan='INTERNATIONAL'",
        "data": [{"total": 9999999}]
    }

    # Simpan dengan kalimat variasi A
    query_a = "Berapa total throughput internasional tahun 2099?"
    semantic_cache.set(query_a, mock_payload)

    # Ambil dengan kalimat variasi B
    query_b = "Throughput internasional di tahun 2099 berapa?"
    cached_res = semantic_cache.get(query_b)

    assert cached_res is not None, "Cache Miss pada variasi semantik!"
    assert cached_res["answer"] == mock_payload["answer"]
    assert cached_res["sql_executed"] == mock_payload["sql_executed"]

    # Bersihkan data uji mock dari cache store
    canon_test_key = semantic_cache._normalize_key(query_a)
    if canon_test_key in semantic_cache.in_memory_cache:
        del semantic_cache.in_memory_cache[canon_test_key]
        semantic_cache._save_disk_cache()

    # 3. Pastikan kueri dengan parameter berbeda menghasilkan cache key berbeda (No False Collisions)
    key_2023 = semantic_cache._normalize_key("Berapa throughput internasional tahun 2023?")
    key_2024 = semantic_cache._normalize_key("Berapa throughput internasional tahun 2024?")
    key_dom = semantic_cache._normalize_key("Berapa throughput domestik tahun 2024?")

    assert key_2023 != key_2024, "Collision terdeteksi antara tahun 2023 dan 2024!"
    assert key_dom != key_2024, "Collision terdeteksi antara domestik dan internasional!"


def test_column_level_schema_pruning():
    """Menguji Column-Level Schema Pruning pada tabel lebar > 20 kolom (TUGAS 3.2)."""
    from agents.sql_gen import prune_columns, get_duckdb_schema

    # 1. Tabel kecil (<= 20 kolom) tidak dipangkas
    small_cols = ["year", "month", "description", "unit", "actual", "budget", "kategori_layanan"]
    assert prune_columns("fakta_throughput", small_cols, "Berapa throughput 2024?") == small_cols

    # 2. Tabel lebar fakta_market_share (54 kolom)
    wide_cols = [
        'tanggal', 'year', 'month', 'lop', 'teus', 'persentase', 'sumber_sheet', 'tahun', 'description', 'unit',
        '2022_actual', '2022_budget', '2022_actual_vs_2022_budget',
        '2023_actual', '2023_budget', '2023_actual_vs_2023_budget',
        '2024_actual', '2024_budget', '2024_actual_vs_2024_actual_budget',
        '2025_actual', '2025_budget', '2025_actual_vs_2025_budget',
        '2026_actual', '2026_budget', '2026_actual_vs_2026_budget',
        'date', 'category', 'box', 'dpp', 'bch', 'bsh', 'average_cd',
        'teus_2023', 'box_2023', 'dpp_2023', 'bch_2023', 'bsh_2023', 'average_cd_2023',
        'tahun_kategori', 'total_teus', 'no', 'service', 'routes', 'city_port',
        'service_mode', 'total_call', 'bmph', 'gmph', 'boxes', 'boxes_teus',
        'on', 'moves', 'moves_teus', 'status'
    ]
    assert len(wide_cols) == 54

    # Uji pruning saat pertanyaan user spesifik tahun 2023 & market share
    q_2023 = "Siapa 3 operator dengan volume market share terbesar tahun 2023?"
    pruned = prune_columns("fakta_market_share", wide_cols, q_2023)

    # Verifikasi penghematan token: kolom terpangkas dari 54 menjadi <= 25 kolom
    assert len(pruned) <= 25, f"Kolom hasil pruning masih terlalu banyak: {len(pruned)}"
    assert len(pruned) < len(wide_cols) / 2, "Pengurangan kolom harus lebih dari 50%"

    # Verifikasi kolom wajib dan kolom relevan tetap ada
    assert "lop" in pruned
    assert "tahun_kategori" in pruned
    assert "total_teus" in pruned
    assert "persentase" in pruned
    assert "2023_actual" in pruned

    # Verifikasi kolom tahun lain yang tidak relevan berhasil dibuang
    assert "2022_actual" not in pruned
    assert "2024_actual" not in pruned
    assert "2025_actual" not in pruned
    assert "2026_actual" not in pruned

    # 3. Uji integrasi get_duckdb_schema dengan user_query
    schema_pruned = get_duckdb_schema(["fakta_market_share"], user_query=q_2023)
    schema_full = get_duckdb_schema(["fakta_market_share"], user_query="")

    assert len(schema_pruned.splitlines()) < len(schema_full.splitlines())
    assert "2023_actual" in schema_pruned
    assert "2025_actual" not in schema_pruned


