from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from typing import List, Dict, Any

class EventTableModel(QAbstractTableModel):
    """
    Virtual scrolling table for the global Event Store (automation logs, API hits, etc).
    """
    def __init__(self, event_store, parent=None):
        super().__init__(parent)
        self.store = event_store
        self.headers = ["Timestamp", "Level", "System", "Message"]
        self.events: List[Dict[str, Any]] = []
        self.refresh_data()
        
    def refresh_data(self):
        self.beginResetModel()
        self.events = self.store.get_recent_events(limit=1000)
        self.endResetModel()
        
    def add_event(self, event: Dict[str, Any]):
        """Efficiently append a single event to the top of the table."""
        self.beginInsertRows(QModelIndex(), 0, 0)
        self.events.insert(0, event)
        self.endInsertRows()
        
        # Trim if too large
        if len(self.events) > 1000:
            self.beginRemoveRows(QModelIndex(), 1000, len(self.events)-1)
            self.events = self.events[:1000]
            self.endRemoveRows()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.events)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.events)):
            return None
            
        evt = self.events[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:
                return evt.get("timestamp", "")
            elif col == 1:
                return evt.get("level", "INFO")
            elif col == 2:
                return evt.get("system", "")
            elif col == 3:
                return evt.get("message", "")
                
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.headers):
                return self.headers[section]
        return None
