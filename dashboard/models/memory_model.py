import datetime
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from typing import List, Dict, Any

class MemoryTableModel(QAbstractTableModel):
    """
    Provides a virtual scrolling table view over the JSON TinyDB store.
    """
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.headers = ["ID", "Category", "Data", "Created At"]
        self.records: List[Dict[str, Any]] = []
        self.refresh_data()
        
    def refresh_data(self):
        self.beginResetModel()
        # Fetch all records, sort by newest first
        # Memory engine store has structure: {id: str, type: str, payload: dict, created_at: float}
        # Actually, let's just get the raw timeline and format it
        timeline = self.engine.get_timeline()
        self.records = timeline
        self.endResetModel()
        
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.records)):
            return None
            
        record = self.records[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:
                return record.get("id", "") or record.get("memory_id", "")
            elif col == 1:
                return record.get("category", "")
            elif col == 2:
                return str(record.get("value", ""))
            elif col == 3:
                ts = record.get("created_at", "")
                if ts:
                    return ts
                return ""
                
        elif role == Qt.UserRole:
            # Return the full underlying record dictionary
            return record
            
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.headers):
                return self.headers[section]
        return None
