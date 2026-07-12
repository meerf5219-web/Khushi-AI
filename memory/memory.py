import json
import logging
import os
from typing import Any, Dict

from utils.paths import get_data_dir

logger = logging.getLogger(__name__)

BASE_DIR = get_data_dir() / "memory"
FILE_NAME = BASE_DIR / "user_memory.json"
# Keep legacy compatibility if older relative paths exist by mapping:
# - old: "memory/user_memory.json" (relative to repo root)
# - new: khushi/memory/user_memory.json
OLD_FILE_NAME = get_data_dir() / "memory" / "user_memory.json"


def load_memory() -> Dict[str, Any]:
    """Load persisted assistant memory from disk."""
    candidate_paths = [FILE_NAME]
    # If an older relative file exists, load it too.
    if os.path.exists(OLD_FILE_NAME):
        candidate_paths.append(OLD_FILE_NAME)

    for path in candidate_paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            logger.warning("Memory file is invalid; starting with empty memory. path=%s", path)
            return {}

    return {}


def save_memory(data: Dict[str, Any]) -> None:
    """Persist assistant memory to disk."""
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(FILE_NAME), exist_ok=True)

    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
