import os
import shutil
import time
from typing import Optional
import subprocess

from automation.models import RiskLevel
from automation.utils import require_confirmation

class FileSystemAutomation:
    """Manages file system operations."""
    
    def open_explorer(self, path: str) -> None:
        """Open File Explorer at the given path."""
        if os.name == 'nt':
            os.startfile(path)
        else:
            # Fallback for future platform support
            subprocess.Popen(['xdg-open', path])

    def create_directory(self, path: str) -> None:
        """Create a directory."""
        os.makedirs(path, exist_ok=True)
        
    def _get_file_info(self, path: str) -> str:
        """Helper to get size and modification date for confirmations."""
        if not os.path.exists(path):
            return "File does not exist."
        size = os.path.getsize(path)
        mtime = os.path.getmtime(path)
        mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        return f"Size: {size} bytes\nLast Modified: {mtime_str}"

    def copy(self, src: str, dst: str) -> None:
        """Copy a file or directory. Prompts if overwriting."""
        if os.path.exists(dst):
            info = self._get_file_info(dst)
            desc = f"Overwrite existing file/directory?\n\n{info}"
            if not require_confirmation(desc, dst, RiskLevel.HIGH):
                raise PermissionError("User cancelled overwrite operation.")
        
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    def move(self, src: str, dst: str) -> None:
        """Move a file or directory. Prompts if overwriting."""
        if os.path.exists(dst):
            info = self._get_file_info(dst)
            desc = f"Overwrite existing file/directory during move?\n\n{info}"
            if not require_confirmation(desc, dst, RiskLevel.HIGH):
                raise PermissionError("User cancelled move/overwrite operation.")
                
        shutil.move(src, dst)

    def rename(self, src: str, dst: str) -> None:
        """Rename a file or directory. Prompts if overwriting."""
        if os.path.exists(dst):
            info = self._get_file_info(dst)
            desc = f"Overwrite existing file/directory during rename?\n\n{info}"
            if not require_confirmation(desc, dst, RiskLevel.HIGH):
                raise PermissionError("User cancelled rename operation.")
                
        os.rename(src, dst)

    def delete(self, path: str) -> None:
        """Delete a file or directory. Always prompts."""
        if not os.path.exists(path):
            return
            
        info = self._get_file_info(path)
        desc = f"Permanently delete this file/directory?\n\n{info}"
        if not require_confirmation(desc, path, RiskLevel.HIGH):
            raise PermissionError("User cancelled delete operation.")
            
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
