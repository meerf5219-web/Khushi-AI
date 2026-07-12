from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Qt

class PluginsView(QWidget):
    """
    UI for viewing and managing loaded Plugins/Skills.
    """
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        
        layout = QVBoxLayout(self)
        
        title = QLabel("<h2>Skill Marketplace & Installed Plugins</h2>")
        layout.addWidget(title)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: #1e1e1e; border: 1px solid #333333; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #333333; }
        """)
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        self.btn_toggle = QPushButton("Enable / Disable")
        self.btn_toggle.clicked.connect(self._toggle_plugin)
        
        self.btn_refresh = QPushButton("Refresh Plugins")
        self.btn_refresh.clicked.connect(self.refresh_data)
        
        btn_layout.addWidget(self.btn_toggle)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        self.refresh_data()
        
    def refresh_data(self):
        if not self.manager: return
        self.list_widget.clear()
        
        self.manager.discover()
        for p_id, manifest in self.manager.manifests.items():
            status = "🟢 Active" if p_id in self.manager.active_plugins else "🔴 Disabled"
            self.list_widget.addItem(f"{status} | {manifest.id} (v{manifest.version}) - Perms: {manifest.permissions}")
            
    def _toggle_plugin(self):
        if not self.manager: return
        item = self.list_widget.currentItem()
        if not item: return
        
        text = item.text()
        p_id = text.split("|")[1].split("(")[0].strip()
        
        if p_id in self.manager.active_plugins:
            self.manager.unload_plugin(p_id)
        else:
            self.manager.load_plugin(p_id)
            
        self.refresh_data()
