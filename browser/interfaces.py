from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BrowserEngine(ABC):
    """Abstract interface for browser automation engine."""
    
    @abstractmethod
    def start(self):
        pass
        
    @abstractmethod
    def stop(self):
        pass
        
    @abstractmethod
    def navigate(self, url: str):
        pass
        
    @abstractmethod
    def get_dom_text(self) -> str:
        pass
