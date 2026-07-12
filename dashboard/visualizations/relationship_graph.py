import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout
import numpy as np

class RelationshipGraph(QWidget):
    """
    Visualizes the "World Model" Knowledge Connections dynamically.
    """
    def __init__(self, parent=None, brain=None):
        super().__init__(parent)
        self.brain = brain
        layout = QVBoxLayout(self)
        
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget(title="Knowledge Connections")
        self.plot_widget.setBackground('#121212')
        self.plot_widget.hideAxis('left')
        self.plot_widget.hideAxis('bottom')
        
        self.graph = pg.GraphItem()
        self.plot_widget.addItem(self.graph)
        
        layout.addWidget(self.plot_widget)
        self.refresh()
        
    def refresh(self):
        """Loads and renders the real WorldModel from the brain."""
        world_model = None
        if self.brain and hasattr(self.brain, "world"):
            world_model = self.brain.world
            
        if not world_model or not hasattr(world_model, "nodes") or not world_model.nodes:
            self._load_mock_data()
            return
            
        self.plot_widget.clear()
        self.graph = pg.GraphItem()
        self.plot_widget.addItem(self.graph)
        
        nodes_dict = world_model.nodes
        graph_dict = world_model.graph
        
        node_ids = list(nodes_dict.keys())
        N = len(node_ids)
        
        id_to_idx = {n_id: i for i, n_id in enumerate(node_ids)}
        pos = np.zeros((N, 2), dtype=float)
        
        # Central node strategy: User node at the center (0, 0)
        user_id = None
        for n_id, n_data in nodes_dict.items():
            if n_data["label"].lower() == "user":
                user_id = n_id
                break
        if not user_id and node_ids:
            user_id = node_ids[0]
            
        user_idx = id_to_idx.get(user_id, 0)
        
        # Distribute non-central nodes radially
        angle = 0.0
        step = 2.0 * np.pi / (N - 1) if N > 1 else 0
        
        for i, n_id in enumerate(node_ids):
            if i == user_idx:
                pos[i] = [0.0, 0.0]
            else:
                pos[i] = [2.5 * np.cos(angle), 2.5 * np.sin(angle)]
                angle += step
                
        # Build adjacency matrix for rendering edges
        adj_list = []
        for n_id, neighbors in graph_dict.items():
            u = id_to_idx.get(n_id)
            if u is None:
                continue
            for neighbor in neighbors:
                v = id_to_idx.get(neighbor)
                if v is not None and u < v:
                    adj_list.append([u, v])
                    
        adj = np.array(adj_list, dtype=int) if adj_list else np.empty((0, 2), dtype=int)
        
        brush_colors = []
        symbols = []
        texts = []
        
        # Set node styles depending on entity labels
        for n_id in node_ids:
            label = nodes_dict[n_id]["label"].lower()
            name = nodes_dict[n_id].get("metadata", {}).get("name", label)
            texts.append(name)
            
            if label == "user":
                brush_colors.append((139, 92, 246))  # Violet
                symbols.append('o')
            elif label == "project":
                brush_colors.append((16, 185, 129))  # Emerald
                symbols.append('t')
            elif label == "goal":
                brush_colors.append((245, 158, 11))  # Amber
                symbols.append('s')
            elif label == "habit":
                brush_colors.append((236, 72, 153))  # Pink
                symbols.append('d')
            else:
                brush_colors.append((59, 130, 246))  # Blue
                symbols.append('o')
                
        self.graph.setData(
            pos=pos,
            adj=adj,
            symbol=symbols,
            size=18,
            symbolBrush=brush_colors,
            symbolPen=pg.mkPen(color=(255, 255, 255, 50), width=1)
        )
        
        # Overlay entity name labels
        for i, text in enumerate(texts):
            ti = pg.TextItem(text, color=(220, 220, 220), anchor=(0.5, 1.5))
            ti.setPos(pos[i][0], pos[i][1])
            self.plot_widget.addItem(ti)
            
    def _load_mock_data(self):
        # Coordinates for nodes
        pos = np.array([
            [0, 0], [1, 2], [2, 0], [3, 3], [4, 1], [-1, 3], [-2, 1]
        ], dtype=float)
        
        # Connections (edges)
        adj = np.array([
            [0, 1], [0, 2], [1, 3], [2, 4], [0, 5], [5, 6], [1, 5]
        ])
        
        symbols = ['o', 'o', 'o', 't', 't', 's', 's']
        texts = ["Self", "AI", "Python", "Dashboard", "Goals", "UPSC", "History"]
        
        self.graph.setData(pos=pos, adj=adj, symbol=symbols, size=15, symbolBrush=(63, 81, 181))
        
        for i, text in enumerate(texts):
            ti = pg.TextItem(text, color=(200, 200, 200), anchor=(0.5, 1.5))
            ti.setPos(pos[i][0], pos[i][1])
            self.plot_widget.addItem(ti)
