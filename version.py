# version.py — Single Source of Truth for Khushi AI Version Management
import datetime
import subprocess
import platform

APP_NAME = "Khushi AI"
APP_VERSION = "4.15"
GENERATION = "Generation 4"
RELEASE_NAME = "Autonomous Companion"
BUILD_DATE = "2026-07-10" # Release build date

def get_git_commit() -> str:
    """Retrieves short git commit hash, falling back to a static hash in packaged state."""
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
        return commit.decode("utf-8").strip()
    except Exception:
        return "a7fbc28"

def get_python_version() -> str:
    return platform.python_version()

def get_architecture() -> str:
    return platform.architecture()[0]

def get_installer_version() -> str:
    return APP_VERSION

def get_about_info() -> dict:
    """Returns dynamic system metadata for display in the About Dialog."""
    return {
        "AppName": APP_NAME,
        "Version": APP_VERSION,
        "Generation": GENERATION,
        "ReleaseName": RELEASE_NAME,
        "PythonVersion": get_python_version(),
        "GitCommit": get_git_commit(),
        "BuildDate": BUILD_DATE,
        "Architecture": get_architecture(),
        "InstallerVersion": get_installer_version()
    }
