"""
utils/paths.py — Legacy-Compatible Path Helpers
================================================
All path logic now delegates to utils.resource_manager.RM.
These functions are kept for backward-compatibility with existing code
that imports them directly.

New code should import:
    from utils.resource_manager import RM
"""
from __future__ import annotations

import sys
from pathlib import Path


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_base_dir() -> Path:
    """
    Read-only resource directory.
    Frozen: sys._MEIPASS  |  Dev: project root
    """
    from utils.resource_manager import RM
    return RM._bundle


def get_data_dir() -> Path:
    """
    Writable user data directory.
    Frozen: %LOCALAPPDATA%/KhushiAI  |  Dev: project root
    """
    from utils.resource_manager import RM
    return RM._data


def resource_path(relative_path: str | Path) -> Path:
    """Absolute path to a read-only bundled resource."""
    from utils.resource_manager import RM
    return RM.resource(relative_path)


def init_writable_folders() -> None:
    """Ensure all writable runtime folders exist (delegates to RM.provision)."""
    from utils.resource_manager import RM
    RM.provision()
