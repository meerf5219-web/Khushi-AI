from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QStackedWidget, QLabel
from PySide6.QtCore import Qt
import importlib
import logging

logger = logging.getLogger(__name__)

from dashboard.styles import DARK_STYLESHEET

# Force PyInstaller static analysis to pick up dynamic dashboard imports
if False:
    from dashboard.views import overview, memory_view, reflections, trackers, plugins
    from dashboard.visualizations import timeline, relationship_graph

class DashboardFallbackWidget(QWidget):
    """Fallback widget displayed if a dashboard page fails to load."""
    def __init__(self, page_name: str, error_msg: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)
        
        icon = QLabel("⚠️")
        icon.setStyleSheet("font-size: 48px; margin-bottom: 10px;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        title = QLabel(f"<h3>{page_name} Component Unavailable</h3>")
        title.setStyleSheet("color: #EF4444; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel(f"An error occurred while loading this dashboard component:\n\n{error_msg}")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94A3B8; font-size: 13px; margin-top: 10px; font-family: monospace;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)


def safe_load_view(view_name: str, module_path: str, class_name: str, *args, **kwargs) -> QWidget:
    """Dynamically import and instantiate a view class, catching any startup errors."""
    try:
        mod = importlib.import_module(module_path)
        view_class = getattr(mod, class_name)
        return view_class(*args, **kwargs)
    except Exception as e:
        import traceback
        logger.error(f"Failed to load dashboard view '{view_name}' ({module_path}.{class_name}): {e}", exc_info=True)
        error_msg = f"{type(e).__name__}: {str(e)}"
        return DashboardFallbackWidget(view_name, error_msg)


class CompanionDashboard(QWidget):
    """
    Main entrypoint for Generation 4.6 Companion Dashboard.
    """
    def __init__(self, brain=None):
        super().__init__()
        self.brain = brain
        
        self.setStyleSheet(DARK_STYLESHEET)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            QListWidget { background-color: #121212; border-right: 1px solid #333333; }
            QListWidget::item { padding: 15px; color: #aaaaaa; }
            QListWidget::item:selected { background-color: #1e1e1e; color: #ffffff; border-left: 4px solid #3f51b5; }
        """)
        
        nav_items = ["Overview", "Memories", "Reflections", "Trackers", "Event Timeline", "Knowledge Graph", "Plugins"]
        self.sidebar.addItems(nav_items)
        
        # Stacked Widget (Main Content)
        self.stack = QStackedWidget()
        
        # Initialize views safely
        self.overview = safe_load_view(
            "Overview", "dashboard.views.overview", "DashboardOverview", self.brain
        )
        
        memory_engine = self.brain.cie if self.brain else None
        
        self.mem_view = safe_load_view(
            "Memories", "dashboard.views.memory_view", "MemoryView", memory_engine
        )
        
        self.reflections = safe_load_view(
            "Reflections", "dashboard.views.reflections", "ReflectionView", memory_engine
        )
        
        self.trackers = safe_load_view(
            "Trackers", "dashboard.views.trackers", "TrackerView", memory_engine
        )
        
        # Initialize Plugins View Safely
        def load_plugins_view():
            if self.brain and hasattr(self.brain, "plugin_manager") and self.brain.plugin_manager is not None:
                plugin_manager = self.brain.plugin_manager
            else:
                from plugins.manager import PluginManager
                plugin_manager = PluginManager(self.brain)
                plugin_manager.load_all()
            
            # Attach to self so main window can access it if needed
            self.plugin_manager = plugin_manager
            
            from dashboard.views.plugins import PluginsView
            return PluginsView(plugin_manager)
            
        try:
            self.plugins_view = load_plugins_view()
        except Exception as e:
            logger.error(f"Failed to load Plugins component: {e}", exc_info=True)
            self.plugins_view = DashboardFallbackWidget("Plugins", f"{type(e).__name__}: {str(e)}")
        
        self.timeline = safe_load_view(
            "Event Timeline", "dashboard.visualizations.timeline", "TimelineChart"
        )
        if hasattr(self.timeline, "refresh_data"):
            try:
                self.timeline.refresh_data([])
            except Exception as e:
                logger.error(f"Failed to refresh timeline mock data: {e}")
        
        self.knowledge_graph = safe_load_view(
            "Knowledge Graph", "dashboard.visualizations.relationship_graph", "RelationshipGraph", brain=self.brain
        )
        
        # Add to stack
        self.stack.addWidget(self.overview)
        self.stack.addWidget(self.mem_view)
        self.stack.addWidget(self.reflections)
        self.stack.addWidget(self.trackers)
        self.stack.addWidget(self.timeline)
        self.stack.addWidget(self.knowledge_graph)
        self.stack.addWidget(self.plugins_view)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        
        def on_row_changed(row):
            self.stack.setCurrentIndex(row)
            if row == 5 and hasattr(self.knowledge_graph, "refresh"):
                try:
                    self.knowledge_graph.refresh()
                except Exception as e:
                    logger.error(f"Failed to refresh knowledge graph: {e}")
                
        self.sidebar.currentRowChanged.connect(on_row_changed)
        self.sidebar.setCurrentRow(0)
