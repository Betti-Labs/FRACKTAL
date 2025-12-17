# Fracktal MCP - Event-Sourced, Verifiable Memory for AI Agents
### By [GoryGrey](https://github.com/GoryGrey) | Gregory Betti

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![MCP Ready](https://img.shields.io/badge/MCP-Ready-green.svg)](https://modelcontextprotocol.io)

Fracktal MCP is a local, plug-and-play MCP server that turns every agent action-tool calls, diffs, tests, plans-into an immutable, lossless event log. Agents can resume any project with a single `restore_working_set` call, search through hybrid structural/lexical/vector indexes, and verify historical context via SHA256-stamped artifacts. Everything runs locally by default, with optional embeddings for semantic recall.

---

## Why teams use Fracktal MCP

- **Event-sourced timeline** - Every tool run, file diff, test result, decision, and checkpoint is stored as a typed event with content-addressed payloads.
- **Lossless & auditable** - Storage is powered by the FRACKTAL recursive symbolic engine; compression is reversible and verifiable (hashes match byte-for-byte on restore).
- **Hybrid retrieval** - Structural fingerprints (FRACKTAL symbols) are fused with BM25 lexical scoring and optional sentence-transformer embeddings, plus metadata filters.
- **Working-set restore** - Cold-start an agent by pulling the latest checkpoint, recent diffs/logs/tests, and open decisions in one tool call.
- **Local-first** - Runs entirely on your machine; embeddings (if enabled) can use local transformer weights. No network calls unless you opt in.

---

## Quick start

```bash
git clone https://github.com/GoryGrey/Fracktal-MCP.git
cd Fracktal-MCP
pip install -e .

# run the MCP server locally
python -m mcp_server.server
```

Configure your MCP client (Claude Desktop example):

```json
{
  "mcpServers": {
    "fracktal-memory": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/FRACKTAL"
    }
  }
}
```

Optional embeddings (hybrid retrieval adds vectors on top of structural+BM25):

```bash
pip install sentence-transformers
export FRACKTAL_ENABLE_EMBEDDINGS=1
# optional: override model
export FRACKTAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## Working with any MCP-capable agent

Fracktal MCP exposes a clean tool surface so every agent (Claude Desktop, Cursor, Bespoke python loops, etc.) can persist its lifecycle without bespoke glue. See **docs/mcp_usage.md** for recommended prompts/policies.

| Tool | Purpose |
|------|---------|
| `store_memory` | Raw lossless storage (notes, transcripts, artifacts). |
| `record_tool_run` | Capture tool inputs/outputs + status. |
| `record_file_change` | Persist diffs or file snapshots (auto-tagged by `path`). |
| `record_test_result` | Store test metadata + logs. |
| `create_checkpoint` / `get_latest_checkpoint` | Maintain working-set summaries & plans. |
| `list_events` | Filter event timeline by project/type. |
| `search_memories` | Hybrid structural/BM25/(optional) embedding retrieval with metadata filters. |
| `restore_working_set` | Return latest checkpoint + grouped recent events so an agent can resume instantly. |

Everything is scoped by `project_id`, `session_id`, `event_type`, `tags`, and optional `path` metadata. Use those knobs to isolate multiple repos or workloads on the same server.

---

## Working-set restore in practice

```jsonc
// restore_working_set(project_id="alpha-app", recent_limit=10)
{
  "project_id": "alpha-app",
  "checkpoint": {
    "content": "Checkpoint body ...",
    "metadata": {
      "summary": "After fixing login regression",
      "tags": ["plan", "checkpoint"],
      "timestamp": 1734417680.12,
      "id": "d6f5..."
    }
  },
  "recent_events": {
    "file_diff": [
      {"id": "a1b2...", "path": "src/auth.py", "summary": "File change: src/auth.py"}
    ],
    "test_result": [
      {"id": "c3d4...", "summary": "Test test_login: failed", "tags": ["tests"], "timestamp": 1734417671.44}
    ],
    "tool_run": [
      {"id": "e5f6...", "summary": "Tool pytest (failure)", "tags": ["logs", "pytest"]}
    ],
    "note": [],
    "decision": [],
    "plan_update": []
  },
  "recent_count": 5
}
```

An agent can immediately reload goals, the latest plan, and the precise diffs/tests/logs needed to continue coding-even after days offline.

---

## Hybrid retrieval & metadata filters

`search_memories` fuses three complementary scores:

1. **Structural** - Jaccard similarity over FRACKTAL symbolic fingerprints (lossless structural understanding).
2. **Lexical (BM25)** - Default dependency; great for identifiers, error messages, stack traces.
3. **Vector (optional embeddings)** - Sentence-transformer cosine similarity for paraphrases.

Weights are tuned to favor structural matches while still surfacing lexical/vector results. Every search call supports filters: `project_id`, `session_id`, `event_types`, `kinds`, `tags`, `path`. Pass an empty query to fetch the most recent scoped events.

---

## Testing, benchmarking, and verification

### Automated tests

```bash
python -m pytest
```

32 tests cover the FRSOE primitives and the full project-aware MCP flow (lossless storage, hybrid search filters, working-set restore, optimizer).

### Stress & throughput profiling

```bash
python stress_test_demo.py --num-memories 100 --storage-dir benchmark_memories --sample-size 15
```

- 100 synthetic memories stored in ~5.5s on a Windows 11 workstation (Python 3.13) -> **~18 mem/s**.
- 0 integrity errors (perfect recall).
- Semantic search latency: **~4-7 ms/query** for a single-result search (structural + BM25).

### Deterministic benchmark harness

```bash
python benchmarks/run_benchmarks.py --storage-dir tmp_bench --output bench_report.json
cat bench_report.json
```

Sample output (reproducible, uses SHA256 equality to prove lossless storage):

```json
{
  "lossless_failures": [],
  "records": 5,
  "memories_per_second": 20.86,
  "retrieval": {
    "fracktal": {"recall_at_5": 1.0, "mrr": 0.83},
    "bm25_only": {"recall_at_5": 1.0, "mrr": 0.75}
  }
}
```

Use this harness in CI to catch regressions in lossless recall or hybrid ranking.

---

## Architecture snapshot

- **FRACKTAL Engine (FRSOE)** - Recursive symbolic ontology that produces reversible codices for every artifact (see appendix).
- **Event Store** - Disk-backed, content-addressed JSON codices plus a metadata index (`fracktal_memories/index.json`).
- **Indexes** - Symbol frequency lists, BM25 corpus, and optional embedding vectors kept in sync as events arrive.
- **MCP Surface** - `mcp_server/server.py` exposes typed tools for storage, retrieval, event logging, checkpoints, and working-set restore.

Because everything is append-only and hashed, you can rebuild indexes safely or audit change history at any time.

---

## Documentation

- **docs/mcp_usage.md** - Agent integration guide, recommended tool policies, and JSON examples.
- **docs/concepts.md** - A deeper look at FRSOE symbolism, fractal hashing, and entropy preservation.
- Stress/benchmark scripts - `stress_test_demo.py`, `benchmarks/run_benchmarks.py`.

Contributions are welcome via standard GitHub PRs; see `CONTRIBUTING.md`.

---

## Appendix: FRSOE compression highlights

The MCP server is powered by the FRACKTAL Recursive Symbolic Ontology Engine (FRSOE). For completeness, the original compression characteristics are preserved below.

### Compression performance

| Data Type | Compression Ratio | Pattern Detection | Reconstruction |
|-----------|------------------|-------------------|----------------|
| Highly Repetitive | 6.28x | Excellent | Perfect |
| Structured Data | 2.46x | Excellent | Perfect |
| Mixed Content | 1.17-1.43x | Good | Perfect |
| Low Repetition | 1.17x | Moderate | Perfect |

### Computational efficiency

- **Compression speed**: 0.003-0.085 s typical payloads
- **Reconstruction speed**: 0.001-0.003 s
- **Memory usage**: CPU-only, low overhead
- **Scalability**: Near-linear with input size

---

## Citation

If you use FRACKTAL in research, please cite:

```bibtex
@software{fracktal2024,
  title={FRACKTAL: Fractal Recursive Symbolic Ontology Engine},
  author={Betti, Gregory},
  year={2024},
  url={https://github.com/GoryGrey/Fracktal-MCP}
}
```

## License / Contact

MIT License for non-commercial use. Commercial licensing: gorygrey@protonmail.com.  
GitHub: [@GoryGrey](https://github.com/GoryGrey)
