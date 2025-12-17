# Fracktal MCP Integration Guide

This document explains how to wire any MCP-capable agent into the Fracktal memory server, capture project timelines, and restore working context on demand.

---

## 1. Concepts & vocabulary

| Term | Meaning |
|------|--------|
| `project_id` | Stable identifier for a repo, workspace, or product track. Everything in Fracktal is partitioned by project. |
| `session_id` | Optional identifier for a single agent run (helps isolate experiments). |
| `event_type` | Typed event such as `tool_run`, `file_diff`, `test_result`, `checkpoint`, `plan_update`, `decision`, `note`. |
| `kind` | Data subtype (`text`, `log`, `file_diff`, `checkpoint`, etc.). |
| `tags`, `path`, `summary` | Arbitrary metadata that drives filtering and UI surfaces. |

Every stored artifact is losslessly compressed via FRACKTAL and can be reconstructed perfectly later. Metadata powers search and working-set restore.

---

## 2. Minimal MCP configuration

1. Install & run the server.
   ```bash
   git clone https://github.com/GoryGrey/Fracktal-MCP.git
   cd Fracktal-MCP
   pip install -e .
   python -m mcp_server.server
   ```
2. Add the server to your MCP client (example for Claude Desktop):
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

No additional infrastructure is required; the server writes to `fracktal_memories/` by default.

---

## 3. Recommended agent policy

1. **Begin session**
   - Fetch `restore_working_set(project_id=...)`.
   - Summarize the checkpoint + open diffs/tests/decisions inside the agent prompt.
2. **While working**
   - After every tool call, log it via `record_tool_run`.
   - After every file edit, send the diff through `record_file_change`.
   - After running tests, call `record_test_result`.
   - When a plan changes or a notable decision happens, store it with `store_memory(..., event_type="plan_update" | "decision")`.
3. **Periodically (e.g. every 5 steps)**
   - Call `create_checkpoint` with a summary of the current plan, blockers, and next steps.
4. **Before exiting**
   - Ensure a final checkpoint is created.

By following this policy, the agent can crash or be restarted days later and still reconstruct context immediately.

---

## 4. Tool reference & examples

### 4.1 Recording tool runs

```jsonc
{
  "tool_name": "record_tool_run",
  "arguments": {
    "project_id": "alpha-app",
    "tool_name": "pytest",
    "input_data": "pytest -q tests/test_auth.py",
    "output_data": "1 failed, 42 passed",
    "status": "failure",
    "session_id": "session-123",
    "tags": ["tests", "pytest"]
  }
}
```

### 4.2 Storing file diffs

```jsonc
{
  "tool_name": "record_file_change",
  "arguments": {
    "project_id": "alpha-app",
    "file_path": "src/auth.py",
    "diff": "diff --git a/src/auth.py b/src/auth.py ...",
    "session_id": "session-123",
    "tags": ["diff", "auth"]
  }
}
```

### 4.3 Capturing checkpoints

```jsonc
{
  "tool_name": "create_checkpoint",
  "arguments": {
    "project_id": "alpha-app",
    "content": "Checkpoint after fixing login regression.\nOpen tasks:\n1) add mobile test\n2) document feature flag.",
    "summary": "Checkpoint – login fix",
    "plan": "1) finalize middleware\n2) extend coverage\n3) rollout",
    "session_id": "session-123",
    "tags": ["plan", "checkpoint"]
  }
}
```

### 4.4 Restoring context

```jsonc
{
  "tool_name": "restore_working_set",
  "arguments": {
    "project_id": "alpha-app",
    "recent_limit": 15
  }
}
```

Use the returned checkpoint + grouped events to build the agent’s working memory block (or feed it into system prompts).

---

## 5. Searching & filtering

- `search_memories(query="pytest failure", project_id="alpha-app", event_types=["test_result"], limit=5)`
- `list_recent_memories(project_id="alpha-app", session_id="session-123", limit=10)`
- `list_events(project_id="alpha-app", event_type="decision", limit=20)`

Filters can be combined to keep multiple repos isolated inside the same server instance.

---

## 6. Troubleshooting & tips

- **Index rebuilds** – Deleting `fracktal_memories/index.json` forces a clean rebuild on next launch; raw codices remain intact.
- **Embeddings** – Install `sentence-transformers` and set `FRACKTAL_ENABLE_EMBEDDINGS=1` to include vector search; otherwise the server falls back to structural + BM25.
- **Storage hygiene** – Old projects can be archived by moving their `.json` codices + updating `index.json`, or by running a second server with a different `--storage-dir`.
- **CI verification** – `python benchmarks/run_benchmarks.py ...` is deterministic; run it in CI to ensure lossless recall and retrieval metrics stay healthy.

---

Questions or feature requests? Reach out at gorygrey@protonmail.com. 
