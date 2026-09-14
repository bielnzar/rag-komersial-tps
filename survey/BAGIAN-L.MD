# 📑 LAPORAN AUDIT TEKNIS & METODOLOGI: BAGIAN L
## ORKESTRASI WORKFLOW BERBASIS LANGGRAPH

**Judul Penelitian:** *Pengembangan Asisten Analitik Data Berbasis Multi-Agent Text-to-SQL dan Medallion Architecture pada Perusahaan Layanan Petikemas: Studi Kasus PT XYZ*  
**Peran Auditor:** Software Architect, Code Auditor, & Technical Documentation Analyst  
**Waktu Audit:** September 2026  
**Metode Audit:** Graph Compilation Tracing (`backend/agents/graph.py`), State Schema Inspection (`backend/agents/state.py`), & State Transition Analysis

---

### 1. Identifikasi Graph Utama
* **Status:** `IMPLEMENTED (LangGraph StateGraph)`
* **File Pengendali:** [`backend/agents/graph.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/graph.py)
* **Fungsi Pembangun:** `build_graph()`
* **Mekanisme:** Menginisialisasi `workflow = StateGraph(AgentState)` yang mengompilasi seluruh node agen dan aturan transisi edge menjadi aplikasi State Machine terpadu (`app = workflow.compile()`). Instance ini di-load saat server FastAPI booting di `backend/main.py:L36` (`agent_app = build_graph()`).

---

### 2. Identifikasi Seluruh Node
Terdapat **5 Node Terdaftar** di dalam StateGraph LangGraph:

| Nama Node di Graf | Fungsi Python yang Dieksekusi | File Sumber | Peran Komputasi |
| :--- | :--- | :--- | :--- |
| `"router"` | `router_node` | `backend/agents/router.py` | Klasifikasi semantik tabel relevan & RBAC (LLM) |
| `"sql_gen"` | `sql_gen_node` | `backend/agents/sql_gen.py` | Sintesis Text-to-SQL berbasis glosarium domain TPS (LLM) |
| `"sanitizer"` | `sanitizer_node` | `backend/agents/sanitizer.py` | Filter keamanan SQL Injection, DDL/DML, dan validasi CTE (Python Rule) |
| `"execute_sql"` | `execute_sql_node` | `backend/agents/execute.py` | Eksekusi SQL ke database DuckDB & deteksi data kosong (DuckDB Engine) |
| `"viz_gen"` | `viz_gen_node` | `backend/agents/viz_gen.py` | Perumusan narasi eksekutif & Apache ECharts JSON config (LLM) |

---

### 3. Identifikasi Seluruh Edge Statis (Fixed Edges)
Edge statis menghubungkan node-node yang alurnya selalu berurutan secara pasti:
1. `workflow.add_edge(START, "router")`: Dari titik awal masuk graf menuju Router Node.
2. `workflow.add_edge("router", "sql_gen")`: Dari Router menuju SQL Generator Node.
3. `workflow.add_edge("sql_gen", "sanitizer")`: Dari SQL Generator menuju Sanitizer Node.
4. `workflow.add_edge("execute_sql", "viz_gen")`: Dari Execution Node menuju Viz Gen Node (Fail-Fast, tanpa loop).
5. `workflow.add_edge("viz_gen", END)`: Dari Viz Gen menuju titik akhir graf.

---

### 4. Identifikasi Conditional Edge (Percabangan Bersyarat)
* **Lokasi Transisi:** Keluar dari node `"sanitizer"`.
* **Fungsi Evaluator:** `should_continue_sanitizer(state: AgentState)` di [`backend/agents/graph.py:L12-L23`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/graph.py#L12-L23).
* **Kode Implementasi:**
  ```python
  workflow.add_conditional_edges(
      "sanitizer",
      should_continue_sanitizer,
      {
          "execute_sql": "execute_sql",  # Jalur 1: Lolos validasi -> lanjut eksekusi DuckDB
          "viz_gen": "viz_gen"           # Jalur 2: Terblokir -> bypass database, langsung ke narasi penolakan
      }
  )
  ```
* **Logika Evaluator:**
  - Jika `state["sql_error"]` mengandung kata `"SANITIZER BLOCKED"` ➔ mengembalikan string `"viz_gen"` (melompati node `execute_sql` demi keamanan).
  - Jika aman (`sql_error is None`) ➔ mengembalikan string `"execute_sql"`.

---

### 5. Definisi State yang Digunakan (`AgentState`)
* **File:** [`backend/agents/state.py`](file:///home/bosmuda/Intern/TPS/rag-komersial-tps/backend/agents/state.py)
* **Tipe Data:** `TypedDict` Python standar yang dilempar dan diperbarui secara bertahap dari satu node ke node berikutnya:

```python
class AgentState(TypedDict):
    user_query: str                    # Pertanyaan asli dari user
    relevant_tables: Optional[List[str]]# Daftar tabel terpilih dari Router
    generated_sql: Optional[str]       # Sintaks SQL hasil rakitan AI
    sql_error: Optional[str]           # Pesan error jika SQL gagal / diblokir / data kosong
    correction_attempts: int           # Status flag eksekusi
    query_result: Optional[List[dict]] # Hasil query dari DuckDB (list of dict records)
    final_answer: Optional[str]        # Jawaban akhir naratif eksekutif
    echarts_config: Optional[dict]     # Konfigurasi JSON Apache ECharts
    force_chart: Optional[bool]        # Flag pemicu grafik visual on-demand
    chat_history: Optional[List[dict]] # Konteks memori 3 obrolan terakhir dari Redis
    role: Optional[str]                # Hak akses pengguna (executive, commercial, dsb.)
```

---

### 6. Bagaimana State Berubah Antar Node (State Lifecycle)

```text
[HTTP Request Masuk di main.py]
  State Diinisialisasi:
  - user_query = "Berapa throughput 2024?"
  - chat_history = session_history[-6:]
  - role = "executive"
  - relevant_tables = None, generated_sql = None, query_result = None, sql_error = None
        │
        ▼
[Node: "router"]
  State Ditambahkan:
  - relevant_tables = ['fakta_throughput']
        │
        ▼
[Node: "sql_gen"]
  State Ditambahkan:
  - generated_sql = "SELECT SUM(actual) FROM fakta_throughput WHERE year = 2024"
        │
        ▼
[Node: "sanitizer"]
  State Ditambahkan (Jika ada pelanggaran):
  - sql_error = "SANITIZER BLOCKED: ..." (Jika melanggar) atau None (Jika lolos)
        │
        ▼
[Node: "execute_sql"]
  State Ditambahkan:
  - query_result = [{'total_throughput': 1479595.0}]
  - sql_error = None (atau "DATA_EMPTY" jika 0 baris)
        │
        ▼
[Node: "viz_gen"]
  State Ditambahkan:
  - final_answer = "1. **Total Throughput 2024** – 1.479.595 TEUs..."
  - echarts_config = {...} (Jika diminta visualisasi)
        │
        ▼
[Output Dikembalikan ke User via FastAPI ChatResponse]
```

---

### 7. Identifikasi Start Node dan End Node
* **`START` Node:** LangGraph predefined constant `START`. Titik masuk utama graf, selalu terhubung langsung ke node **`"router"`**.
* **`END` Node:** LangGraph predefined constant `END`. Titik terminasi graf, selalu menerima output akhir dari node **`"viz_gen"`**.

---

### 8. Alur Eksekusi Normal (Happy Path Execution)

```text
START
  │
  ▼
[Node 1: router]
  │  (Memilih tabel relevan dari katalog 9 tabel)
  ▼
[Node 2: sql_gen]
  │  (Merakit DuckDB SQL murni)
  ▼
[Node 3: sanitizer]
  │  (Validasi sintaks: Lolos 100%)
  ▼
[Condition: should_continue_sanitizer ➔ "execute_sql"]
  │
  ▼
[Node 4: execute_sql]
  │  (Eksekusi DuckDB: Berhasil mengembalikan N baris data)
  ▼
[Node 5: viz_gen]
  │  (Merangkum narasi eksekutif + Apache ECharts config)
  ▼
END
```

---

### 9. Alur Eksekusi Kegagalan / Fail-Fast (Failure Paths)

Sistem menerapkan **Fail-Fast Single-Pass** tanpa perulangan siklik (*No Cyclic Retry Loop*):

#### A. Skenario 1: Pelanggaran Keamanan (Sanitizer Blocked)
Jika kueri mengandung karakter titik koma (`;`), komentar, atau kata kunci terlarang (`DROP/DELETE`):
```text
START 
  ➔ router 
  ➔ sql_gen 
  ➔ sanitizer 
  ➔ [Condition: should_continue_sanitizer ➔ "viz_gen"] (BYPASS execute_sql)
  ➔ viz_gen (Menampilkan Pesan Penolakan Keamanan)
  ➔ END
```

#### B. Skenario 2: Kesalahan Sintaks Database / Data Kosong (`DATA_EMPTY` / `DB_SYNTAX_ERROR`)
Jika SQL keliru atau kriteria tahun/operator tidak ditemukan di database:
```text
START 
  ➔ router 
  ➔ sql_gen 
  ➔ sanitizer 
  ➔ [Condition: should_continue_sanitizer ➔ "execute_sql"]
  ➔ execute_sql (Mencatat flag DATA_EMPTY / DB_SYNTAX_ERROR)
  ➔ viz_gen (Menampilkan Pesan Graceful Degradation & Saran Kata Kunci)
  ➔ END
```
*(Catatan: Tidak ada edge putar balik dari `execute_sql` atau `sanitizer` kembali ke `sql_gen`, memastikan waktu respons tetap di bawah 1 detik).*
