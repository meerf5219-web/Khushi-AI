from __future__ import annotations

import os
import sys
import inspect
import builtins
import pathlib
import sqlite3
import json
import traceback
import threading
import atexit

# Thread-local storage to prevent recursion when the logging logic itself accesses files.
_local_state = threading.local()

def is_instrumenting():
    return getattr(_local_state, "in_instrumentation", 0) > 0

class InstrumentationGuard:
    def __enter__(self):
        _local_state.in_instrumentation = getattr(_local_state, "in_instrumentation", 0) + 1
    def __exit__(self, exc_type, exc_val, exc_tb):
        _local_state.in_instrumentation = max(0, getattr(_local_state, "in_instrumentation", 1) - 1)

# Accumulators for the final report
accessed_records = []
lock = threading.Lock()


def _get_logs_dir() -> str:
    """Get writable logs directory — deferred to avoid circular imports at module load."""
    try:
        from utils.resource_manager import RM
        p = RM.logs()
        p.mkdir(parents=True, exist_ok=True)
        return str(p)
    except Exception:
        import tempfile
        return tempfile.gettempdir()

def log_access(path: str, operation: str, caller_file: str, line_number: int, success: bool, error: Exception | None = None):
    with lock:
        entry = {
            "path": path,
            "operation": operation,
            "caller": f"{caller_file}:{line_number}",
            "success": success,
            "error": str(error) if error else None
        }
        accessed_records.append(entry)
        
        # Write to JSON report in real-time using original open to avoid recursion
        with InstrumentationGuard():
            try:
                logs_dir = _get_logs_dir()
                report_path = os.path.join(logs_dir, "startup_report.json")
                # Using original built-in open to prevent recursion
                with original_open(report_path, "w", encoding="utf-8") as f:
                    json.dump(accessed_records, f, indent=2)
            except Exception:
                pass
            
            # Write a human readable log line
            try:
                logs_dir = _get_logs_dir()
                log_path = os.path.join(logs_dir, "startup_report.log")
                status = "SUCCESS" if success else f"FAILED ({error})"
                line = f"[{operation}] {path} | Caller: {caller_file}:{line_number} | Status: {status}\n"
                with original_open(log_path, "a", encoding="utf-8") as f:
                    f.write(line)
            except Exception:
                pass

def get_caller_info():
    frame = inspect.currentframe()
    while frame:
        filename = frame.f_code.co_filename
        # Skip this instrumentation file itself, builtins, and inspect module
        if ("instrumentation.py" not in os.path.basename(filename) and 
            "inspect" not in os.path.basename(filename) and
            "<" not in filename):
            return filename, frame.f_lineno
        frame = frame.f_back
    return "unknown", 0

def handle_fnf(abs_path: str, exc: Exception):
    with InstrumentationGuard():
        print("=" * 80, file=sys.stderr)
        print(f"CRITICAL FILE NOT FOUND: {abs_path}", file=sys.stderr)
        print(f"Current Working Directory: {os.getcwd()}", file=sys.stderr)
        print(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'Not Frozen')}", file=sys.stderr)
        print(f"sys.executable: {sys.executable}", file=sys.stderr)
        print(f"__file__ (instrumentation): {__file__}", file=sys.stderr)
        print("Traceback:", file=sys.stderr)
        try:
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
        except Exception as e:
            print(f"[Instrumentation Error] Failed to print traceback: {e}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)

# Save original functions
original_open = builtins.open
original_Path_exists = pathlib.Path.exists
original_Path_open = pathlib.Path.open
original_os_path_exists = os.path.exists
original_os_listdir = os.listdir
original_sqlite3_connect = sqlite3.connect
original_json_load = json.load

# 1. builtins.open
def instrumented_open(file, *args, **kwargs):
    if is_instrumenting():
        return original_open(file, *args, **kwargs)
    
    abs_path = ""
    try:
        if isinstance(file, (str, bytes)):
            abs_path = os.path.abspath(file)
        elif hasattr(file, "name"):
            abs_path = os.path.abspath(file.name)
        elif isinstance(file, pathlib.Path):
            abs_path = str(file.resolve())
    except Exception:
        pass
    
    caller_file, caller_line = get_caller_info()
    with InstrumentationGuard():
        try:
            res = original_open(file, *args, **kwargs)
            log_access(abs_path, "open", caller_file, caller_line, success=True)
            return res
        except Exception as e:
            log_access(abs_path, "open", caller_file, caller_line, success=False, error=e)
            if isinstance(e, FileNotFoundError):
                handle_fnf(abs_path, e)
            raise
builtins.open = instrumented_open

# 2. Path.exists
def instrumented_Path_exists(self, *args, **kwargs):
    if is_instrumenting():
        return original_Path_exists(self, *args, **kwargs)
    
    abs_path = ""
    try:
        abs_path = str(self.resolve())
    except Exception:
        pass
    
    caller_file, caller_line = get_caller_info()
    with InstrumentationGuard():
        try:
            res = original_Path_exists(self, *args, **kwargs)
            log_access(abs_path, "Path.exists", caller_file, caller_line, success=res)
            return res
        except Exception as e:
            log_access(abs_path, "Path.exists", caller_file, caller_line, success=False, error=e)
            if isinstance(e, FileNotFoundError):
                handle_fnf(abs_path, e)
            raise
pathlib.Path.exists = instrumented_Path_exists

# 3. Path.open
def instrumented_Path_open(self, *args, **kwargs):
    if is_instrumenting():
        return original_Path_open(self, *args, **kwargs)
    
    abs_path = ""
    try:
        abs_path = str(self.resolve())
    except Exception:
        pass
    
    caller_file, caller_line = get_caller_info()
    with InstrumentationGuard():
        try:
            res = original_Path_open(self, *args, **kwargs)
            log_access(abs_path, "Path.open", caller_file, caller_line, success=True)
            return res
        except Exception as e:
            log_access(abs_path, "Path.open", caller_file, caller_line, success=False, error=e)
            if isinstance(e, FileNotFoundError):
                handle_fnf(abs_path, e)
            raise
pathlib.Path.open = instrumented_Path_open

# 4. os.path.exists
def instrumented_os_path_exists(path, *args, **kwargs):
    if is_instrumenting():
        return original_os_path_exists(path, *args, **kwargs)
    
    abs_path = ""
    try:
        abs_path = os.path.abspath(path)
    except Exception:
        pass
    
    caller_file, caller_line = get_caller_info()
    with InstrumentationGuard():
        try:
            res = original_os_path_exists(path, *args, **kwargs)
            log_access(abs_path, "os.path.exists", caller_file, caller_line, success=res)
            return res
        except Exception as e:
            log_access(abs_path, "os.path.exists", caller_file, caller_line, success=False, error=e)
            if isinstance(e, FileNotFoundError):
                handle_fnf(abs_path, e)
            raise
os.path.exists = instrumented_os_path_exists

# 5. os.listdir
def instrumented_os_listdir(path=".", *args, **kwargs):
    if is_instrumenting():
        return original_os_listdir(path, *args, **kwargs)
    
    abs_path = ""
    try:
        abs_path = os.path.abspath(path)
    except Exception:
        pass
    
    caller_file, caller_line = get_caller_info()
    with InstrumentationGuard():
        try:
            res = original_os_listdir(path, *args, **kwargs)
            log_access(abs_path, "os.listdir", caller_file, caller_line, success=True)
            return res
        except Exception as e:
            log_access(abs_path, "os.listdir", caller_file, caller_line, success=False, error=e)
            if isinstance(e, FileNotFoundError):
                handle_fnf(abs_path, e)
            raise
os.listdir = instrumented_os_listdir

# 6. sqlite3.connect
def instrumented_sqlite3_connect(database, *args, **kwargs):
    if is_instrumenting():
        return original_sqlite3_connect(database, *args, **kwargs)
    
    abs_path = ""
    try:
        if isinstance(database, (str, bytes)):
            abs_path = os.path.abspath(database)
        elif isinstance(database, pathlib.Path):
            abs_path = str(database.resolve())
    except Exception:
        pass
    
    caller_file, caller_line = get_caller_info()
    with InstrumentationGuard():
        try:
            res = original_sqlite3_connect(database, *args, **kwargs)
            log_access(abs_path, "sqlite3.connect", caller_file, caller_line, success=True)
            return res
        except Exception as e:
            log_access(abs_path, "sqlite3.connect", caller_file, caller_line, success=False, error=e)
            if isinstance(e, FileNotFoundError):
                handle_fnf(abs_path, e)
            raise
sqlite3.connect = instrumented_sqlite3_connect

# 7. json.load
def instrumented_json_load(fp, *args, **kwargs):
    if is_instrumenting():
        return original_json_load(fp, *args, **kwargs)
    
    abs_path = ""
    try:
        if hasattr(fp, "name"):
            abs_path = os.path.abspath(fp.name)
    except Exception:
        pass
    
    caller_file, caller_line = get_caller_info()
    with InstrumentationGuard():
        try:
            res = original_json_load(fp, *args, **kwargs)
            log_access(abs_path, "json.load", caller_file, caller_line, success=True)
            return res
        except Exception as e:
            log_access(abs_path, "json.load", caller_file, caller_line, success=False, error=e)
            if isinstance(e, FileNotFoundError):
                handle_fnf(abs_path, e)
            raise
json.load = instrumented_json_load

# Optional Modules: PyYAML, toml, tomllib, sentence_transformers, torch, PySide6

# 8. PyYAML
try:
    import yaml
    original_yaml_load = yaml.load
    def instrumented_yaml_load(stream, *args, **kwargs):
        if is_instrumenting():
            return original_yaml_load(stream, *args, **kwargs)
        abs_path = ""
        try:
            if hasattr(stream, "name"):
                abs_path = os.path.abspath(stream.name)
        except Exception:
            pass
        caller_file, caller_line = get_caller_info()
        with InstrumentationGuard():
            try:
                res = original_yaml_load(stream, *args, **kwargs)
                log_access(abs_path, "yaml.load", caller_file, caller_line, success=True)
                return res
            except Exception as e:
                log_access(abs_path, "yaml.load", caller_file, caller_line, success=False, error=e)
                if isinstance(e, FileNotFoundError):
                    handle_fnf(abs_path, e)
                raise
    yaml.load = instrumented_yaml_load
except ImportError:
    pass

# 9. tomllib / toml
try:
    import tomllib
    original_tomllib_load = tomllib.load
    def instrumented_tomllib_load(fp, *args, **kwargs):
        if is_instrumenting():
            return original_tomllib_load(fp, *args, **kwargs)
        abs_path = ""
        try:
            if hasattr(fp, "name"):
                abs_path = os.path.abspath(fp.name)
        except Exception:
            pass
        caller_file, caller_line = get_caller_info()
        with InstrumentationGuard():
            try:
                res = original_tomllib_load(fp, *args, **kwargs)
                log_access(abs_path, "tomllib.load", caller_file, caller_line, success=True)
                return res
            except Exception as e:
                log_access(abs_path, "tomllib.load", caller_file, caller_line, success=False, error=e)
                if isinstance(e, FileNotFoundError):
                    handle_fnf(abs_path, e)
                raise
    tomllib.load = instrumented_tomllib_load
except ImportError:
    pass

try:
    import toml
    original_toml_load = toml.load
    def instrumented_toml_load(f, *args, **kwargs):
        if is_instrumenting():
            return original_toml_load(f, *args, **kwargs)
        abs_path = ""
        try:
            if hasattr(f, "name"):
                abs_path = os.path.abspath(f.name)
            elif isinstance(f, (str, pathlib.Path)):
                abs_path = os.path.abspath(f)
        except Exception:
            pass
        caller_file, caller_line = get_caller_info()
        with InstrumentationGuard():
            try:
                res = original_toml_load(f, *args, **kwargs)
                log_access(abs_path, "toml.load", caller_file, caller_line, success=True)
                return res
            except Exception as e:
                log_access(abs_path, "toml.load", caller_file, caller_line, success=False, error=e)
                if isinstance(e, FileNotFoundError):
                    handle_fnf(abs_path, e)
                raise
    toml.load = instrumented_toml_load
except ImportError:
    pass

# 10. sentence_transformers (SentenceTransformer)
try:
    import sentence_transformers
    original_SentenceTransformer = sentence_transformers.SentenceTransformer
    class InstrumentedSentenceTransformer(original_SentenceTransformer):
        def __init__(self, model_name_or_path, *args, **kwargs):
            if is_instrumenting():
                super().__init__(model_name_or_path, *args, **kwargs)
                return
            abs_path = os.path.abspath(model_name_or_path) if isinstance(model_name_or_path, (str, pathlib.Path)) else str(model_name_or_path)
            caller_file, caller_line = get_caller_info()
            with InstrumentationGuard():
                try:
                    super().__init__(model_name_or_path, *args, **kwargs)
                    log_access(abs_path, "SentenceTransformer", caller_file, caller_line, success=True)
                except Exception as e:
                    log_access(abs_path, "SentenceTransformer", caller_file, caller_line, success=False, error=e)
                    if isinstance(e, FileNotFoundError):
                        handle_fnf(abs_path, e)
                    raise
    sentence_transformers.SentenceTransformer = InstrumentedSentenceTransformer
except ImportError:
    pass

# 11. torch (torch.load)
# IMPORTANT: Torch DLL load failures in packaged builds raise OSError (e.g., WinError 126),
# not ImportError. Never allow this to crash startup.
# Minimal stability fix: guard torch import + log full failure (append-only) and continue.

torch = None
_torch_import_failure_logged = False


def _append_torch_import_failure_to_log(exc: BaseException) -> None:
    global _torch_import_failure_logged
    if _torch_import_failure_logged:
        return
    _torch_import_failure_logged = True

    try:
        # ISO-8601 UTC timestamp
        import datetime
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        tb_str = ""
        try:
            tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        except Exception:
            tb_str = str(exc)

        # Append-only (never overwrite existing logs)
        logs_dir = _get_logs_dir()
        log_path = os.path.join(logs_dir, "startup_report.log")

        header = (
            "==================================================\n"
            "TORCH IMPORT FAILURE\n"
            "==================================================\n"
            f"Timestamp: {ts}\n"
            f"Exception Type: {type(exc).__name__}\n"
            f"Exception Message: {exc}\n"
            "Traceback:\n\n"
            f"{tb_str}\n"
            "==================================================\n"
        )

        with InstrumentationGuard():
            with original_open(log_path, "a", encoding="utf-8") as f:
                f.write(header)
    except Exception:
        # Never break startup because torch is unavailable.
        pass


try:
    # Guarded lazy import
    import torch as _torch

    torch = _torch
    original_torch_load = torch.load

    def instrumented_torch_load(f, *args, **kwargs):
        if is_instrumenting():
            return original_torch_load(f, *args, **kwargs)
        abs_path = ""
        try:
            if isinstance(f, (str, pathlib.Path)):
                abs_path = os.path.abspath(f)
            elif hasattr(f, "name"):
                abs_path = os.path.abspath(f.name)
        except Exception:
            pass
        caller_file, caller_line = get_caller_info()
        with InstrumentationGuard():
            try:
                res = original_torch_load(f, *args, **kwargs)
                log_access(abs_path, "torch.load", caller_file, caller_line, success=True)
                return res
            except Exception as e:
                log_access(abs_path, "torch.load", caller_file, caller_line, success=False, error=e)
                if isinstance(e, FileNotFoundError):
                    handle_fnf(abs_path, e)
                raise

    torch.load = instrumented_torch_load
except (ImportError, OSError) as e:
    # ImportError for missing torch; OSError for DLL load failures (WinError 126)
    _append_torch_import_failure_to_log(e)
    torch = None
except Exception as e:
    # Any unexpected torch initialization exception
    _append_torch_import_failure_to_log(e)
    torch = None


# 12, 13, 14, 15. PySide6 QPixmap, QIcon, QMovie, QFontDatabase
try:
    import PySide6.QtGui
    
    # QPixmap
    original_QPixmap = PySide6.QtGui.QPixmap
    class InstrumentedQPixmap(original_QPixmap):
        def __init__(self, *args, **kwargs):
            if is_instrumenting():
                super().__init__(*args, **kwargs)
                return
            abs_path = ""
            if args and isinstance(args[0], (str, pathlib.Path)):
                abs_path = os.path.abspath(args[0])
            caller_file, caller_line = get_caller_info()
            with InstrumentationGuard():
                try:
                    super().__init__(*args, **kwargs)
                    if abs_path:
                        success = not self.isNull()
                        log_access(abs_path, "QPixmap", caller_file, caller_line, success=success)
                except Exception as e:
                    if abs_path:
                        log_access(abs_path, "QPixmap", caller_file, caller_line, success=False, error=e)
                    raise
    PySide6.QtGui.QPixmap = InstrumentedQPixmap
    
    # QIcon
    original_QIcon = PySide6.QtGui.QIcon
    class InstrumentedQIcon(original_QIcon):
        def __init__(self, *args, **kwargs):
            if is_instrumenting():
                super().__init__(*args, **kwargs)
                return
            abs_path = ""
            if args and isinstance(args[0], (str, pathlib.Path)):
                abs_path = os.path.abspath(args[0])
            caller_file, caller_line = get_caller_info()
            with InstrumentationGuard():
                try:
                    super().__init__(*args, **kwargs)
                    if abs_path:
                        success = not self.isNull() if hasattr(self, "isNull") else True
                        log_access(abs_path, "QIcon", caller_file, caller_line, success=success)
                except Exception as e:
                    if abs_path:
                        log_access(abs_path, "QIcon", caller_file, caller_line, success=False, error=e)
                    raise
    PySide6.QtGui.QIcon = InstrumentedQIcon
    
    # QMovie
    original_QMovie = PySide6.QtGui.QMovie
    class InstrumentedQMovie(original_QMovie):
        def __init__(self, *args, **kwargs):
            if is_instrumenting():
                super().__init__(*args, **kwargs)
                return
            abs_path = ""
            if args and isinstance(args[0], (str, pathlib.Path)):
                abs_path = os.path.abspath(args[0])
            caller_file, caller_line = get_caller_info()
            with InstrumentationGuard():
                try:
                    super().__init__(*args, **kwargs)
                    if abs_path:
                        success = self.isValid()
                        log_access(abs_path, "QMovie", caller_file, caller_line, success=success)
                except Exception as e:
                    if abs_path:
                        log_access(abs_path, "QMovie", caller_file, caller_line, success=False, error=e)
                    raise
    PySide6.QtGui.QMovie = InstrumentedQMovie

    # QFontDatabase
    original_QFontDatabase = PySide6.QtGui.QFontDatabase
    class InstrumentedQFontDatabase(original_QFontDatabase):
        @staticmethod
        def addApplicationFont(fileName, *args, **kwargs):
            if is_instrumenting():
                return original_QFontDatabase.addApplicationFont(fileName, *args, **kwargs)
            abs_path = os.path.abspath(fileName) if isinstance(fileName, (str, pathlib.Path)) else str(fileName)
            caller_file, caller_line = get_caller_info()
            with InstrumentationGuard():
                try:
                    res = original_QFontDatabase.addApplicationFont(fileName, *args, **kwargs)
                    success = (res != -1)
                    log_access(abs_path, "QFontDatabase.addApplicationFont", caller_file, caller_line, success=success)
                    return res
                except Exception as e:
                    log_access(abs_path, "QFontDatabase.addApplicationFont", caller_file, caller_line, success=False, error=e)
                    raise
    PySide6.QtGui.QFontDatabase = InstrumentedQFontDatabase
except ImportError:
    pass


def generate_final_report():
    """Generate final diagnostic summary report on exit."""
    with lock:
        requested = []
        found = []
        missing = []
        not_bundled = []
        
        mei_pass = getattr(sys, '_MEIPASS', None)
        
        for record in accessed_records:
            path = record["path"]
            success = record["success"]
            
            if path not in requested:
                requested.append(path)
                
            if success:
                if path not in found:
                    found.append(path)
            else:
                if path not in missing:
                    missing.append(path)
                
                # Check if it was supposed to be bundled under _MEIPASS
                if mei_pass and path.startswith(mei_pass):
                    if path not in not_bundled:
                        not_bundled.append(path)
        
        report_md = [
            "# PyInstaller Startup Diagnostics Report",
            "",
            "## Summary",
            f"- **Files Accessed**: {len(requested)}",
            f"- **Files Found**: {len(found)}",
            f"- **Files Missing**: {len(missing)}",
            f"- **Files Not Bundled**: {len(not_bundled)}",
            "",
            "## FILES REQUESTED",
        ]
        for p in sorted(requested):
            report_md.append(f"- `{p}`")
            
        report_md.append("\n## FILES FOUND")
        for p in sorted(found):
            report_md.append(f"- `{p}`")
            
        report_md.append("\n## FILES MISSING")
        for p in sorted(missing):
            report_md.append(f"- `{p}`")
            
        report_md.append("\n## FILES NOT BUNDLED (Required under _MEIPASS)")
        for p in sorted(not_bundled):
            report_md.append(f"- `{p}`")
            
        with InstrumentationGuard():
            try:
                logs_dir = _get_logs_dir()
                report_path = os.path.join(logs_dir, "startup_report.md")
                with original_open(report_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(report_md))
            except Exception:
                pass

def _safe_write_text(path: str, text: str) -> None:
    try:
        with original_open(path, "a", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass


def _safe_write_json(path: str, payload: object) -> None:
    try:
        with original_open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.flush()
    except Exception:
        pass


def _collect_runtime_context(startup_stage: str | None = None) -> dict:
    # Keep this intentionally lightweight.
    ctx = {
        "timestamp": None,
        "pid": None,
        "thread_id": None,
        "thread_name": None,
        "python_version": sys.version,
        "executable": str(getattr(sys, "executable", "")),
        "frozen": _is_frozen() if hasattr(sys, "frozen") or hasattr(sys, "_MEIPASS") else False,
        "_MEIPASS": getattr(sys, "_MEIPASS", ""),
        "startup_stage": startup_stage,
        "process_mode": "frozen" if _is_frozen() else "source",
    }
    try:
        import datetime
        ctx["timestamp"] = datetime.datetime.now().isoformat()
    except Exception:
        ctx["timestamp"] = None

    try:
        ctx["pid"] = os.getpid()
    except Exception:
        ctx["pid"] = None

    try:
        ctx["thread_id"] = threading.get_ident()
        ctx["thread_name"] = threading.current_thread().name
    except Exception:
        ctx["thread_id"] = None
        ctx["thread_name"] = None

    return ctx


def _write_crash_entry(exc_type, exc_value, exc_tb, *, extra: dict | None = None) -> None:
    # Lightweight + failure-safe.
    try:
        logs_dir = _get_logs_dir()
        crash_path = os.path.join(logs_dir, "crash.log")
        thread_report_path = os.path.join(logs_dir, "thread_report.json")
        os.makedirs(logs_dir, exist_ok=True)

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        entry = {
            **_collect_runtime_context(extra.get("startup_stage") if extra else None),
            "completion_status": "FAILED",
            "exception_type": getattr(exc_type, "__name__", str(exc_type)),
            "exception_value": str(exc_value),
            "traceback": tb_str,
        }
        if extra:
            entry.update({k: v for k, v in extra.items() if v is not None and k not in entry})

        _safe_write_text(crash_path, "\n" + "=" * 60 + "\n" + json.dumps(entry, ensure_ascii=False) + "\n")

        # Thread report is a JSON array of entries.
        try:
            existing = []
            if os.path.exists(thread_report_path):
                with original_open(thread_report_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = []
            existing.append(entry)
            _safe_write_json(thread_report_path, existing)
        except Exception:
            # Never fail crash logging.
            pass
    except Exception:
        pass


def _install_exception_hooks() -> None:
    # Capture main-thread uncaught exceptions.
    def _sys_excepthook(exc_type, exc_value, exc_tb):
        try:
            _write_crash_entry(exc_type, exc_value, exc_tb, extra={"source": "sys.excepthook"})
        except Exception:
            pass
        # Never suppress default behavior.
        return sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _sys_excepthook

    # Capture background thread exceptions.
    def _thread_excepthook(args):
        try:
            _write_crash_entry(args.exc_type, args.exc_value, args.exc_traceback, extra={
                "source": "threading.excepthook",
                "thread_name": getattr(args.thread, "name", None) if hasattr(args, "thread") else None,
                "thread_id": getattr(args.thread, "ident", None) if hasattr(args, "thread") else None,
            })
        except Exception:
            pass
        # Never suppress.

    threading.excepthook = _thread_excepthook

    # Capture non-exception issues.
    def _unraisablehook(unraisable):
        try:
            # unraisable.exc_value may be None
            exc_type = type(unraisable.exc_value) if unraisable.exc_value is not None else RuntimeError
            exc_value = unraisable.exc_value if unraisable.exc_value is not None else RuntimeError(str(unraisable.obj))
            tb = None
            _write_crash_entry(exc_type, exc_value, tb, extra={
                "source": "sys.unraisablehook",
                "unraisable_obj": repr(unraisable.obj),
                "unraisable_name": getattr(unraisable, "name", None),
            })
        except Exception:
            pass

    try:
        sys.unraisablehook = _unraisablehook
    except Exception:
        pass


try:
    _install_exception_hooks()
except Exception:
    pass

atexit.register(generate_final_report)

