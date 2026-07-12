# Modern Dark Mode Stylesheet for PySide6
DARK_STYLESHEET = """
QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}

QTableView {
    background-color: #1e1e1e;
    gridline-color: #333333;
    selection-background-color: #3f51b5;
    border: 1px solid #333333;
    border-radius: 4px;
}

QHeaderView::section {
    background-color: #2c2c2c;
    color: #ffffff;
    padding: 6px;
    border: 1px solid #333333;
    font-weight: bold;
}

QPushButton {
    background-color: #3f51b5;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #5c6bc0;
}

QPushButton:pressed {
    background-color: #303f9f;
}

QLineEdit, QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #3f51b5;
}

QProgressBar {
    border: 1px solid #444444;
    border-radius: 4px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #3f51b5;
    border-radius: 4px;
}

QTabWidget::pane {
    border: 1px solid #333333;
    top: -1px; 
}

QTabBar::tab {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    padding: 8px 12px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #2c2c2c;
    border-bottom-color: #2c2c2c; 
    color: #8c9eff;
}
"""
