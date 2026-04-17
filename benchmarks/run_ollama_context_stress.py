"""
Stress runner for the local Ollama context benchmark.

This executes repeated trials across one or more models and noise profiles,
then aggregates token savings and answer-quality metrics.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from benchmarks.run_ollama_context_benchmark import run_benchmark


def parse_noise_profiles(raw: Sequence[str]) -> List[Tuple[int, int]]:
    profiles: List[Tuple[int, int]] = []
    for item in raw:
        left, right = item.split(":", 1)
        profiles.append((int(left), int(right)))
    return profiles


def mean(values: List[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def summarize_group(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompt_reduction = [run["summary"]["prompt_eval_reduction_pct"] for run in runs]
    prompt_saved = [run["summary"]["prompt_eval_saved"] for run in runs]
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


def run_stress(args: argparse.Namespace) -> Dict[str, Any]:
    all_runs: List[Dict[str, Any]] = []
    by_group: Dict[str, List[Dict[str, Any]]] = {}

    models = [model.strip() for model in args.models.split(",") if model.strip()]
    profiles = parse_noise_profiles(args.noise_profiles)

    for model in models:
        for noise_logs, noise_ui in profiles:
            group_key = f"{model}|logs={noise_logs}|ui={noise_ui}"
            by_group[group_key] = []
            for trial in range(args.trials):
                seed = args.seed + trial
                storage_dir = f"{args.storage_prefix}_{model.replace(':', '_').replace('.', '_')}_{noise_logs}_{noise_ui}_trial{trial}"
                output = f"{args.output_prefix}_{model.replace(':', '_').replace('.', '_')}_{noise_logs}_{noise_ui}_trial{trial}.json"
                run_args = SimpleNamespace(
                    model=model,
                    storage_dir=storage_dir,
                    output=output,
                    enable_embeddings=args.enable_embeddings,
                    seed=seed,
                    num_predict=args.num_predict,
                    noise_logs=noise_logs,
                    noise_ui=noise_ui,
                )
                report = run_benchmark(run_args)
                report["trial"] = trial
                all_runs.append(report)
                by_group[group_key].append(report)

    summary = {group: summarize_group(runs) for group, runs in by_group.items()}
    aggregate = summarize_group(all_runs)
    result = {
        "models": models,
        "noise_profiles": [{"noise_logs": logs, "noise_ui": ui} for logs, ui in profiles],
        "trials": args.trials,
        "seed_start": args.seed,
        "aggregate": aggregate,
        "groups": summary,
        "runs": all_runs,
    }
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repeated Ollama context benchmark trials.")
    parser.add_argument("--models", default="qwen2.5-coder:1.5b", help="Comma-separated Ollama model names.")
    parser.add_argument("--trials", type=int, default=3, help="How many trials to run per model/profile.")
    parser.add_argument(
        "--noise-profiles",
        nargs="+",
        default=["24:12", "80:40"],
        help="Pairs of noise_logs:noise_ui, for example '24:12 80:40'.",
    )
    parser.add_argument("--seed", type=int, default=7, help="Starting seed; each trial increments by one.")
    parser.add_argument("--num-predict", type=int, default=220, help="Maximum generated tokens per answer.")
    parser.add_argument("--storage-prefix", default=".ollama_context_stress", help="Prefix for temporary storage directories.")
    parser.add_argument("--output-prefix", default="ollama_context_trial", help="Prefix for per-trial JSON reports.")
    parser.add_argument("--output", default="ollama_context_stress.json", help="Where to write the aggregate JSON report.")
    parser.add_argument("--enable-embeddings", action="store_true", help="Enable optional embedding retrieval in FRACKTAL.")
    args = parser.parse_args()

    result = run_stress(args)
    print(json.dumps(result["aggregate"], indent=2))


if __name__ == "__main__":
    main()
