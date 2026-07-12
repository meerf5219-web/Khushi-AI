from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QTimer, Signal
from version import APP_NAME

class ToastNotification(QWidget):
    """
    Subtle overlay notification that fades in and out.
    """
    accepted = Signal()
    declined = Signal()
    
    def __init__(self, parent=None, title=None, message=""):
        super().__init__(parent)
        if title is None:
            title = APP_NAME
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border: 1px solid #3f51b5;
                border-radius: 8px;
            }
        """)
        c_layout = QVBoxLayout(container)
        
        lbl_title = QLabel(f"<b>{title}</b>")
        lbl_title.setStyleSheet("color: #8c9eff; border: none;")
        
        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #ffffff; border: none;")
        
        c_layout.addWidget(lbl_title)
        c_layout.addWidget(lbl_msg)
        
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignRight)
        
        btn_acc = QPushButton("Okay")
        btn_acc.setStyleSheet("background-color: #3f51b5; color: white; border-radius: 4px; padding: 4px 10px;")
        btn_acc.clicked.connect(self._on_accept)
        
        btn_dec = QPushButton("Dismiss")
        btn_dec.setStyleSheet("background-color: transparent; color: #aaaaaa; border: none; padding: 4px 10px;")
        btn_dec.clicked.connect(self._on_decline)
        
        btn_layout.addWidget(btn_dec)
        btn_layout.addWidget(btn_acc)
        c_layout.addLayout(btn_layout)
        
        layout.addWidget(container)
        
        # Fade effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(500)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.finished.connect(self.close)
        
        # Auto dismiss
        self.timer = QTimer()
        self.timer.timeout.connect(self.hide_toast)
        
    def show_toast(self, timeout_ms=8000):
        # Position at bottom right of screen
        screen = self.screen().availableGeometry()
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 20)
        self.show()
        self.fade_in.start()
        if timeout_ms > 0:
            self.timer.start(timeout_ms)
            
    def hide_toast(self):
        self.timer.stop()
        self.fade_out.start()
        
    def _on_accept(self):
        self.accepted.emit()
        self.hide_toast()
        
    def _on_decline(self):
        self.declined.emit()
        self.hide_toast()
