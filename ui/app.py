"""
ui/app.py — Desktop GUI Application Entry Point
=================================================
Manages QApplication creation, stylesheet themes, splash loading screen presentation,
model loading synchronization, and launching the main window interface.
"""
from __future__ import annotations

import sys
import logging
from typing import Any
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from ui.splash import SplashWindow
from ui.main_window import MainWindow
from ui.theme import get_qss
from ui.workers.loading_worker import LoadingWorker

logger = logging.getLogger(__name__)


class KhushiApp:
    """
    Main Application Manager wrapper coordinating splash screen and mainWindow.
    """

    def __init__(self, debug: bool = False) -> None:
        self.app = QApplication(sys.argv)
        self.debug = debug
        
        # High DPI scaling is enabled by default in Qt6, but set text scaling behavior
        self.app.setAttribute(Qt.AA_DontShowIconsInMenus, False)
        
        # Apply dark theme by default
        self.app.setStyleSheet(get_qss("dark", "purple"))

        self.splash = SplashWindow()
        self.main_window = None
        self.loader = None
        self.api_runner = None
        
        self._watchdog_timer = QTimer()
        self._watchdog_timer.timeout.connect(self._on_watchdog_tick)
        self._elapsed_seconds = 0
        self._startup_completed = False

    def run(self) -> int:
        # Show splash screen centered
        self.splash.show()
        self._center_widget(self.splash)

        # 1. Start background loader (Phase 5)
        self.loader = LoadingWorker()
        self.loader.progress.connect(self.splash.update_progress)
        self.loader.completed.connect(self._on_loading_completed)
        self.loader.start()
        
        self._watchdog_timer.start(1000)

        exit_code = self.app.exec()
        if self.api_runner:
            try:
                self.api_runner.stop()
            except Exception as e:
                logger.error(f"Failed to stop API Server: {e}")
                
        try:
            from voice_companion.speech_router import voice_router
            voice_router.stop_service()
            logger.info("[APP] Voice Companion background service stopped successfully.")
        except Exception as e:
            logger.error(f"Failed to stop Voice Companion service: {e}")
            
        return exit_code

    def _on_watchdog_tick(self) -> None:
        if self._startup_completed:
            self._watchdog_timer.stop()
            return
            
        self._elapsed_seconds += 1
        
        if self._elapsed_seconds == 15:
            if self.splash:
                self.splash.update_progress(50, "Still loading subsystems...", "Watchdog")
        elif self._elapsed_seconds == 30:
            if self.splash:
                self.splash.update_progress(50, "Loading is taking longer than expected.", "Watchdog")
        elif self._elapsed_seconds == 60:
            logger.warning("[APP] Startup watchdog triggered (60s elapsed).")
            self._watchdog_timer.stop()

    def _on_loading_completed(self, brain: Any) -> None:
        if self._startup_completed:
            return
            
        self._startup_completed = True
        self._watchdog_timer.stop()
        logger.info("[APP] Subsystems loaded successfully. Transitioning from Splash to Main Window...")
        
        # Hide splash and destroy it
        if self.splash:
            self.splash.hide()
            self.splash.deleteLater()
            self.splash = None
            
        # Instantiate and show main window with fully initialized brain
        self.main_window = MainWindow(brain=brain)
        self.main_window.show()
        self._center_widget(self.main_window)

        # Start local API server
        try:
            from api.server import APIServerRunner
            self.api_runner = APIServerRunner(brain)
            self.api_runner.start()
            logger.info("[APP] API Server started successfully.")
        except Exception as e:
            logger.error(f"[APP] Failed to start local API Server: {e}")
            
        # Start Voice Companion
        try:
            from voice_companion.speech_router import voice_router
            voice_router.brain = brain
            voice_router.start_service()
            logger.info("[APP] Voice Companion background service started successfully.")
        except Exception as e:
            logger.error(f"[APP] Failed to start Voice Companion service: {e}")
        
        # Speak the initial welcoming speech from startup
        from voice.speaker import speak
        speak("Welcome back Faisal.", block=False)
        speak("I am ready.", block=False)

    def _center_widget(self, widget: QWidget) -> None:
        """Helper to position the given widget at the center of the primary screen."""
        screen = self.app.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            width = widget.width()
            height = widget.height()
            
            x = (screen_geometry.width() - width) // 2
            y = (screen_geometry.height() - height) // 2
            widget.move(x, y)


def launch_gui(debug: bool = False) -> int:
    """
    Entry point function for launching the desktop application.
    """
    from utils.resource_manager import RM
    log_file = RM.logs() / "khushi_gui.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_file), mode="w", encoding="utf-8")
        ]
    )
    logger.info("Initializing Khushi Desktop GUI Application...")

    app = KhushiApp(debug=debug)
    return app.run()


if __name__ == "__main__":
    sys.exit(launch_gui())
