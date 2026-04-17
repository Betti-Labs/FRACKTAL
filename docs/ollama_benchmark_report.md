# Ollama Context Benchmark Report

Benchmark date: April 16-17, 2026

## Scope

This report summarizes the local-model benchmark runs comparing:

- `baseline`: send the full project history to the model inline
- `fracktal`: send a compact context assembled from the latest checkpoint, relevant recent events, and targeted search results from Fracktal

The benchmark was run with local Ollama models against the synthetic project-history workload implemented in `benchmarks/run_ollama_context_benchmark.py` and the overnight matrix runner in `benchmarks/run_overnight_context_benchmarks.py`.

## Environment

- Runtime: local Ollama
- Models:
  - `qwen2.5-coder:1.5b`
  - `llama3.2:1b`
- Trials: `5` per model/profile
- Noise profiles:
  - `24` irrelevant logs / `12` irrelevant UI diffs
  - `80` irrelevant logs / `40` irrelevant UI diffs
  - `160` irrelevant logs / `80` irrelevant UI diffs
- Total completed runs: `30`

## Measurement

Token usage was measured from Ollama's own response fields:

- `prompt_eval_count`
- `eval_count`

Answer quality was scored with a simple keyword-match rubric over three tasks:

- `regression_root_cause`
- `next_steps`
- `cache_flag`

This quality metric is useful for consistency across many trials, but it is still a heuristic. It is not a substitute for human evaluation.

## Headline Results

Aggregate overnight summary:

- Average prompt tokens saved per run: `8890`
- Average prompt-token reduction: `78.2%`
- Reduction range: `67.8%` to `83.8%`
- Average baseline quality: `0.148`
- Average Fracktal quality: `0.494`
- Fracktal quality win rate: `1.0`

Interpretation:

- On this benchmark suite, Fracktal consistently reduced prompt-token usage versus full-history prompting.
- On the same tasks, Fracktal also outperformed the baseline quality metric in every model/noise group that was tested.

## Results By Group

| Model | Noise Profile | Avg Prompt Reduction | Baseline Quality | Fracktal Quality |
|------|------|------:|------:|------:|
| `qwen2.5-coder:1.5b` | `24/12` | `67.9%` | `0.50` | `0.67` |
| `qwen2.5-coder:1.5b` | `80/40` | `82.7%` | `0.00` | `0.38` |
| `qwen2.5-coder:1.5b` | `160/80` | `82.7%` | `0.00` | `0.34` |
| `llama3.2:1b` | `24/12` | `68.5%` | `0.39` | `0.84` |
| `llama3.2:1b` | `80/40` | `83.7%` | `0.00` | `0.39` |
| `llama3.2:1b` | `160/80` | `83.6%` | `0.00` | `0.34` |

## What The Benchmark Supports

These results support the following claim:

- For noisy project-history tasks like the ones in this suite, Fracktal can reduce prompt-token usage substantially while improving retrieval quality relative to a naive full-history baseline.

These results do not yet support stronger claims such as:

- Fracktal is always better than every other context strategy
- Fracktal improves every task type
- The measured gains generalize to larger models, longer coding sessions, or production workloads without further testing

## Audit Findings

### 1. The baseline degrades badly under noisy history

Once irrelevant history is increased, the baseline quality falls to `0.0` for both tested models in the `80/40` and `160/80` profiles.

That means the raw "dump the whole timeline into the prompt" strategy is not resilient to history growth on this workload.

### 2. Fracktal's gains come mostly from prompt compression plus relevance filtering

The biggest token savings appear when the history becomes noisy:

- around `68%` savings at lower noise
- around `83%` savings at medium/high noise

This is consistent with the design: Fracktal is helping by filtering irrelevant history, not by making the model intrinsically smarter.

### 3. The main weak spot is partial recovery of root-cause details under heavy noise

The weakest Fracktal task across models was `regression_root_cause` under the heavier noise profiles.

Observed pattern:

- the model often recovered the correct file path
- it often missed the exact failing test name
- it sometimes mixed the auth regression with the cache observation

This is a retrieval-packaging or prompt-shaping issue, not evidence that the full-history baseline is better. In the same heavy-noise settings, the baseline usually collapsed completely.

### 4. The `next_steps` task was stable but often only partially credited by the rubric

Fracktal consistently returned useful next-step answers, usually:

- add regression coverage
- document token rotation behavior

However, many answers scored `0.5` instead of `1.0` because the rubric required exact keyword coverage rather than allowing semantically equivalent phrasing.

### 5. The `cache_flag` task is still brittle at higher noise

Under heavier noise, Fracktal often correctly surfaced `tenant flag beta=true`, but sometimes failed to also state the full condition in the exact expected phrasing.

This suggests two next improvements:

- make targeted search more explicit for config/flag questions
- use a more semantic evaluator instead of exact keyword matching

## Representative Failure Modes

Examples seen in the trial outputs:

- the model answered "`src/auth/session.py`" correctly but misattributed the root cause to the cache issue
- the model identified "add regression test covering refresh-token rotation" as a next step, but the score stayed partial because the evaluator expected a narrower exact phrase
- the model recognized `tenant flag beta=true` but omitted the full "during bootstrap warmup" condition

## Recommended Next Steps

1. Add a second benchmark suite based on real coding-session histories from this repository.
2. Introduce a semantic or LLM-judged evaluator in addition to keyword matching.
3. Compare Fracktal against stronger baselines than "full history inline", such as naive recency truncation or BM25-only retrieval.
4. Run the same matrix on larger local models to check whether the gains persist as model capacity rises.
5. Tune the Fracktal context pack for root-cause tasks under extreme noise.
