import os
from typing import Optional
from browser.tabs import TabManager

class DownloadManager:
    """Intersects and manages Playwright downloads."""
    
    def __init__(self, tabs: TabManager, download_dir: str):
        self.tabs = tabs
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        
    def wait_for_download(self, trigger_func):
        """
        Executes trigger_func (which should cause a download) and waits for it to complete.
        Returns the saved file path.
        """
        page = self.tabs.get_active_tab()
        with page.expect_download() as download_info:
            trigger_func()
            
        download = download_info.value
        file_path = os.path.join(self.download_dir, download.suggested_filename)
        download.save_as(file_path)
        return file_path
