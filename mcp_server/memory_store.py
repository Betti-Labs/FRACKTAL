import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from fracktal import RecursiveFRSOE

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover - optional dependency
    BM25Okapi = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - optional dependency
    SentenceTransformer = None


EVENT_TYPES = {
    "note",
    "tool_run",
    "file_diff",
    "test_result",
    "checkpoint",
    "plan_update",
    "decision",
}


@dataclass
class MemoryMetadata:
    id: str
    timestamp: float
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    kind: str = "text"
    event_type: str = "note"
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None
    path: Optional[str] = None
    summary: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    id: str
    preview: str
    score: float
    tags: List[str]
    session_id: Optional[str]
    project_id: Optional[str]
    kind: str
    event_type: str
    path: Optional[str]
    summary: Optional[str]


class MemoryStore:
    def __init__(self, storage_dir: str = "memories", enable_embeddings: Optional[bool] = None):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"

        self.engine = RecursiveFRSOE()
        self.memory_index: Dict[str, Dict[str, Any]] = {}

        self._bm25 = None
        self._bm25_docs: List[List[str]] = []
        self._bm25_ids: List[str] = []
        self._embeddings: Dict[str, np.ndarray] = {}
        self._embedding_model = None
        self.enable_embeddings = self._should_enable_embeddings(enable_embeddings)

        self._load_index()
        self._maybe_load_embedding_model()
        self._rebuild_text_indexes()

    # ----------------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------------

    def _should_enable_embeddings(self, override: Optional[bool]) -> bool:
        if override is not None:
            return override
        env = os.getenv("FRACKTAL_ENABLE_EMBEDDINGS", "0").lower()
        return env in {"1", "true", "yes", "on"}

    def _maybe_load_embedding_model(self) -> None:
        if not self.enable_embeddings or SentenceTransformer is None:
            self.enable_embeddings = False
            return
        model_name = os.getenv("FRACKTAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        try:
            self._embedding_model = SentenceTransformer(model_name)
        except Exception:
            self._embedding_model = None
            self.enable_embeddings = False

    def _tokenize(self, text: str) -> List[str]:
        cleaned = text.replace("\n", " ").replace("\t", " ")
        return [token.lower() for token in cleaned.split() if token.strip()]

    def _rebuild_text_indexes(self) -> None:
        texts = []
        ids = []
        for mid, record in self.memory_index.items():
            text = record.get("text") or record.get("preview", "")
            tokens = self._tokenize(text)
            texts.append(tokens)
            ids.append(mid)
            if self.enable_embeddings and self._embedding_model and text:
                self._embeddings[mid] = self._embedding_model.encode(text)
        if texts and BM25Okapi is not None:
            self._bm25_docs = texts
            self._bm25_ids = ids
            self._bm25 = BM25Okapi(texts)
        else:
            self._bm25 = None
            self._bm25_docs = []
            self._bm25_ids = []

    def _add_to_indexes(self, memory_id: str, text: str) -> None:
        tokens = self._tokenize(text)
        if tokens:
            self._bm25_docs.append(tokens)
            self._bm25_ids.append(memory_id)
            if BM25Okapi is not None:
                self._bm25 = BM25Okapi(self._bm25_docs)
        if self.enable_embeddings and self._embedding_model and text:
            self._embeddings[memory_id] = self._embedding_model.encode(text)

    def _load_index(self) -> None:
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    self.memory_index = json.load(f)
            except json.JSONDecodeError:
                self.memory_index = {}
        else:
            self.memory_index = {}

        for record in self.memory_index.values():
            record.setdefault("text", record.get("preview", ""))
            metadata = record.get("metadata", {})
            metadata.setdefault("project_id", None)
            metadata.setdefault("event_type", "note")
            metadata.setdefault("tags", [])
            metadata.setdefault("source", None)
            metadata.setdefault("path", None)
            metadata.setdefault("summary", None)
            metadata.setdefault("extra", {})
            record["metadata"] = metadata

    def _save_index(self) -> None:
        with open(self.index_file, "w") as f:
            json.dump(self.memory_index, f, indent=2)

    def _filter_records(
        self,
        project_id: Optional[str],
        session_id: Optional[str],
        kinds: Optional[Sequence[str]],
        event_types: Optional[Sequence[str]],
        tags: Optional[Sequence[str]],
        path: Optional[str],
    ) -> Dict[str, Dict[str, Any]]:
        filtered = {}
        for mid, record in self.memory_index.items():
            meta = record["metadata"]
            if project_id and meta.get("project_id") != project_id:
                continue
            if session_id and meta.get("session_id") != session_id:
                continue
            if kinds and meta.get("kind") not in kinds:
                continue
            if event_types and meta.get("event_type") not in event_types:
                continue
            if path and meta.get("path") != path:
                continue
            if tags and not set(tags).issubset(set(meta.get("tags", []))):
                continue
            filtered[mid] = record
        return filtered

    def _bm25_scores(self, query: str) -> Dict[str, float]:
        if not self._bm25 or BM25Okapi is None:
            return {}
        tokens = self._tokenize(query)
        if not tokens:
            return {}
        raw_scores = self._bm25.get_scores(tokens)
        if not raw_scores.any():
            return {}
        max_score = raw_scores.max()
        if max_score <= 0:
            return {}
        normalized = raw_scores / max_score
        return {mid: float(score) for mid, score in zip(self._bm25_ids, normalized)}

    def _embedding_scores(self, query: str) -> Dict[str, float]:
        if not self.enable_embeddings or not self._embedding_model or not self._embeddings:
            return {}
        vector = self._embedding_model.encode(query)
        if vector is None or not len(vector):
            return {}
        scores = {}
        query_norm = np.linalg.norm(vector)
        if query_norm == 0:
            return {}
        for mid, emb in self._embeddings.items():
            denom = np.linalg.norm(emb) * query_norm
            if denom == 0:
                continue
            cosine = float(np.dot(vector, emb) / denom)
            scores[mid] = (cosine + 1.0) / 2.0  # map [-1,1] -> [0,1]
        return scores

    def _structural_scores(self, query_symbols: set, candidates: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        scores = {}
        if not query_symbols:
            return scores
        for mid, record in candidates.items():
            mem_symbols = set(record.get("symbols", []))
            if not mem_symbols:
                continue
            intersection = len(query_symbols.intersection(mem_symbols))
            union = len(query_symbols.union(mem_symbols))
            if union == 0:
                continue
            scores[mid] = intersection / union
        return scores

    def _combine_scores(
        self,
        sid: str,
        structural: Dict[str, float],
        lexical: Dict[str, float],
        embedding: Dict[str, float],
    ) -> float:
        weights = {
            "structural": 0.5,
            "lexical": 0.35,
            "embedding": 0.15,
        }
        return (
            weights["structural"] * structural.get(sid, 0.0)
            + weights["lexical"] * lexical.get(sid, 0.0)
            + weights["embedding"] * embedding.get(sid, 0.0)
        )

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------

    def store_memory(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        kind: str = "text",
        project_id: Optional[str] = None,
        event_type: str = "note",
        source: Optional[str] = None,
        path: Optional[str] = None,
        summary: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        memory_id = str(uuid.uuid4())
        timestamp = time.time()
        tags = tags or []
        extra_metadata = extra_metadata or {}
        event_type = event_type if event_type in EVENT_TYPES else "note"

        compressed_result = self.engine.compress(content)
        codex_map = compressed_result["frsoe_codex"]
        unique_symbols = sorted(list(codex_map.get_symbol_frequency().keys()))

        metadata = MemoryMetadata(
            id=memory_id,
            timestamp=timestamp,
            session_id=session_id,
            project_id=project_id,
            kind=kind,
            event_type=event_type,
            tags=tags,
            source=source,
            path=path,
            summary=summary,
            extra=extra_metadata,
        )

        memory_record = {
            "metadata": asdict(metadata),
            "symbols": unique_symbols,
            "codex_path": f"{memory_id}.json",
            "preview": content[:200],
            "text": content,
        }

        codex_dict = codex_map.to_dict()
        saveable_data = {
            "original_data": compressed_result["original_data"],
            "frsoe_codex": codex_dict,
            "recursive_compression": compressed_result["recursive_compression"],
            "combined_stats": compressed_result["combined_stats"],
        }

        codex_path = self.storage_dir / f"{memory_id}.json"
        with open(codex_path, "w") as f:
            json.dump(saveable_data, f, indent=2, default=str)

        self.memory_index[memory_id] = memory_record
        self._save_index()
        self._add_to_indexes(memory_id, content)

        return memory_id

    def retrieve_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        if memory_id not in self.memory_index:
            return None

        record = self.memory_index[memory_id]
        codex_path = self.storage_dir / record["codex_path"]
        if not codex_path.exists():
            return None

        with open(codex_path, "r") as f:
            full_compressed_data = json.load(f)

        from fracktal.models import CodexMap, SymbolicTree
        import pandas as pd

        codex_dict = full_compressed_data["frsoe_codex"]
        c_df = pd.DataFrame(codex_dict["codex_df"])
        s_tree = SymbolicTree(codex_dict["symbolic_tree"]["nodes"])

        rehydrated_codex = CodexMap(
            original_data=codex_dict["original_data"],
            codex_df=c_df,
            symbolic_tree=s_tree,
            fractal_hashes=codex_dict["fractal_hashes"],
            fingerprint=codex_dict["fingerprint"],
            compression_ratio=codex_dict["compression_ratio"],
            metadata=codex_dict.get("metadata", {}),
            timestamp=codex_dict.get("timestamp"),
        )

        full_compressed_data["frsoe_codex"] = rehydrated_codex
        reconstructed_content = self.engine.reconstruct(full_compressed_data)

        return {
            "content": reconstructed_content,
            "metadata": record["metadata"],
        }

    def search_memories(
        self,
        query: str,
        limit: int = 5,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        kinds: Optional[Sequence[str]] = None,
        event_types: Optional[Sequence[str]] = None,
        tags: Optional[Sequence[str]] = None,
        path: Optional[str] = None,
    ) -> List[SearchResult]:
        filtered_records = self._filter_records(project_id, session_id, kinds, event_types, tags, path)
        if not filtered_records:
            return []

        if not query.strip():
            items = list(filtered_records.values())
            items.sort(key=lambda r: r["metadata"]["timestamp"], reverse=True)
            ranked = []
            for record in items[:limit]:
                meta = record["metadata"]
                ranked.append(
                    SearchResult(
                        id=meta["id"],
                        preview=record.get("preview", ""),
                        score=1.0,
                        tags=meta.get("tags", []),
                        session_id=meta.get("session_id"),
                        project_id=meta.get("project_id"),
                        kind=meta.get("kind", "text"),
                        event_type=meta.get("event_type", "note"),
                        path=meta.get("path"),
                        summary=meta.get("summary"),
                    )
                )
            return ranked

        query_result = self.engine.compress(query)
        query_symbols = set(query_result["frsoe_codex"].get_symbol_frequency().keys())
        structural_scores = self._structural_scores(query_symbols, filtered_records)
        lexical_scores = self._bm25_scores(query)
        embedding_scores = self._embedding_scores(query)

        ranked: List[SearchResult] = []
        for mid, record in filtered_records.items():
            final_score = self._combine_scores(mid, structural_scores, lexical_scores, embedding_scores)
            if final_score <= 0:
                continue
            meta = record["metadata"]
            ranked.append(
                SearchResult(
                    id=mid,
                    preview=record.get("preview", ""),
                    score=final_score,
                    tags=meta.get("tags", []),
                    session_id=meta.get("session_id"),
                    project_id=meta.get("project_id"),
                    kind=meta.get("kind", "text"),
                    event_type=meta.get("event_type", "note"),
                    path=meta.get("path"),
                    summary=meta.get("summary"),
                )
            )

        ranked.sort(key=lambda r: r.score, reverse=True)
        return ranked[:limit]

    def list_recent_memories(
        self,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        items = list(self.memory_index.values())
        if session_id:
            items = [m for m in items if m["metadata"].get("session_id") == session_id]
        if project_id:
            items = [m for m in items if m["metadata"].get("project_id") == project_id]

        items.sort(key=lambda x: x["metadata"]["timestamp"], reverse=True)
        return [
            {
                "id": m["metadata"]["id"],
                "preview": m["preview"],
                "timestamp": m["metadata"]["timestamp"],
                "kind": m["metadata"]["kind"],
                "event_type": m["metadata"]["event_type"],
                "project_id": m["metadata"]["project_id"],
                "tags": m["metadata"]["tags"],
            }
            for m in items[:limit]
        ]

    def get_stats(self) -> Dict[str, Any]:
        project_totals: Dict[str, int] = {}
        for record in self.memory_index.values():
            project_id = record["metadata"].get("project_id") or "unscoped"
            project_totals[project_id] = project_totals.get(project_id, 0) + 1

        total_memories = len(self.memory_index)
        total_symbols = sum(len(m.get("symbols", [])) for m in self.memory_index.values())

        return {
            "total_memories": total_memories,
            "total_symbols_indexed": total_symbols,
            "projects": project_totals,
            "embeddings_enabled": self.enable_embeddings,
        }

    def optimize_corpus(self) -> Dict[str, Any]:
        symbol_counts: Dict[str, int] = {}
        for record in self.memory_index.values():
            for sym in record.get("symbols", []):
                symbol_counts[sym] = symbol_counts.get(sym, 0) + 1
        sorted_syms = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return {
            "optimized": True,
            "message": "Corpus analysis complete. Frequent structural patterns identified.",
            "top_global_patterns": sorted_syms,
        }

    # ----------------------------------------------------------------------
    # Project-aware helpers
    # ----------------------------------------------------------------------

    def record_tool_run(
        self,
        project_id: str,
        tool_name: str,
        input_data: str,
        output_data: str,
        session_id: Optional[str] = None,
        status: str = "success",
        tags: Optional[List[str]] = None,
    ) -> str:
        summary = f"Tool {tool_name} ({status})"
        content = f"### Tool Execution: {tool_name}\n\nStatus: {status}\n\nInput:\n{input_data}\n\nOutput:\n{output_data}"
        extra = {"tool_name": tool_name, "status": status}
        return self.store_memory(
            content=content,
            tags=tags,
            session_id=session_id,
            kind="log",
            project_id=project_id,
            event_type="tool_run",
            source="tool",
            summary=summary,
            extra_metadata=extra,
        )

    def record_file_change(
        self,
        project_id: str,
        file_path: str,
        diff: str,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        summary = f"File change: {file_path}"
        extra = {"file_path": file_path}
        return self.store_memory(
            content=diff,
            tags=tags,
            session_id=session_id,
            kind="file_diff",
            project_id=project_id,
            event_type="file_diff",
            path=file_path,
            summary=summary,
            extra_metadata=extra,
        )

    def record_test_result(
        self,
        project_id: str,
        test_name: str,
        result: str,
        output: str,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        summary = f"Test {test_name}: {result}"
        content = f"### Test Result: {test_name}\n\nResult: {result}\n\nOutput:\n{output}"
        extra = {"test_name": test_name, "result": result}
        return self.store_memory(
            content=content,
            tags=tags,
            session_id=session_id,
            kind="test_result",
            project_id=project_id,
            event_type="test_result",
            summary=summary,
            extra_metadata=extra,
        )

    def create_checkpoint(
        self,
        project_id: str,
        content: str,
        summary: Optional[str] = None,
        plan: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        extra = {"plan": plan} if plan else {}
        return self.store_memory(
            content=content,
            tags=tags,
            session_id=session_id,
            kind="checkpoint",
            project_id=project_id,
            event_type="checkpoint",
            summary=summary or "Checkpoint",
            extra_metadata=extra,
        )

    def get_latest_checkpoint(self, project_id: str) -> Optional[Dict[str, Any]]:
        checkpoints = [
            record
            for record in self.memory_index.values()
            if record["metadata"].get("project_id") == project_id and record["metadata"].get("event_type") == "checkpoint"
        ]
        if not checkpoints:
            return None
        checkpoints.sort(key=lambda r: r["metadata"]["timestamp"], reverse=True)
        latest = checkpoints[0]
        return self.retrieve_memory(latest["metadata"]["id"])

    def list_events(
        self,
        project_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        records = list(self.memory_index.values())
        if project_id:
            records = [r for r in records if r["metadata"].get("project_id") == project_id]
        if event_type:
            records = [r for r in records if r["metadata"].get("event_type") == event_type]
        records.sort(key=lambda r: r["metadata"]["timestamp"], reverse=True)
        return records[:limit]

    def restore_working_set(self, project_id: str, recent_limit: int = 20) -> Dict[str, Any]:
        checkpoint = self.get_latest_checkpoint(project_id)
        project_events = [
            record
            for record in self.memory_index.values()
            if record["metadata"].get("project_id") == project_id
        ]
        project_events.sort(key=lambda r: r["metadata"]["timestamp"], reverse=True)
        recent = project_events[:recent_limit]

        grouped = {
            "file_diff": [],
            "test_result": [],
            "tool_run": [],
            "note": [],
            "plan_update": [],
            "decision": [],
        }
        for record in recent:
            event_type = record["metadata"].get("event_type", "note")
            grouped.setdefault(event_type, [])
            grouped[event_type].append(
                {
                    "id": record["metadata"]["id"],
                    "summary": record["metadata"].get("summary"),
                    "timestamp": record["metadata"]["timestamp"],
                    "preview": record.get("preview"),
                    "path": record["metadata"].get("path"),
                    "tags": record["metadata"].get("tags"),
                }
            )

        return {
            "project_id": project_id,
            "checkpoint": checkpoint,
            "recent_events": grouped,
            "recent_count": len(recent),
        }
