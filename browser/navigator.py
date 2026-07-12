from browser.tabs import TabManager

class Navigator:
    """Handles high-level navigation across tabs."""
    
    def __init__(self, tab_manager: TabManager):
        self.tabs = tab_manager
        
    def go_to(self, url: str) -> bool:
        page = self.tabs.get_active_tab()
        try:
            # Playwright navigation
            page.goto(url, wait_until="domcontentloaded")
            return True
        except Exception as e:
            return False
            
    def go_back(self):
        page = self.tabs.get_active_tab()
        page.go_back(wait_until="domcontentloaded")
        
    def go_forward(self):
        page = self.tabs.get_active_tab()
        page.go_forward(wait_until="domcontentloaded")
        
    def refresh(self):
        page = self.tabs.get_active_tab()
        page.reload(wait_until="domcontentloaded")
