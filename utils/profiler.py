import logging
import time
import tracemalloc
import psutil
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """
    Performance profiling and memory leak tracking engine.
    Monitors process heap allocations and checks execution speed metrics.
    """
    def __init__(self) -> None:
        self.snapshots = []
        
    def start_leak_tracking(self) -> None:
        """Starts heap allocations tracing."""
        logger.info("Initializing heap allocation tracker...")
        tracemalloc.start()
        self.snapshots.append(tracemalloc.take_snapshot())

    def check_for_leaks(self) -> Dict[str, Any]:
        """Compares current heap allocations with start snap to detect potential memory leaks."""
        if not tracemalloc.is_tracing():
            return {"status": "error", "message": "Heap tracer not running."}
            
        current_snap = tracemalloc.take_snapshot()
        # Compare snapshot with the original
        stats = current_snap.compare_to(self.snapshots[0], 'lineno')
        
        # Grab top 5 memory increments
        top_leaks = []
        for stat in stats[:5]:
            top_leaks.append({
                "file": stat.traceback[0].filename,
                "line": stat.traceback[0].lineno,
                "size_diff_bytes": stat.size_diff,
                "count_diff": stat.count_diff
            })
            
        process = psutil.Process()
        ram_bytes = process.memory_info().rss
        
        logger.info(f"Memory leak check complete. Process RAM Usage: {ram_bytes / (1024*1024):.2f} MB")
        return {
            "status": "success",
            "ram_allocated_bytes": ram_bytes,
            "top_increments": top_leaks
        }

    def profile_function(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """Profiles a single callable execution time and logs output speed warnings."""
        t0 = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - t0
            logger.info(f"[PROFILER] Call '{name}' completed in {elapsed:.6f} seconds.")
            # Speed warning threshold: 2.0 seconds
            if elapsed > 2.0:
                logger.warning(f"[PROFILER WARNING] slow function execution speed on '{name}' ({elapsed:.2f}s).")
