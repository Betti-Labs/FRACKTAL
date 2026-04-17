"""
Real context-recovery benchmark for FRACKTAL MCP using a local Ollama model.

This compares two prompting modes for the same task set:

1. Baseline: send the model the full project timeline inline.
2. FRACKTAL-assisted: retrieve a compact working set with restore_working_set
   plus targeted search results and send only that context.

Outputs actual Ollama token counters (`prompt_eval_count`, `eval_count`) so the
comparison reflects real model usage instead of estimates.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import textwrap
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from mcp_server.memory_store import MemoryStore

PROJECT_ID = "ollama-context-benchmark"
SESSION_ID = "qwen-context-session"
DEFAULT_SEED = 7
DEFAULT_NUM_PREDICT = 220


@dataclass(frozen=True)
class TaskSpec:
    name: str
    question: str
    expected_keywords: Sequence[str]


TASKS: Sequence[TaskSpec] = (
    TaskSpec(
        name="regression_root_cause",
        question=(
            "What test is failing, which file was changed most recently for the auth work, "
            "and what is the likely cause of the regression? Answer in 3 bullets."
        ),
        expected_keywords=("test_login_refresh_token", "src/auth/session.py", "refresh token"),
    ),
    TaskSpec(
        name="next_steps",
        question=(
            "What are the next two recommended actions for the team based on the latest checkpoint "
            "and recent failures? Keep it to 2 bullets."
        ),
        expected_keywords=("add regression test", "document token rotation"),
    ),
    TaskSpec(
        name="cache_flag",
        question=(
            "Which feature flag or config setting is linked to the cache issue, and under what "
            "condition does it spike? Answer in 2 bullets."
        ),
        expected_keywords=("tenant flag beta=true", "cache misses spike"),
    ),
)


def ollama_generate(model: str, prompt: str, seed: int = DEFAULT_SEED, num_predict: int = DEFAULT_NUM_PREDICT) -> Dict[str, Any]:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": num_predict,
                "seed": seed,
            },
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def store_event(
    store: MemoryStore,
    *,
    content: str,
    kind: str,
    event_type: str,
    summary: str,
    tags: List[str],
    path: str | None = None,
) -> str:
    return store.store_memory(
        content=content,
        kind=kind,
        event_type=event_type,
        project_id=PROJECT_ID,
        session_id=SESSION_ID,
        summary=summary,
        tags=tags,
        path=path,
    )


def populate_store(store: MemoryStore, noise_logs: int = 24, noise_ui: int = 12) -> None:
    store_event(
        store,
        content=textwrap.dedent(
            """\
            Checkpoint after auth hotfix attempt.
            Priorities:
            1. add regression test covering refresh-token rotation
            2. document token rotation behavior for the desktop client
            3. verify the cache issue is unrelated before release
            """
        ),
        kind="checkpoint",
        event_type="checkpoint",
        summary="Checkpoint after auth hotfix attempt",
        tags=["plan", "checkpoint", "auth"],
    )
    store_event(
        store,
        content=textwrap.dedent(
            """\
            diff --git a/src/auth/session.py b/src/auth/session.py
            @@
            -refresh_token = token_store.current(user_id)
            +refresh_token = token_store.latest(user_id)
            +if refresh_token is None:
            +    return unauthorized("missing refresh token")
            """
        ),
        kind="file_diff",
        event_type="file_diff",
        summary="Auth session refresh flow update",
        tags=["auth", "diff"],
        path="src/auth/session.py",
    )
    store_event(
        store,
        content="pytest::test_login_refresh_token FAILED AssertionError: expected 200 got 401 after token rotation",
        kind="test_result",
        event_type="test_result",
        summary="Refresh token regression in auth suite",
        tags=["tests", "auth", "failure"],
    )
    store_event(
        store,
        content="[ERROR] desktop login uses stale refresh token after rotation; server now expects latest(user_id)",
        kind="log",
        event_type="tool_run",
        summary="Auth failure trace from desktop login",
        tags=["logs", "auth"],
    )
    store_event(
        store,
        content="Cache misses spike when tenant flag beta=true during bootstrap warmup; likely separate from auth regression.",
        kind="note",
        event_type="note",
        summary="Observation about cache spikes",
        tags=["cache", "note"],
    )
    store_event(
        store,
        content="Decision: postpone rollout until token rotation docs are updated and a regression test is merged.",
        kind="decision",
        event_type="decision",
        summary="Rollout blocked on docs and regression coverage",
        tags=["decision", "release"],
    )

    # Add noise so the baseline prompt has a realistic amount of irrelevant history.
    for idx in range(noise_logs):
        store_event(
            store,
            content=textwrap.dedent(
                f"""\
                Build log {idx}.
                Module: analytics.worker_{idx}
                Status: success
                Note: processed shard {idx} with no auth impact.
                """
            ),
            kind="log",
            event_type="tool_run",
            summary=f"Background analytics run {idx}",
            tags=["analytics", "noise"],
        )
    for idx in range(noise_ui):
        store_event(
            store,
            content=textwrap.dedent(
                f"""\
                diff --git a/src/ui/panel_{idx}.tsx b/src/ui/panel_{idx}.tsx
                @@
                -oldColor = "gray"
                +oldColor = "blue"
                """
            ),
            kind="file_diff",
            event_type="file_diff",
            summary=f"UI cosmetic tweak {idx}",
            tags=["ui", "noise"],
            path=f"src/ui/panel_{idx}.tsx",
        )


def serialize_full_timeline(store: MemoryStore) -> str:
    events = store.list_events(project_id=PROJECT_ID, limit=200)
    sections = []
    for record in reversed(events):
        meta = record["metadata"]
        sections.append(
            textwrap.dedent(
                f"""\
                EVENT_TYPE: {meta.get('event_type')}
                KIND: {meta.get('kind')}
                SUMMARY: {meta.get('summary')}
                PATH: {meta.get('path')}
                TAGS: {', '.join(meta.get('tags', []))}
                CONTENT:
                {record.get('text', '')}
                """
            ).strip()
        )
    return "\n\n".join(sections)


def serialize_mcp_context(store: MemoryStore, question: str) -> str:
    checkpoint = store.get_latest_checkpoint(PROJECT_ID)
    recent_events = store.list_events(project_id=PROJECT_ID, limit=80)
    relevant_recent = [
        event
        for event in recent_events
        if "noise" not in event["metadata"].get("tags", [])
        and event["metadata"].get("event_type") != "checkpoint"
    ][:6]
    search_results = store.search_memories(
        question,
        project_id=PROJECT_ID,
        limit=6,
        event_types=["checkpoint", "file_diff", "test_result", "tool_run", "decision", "note"],
    )

    recent_sections = []
    for event in reversed(relevant_recent):
        meta = event["metadata"]
        recent_sections.append(
            textwrap.dedent(
                f"""\
                SUMMARY: {meta.get('summary')}
                EVENT_TYPE: {meta.get('event_type')}
                PATH: {meta.get('path')}
                TAGS: {', '.join(meta.get('tags', []))}
                CONTENT:
                {event.get('text', '')}
                """
            ).strip()
        )

    search_sections = []
    for result in search_results:
        restored = store.retrieve_memory(result.id)
        search_sections.append(
            textwrap.dedent(
                f"""\
                SUMMARY: {result.summary}
                EVENT_TYPE: {result.event_type}
                PATH: {result.path}
                SCORE: {result.score:.3f}
                CONTENT:
                {restored['content'] if restored else result.preview}
                """
            ).strip()
        )

    checkpoint_text = json.dumps(checkpoint, indent=2, default=str) if checkpoint else "{}"
    return (
        "LATEST_CHECKPOINT:\n"
        + checkpoint_text
        + "\n\nRECENT_RELEVANT_EVENTS:\n"
        + "\n\n".join(recent_sections)
        + "\n\nTARGETED_SEARCH:\n"
        + "\n\n".join(search_sections)
    )


def build_prompt(context_label: str, context: str, question: str) -> str:
    return textwrap.dedent(
        f"""\
        You are validating project state from a development history.
        Use only the provided context.
        If the answer is uncertain, say so instead of inventing facts.

        CONTEXT_MODE: {context_label}
        CONTEXT:
        {context}

        QUESTION:
        {question}
        """
    )


def score_response(response: str, expected_keywords: Sequence[str]) -> Dict[str, Any]:
    lowered = response.lower()
    matches = [keyword for keyword in expected_keywords if keyword.lower() in lowered]
    return {
        "matched_keywords": matches,
        "score": len(matches) / len(expected_keywords),
    }


def run_mode(
    model: str,
    mode_name: str,
    store: MemoryStore,
    task: TaskSpec,
    *,
    seed: int = DEFAULT_SEED,
    num_predict: int = DEFAULT_NUM_PREDICT,
) -> Dict[str, Any]:
    if mode_name == "baseline":
        context = serialize_full_timeline(store)
    elif mode_name == "fracktal":
        context = serialize_mcp_context(store, task.question)
    else:
        raise ValueError(f"Unknown mode: {mode_name}")

    prompt = build_prompt(mode_name, context, task.question)
    result = ollama_generate(model, prompt, seed=seed, num_predict=num_predict)
    quality = score_response(result.get("response", ""), task.expected_keywords)
    return {
        "mode": mode_name,
        "prompt_chars": len(prompt),
        "context_chars": len(context),
        "prompt_eval_count": result.get("prompt_eval_count"),
        "eval_count": result.get("eval_count"),
        "response": result.get("response", "").strip(),
        "quality": quality,
    }


def summarize(results: Dict[str, Any]) -> Dict[str, Any]:
    baseline_prompt = sum(item["baseline"]["prompt_eval_count"] for item in results["tasks"])
    fracktal_prompt = sum(item["fracktal"]["prompt_eval_count"] for item in results["tasks"])
    baseline_eval = sum(item["baseline"]["eval_count"] for item in results["tasks"])
    fracktal_eval = sum(item["fracktal"]["eval_count"] for item in results["tasks"])
    baseline_quality = sum(item["baseline"]["quality"]["score"] for item in results["tasks"]) / len(results["tasks"])
    fracktal_quality = sum(item["fracktal"]["quality"]["score"] for item in results["tasks"]) / len(results["tasks"])
    return {
        "baseline_prompt_eval_total": baseline_prompt,
        "fracktal_prompt_eval_total": fracktal_prompt,
        "prompt_eval_saved": baseline_prompt - fracktal_prompt,
        "prompt_eval_reduction_pct": ((baseline_prompt - fracktal_prompt) / baseline_prompt * 100) if baseline_prompt else 0.0,
        "baseline_eval_total": baseline_eval,
        "fracktal_eval_total": fracktal_eval,
        "baseline_quality_avg": baseline_quality,
        "fracktal_quality_avg": fracktal_quality,
    }


def run_benchmark(args: argparse.Namespace) -> Dict[str, Any]:
    storage_dir = Path(args.storage_dir)
    if storage_dir.exists():
        for _ in range(5):
            try:
                shutil.rmtree(storage_dir)
                break
            except PermissionError:
                time.sleep(0.5)
        else:
            fallback = storage_dir.with_name(f"{storage_dir.name}_{os.getpid()}")
            storage_dir = fallback
    storage_dir.mkdir(parents=True)

    store = MemoryStore(storage_dir=str(storage_dir), enable_embeddings=args.enable_embeddings)
    populate_store(store, noise_logs=args.noise_logs, noise_ui=args.noise_ui)

    task_results = []
    for task in TASKS:
        baseline = run_mode(args.model, "baseline", store, task, seed=args.seed, num_predict=args.num_predict)
        fracktal = run_mode(args.model, "fracktal", store, task, seed=args.seed, num_predict=args.num_predict)
        task_results.append(
            {
                "task": task.name,
                "question": task.question,
                "baseline": baseline,
                "fracktal": fracktal,
            }
        )

    report = {
        "model": args.model,
        "project_id": PROJECT_ID,
        "seed": args.seed,
        "num_predict": args.num_predict,
        "noise_logs": args.noise_logs,
        "noise_ui": args.noise_ui,
        "tasks": task_results,
    }
    report["summary"] = summarize(report)
    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark prompt usage with and without FRACKTAL context retrieval.")
    parser.add_argument("--model", default="qwen2.5-coder:1.5b", help="Local Ollama model to benchmark.")
    parser.add_argument("--storage-dir", default=".ollama_context_bench", help="Temporary storage directory for benchmark memories.")
    parser.add_argument("--output", default="ollama_context_benchmark.json", help="Where to write the JSON report.")
    parser.add_argument("--enable-embeddings", action="store_true", help="Enable optional embedding retrieval in FRACKTAL.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic Ollama seed.")
    parser.add_argument("--num-predict", type=int, default=DEFAULT_NUM_PREDICT, help="Maximum generated tokens per answer.")
    parser.add_argument("--noise-logs", type=int, default=24, help="Number of irrelevant log events to inject.")
    parser.add_argument("--noise-ui", type=int, default=12, help="Number of irrelevant UI diffs to inject.")
    args = parser.parse_args()

    try:
        report = run_benchmark(args)
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to reach Ollama API at http://127.0.0.1:11434: {exc}") from exc

    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
