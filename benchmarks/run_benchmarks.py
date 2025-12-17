"""
Benchmark harness for FRACKTAL MCP.

Outputs:
- Lossless recall report (SHA256 equality).
- Throughput metrics (memories/sec).
- Retrieval effectiveness (Recall@5 + MRR) comparing FRACKTAL hybrid search vs BM25-only baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from rank_bm25 import BM25Okapi

from mcp_server.memory_store import MemoryStore

PROJECT_ID = "benchmark-project"


@dataclass
class Sample:
    label: str
    content: str
    event_type: str
    kind: str
    tags: List[str]
    summary: str


DATASET: Sequence[Sample] = [
    Sample(
        label="code_handler",
        kind="file_diff",
        event_type="file_diff",
        tags=["code", "handler"],
        summary="API handler refactor",
        content="""\
diff --git a/api/handler.py b/api/handler.py
@@
-def handle_user(req):
-    # legacy auth
-    if not req.user:
-        raise AuthError("missing user")
+def handle_user(request):
+    if not request.user:
+        raise AuthError("missing user")
+    if not request.user.is_active:
+        raise AuthError("inactive")
""",
    ),
    Sample(
        label="log_auth",
        kind="log",
        event_type="tool_run",
        tags=["logs", "auth"],
        summary="Auth failure trace",
        content="[ERROR] auth middleware rejected token=abc123 reason=expired signature",
    ),
    Sample(
        label="test_suite",
        kind="test_result",
        event_type="test_result",
        tags=["tests"],
        summary="Regression suite run",
        content="pytest::test_auth_flow FAILED AssertionError: expected 200 got 401",
    ),
    Sample(
        label="plan_checkpoint",
        kind="checkpoint",
        event_type="checkpoint",
        tags=["plan"],
        summary="Checkpoint after auth fix",
        content="Goals: ensure login works across desktop/mobile.\nPlan: 1) fix middleware 2) add regression test 3) document rollout.",
    ),
    Sample(
        label="note_observation",
        kind="note",
        event_type="note",
        tags=["note"],
        summary="Observation about caching",
        content="Cache misses spike when tenant flag beta=true; potential race with bootstrap job.",
    ),
]

QUERIES = [
    {"query": "auth middleware failure", "relevant": {"log_auth", "test_suite"}},
    {"query": "checkpoint plan rollout", "relevant": {"plan_checkpoint"}},
    {"query": "api handler refactor diff", "relevant": {"code_handler"}},
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_baseline(dataset: Sequence[Sample]):
    docs = [sample.content for sample in dataset]
    tokens = [doc.lower().split() for doc in docs]
    bm25 = BM25Okapi(tokens)

    def search(query: str, limit: int = 5) -> List[int]:
        scores = bm25.get_scores(query.lower().split())
        ranked = list(sorted(enumerate(scores), key=lambda kv: kv[1], reverse=True))
        return [idx for idx, _ in ranked[:limit]]

    return search


def run_benchmark(args: argparse.Namespace) -> Dict[str, any]:
    storage_dir = Path(args.storage_dir)
    if storage_dir.exists():
        shutil.rmtree(storage_dir)
    storage_dir.mkdir(parents=True)

    store = MemoryStore(storage_dir=str(storage_dir), enable_embeddings=args.enable_embeddings)

    label_to_id: Dict[str, str] = {}
    lossless_failures = []
    start = time.time()
    for sample in DATASET:
        mid = store.store_memory(
            content=sample.content,
            tags=sample.tags,
            kind=sample.kind,
            project_id=PROJECT_ID,
            event_type=sample.event_type,
            summary=sample.summary,
        )
        label_to_id[sample.label] = mid
        retrieved = store.retrieve_memory(mid)
        if sha256_text(retrieved["content"]) != sha256_text(sample.content):
            lossless_failures.append(sample.label)
    ingest_time = time.time() - start
    throughput = len(DATASET) / ingest_time if ingest_time > 0 else 0.0

    # Retrieval metrics
    fracktal_hits = evaluate_retrieval(store, label_to_id)
    baseline_search = build_baseline(DATASET)
    baseline_hits = evaluate_baseline(baseline_search)

    result = {
        "lossless_failures": lossless_failures,
        "records": len(DATASET),
        "ingest_seconds": ingest_time,
        "memories_per_second": throughput,
        "retrieval": {
            "fracktal": fracktal_hits,
            "bm25_only": baseline_hits,
        },
    }
    output_path = Path(args.output)
    output_path.write_text(json.dumps(result, indent=2))
    return result


def metrics_from_hits(hits: List[Tuple[str, float]]) -> Dict[str, float]:
    recall_at_5 = sum(1 for label, _ in hits if label == "hit") / len(hits)
    mrr = sum(score for _, score in hits) / len(hits)
    return {"recall_at_5": recall_at_5, "mrr": mrr}


def evaluate_retrieval(store: MemoryStore, label_map: Dict[str, str]) -> Dict[str, float]:
    id_to_label = {mid: label for label, mid in label_map.items()}
    per_query = []
    for spec in QUERIES:
        results = store.search_memories(spec["query"], project_id=PROJECT_ID, limit=5)
        ids = [r.id for r in results]
        hit_score = 0.0
        for rank, rid in enumerate(ids, start=1):
            label = id_to_label.get(rid)
            if label and label in spec["relevant"]:
                hit_score = 1.0 / rank
                break
        per_query.append(("hit" if hit_score else "miss", hit_score))
    return metrics_from_hits(per_query)


def evaluate_baseline(search_fn) -> Dict[str, float]:
    per_query = []
    for spec in QUERIES:
        indices = search_fn(spec["query"], limit=5)
        hit_score = 0.0
        for rank, idx in enumerate(indices, start=1):
            label = DATASET[idx].label
            if label in spec["relevant"]:
                hit_score = 1.0 / rank
                break
        per_query.append(("hit" if hit_score else "miss", hit_score))
    return metrics_from_hits(per_query)


def main():
    parser = argparse.ArgumentParser(description="Run FRACKTAL MCP benchmarks.")
    parser.add_argument("--storage-dir", default=".benchmark_memories", help="Where to store temporary benchmark memories.")
    parser.add_argument("--output", default="benchmark_report.json", help="Where to write the JSON report.")
    parser.add_argument("--enable-embeddings", action="store_true", help="Enable optional embedding retrieval during the benchmark.")
    args = parser.parse_args()

    result = run_benchmark(args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
