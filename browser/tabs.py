from typing import Optional, List
from playwright.sync_api import Page
from browser.sessions import BrowserSession

class TabManager:
    """Manages tabs within the Playwright session."""
    
    def __init__(self, session: BrowserSession):
        self.session = session
        self.active_page: Optional[Page] = None
        
    def _get_pages(self) -> List[Page]:
        context = self.session.get_context()
        return context.pages

    def new_tab(self) -> Page:
        context = self.session.get_context()
        page = context.new_page()
        self.active_page = page
        return page
        
    def get_active_tab(self) -> Page:
        if not self.active_page:
            pages = self._get_pages()
            if pages:
                self.active_page = pages[-1]
            else:
                self.active_page = self.new_tab()
        return self.active_page
        
    def switch_to(self, index: int) -> bool:
        pages = self._get_pages()
        if 0 <= index < len(pages):
            self.active_page = pages[index]
            self.active_page.bring_to_front()
            return True
        return False
        
    def close_active(self):
        if self.active_page:
            self.active_page.close()
            self.active_page = None
            
    def get_tab_info(self) -> List[dict]:
        pages = self._get_pages()
        info = []
        for p in pages:
            info.append({
                "title": p.title(),
                "url": p.url
            })
        return info
