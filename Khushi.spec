# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

# Entry point
entry_script = "main.py"

# Bundle these read-only folders into the frozen temp bundle.
# ResourceManager will reference sys._MEIPASS at runtime.
PROJECT_ROOT = Path('.') .resolve()

# Paths relative to project root
DATA_DIRS = [
    "assets",
    "fonts",
    "icons",
    "ui/assets",
    "ui/icons",
    "ui/resources",
    "ui/theme",
    "themes",
    "models",
    "downloads",
    "exports",
    "knowledge",
]

# Add UI module + templates/resources (if present)

def collect_datas():
    datas = []
    for rel in DATA_DIRS:
        p = PROJECT_ROOT / rel
        if p.exists():
            if p.is_dir():
                datas.append((str(p), rel))
            else:
                datas.append((str(p), str(Path(rel).parent)))
    return datas

datas = collect_datas()

# Ensure version_info.txt exists (build_rc generates it)
if (PROJECT_ROOT / "version_info.txt").exists():
    datas.append((str(PROJECT_ROOT / "version_info.txt"), "."))

a = Analysis(
    [entry_script],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    upx_exclude=[],
    console=True,

    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=os.path.join(str(PROJECT_ROOT), "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Khushi",
)

