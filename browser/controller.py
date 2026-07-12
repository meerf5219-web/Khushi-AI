import time
import os
from typing import Dict, Any, Callable
from PySide6.QtCore import QObject

from brain.event_bus import event_bus
from utils.resource_manager import RM
from browser.workers import BrowserWorker
from browser.sessions import BrowserSession
from browser.tabs import TabManager
from browser.navigator import Navigator
from browser.dom import DOMReader
from browser.forms import FormAutomator
from browser.downloads import DownloadManager
from browser.summaries import PageSummarizer

class BrowserController(QObject):
    """
    Public API for the Browser Intelligence Layer.
    Orchestrates headless/visible browsing synchronously in background threads.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = BrowserSession()
        self.tabs = TabManager(self.session)
        self.nav = Navigator(self.tabs)
        self.dom = DOMReader(self.tabs)
        self.forms = FormAutomator(self.tabs)
        
        dl_dir = str(RM.downloads())
        self.downloads = DownloadManager(self.tabs, dl_dir)
        self.summarizer = PageSummarizer(self.dom)
        
        self._active_workers: Dict[str, BrowserWorker] = {}
        
    def _publish(self, topic: str, data: Dict[str, Any]):
        event_bus.publish('browser', {"topic": topic, "data": data})
        
    def _execute_async(self, action_name: str, func: Callable, *args, **kwargs) -> str:
        """Run a browser task in the background."""
        worker_id = f"{action_name}_{time.time()}"
        worker = BrowserWorker(action_name, func, *args, **kwargs)
        self._active_workers[worker_id] = worker
        
        def on_started(name):
            pass
            
        def on_completed(name, result):
            self._publish(f"{name.upper()}_COMPLETED", {"result": result})
            self._cleanup_worker(worker_id)
            
        def on_failed(name, error_msg):
            self._publish(f"{name.upper()}_FAILED", {"error": error_msg})
            self._cleanup_worker(worker_id)
            
        worker.started_action.connect(on_started)
        worker.completed_action.connect(on_completed)
        worker.failed_action.connect(on_failed)
        worker.start()
        return worker_id
        
    def _cleanup_worker(self, worker_id: str):
        if worker_id in self._active_workers:
            self._active_workers[worker_id].deleteLater()
            del self._active_workers[worker_id]
            
    # --- Public API ---

    def start_session(self, headless: bool = False):
        return self._execute_async("start_session", self.session.start, headless=headless)

    def stop_session(self):
        return self._execute_async("stop_session", self.session.stop)

    def navigate(self, url: str):
        self._publish("PAGE_OPENED", {"url": url})
        return self._execute_async("navigate", self.nav.go_to, url)
        
    def extract_summary(self):
        self._publish("SUMMARY_GENERATED", {"status": "pending"})
        return self._execute_async("summarize", self.summarizer.generate_page_context)
        
    def fill_and_submit(self, selector: str, text: str, submit_selector: str):
        def _action():
            self.forms.fill_input(selector, text)
            self.forms.click_button(submit_selector)
        self._publish("FORM_SUBMITTED", {"selector": selector})
        return self._execute_async("fill_form", _action)

# Singleton
browser_controller = BrowserController()
