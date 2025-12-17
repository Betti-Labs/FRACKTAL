import sys
from pathlib import Path

from mcp_server.memory_store import MemoryStore

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))


def test_project_aware_flow(tmp_path):
    storage_dir = tmp_path / "memories"
    store = MemoryStore(storage_dir=str(storage_dir), enable_embeddings=False)

    project_id = "proj-alpha"
    session_id = "session-42"

    # Lossless storage + retrieval
    raw = "Initial design doc for project alpha."
    mem_id = store.store_memory(raw, tags=["design"], session_id=session_id, kind="note", project_id=project_id)
    retrieved = store.retrieve_memory(mem_id)
    assert retrieved is not None
    assert retrieved["content"] == raw
    assert retrieved["metadata"]["project_id"] == project_id

    # Structured events
    diff_id = store.record_file_change(project_id, "src/app.py", "+++import os", session_id=session_id)
    tool_id = store.record_tool_run(project_id, "pytest", "pytest -q", "1 failed", session_id=session_id, status="failure")
    test_id = store.record_test_result(project_id, "test_login", "failed", "AssertionError", session_id=session_id)
    checkpoint_id = store.create_checkpoint(project_id, "Checkpoint body", summary="After fixing login", plan="1) fix login\n2) add tests")

    assert diff_id != tool_id != test_id != checkpoint_id

    # Hybrid search with filters (ensure IDs returned)
    results = store.search_memories("login failure", project_id=project_id, event_types=["test_result"], limit=3)
    assert results
    assert results[0].event_type == "test_result"
    assert any(r.id == test_id for r in results)

    # Recent listing scoped by project
    recent = store.list_recent_memories(project_id=project_id, limit=5)
    assert len(recent) == 5  # we inserted 5 events for the project

    # Working set restoration returns checkpoint + grouped events
    working_set = store.restore_working_set(project_id, recent_limit=10)
    assert working_set["project_id"] == project_id
    assert working_set["checkpoint"]["metadata"]["id"] == checkpoint_id
    assert working_set["recent_events"]["file_diff"][0]["id"] == diff_id
    assert working_set["recent_events"]["tool_run"][0]["id"] == tool_id
    assert working_set["recent_events"]["test_result"][0]["id"] == test_id

    # Stats include project totals and optimizer still runs
    stats = store.get_stats()
    assert stats["projects"][project_id] >= 5
    optimize = store.optimize_corpus()
    assert optimize["optimized"] is True
