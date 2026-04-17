"""
Overnight runner for local Ollama context benchmarks.

This script is designed for long unattended runs:
- discovers locally installed Ollama models
- runs a larger benchmark matrix
- skips trials that already have JSON output
- writes an aggregate report after every completed trial
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from benchmarks.run_ollama_context_benchmark import run_benchmark


SUPPORTED_DEFAULT_MODELS = (
    "qwen2.5-coder:1.5b",
    "llama3.2:1b",
)


def parse_noise_profiles(raw: Sequence[str]) -> List[Tuple[int, int]]:
    profiles: List[Tuple[int, int]] = []
    for item in raw:
        left, right = item.split(":", 1)
        profiles.append((int(left), int(right)))
    return profiles


def discover_ollama_models() -> List[str]:
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    installed = [model["name"] for model in payload.get("models", [])]
    selected = [name for name in SUPPORTED_DEFAULT_MODELS if name in installed]
    return selected or installed


def mean(values: List[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def summarize_runs(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompt_saved = [run["summary"]["prompt_eval_saved"] for run in runs]
    prompt_reduction = [run["summary"]["prompt_eval_reduction_pct"] for run in runs]
    baseline_quality = [run["summary"]["baseline_quality_avg"] for run in runs]
    fracktal_quality = [run["summary"]["fracktal_quality_avg"] for run in runs]
    return {
        "runs": len(runs),
        "avg_prompt_eval_saved": mean(prompt_saved),
        "avg_prompt_eval_reduction_pct": mean(prompt_reduction),
        "min_prompt_eval_reduction_pct": min(prompt_reduction) if prompt_reduction else 0.0,
        "max_prompt_eval_reduction_pct": max(prompt_reduction) if prompt_reduction else 0.0,
        "avg_baseline_quality": mean(baseline_quality),
        "avg_fracktal_quality": mean(fracktal_quality),
        "fracktal_quality_win_rate": (
            sum(1 for b, f in zip(baseline_quality, fracktal_quality) if f >= b) / len(runs) if runs else 0.0
        ),
    }


def estimate_total_duration_minutes(models: Sequence[str], profiles: Sequence[Tuple[int, int]], trials: int) -> float:
    total_minutes = 0.0
    for _model in models:
        for noise_logs, noise_ui in profiles:
            if noise_logs >= 160 or noise_ui >= 80:
                per_run = 16.0
            elif noise_logs >= 80 or noise_ui >= 40:
                per_run = 11.0
            else:
                per_run = 7.0
            total_minutes += per_run * trials
    return total_minutes


def build_output_name(prefix: str, model: str, noise_logs: int, noise_ui: int, trial: int) -> str:
    safe_model = model.replace(":", "_").replace(".", "_")
    return f"{prefix}_{safe_model}_{noise_logs}_{noise_ui}_trial{trial}.json"


def run_overnight(args: argparse.Namespace) -> Dict[str, Any]:
    models = [item.strip() for item in args.models.split(",") if item.strip()] if args.models else discover_ollama_models()
    profiles = parse_noise_profiles(args.noise_profiles)

    all_runs: List[Dict[str, Any]] = []
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    aggregate_path = Path(args.output)

    for model in models:
        for noise_logs, noise_ui in profiles:
            group_key = f"{model}|logs={noise_logs}|ui={noise_ui}"
            grouped.setdefault(group_key, [])
            for trial in range(args.trials):
                output_name = build_output_name(args.output_prefix, model, noise_logs, noise_ui, trial)
                storage_name = build_output_name(args.storage_prefix, model, noise_logs, noise_ui, trial).removesuffix(".json")
                output_path = Path(output_name)

                if output_path.exists():
                    report = json.loads(output_path.read_text(encoding="utf-8"))
                else:
                    run_args = SimpleNamespace(
                        model=model,
                        storage_dir=storage_name,
                        output=output_name,
                        enable_embeddings=args.enable_embeddings,
                        seed=args.seed + trial,
                        num_predict=args.num_predict,
                        noise_logs=noise_logs,
                        noise_ui=noise_ui,
                    )
                    report = run_benchmark(run_args)

                report["trial"] = trial
                all_runs.append(report)
                grouped[group_key].append(report)

                aggregate = {
                    "models": models,
                    "noise_profiles": [{"noise_logs": logs, "noise_ui": ui} for logs, ui in profiles],
                    "trials": args.trials,
                    "seed_start": args.seed,
                    "estimated_duration_minutes": estimate_total_duration_minutes(models, profiles, args.trials),
                    "aggregate": summarize_runs(all_runs),
                    "groups": {key: summarize_runs(runs) for key, runs in grouped.items()},
                }
                aggregate_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")

    return json.loads(aggregate_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a resumable overnight benchmark matrix for local Ollama models.")
    parser.add_argument("--models", default="", help="Comma-separated Ollama models. Default: auto-discover local models.")
    parser.add_argument("--trials", type=int, default=5, help="Trials per model/profile.")
    parser.add_argument(
        "--noise-profiles",
        nargs="+",
        default=["24:12", "80:40", "160:80"],
        help="Pairs of noise_logs:noise_ui.",
    )
    parser.add_argument("--seed", type=int, default=7, help="Starting seed.")
    parser.add_argument("--num-predict", type=int, default=220, help="Maximum generated tokens per answer.")
    parser.add_argument("--storage-prefix", default=".ollama_overnight_context", help="Prefix for temporary memory stores.")
    parser.add_argument("--output-prefix", default="ollama_overnight_trial", help="Prefix for per-trial JSON files.")
    parser.add_argument("--output", default="ollama_overnight_summary.json", help="Aggregate summary path.")
    parser.add_argument("--enable-embeddings", action="store_true", help="Enable optional embedding retrieval.")
    args = parser.parse_args()

    summary = run_overnight(args)
    print(json.dumps(summary["aggregate"], indent=2))


if __name__ == "__main__":
    main()
