import json
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from .memory_store import MemoryStore

# Initialize Server
mcp = FastMCP("Fracktal Memory Backend")

# Initialize Memory Store (default location inside repo)
store = MemoryStore(storage_dir="fracktal_memories")


@mcp.tool()
def store_memory(
    content: str,
    tags: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    kind: str = "text",
    project_id: Optional[str] = None,
    event_type: str = "note",
    source: Optional[str] = None,
    path: Optional[str] = None,
    summary: Optional[str] = None,
) -> str:
    """
    Store arbitrary content losslessly with rich metadata.
    """
    return store.store_memory(
        content=content,
        tags=tags,
        session_id=session_id,
        kind=kind,
        project_id=project_id,
        event_type=event_type,
        source=source,
        path=path,
        summary=summary,
    )


@mcp.tool()
def retrieve_memory(memory_id: str) -> str:
    """
    Retrieve a memory by ID.
    """
    result = store.retrieve_memory(memory_id)
    if result:
        return json.dumps(result, indent=2, default=str)
    return json.dumps({"error": "Memory not found."}, indent=2)


@mcp.tool()
def search_memories(
    query: str,
    limit: int = 5,
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    kinds: Optional[List[str]] = None,
    event_types: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    path: Optional[str] = None,
) -> str:
    """
    Search memories using hybrid (structural + lexical + vector) retrieval with optional filters.
    """
    results = store.search_memories(
        query=query,
        limit=limit,
        project_id=project_id,
        session_id=session_id,
        kinds=kinds,
        event_types=event_types,
        tags=tags,
        path=path,
    )
    serialized = [
        {
            "id": r.id,
            "preview": r.preview,
            "score": r.score,
            "tags": r.tags,
            "session_id": r.session_id,
            "project_id": r.project_id,
            "kind": r.kind,
            "event_type": r.event_type,
            "path": r.path,
            "summary": r.summary,
        }
        for r in results
    ]
    return json.dumps(serialized, indent=2)


@mcp.tool()
def list_recent_memories(
    session_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 20,
) -> str:
    """
    List the most recent memories for a session/project.
    """
    results = store.list_recent_memories(session_id=session_id, project_id=project_id, limit=limit)
    return json.dumps(results, indent=2, default=str)


@mcp.tool()
def get_memory_stats() -> str:
    """
    Get global statistics about the memory store.
    """
    return json.dumps(store.get_stats(), indent=2)


@mcp.tool()
def optimize_corpus() -> str:
    """
    Trigger a symbolic corpus analysis pass.
    """
    return json.dumps(store.optimize_corpus(), indent=2)


@mcp.tool()
def record_tool_run(
    project_id: str,
    tool_name: str,
    input_data: str,
    output_data: str,
    session_id: Optional[str] = None,
    status: str = "success",
    tags: Optional[List[str]] = None,
) -> str:
    """
    Persist a tool execution (input/output/status) as a structured event.
    """
    return store.record_tool_run(
        project_id=project_id,
        tool_name=tool_name,
        input_data=input_data,
        output_data=output_data,
        session_id=session_id,
        status=status,
        tags=tags,
    )


@mcp.tool()
def record_file_change(
    project_id: str,
    file_path: str,
    diff: str,
    session_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> str:
    """
    Store a file diff or snapshot for a project.
    """
    return store.record_file_change(
        project_id=project_id,
        file_path=file_path,
        diff=diff,
        session_id=session_id,
        tags=tags,
    )


@mcp.tool()
def record_test_result(
    project_id: str,
    test_name: str,
    result: str,
    output: str,
    session_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> str:
    """
    Store the outcome of a test run.
    """
    return store.record_test_result(
        project_id=project_id,
        test_name=test_name,
        result=result,
        output=output,
        session_id=session_id,
        tags=tags,
    )


@mcp.tool()
def create_checkpoint(
    project_id: str,
    content: str,
    summary: Optional[str] = None,
    plan: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> str:
    """
    Create a project checkpoint (working set summary + plan).
    """
    return store.create_checkpoint(
        project_id=project_id,
        content=content,
        summary=summary,
        plan=plan,
        session_id=session_id,
        tags=tags,
    )


@mcp.tool()
def get_latest_checkpoint(project_id: str) -> str:
    """
    Retrieve the latest checkpoint for a project.
    """
    checkpoint = store.get_latest_checkpoint(project_id)
    if not checkpoint:
        return json.dumps({"error": "No checkpoint available"}, indent=2)
    return json.dumps(checkpoint, indent=2, default=str)


@mcp.tool()
def restore_working_set(project_id: str, recent_limit: int = 20) -> str:
    """
    Return the latest checkpoint + recent structured events for a project.
    """
    data = store.restore_working_set(project_id=project_id, recent_limit=recent_limit)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def list_events(
    project_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
) -> str:
    """
    List structured events (diffs, tool runs, etc.) with optional filters.
    """
    events = store.list_events(project_id=project_id, event_type=event_type, limit=limit)
    return json.dumps(events, indent=2, default=str)


if __name__ == "__main__":
    mcp.run()
