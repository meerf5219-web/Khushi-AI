from typing import List, Dict, Any
from browser.tabs import TabManager

class DOMReader:
    """Intelligently parses DOM and extracts semantics."""
    
    def __init__(self, tabs: TabManager):
        self.tabs = tabs
        
    def get_text_content(self) -> str:
        """Get all visible text from the page."""
        page = self.tabs.get_active_tab()
        # Fallback to body innerText which gives human readable format
        return page.evaluate("document.body.innerText")
        
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract title, meta description."""
        page = self.tabs.get_active_tab()
        title = page.title()
        desc = page.evaluate('''(function() {
            var el = document.querySelector('meta[name="description"]');
            return el ? el.content : "";
        })()''')
        return {"title": title, "description": desc}
        
    def extract_links(self) -> List[Dict[str, str]]:
        page = self.tabs.get_active_tab()
        links = page.evaluate('''(function() {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText,
                url: a.href
            })).filter(a => a.text.trim() !== '');
        })()''')
        return links
        
    def extract_headings(self) -> List[str]:
        page = self.tabs.get_active_tab()
        headings = page.evaluate('''(function() {
            return Array.from(document.querySelectorAll('h1, h2, h3'))
                .map(h => h.innerText)
                .filter(text => text.trim() !== '');
        })()''')
        return headings
