import os
import sys
import shutil
import stat
import subprocess
import time

def remove_readonly(func, path, excinfo):
    """Callback to strip read-only attributes and retry deleting files."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"Warning: Failed to remove {path}: {e}")

def clean_build_artifacts():
    print("=== STEP 1: Cleaning build artifacts and cache ===")
    target_dirs = ["dist", "build"]
    for dir_name in target_dirs:
        if os.path.exists(dir_name):
            print(f"Force-removing directory: {dir_name}...")
            for i in range(5):
                try:
                    shutil.rmtree(dir_name, onerror=remove_readonly)
                    break
                except Exception as e:
                    print(f"Attempt {i+1} failed to remove {dir_name}: {e}. Retrying...")
                    time.sleep(1)

    print("Cleaning __pycache__ directories and *.pyc files recursively...")
    for root, dirs, files in os.walk("."):
        # Skip .venv
        if ".venv" in root or ".git" in root:
            continue
            
        for d in dirs:
            if d == "__pycache__":
                pycache_path = os.path.join(root, d)
                try:
                    shutil.rmtree(pycache_path, onerror=remove_readonly)
                except Exception:
                    pass
                    
        for f in files:
            if f.endswith(".pyc") or f.endswith(".pyo"):
                file_path = os.path.join(root, f)
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    # Clear PyInstaller system cache if possible
    pyinstaller_cache = os.path.join(os.environ.get("LOCALAPPDATA", ""), "pyinstaller")
    if os.path.exists(pyinstaller_cache):
        print(f"Clearing PyInstaller system cache at: {pyinstaller_cache}")
        try:
            shutil.rmtree(pyinstaller_cache, onerror=remove_readonly)
        except Exception as e:
            print(f"Warning: Failed to clear PyInstaller system cache: {e}")
            
    print("Cleanup complete.")

def generate_version_info():
    print("\n=== STEP 1.5: Generating version_info.txt dynamically ===")
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    try:
        from version import APP_NAME, APP_VERSION, BUILD_DATE
        print(f"Loaded: APP_NAME={APP_NAME}, APP_VERSION={APP_VERSION}, BUILD_DATE={BUILD_DATE}")
    except Exception as e:
        print(f"Error importing version info: {e}")
        # fallback defaults
        APP_NAME = "Khushi AI"
        APP_VERSION = "4.15"
        BUILD_DATE = "2026-07-10"

    parts = APP_VERSION.split(".")
    version_tuple = [0, 0, 0, 0]
    for idx, p in enumerate(parts):
        try:
            version_tuple[idx] = int(p)
        except ValueError:
            pass
    ver_tup_str = f"({', '.join(map(str, version_tuple))})"
    
    content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={ver_tup_str},
    prodvers={ver_tup_str},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904b0',
        [StringStruct('CompanyName', '{APP_NAME}'),
        StringStruct('FileDescription', 'Autonomous Desktop Companion'),
        StringStruct('FileVersion', '{APP_VERSION}'),
        StringStruct('InternalName', 'Khushi'),
        StringStruct('LegalCopyright', 'Copyright (c) {BUILD_DATE.split("-")[0]} {APP_NAME}'),
        StringStruct('OriginalFilename', 'Khushi.exe'),
        StringStruct('ProductName', '{APP_NAME}'),
        StringStruct('ProductVersion', '{APP_VERSION}')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    with open("version_info.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("version_info.txt generated successfully.")

def compile_khushi_exe():
    print("\n=== STEP 2: Compiling Khushi.exe ===")
    cmd = [sys.executable, "-m", "PyInstaller", "Khushi.spec", "--clean", "--noconfirm"]
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("Khushi.exe compilation successful.")

def compile_installer_exe():
    print("\n=== STEP 3: Compiling Installer.exe ===")
    # Standalone GUI installer bundling dist/Khushi payload
    cmd = [
        sys.executable, "-m", 
        "PyInstaller", "installer.py", 
        "--onefile", 
        "--noconsole", 
        "--add-data", "dist/Khushi;Khushi", 
        "--clean",
        "--noconfirm"
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("Installer.exe compilation successful.")

if __name__ == "__main__":
    try:
        clean_build_artifacts()
        generate_version_info()
        compile_khushi_exe()
        compile_installer_exe()
        print("\n=== SUCCESS: All packaging steps completed cleanly! ===")
    except Exception as e:
        print(f"\n=== FAILURE: Build pipeline failed: {e} ===")
        sys.exit(1)
