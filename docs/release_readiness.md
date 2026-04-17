# Release Readiness

Use this checklist before tagging or publishing `fracktal-mcp`.

## 1. Clean environment

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Why: a clean virtualenv catches undeclared dependencies and packaging drift that a long-lived workstation can hide.

## 2. Automated verification

```bash
python -m pytest
python benchmarks/run_benchmarks.py --storage-dir tmp_bench --output bench_report.json
```

Expected outcome:

- tests pass
- benchmark run completes without lossless failures
- benchmark JSON is generated and readable

## 3. MCP smoke test

```bash
python -m mcp_server.server
```

From your MCP client, verify this minimum flow:

1. `store_memory`
2. `search_memories`
3. `record_file_change`
4. `record_test_result`
5. `create_checkpoint`
6. `restore_working_set`

Expected outcome:

- the server starts without import errors
- `fracktal_memories/` is created, or the path from `FRACKTAL_STORAGE_DIR`
- checkpoint and recent events are returned for the target `project_id`

## 4. Persistence recovery

Delete only `index.json`, then restart the server.

Expected outcome:

- the index rebuilds automatically from the stored codex files
- previously stored memories are still retrievable

## 5. Docs and package metadata

Confirm these are accurate before release:

- version in `setup.py` and `fracktal/__init__.py`
- repository URLs in `setup.py`
- install commands in `README.md`
- MCP usage examples in `docs/mcp_usage.md`

## 6. Optional features

If you plan to advertise embeddings or visualization support, verify them explicitly:

```bash
python -m pip install sentence-transformers
python -m pip install -e .[viz]
```

Then test:

- `FRACKTAL_ENABLE_EMBEDDINGS=1`
- visualization utilities in `fracktal.utils`

If you do not test an optional feature, document it as optional and leave it out of the release notes.

## 7. Local LLM benchmark

If you want to claim context-efficiency or token savings, run the local Ollama benchmarks and keep the JSON reports:

```bash
python benchmarks/run_ollama_context_benchmark.py --model qwen2.5-coder:1.5b --output ollama_context_benchmark.json
python benchmarks/run_ollama_context_stress.py --models qwen2.5-coder:1.5b,llama3.2:1b --trials 2 --noise-profiles 24:12 80:40 --output ollama_context_stress.json
```

What to verify:

- `prompt_eval_count` is lower with Fracktal than with the full-history baseline
- answer quality is at least comparable for the same tasks
- the result still holds when irrelevant history is increased
