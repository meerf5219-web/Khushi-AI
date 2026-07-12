from browser.tabs import TabManager
from automation.utils import require_confirmation
from automation.models import RiskLevel
from playwright.sync_api import Locator

class FormAutomator:
    """Automates form interactions with built-in safety interception."""
    
    DESTRUCTIVE_KEYWORDS = ["buy", "pay", "delete", "post", "send", "purchase", "checkout"]

    def __init__(self, tabs: TabManager):
        self.tabs = tabs
        
    def _is_high_risk(self, text: str) -> bool:
        lower_text = text.lower()
        return any(k in lower_text for k in self.DESTRUCTIVE_KEYWORDS)

    def fill_input(self, selector: str, text: str):
        page = self.tabs.get_active_tab()
        page.fill(selector, text)
        
    def click_button(self, selector: str, text_content: str = ""):
        page = self.tabs.get_active_tab()
        
        # Determine risk based on text content or inner text
        if not text_content:
            try:
                text_content = page.locator(selector).first.inner_text()
            except:
                pass
                
        if self._is_high_risk(text_content):
            if not require_confirmation(f"Browser action: Click '{text_content}'", selector, RiskLevel.HIGH):
                raise PermissionError("User rejected high-risk browser action.")
                
        page.click(selector)
