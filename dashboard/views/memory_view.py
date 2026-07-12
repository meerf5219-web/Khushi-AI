from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QMenu, QMessageBox
from PySide6.QtCore import Qt

from dashboard.models.memory_model import MemoryTableModel

class MemoryView(QWidget):
    """
    Shows a searchable table of all memories with right-click actions.
    """
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.model = MemoryTableModel(engine)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.table)
        
    def _show_context_menu(self, pos):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
            
        menu = QMenu(self)
        
        edit_act = menu.addAction("Edit Memory")
        del_act = menu.addAction("Delete Memory")
        archive_act = menu.addAction("Archive")
        
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        
        if action == edit_act:
            self._edit_memory(index)
        elif action == del_act:
            self._delete_memory(index)
            
    def _delete_memory(self, index):
        record = self.model.data(index, Qt.UserRole)
        if not record: return
        
        rec_id = record.get("id") or record.get("memory_id")
        if not rec_id: return
        
        reply = QMessageBox.question(self, 'Confirm Delete', f"Delete memory {rec_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            try:
                if ":" in rec_id:
                    bucket, _ = rec_id.split(":", 1)
                else:
                    bucket = "identity"
                
                success = self.engine._store.delete_record(bucket, rec_id)
                
                # Also try to clean up the timeline entry referencing this memory if needed
                self.engine._store.delete_record("timeline", rec_id)
                
                self.model.refresh_data()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete: {e}")
                
    def _edit_memory(self, index):
        # Placeholder for edit functionality
        QMessageBox.information(self, "Edit", "Memory editing will open a custom dialog.")
