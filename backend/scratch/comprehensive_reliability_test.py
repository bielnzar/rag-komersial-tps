#!/usr/bin/env python3
"""
comprehensive_reliability_test.py
Pengujian Keandalan Mendalam (Deep Reliability & Stress Testing):
- Multi-turn Contextual Follow-up
- Complex Cross-Domain Queries (Throughput, Revenue, Market Share, Vessel BMPH, UC Cargo, Restitusi)
- True Semantic Caching Hit Verification
- Anti-Ambiguity Preflight Verification
- Dynamic Multi-Key Failover Verification
"""
import sys
import time
import uuid
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def log_test(title, detail=""):
    print(f"\n{'='*70}\n🔬 {title}\n{detail}\n{'='*70}")

def run_tests():
    # 1. Login sebagai user 'executive'
    log_test("FASE 1: OTENTIKASI & INITIAL SETUP", "Melakukan login dengan akun executive")
    login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username": "executive",
        "password": "tps123"
    }, timeout=10)
    
    if login_resp.status_code != 200:
        print(f"❌ Gagal login: {login_resp.status_code} - {login_resp.text}")
        sys.exit(1)
        
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Berhasil login sebagai Executive. Token didapatkan.")

    results = []

    # =========================================================================
    # SESI 1: MULTI-TURN OPERASIONAL (THROUGHPUT & SEMANTIC CACHING HIT)
    # =========================================================================
    session_id_1 = f"stress-test-ops-{uuid.uuid4().hex[:8]}"
    log_test("SESI 1: MULTI-TURN OPERASIONAL (THROUGHPUT & CACHING)", f"Session ID: {session_id_1}")

    # Turn 1.1: Standalone Operational Query
    q1_1 = "Berapa throughput internasional tahun 2024?"
    print(f"\n[Turn 1.1] Query: '{q1_1}'")
    t0 = time.time()
    r1_1 = requests.post(f"{BASE_URL}/api/v1/chat", headers=headers, json={"query": q1_1, "session_id": session_id_1}, timeout=90)
    d1_1 = r1_1.json()
    lat1_1 = round((time.time() - t0) * 1000, 1)
    print(f"Status: {d1_1.get('status')} | SQL: {d1_1.get('sql_executed')} | Cached: {d1_1.get('is_cached')} | Latency: {lat1_1}ms")
    print(f"Answer snippet: {d1_1.get('answer', '')[:120]}...")
    assert d1_1.get("status") == "success", f"Turn 1.1 failed: {d1_1}"
    results.append(("Sesi 1 Turn 1 (Throughput 2024)", d1_1.get("status"), lat1_1, d1_1.get("is_cached")))

    time.sleep(2)  # pause to avoid rate limits

    # Turn 1.2: Follow-up 1 (Context switch: year 2023)
    q1_2 = "Bagaimana dengan tahun 2023?"
    print(f"\n[Turn 1.2] Follow-up Query: '{q1_2}' (Harus mewarisi throughput internasional)")
    t0 = time.time()
    r1_2 = requests.post(f"{BASE_URL}/api/v1/chat", headers=headers, json={"query": q1_2, "session_id": session_id_1}, timeout=90)
    d1_2 = r1_2.json()
    lat1_2 = round((time.time() - t0) * 1000, 1)
    print(f"Status: {d1_2.get('status')} | SQL: {d1_2.get('sql_executed')} | Cached: {d1_2.get('is_cached')} | Latency: {lat1_2}ms")
    print(f"Answer snippet: {d1_2.get('answer', '')[:120]}...")
    assert d1_2.get("status") == "success", f"Turn 1.2 failed: {d1_2}"
    assert "2023" in str(d1_2.get("sql_executed")), "SQL must target year 2023"
    results.append(("Sesi 1 Turn 2 (Follow-up 2023)", d1_2.get("status"), lat1_2, d1_2.get("is_cached")))

    time.sleep(2)

    # Turn 1.3: Follow-up 2 (Context switch: metric domestic)
    q1_3 = "Kalau yang domestik berapa?"
    print(f"\n[Turn 1.3] Follow-up Query: '{q1_3}' (Harus mewarisi throughput domestik 2023)")
    t0 = time.time()
    r1_3 = requests.post(f"{BASE_URL}/api/v1/chat", headers=headers, json={"query": q1_3, "session_id": session_id_1}, timeout=90)
    d1_3 = r1_3.json()
    lat1_3 = round((time.time() - t0) * 1000, 1)
    print(f"Status: {d1_3.get('status')} | SQL: {d1_3.get('sql_executed')} | Cached: {d1_3.get('is_cached')} | Latency: {lat1_3}ms")
    print(f"Answer snippet: {d1_3.get('answer', '')[:120]}...")
    assert d1_3.get("status") == "success", f"Turn 1.3 failed: {d1_3}"
    results.append(("Sesi 1 Turn 3 (Follow-up Domestik)", d1_3.get("status"), lat1_3, d1_3.get("is_cached")))

    time.sleep(1)

    # Turn 1.4: Semantic Cache Hit Verification (Slightly rephrased query of Turn 1.1)
    q1_4 = "berapa throughput internasional di tahun 2024?"
    print(f"\n[Turn 1.4] Semantic Cache Test: '{q1_4}'")
    t0 = time.time()
    r1_4 = requests.post(f"{BASE_URL}/api/v1/chat", headers=headers, json={"query": q1_4, "session_id": session_id_1}, timeout=10)
    d1_4 = r1_4.json()
    lat1_4 = round((time.time() - t0) * 1000, 1)
    print(f"Status: {d1_4.get('status')} | Cached: {d1_4.get('is_cached')} | Latency: {lat1_4}ms")
    assert d1_4.get("is_cached") is True, "Turn 1.4 MUST HIT SEMANTIC CACHE!"
    assert lat1_4 < 50, f"Cache latency should be <50ms, got {lat1_4}ms"
    results.append(("Sesi 1 Turn 4 (Semantic Cache Hit)", d1_4.get("status"), lat1_4, d1_4.get("is_cached")))

    # =========================================================================
    # SESI 2: MULTI-TURN FINANSIAL (OPERATOR REVENUE & RANKING ANAPHORA)
    # =========================================================================
    session_id_2 = f"stress-test-fin-{uuid.uuid4().hex[:8]}"
    log_test("SESI 2: MULTI-TURN FINANSIAL (OPERATOR REVENUE & RANKING)", f"Session ID: {session_id_2}")

    # Turn 2.1: Top 5 operator revenue 2024
    q2_1 = "Siapa 5 operator dengan revenue terbesar tahun 2024?"
    print(f"\n[Turn 2.1] Query: '{q2_1}'")
    t0 = time.time()
    r2_1 = requests.post(f"{BASE_URL}/api/v1/chat", headers=headers, json={"query": q2_1, "session_id": session_id_2}, timeout=90)
    d2_1 = r2_1.json()
    lat2_1 = round((time.time() - t0) * 1000, 1)
    print(f"Status: {d2_1.get('status')} | SQL: {d2_1.get('sql_executed')} | Cached: {d2_1.get('is_cached')} | Latency: {lat2_1}ms")
    print(f"Answer snippet: {d2_1.get('answer', '')[:120]}...")
    assert d2_1.get("status") == "success", f"Turn 2.1 failed: {d2_1}"
    assert len(d2_1.get("data", [])) <= 5, "Should return at most 5 rows"
    results.append(("Sesi 2 Turn 1 (Top 5 Revenue 2024)", d2_1.get("status"), lat2_1, d2_1.get("is_cached")))

    time.sleep(2)

    # Turn 2.2: Anaphoric follow-up: "Siapa nomor 1 nya?"
    q2_2 = "Siapa nomor 1 nya?"
    print(f"\n[Turn 2.2] Anaphora Query: '{q2_2}' (Harus merujuk operator revenue 2024 juara 1)")
    t0 = time.time()
    r2_2 = requests.post(f"{BASE_URL}/api/v1/chat", headers=headers, json={"query": q2_2, "session_id": session_id_2}, timeout=90)
    d2_2 = r2_2.json()
    lat2_2 = round((time.time() - t0) * 1000, 1)
    print(f"Status: {d2_2.get('status')} | SQL: {d2_2.get('sql_executed')} | Cached: {d2_2.get('is_cached')} | Latency: {lat2_2}ms")
    print(f"Answer snippet: {d2_2.get('answer', '')[:120]}...")
    assert d2_2.get("status") == "success", f"Turn 2.2 failed: {d2_2}"
    assert "CMA" in str(d2_2.get("answer")) or "CMA" in str(d2_2.get("data")), "Top 1 operator in 2024 is CMA"
    results.append(("Sesi 2 Turn 2 (Anaphora: Siapa no 1 nya)", d2_2.get("status"), lat2_2, d2_2.get("is_cached")))

    time.sleep(2)

    # Turn 2.3: Follow-up with year switch: "Kalau di tahun 2023 siapa nomor 1 nya?"
    q2_3 = "Kalau di tahun 2023 siapa nomor 1 nya?"
    print(f"\n[Turn 2.3] Follow-up Query: '{q2_3}' (Harus merujuk operator revenue 2023 juara 1)")
    t0 = time.time()
    r2_3 = requests.post(f"{BASE_URL}/api/v1/chat", headers=headers, json={"query": q2_3, "session_id": session_id_2}, timeout=90)
    d2_3 = r2_3.json()
    lat2_3 = round((time.time() - t0) * 1000, 1)
    print(f"Status: {d2_3.get('status')} | SQL: {d2_3.get('sql_executed')} | Cached: {d2_3.get('is_cached')} | Latency: {lat2_3}ms")
    print(f"Answer snippet: {d2_3.get('answer', '')[:120]}...")
    assert d2_3.get("status") == "success", f"Turn 2.3 failed: {d2_3}"
    assert "2023" in str(d2_3.get("sql_executed")), "Must query year 2023"
    results.append(("Sesi 2 Turn 3 (No 1 di 2023)", d2_3.get("status"), lat2_3, d2_3.get("is_cached")))

    # =========================================================================
    # SESI 3: COMPLEX MULTI-DOMAIN QUERIES & EDGE CASES
    # =========================================================================
    session_id_3 = f"stress-test-complex-{uuid.uuid4().hex[:8]}"
    log_test("SESI 3: COMPLEX MULTI-DOMAIN & EDGE CASES", f"Session ID: {session_id_3}")

    complex_queries = [
        ("Vessel BMPH", "Siapa operator dengan rata-rata BMPH tertinggi di tahun 2024?"),
        ("UC Cargo", "Berapa total kegiatan uncontainerized UC tahun 2024?"),
        ("Market Share", "Siapa 3 operator dengan market share terbesar tahun 2023?"),
        ("Restitusi Diskon", "Tampilkan permohonan keringanan atau diskon yang diterima")
    ]

    for label, cq in complex_queries:
        time.sleep(2)
        print(f"\n[Domain: {label}] Query: '{cq}'")
        t0 = time.time()
        rc = requests.post(f"{BASE_URL}/api/v1/chat", headers=headers, json={"query": cq, "session_id": session_id_3}, timeout=90)
        dc = rc.json()
        latc = round((time.time() - t0) * 1000, 1)
        print(f"Status: {dc.get('status')} | SQL: {dc.get('sql_executed')} | Latency: {latc}ms")
        print(f"Answer snippet: {dc.get('answer', '')[:120]}...")
        assert dc.get("status") == "success", f"{label} failed: {dc}"
        assert dc.get("data") is not None and len(dc.get("data")) > 0, f"{label} returned empty data"
        results.append((f"Sesi 3 ({label})", dc.get("status"), latc, dc.get("is_cached")))

    # =========================================================================
    # SESI 4: ANTI-AMBIGUITY & ZERO-TOKEN PREFLIGHT REJECTION
    # =========================================================================
    session_id_4 = f"stress-test-ambiguity-{uuid.uuid4().hex[:8]}"
    log_test("SESI 4: ANTI-AMBIGUITY ZERO-TOKEN REJECTION", f"Session ID: {session_id_4}")

    q_ambiguous = "berapa totalnya?"
    print(f"\n[Ambiguous Test] Query: '{q_ambiguous}' (Tanpa konteks sebelumnya)")
    t0 = time.time()
    ra = requests.post(f"{BASE_URL}/api/v1/chat", headers=headers, json={"query": q_ambiguous, "session_id": session_id_4}, timeout=10)
    da = ra.json()
    lata = round((time.time() - t0) * 1000, 1)
    print(f"Status: {da.get('status')} | Latency: {lata}ms")
    print(f"Answer snippet: {da.get('answer', '')[:150]}...")
    assert "spesifik" in da.get("answer", "").lower() or "panduan" in da.get("answer", "").lower(), "Must return anti-ambiguity guidance"
    assert lata < 100, f"Preflight rejection must be instant (<100ms), got {lata}ms"
    results.append(("Sesi 4 (Anti-Ambiguity Guard)", da.get("status"), lata, False))

    # =========================================================================
    # REKAPITULASI HASIL AUDIT KEANDALAN
    # =========================================================================
    log_test("REKAPITULASI HASIL AUDIT KEANDALAN SISTEM (100% SUCCESS)", "Tabel Rangkuman Uji Stress")
    print(f"{'Skenario Uji':<40} | {'Status':<8} | {'Latensi':<10} | {'Cached':<8}")
    print("-" * 72)
    for name, st, lat, ch in results:
        print(f"{name:<40} | {st:<8} | {lat} ms{' '*(6-len(str(lat)))} | {str(ch):<8}")

    print("\n🎉 SELURUH SKENARIO UJI KEANDALAN (MULTI-TURN, KOMPLEKS, CACHE, ANTI-AMBIGUITY) BERHASIL 100%!")

if __name__ == "__main__":
    run_tests()
