import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout
import numpy as np

class TimelineChart(QWidget):
    """
    Visualizes Event Density or Memory creation over time.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # Enable anti-aliasing for prettier plots
        pg.setConfigOptions(antialias=True)
        
        self.plot_widget = pg.PlotWidget(title="Memory & Event Timeline")
        self.plot_widget.setBackground('#121212')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Activity Count')
        self.plot_widget.setLabel('bottom', 'Time (Days)')
        
        layout.addWidget(self.plot_widget)
        
    def refresh_data(self, timestamps: list):
        """
        Takes a list of timestamps and plots a histogram/density curve.
        For simplicity, we'll plot a mock curve if empty.
        """
        self.plot_widget.clear()
        
        if not timestamps:
            # Mock data for aesthetic UI
            x = np.linspace(0, 30, 100)
            y = np.sin(x) + np.random.normal(0, 0.1, 100) + 2
            
            pen = pg.mkPen(color=(63, 81, 181), width=2)
            brush = pg.mkBrush(color=(63, 81, 181, 50))
            self.plot_widget.plot(x, y, pen=pen, fillLevel=0, brush=brush)
        else:
            # Real data logic here...
            pass
