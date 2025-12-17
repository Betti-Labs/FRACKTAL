
import argparse
import json
import os
import random
import string
import sys
import time
import uuid

# Ensure we can import the server modules
sys.path.append(os.getcwd())

from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from rich.table import Table

from mcp_server.memory_store import MemoryStore

console = Console()

def generate_random_text(length=100):
    return ''.join(random.choices(string.ascii_letters + string.digits + " ", k=length))

def generate_complex_memory(index):
    """Generates varied structured data."""
    types = ["code", "json", "log", "prose"]
    kind = types[index % 4]
    
    if kind == "code":
        content = f"""
def recursive_fractal_{index}(n):
    # This is a synthetic fractal function #{index}
    if n <= 0: return {random.random()}
    return recursive_fractal_{index}(n-1) + recursive_fractal_{index}(n-2)
"""
        tags = ["python", "math", "recursion"]
    elif kind == "json":
        data = {
            "id": str(uuid.uuid4()),
            "metrics": [random.random() for _ in range(10)],
            "status": "active" if index % 2 == 0 else "dormant",
            "payload": generate_random_text(50)
        }
        content = json.dumps(data, indent=2)
        tags = ["data", "system"]
    elif kind == "log":
        content = f"[ERROR] Timestamp {time.time()}: System failure in module {index}. Stack trace: {generate_random_text(30)}"
        tags = ["error", "logs"]
    else:
        content = f"The ontological status of memory #{index} is questionable. Is it a wave or a particle? {generate_random_text(50)}"
        tags = ["philosophy", "thought"]
        
    return content, tags, kind

def run_stress_test(num_memories=50, storage_dir="fracktal_memories", session_id="stress_test_session", sample_size=10):
    console.print(Panel.fit("[bold red]Starting FRACKTAL MCP Stress Test[/bold red]", border_style="red"))
    store = MemoryStore(storage_dir=storage_dir)

    start_time = time.time()
    memory_ids = []
    
    # 1. Mass Storage
    console.print(f"[yellow]Generating and storing {num_memories} memories...[/yellow]")
    for i in track(range(num_memories), description="Storing..."):
        content, tags, kind = generate_complex_memory(i)
        mid = store.store_memory(content, tags=tags, session_id=session_id, kind=kind)
        memory_ids.append((mid, content))
        
    duration = time.time() - start_time
    throughput = num_memories / duration if duration > 0 else float("inf")
    console.print(f"[green]Successfully stored {num_memories} memories in {duration:.2f}s ({throughput:.2f} mems/s)[/green]")
    
    # 2. Integrity Check
    console.print("\n[yellow]Verifying random sample integrity...[/yellow]")
    errors = 0
    checks = min(sample_size, num_memories)
    sample_indices = random.sample(range(num_memories), checks) if num_memories else []
    for i in sample_indices:
        mid, original_content = memory_ids[i]
        retrieved = store.retrieve_memory(mid)
        if retrieved["content"] != original_content:
            console.print(f"[bold red]INTEGRITY FAILURE at ID {mid}[/bold red]")
            errors += 1
            
    if errors == 0:
        console.print("[bold green]Integrity Check PASSED: 100% Lossless Recall[/bold green]")
    else:
         console.print(f"[bold red]Integrity Check FAILED: {errors} errors found[/bold red]")

    # 3. Heavy Search
    console.print("\n[yellow]Running semantic search benchmarking...[/yellow]")
    queries = ["python recursion", "system failure", "ontological wave", "json payload"]
    
    table = Table(title="Search Performance")
    table.add_column("Query", style="cyan")
    table.add_column("Top Match ID", style="magenta")
    table.add_column("Score", style="green")
    
    search_timings = []
    for q in queries:
        s_start = time.time()
        results = store.search_memories(q, limit=1)
        s_dur = time.time() - s_start
        if results:
            table.add_row(q, results[0].id[:8] + "...", f"{results[0].score:.4f} ({s_dur*1000:.1f}ms)")
            search_timings.append({"query": q, "score": results[0].score, "latency_ms": s_dur * 1000})
        else:
            table.add_row(q, "No results", "-")
            search_timings.append({"query": q, "score": None, "latency_ms": s_dur * 1000})
            
    console.print(table)
    
    # 4. Global Stats
    console.print("\n[yellow]Global Stats:[/yellow]")
    stats = store.get_stats()
    console.print(json.dumps(stats, indent=2))
    
    console.print(Panel.fit("[bold blue]Stress Test Complete[/bold blue]", border_style="blue"))

    return {
        "memories": num_memories,
        "duration_sec": duration,
        "throughput_mps": throughput,
        "sample_size": checks,
        "integrity_errors": errors,
        "search_timings": search_timings,
        "stats": stats
    }


def _parse_args():
    parser = argparse.ArgumentParser(description="Benchmark the FRACKTAL MCP memory store.")
    parser.add_argument("--num-memories", type=int, default=50, help="How many synthetic memories to store.")
    parser.add_argument("--storage-dir", default="fracktal_memories", help="Target storage directory for benchmark data.")
    parser.add_argument("--session-id", default="stress_test_session", help="Session identifier applied to generated memories.")
    parser.add_argument("--sample-size", type=int, default=10, help="Sample size used for integrity checks.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_stress_test(
        num_memories=args.num_memories,
        storage_dir=args.storage_dir,
        session_id=args.session_id,
        sample_size=args.sample_size
    )
