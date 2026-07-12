# -*- mode: python ; coding: utf-8 -*-
"""
Khushi.spec — Production PyInstaller Specification
===================================================
Generates a single-directory distribution (COLLECT mode).

Build command:
    .venv\Scripts\python -m PyInstaller Khushi.spec --clean --noconfirm

Output:
    dist\Khushi\Khushi.exe
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ---------------------------------------------------------------------------
# Collect PySide6 data files + plugins (icons, styles, platforms, etc.)
# ---------------------------------------------------------------------------
pyside6_datas = collect_data_files("PySide6", include_py_files=False)

# ---------------------------------------------------------------------------
# Project data files: all read-only bundled assets
# ---------------------------------------------------------------------------
def safe_data(src, dst):
    """Include a data dir only if it exists and is non-empty."""
    if os.path.isdir(src) and os.listdir(src):
        return (src, dst)
    return None

raw_datas = [
    safe_data("assets",      "assets"),
    safe_data("icons",       "icons"),
    safe_data("themes",      "themes"),
    safe_data("fonts",       "fonts"),
    safe_data("knowledge",   "knowledge"),
    safe_data("memory",      "memory"),
    safe_data("config",      "config"),
    safe_data("models",      "models"),
    safe_data("plugins",     "plugins"),
    safe_data("database",    "database"),
    safe_data("voice",       "voice"),
    safe_data("ui/assets",   "ui/assets"),
    safe_data("ui/icons",    "ui/icons"),
]
project_datas = [d for d in raw_datas if d is not None]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=pyside6_datas + project_datas,
    hiddenimports=[
        # PySide6 / Qt
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtNetwork",
        "PySide6.QtSvg",
        # Standard library modules that PyInstaller sometimes misses
        "sqlite3",
        "json",
        "logging",
        "logging.handlers",
        "threading",
        "queue",
        "importlib",
        "importlib.util",
        "importlib.metadata",
        # Text-to-speech (pyttsx3 uses dynamic driver discovery)
        "pyttsx3",
        "pyttsx3.drivers",
        "pyttsx3.drivers.sapi5",
        "pyttsx3.drivers.nsss",
        "pyttsx3.drivers.espeak",
        # Speech recognition
        "speech_recognition",
        # psutil (system info skill)
        "psutil",
        # Project internal submodules
        "utils.resource_manager",
        "utils.paths",
        "utils.instrumentation",
        "knowledge._vector_store_legacy",
        "fastapi",
        "uvicorn",
        "websockets",
        "multipart",
        "cryptography",
        "devices",
        "devices.registry",
        "devices.bluetooth.discovery",
        "devices.serial.connection",
        "devices.vehicle.obd.obd_connection",
        "devices.vehicle.obd.can_bus",
        "devices.vehicle.obd.command_queue",
        "memory.backup",
        "api.config",
        "api.server",
        # Dashboard Views & Visualizations
        "dashboard.views.overview",
        "dashboard.views.memory_view",
        "dashboard.views.reflections",
        "dashboard.views.trackers",
        "dashboard.views.plugins",
        "dashboard.visualizations.timeline",
        "dashboard.visualizations.relationship_graph",
        # Knowledge Vector Store Package and Submodules
        "knowledge.vector_store",
        "knowledge.vector_store.base",
        "knowledge.vector_store.chroma_store",
        "knowledge.vector_store.faiss_store",
        "knowledge.indexer",
        "knowledge.retriever",
        "knowledge.rag_engine",
        "knowledge.embedding_manager",
        "knowledge.document_loader",
        "knowledge.chunker"
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavyweight packages not installed in this venv
        "torch",
        "torchvision",
        "torchaudio",
        "tensorflow",
        "keras",
        "scipy",
        "sklearn",
        "matplotlib",
        "pandas",
        "notebook",
        "IPython",
        "ipykernel",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Khushi",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                          # Windowed mode — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    version="version_info.txt",
    icon=None,                              # Add icon path here if available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Khushi",
)
