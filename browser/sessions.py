import logging
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)

class BrowserSession:
    """Manages the global Playwright lifecycle."""
    
    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        
    def start(self, headless: bool = False):
        if not self._playwright:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=headless)
            self._context = self._browser.new_context()
            logger.info("Playwright session started.")
            
    def stop(self):
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
        logger.info("Playwright session stopped.")
            
    def get_context(self) -> BrowserContext:
        if not self._context:
            self.start()
        return self._context
