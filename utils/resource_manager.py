"""
utils/resource_manager.py — Centralized Runtime Resource Manager
=================================================================
Single source of truth for ALL file path resolution in Khushi AI.

Supports three execution contexts:
  1. Development (source checkout)          → project root
  2. Frozen PyInstaller build (_MEIPASS)     → %LOCALAPPDATA%/KhushiAI for writable data
  3. Any future deployment mode

Rules:
  - READ-ONLY bundled assets  → ResourceManager.resource(path)  → sys._MEIPASS or project root
  - WRITABLE user data        → ResourceManager.data(path)       → LOCALAPPDATA/KhushiAI or project root
  - All named helpers are convenience wrappers around data() / resource()
"""
from __future__ import annotations

import os
import sys
import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _is_frozen() -> bool:
    """Return True when running inside a PyInstaller frozen executable."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _bundle_dir() -> Path:
    """
    Directory containing read-only bundled assets.
    In frozen builds this is sys._MEIPASS (the temp extraction dir).
    In development this is the project root (parent of utils/).
    """
    if _is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _data_root() -> Path:
    """
    Root directory for ALL writable user data.
    Windows frozen: %LOCALAPPDATA%\\KhushiAI
    Development:    project root (same as bundle dir)
    """
    if _is_frozen():
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            root = Path(local_app_data) / "KhushiAI"
        else:
            # Fallback: home directory
            root = Path.home() / ".KhushiAI"
    else:
        root = Path(__file__).resolve().parent.parent
    return root


class ResourceManager:
    """
    Central resource path resolver for all Khushi AI file operations.

    Usage (always import the singleton, never instantiate directly):
        from utils.resource_manager import RM
        icon_path = RM.resource("icons/logo.png")
        log_path  = RM.logs() / "khushi.log"
    """

    def __init__(self) -> None:
        self._bundle = _bundle_dir()
        self._data = _data_root()

    # ------------------------------------------------------------------
    # READ-ONLY: bundled assets (icons, themes, fonts, config templates)
    # ------------------------------------------------------------------

    def resource(self, relative: str | Path) -> Path:
        """Absolute path to a read-only bundled resource."""
        return self._bundle / relative

    # ------------------------------------------------------------------
    # WRITABLE: user data paths
    # ------------------------------------------------------------------

    def data(self, relative: str | Path = "") -> Path:
        """Root writable data directory, optionally sub-pathed."""
        if relative:
            return self._data / relative
        return self._data

    def logs(self) -> Path:
        return self._data / "logs"

    def memory(self) -> Path:
        return self._data / "memory"

    def companion_memory(self) -> Path:
        return self._data / "memory" / "companion"

    def config(self) -> Path:
        return self._data / "config"

    def database(self) -> Path:
        return self._data / "database"

    def cache(self) -> Path:
        return self._data / "cache"

    def knowledge(self) -> Path:
        return self._data / "knowledge"

    def knowledge_vector_db(self) -> Path:
        return self._data / "knowledge" / "vector_db"

    def knowledge_documents(self) -> Path:
        return self._data / "knowledge" / "documents"

    def plugins(self) -> Path:
        return self._data / "plugins"

    def exports(self) -> Path:
        return self._data / "exports"

    def downloads(self) -> Path:
        return self._data / "downloads"

    def screenshots(self) -> Path:
        return self._data / "screenshots"

    # ------------------------------------------------------------------
    # First-launch provisioning: create all dirs + default files
    # ------------------------------------------------------------------

    def provision(self) -> None:
        """
        Ensure every writable folder exists and create default files if missing.
        Called once at startup. Safe to call multiple times (idempotent).
        """
        dirs = [
            self.logs(),
            self.memory(),
            self.companion_memory(),
            self.config(),
            self.database(),
            self.cache(),
            self.knowledge(),
            self.knowledge_vector_db(),
            self.knowledge_documents(),
            self.plugins(),
            self.exports(),
            self.downloads(),
            self.screenshots(),
        ]
        for d in dirs:
            try:
                d.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning("[ResourceManager] Could not create directory %s: %s", d, e)

        # Default user_memory.json
        self._ensure_json(self.memory() / "user_memory.json", {})

        # Default notes.json
        self._ensure_json(self.memory() / "notes.json", {"notes": []})

        # Default learning_corrections.json
        self._ensure_json(self.data() / "learning_corrections.json", {})

        # Default companion_memory.json
        self._ensure_json(
            self.companion_memory() / "companion_memory.json",
            {
                "version": 1,
                "identity": {"records": {}},
                "timeline": {"records": []},
                "preferences": {"records": {}},
                "goals": {"records": {}},
                "projects": {"records": {}},
                "habits": {"records": {}},
                "life_events": {"records": []},
                "vehicles": {"records": {}},
                "devices": {"records": {}},
                "education": {"records": {}},
                "career": {"records": {}},
                "relationships": {"records": {}},
                "health": {"records": {}},
                "knowledge_references": {"records": {}},
            }
        )

        # Default SQLite event store
        self._ensure_sqlite(self.memory() / "raw_events.db")

        logger.debug("[ResourceManager] Provisioning complete. Data root: %s", self._data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_json(self, path: Path, default: object) -> None:
        if not path.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(default, f, indent=2)
            except Exception as e:
                logger.warning("[ResourceManager] Could not create default file %s: %s", path, e)

    def _ensure_sqlite(self, path: Path) -> None:
        if not path.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(str(path))
                conn.close()
            except Exception as e:
                logger.warning("[ResourceManager] Could not create SQLite DB %s: %s", path, e)

    # ------------------------------------------------------------------
    # Startup diagnostics
    # ------------------------------------------------------------------

    def write_startup_log(self, duration: float, extras: dict | None = None) -> None:
        """Write a human-readable startup log to the logs directory."""
        import datetime
        log_path = self.logs() / "startup.log"
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write(f"Khushi AI Startup Log\n")
                f.write(f"Generated: {datetime.datetime.now().isoformat()}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Python Version  : {sys.version}\n")
                f.write(f"Executable      : {sys.executable}\n")
                f.write(f"Frozen          : {_is_frozen()}\n")
                f.write(f"_MEIPASS        : {getattr(sys, '_MEIPASS', 'N/A')}\n")
                f.write(f"Bundle Dir      : {self._bundle}\n")
                f.write(f"Data Root       : {self._data}\n")
                f.write(f"Logs Dir        : {self.logs()}\n")
                f.write(f"Memory Dir      : {self.memory()}\n")
                f.write(f"Knowledge Dir   : {self.knowledge()}\n")
                f.write(f"Database Dir    : {self.database()}\n")
                f.write(f"Startup Duration: {duration:.3f}s\n")
                if extras:
                    f.write("\n--- Additional Info ---\n")
                    for k, v in extras.items():
                        f.write(f"{k}: {v}\n")
                f.write("\n--- Directory Status ---\n")
                for label, path in [
                    ("logs", self.logs()),
                    ("memory", self.memory()),
                    ("knowledge", self.knowledge()),
                    ("database", self.database()),
                    ("cache", self.cache()),
                    ("exports", self.exports()),
                    ("screenshots", self.screenshots()),
                ]:
                    status = "EXISTS" if path.exists() else "MISSING"
                    f.write(f"  {label:12s}: {status}  ({path})\n")
                f.write("\n")
        except Exception as e:
            logger.warning("[ResourceManager] Could not write startup log: %s", e)

    def write_startup_report_json(self, duration: float, extras: dict | None = None) -> None:
        """Write a machine-readable startup report JSON to the logs directory."""
        import datetime
        report_path = self.logs() / "startup_report.json"
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report = {
                "timestamp": datetime.datetime.now().isoformat(),
                "python_version": sys.version,
                "executable": str(sys.executable),
                "frozen": _is_frozen(),
                "meipass": str(getattr(sys, "_MEIPASS", "")),
                "bundle_dir": str(self._bundle),
                "data_root": str(self._data),
                "startup_duration_s": round(duration, 3),
                "directories": {
                    "logs": {"path": str(self.logs()), "exists": self.logs().exists()},
                    "memory": {"path": str(self.memory()), "exists": self.memory().exists()},
                    "knowledge": {"path": str(self.knowledge()), "exists": self.knowledge().exists()},
                    "database": {"path": str(self.database()), "exists": self.database().exists()},
                    "cache": {"path": str(self.cache()), "exists": self.cache().exists()},
                    "exports": {"path": str(self.exports()), "exists": self.exports().exists()},
                },
            }
            if extras:
                report.update(extras)
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            logger.warning("[ResourceManager] Could not write startup report JSON: %s", e)

    def __repr__(self) -> str:
        return (
            f"ResourceManager(frozen={_is_frozen()}, "
            f"bundle={self._bundle}, data={self._data})"
        )


# ---------------------------------------------------------------------------
# Singleton — import this everywhere:  from utils.resource_manager import RM
# ---------------------------------------------------------------------------
RM = ResourceManager()
