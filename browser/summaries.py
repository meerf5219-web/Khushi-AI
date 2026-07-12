from browser.dom import DOMReader
from typing import Dict, Any

class PageSummarizer:
    """Prepares webpage content for Brain/LLM summarization."""
    
    def __init__(self, dom: DOMReader):
        self.dom = dom
        
    def generate_page_context(self) -> Dict[str, Any]:
        """Collects DOM metadata and text to pass to the NLP brain."""
        meta = self.dom.extract_metadata()
        text = self.dom.get_text_content()
        
        # We truncate text to avoid token limits for standard models
        truncated_text = text[:10000] if len(text) > 10000 else text
        
        return {
            "url": "current_tab", # Ideally grabbed from TabManager
            "title": meta.get("title", ""),
            "description": meta.get("description", ""),
            "content": truncated_text
        }
