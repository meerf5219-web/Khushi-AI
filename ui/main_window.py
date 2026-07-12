"""
ui/main_window.py — Main Application Window Layout
===================================================
Orchestrates the sidebar, conversation panel, dashboard, status controls,
and background workers (Brain, Voice, Event Stream).
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton,
    QLabel, QFrame, QStackedWidget
)

from ui.widgets.sidebar import SidebarWidget
from ui.widgets.conversation import ConversationWidget
from ui.widgets.dashboard import DashboardWidget
from ui.widgets.waveform import WaveformWidget
from ui.widgets.status import StatusWidget
from ui.widgets.microphone import MicrophoneWidget
from ui.widgets.settings import SettingsWidget

from ui.workers.brain_worker import BrainWorker
from ui.workers.voice_worker import VoiceWorker
from ui.workers.stream_worker import StreamWorker
from voice.speaker import speaking_engine
from version import APP_NAME, APP_VERSION, GENERATION

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main desktop window container coordinates for Khushi AI.
    """

    def __init__(self, brain: Any = None) -> None:
        super().__init__()
        self.brain = brain
        self.setWindowTitle(f"{APP_NAME} - {GENERATION} (v{APP_VERSION})")
        self.resize(1024, 680)
        
        # Keep references to background worker threads
        self.brain_worker: Optional[BrainWorker] = None
        self.voice_worker: Optional[VoiceWorker] = None
        self.stream_worker: Optional[StreamWorker] = None
        
        self._init_ui()
        
        if self.brain is not None:
            self._start_workers()
        else:
            self._set_ui_disabled(True)
            self.chat.add_message("System starting. Initializing subsystems...", "assistant")

    @Slot(int, str, str)
    def update_startup_progress(self, percent: int, msg: str, module_name: str) -> None:
        """Receive progress from LoadingWorker while UI is visible."""
        self.status.set_state("thinking")
        self.lbl_model.setText(f"Loading: {module_name} ({percent}%)")

    def inject_brain(self, brain: Any) -> None:
        """Inject the fully initialized Brain after the background worker finishes."""
        self.brain = brain
        self.dashboard.brain = brain  # update dashboard ref
        
        # update companion dashboard refs
        if hasattr(self, 'companion_dashboard'):
            self.companion_dashboard.brain = brain
            
            overview = getattr(self.companion_dashboard, 'overview', None)
            if overview and hasattr(overview, 'refresh_data'):
                overview.brain = brain
                try:
                    overview.refresh_data()
                except Exception as e:
                    logger.error(f"Failed to refresh dashboard overview data: {e}")
                
            if hasattr(brain, 'cie'):
                mem_view = getattr(self.companion_dashboard, 'mem_view', None)
                if mem_view and hasattr(mem_view, 'model'):
                    mem_view.engine = brain.cie
                    if hasattr(mem_view.model, 'engine'):
                        mem_view.model.engine = brain.cie
                        try:
                            mem_view.model.refresh_data()
                        except Exception as e:
                            logger.error(f"Failed to refresh dashboard memories data: {e}")
                
                reflections = getattr(self.companion_dashboard, 'reflections', None)
                if reflections and hasattr(reflections, 'refresh_data'):
                    reflections.engine = brain.cie
                    try:
                        reflections.refresh_data()
                    except Exception as e:
                        logger.error(f"Failed to refresh dashboard reflections data: {e}")
                
                trackers = getattr(self.companion_dashboard, 'trackers', None)
                if trackers and hasattr(trackers, 'refresh_data'):
                    trackers.engine = brain.cie
                    try:
                        trackers.refresh_data()
                    except Exception as e:
                        logger.error(f"Failed to refresh dashboard trackers data: {e}")
                
        # Start the autonomous core
        try:
            from companion.autonomy.engine import ProactiveEngine
            self.autonomy_engine = ProactiveEngine(brain)
            self.autonomy_engine.suggestion_ready.connect(self._show_autonomous_notification)
            self.autonomy_engine.start()
        except Exception as e:
            logger.error(f"Failed to start Autonomy Core: {e}")
                
        self._start_workers()
        self._set_ui_disabled(False)
        self.chat.add_message("System subsystems loaded successfully. Ready.", "assistant")
        self.lbl_model.setText("Model: Ollama (Local)")
        self.status.set_state("listening" if self.settings.chk_continuous.isChecked() else "offline")

    def _set_ui_disabled(self, disabled: bool) -> None:
        self.input_box.setDisabled(disabled)
        self.btn_send.setDisabled(disabled)
        self.mic.setDisabled(disabled)

    def _init_ui(self) -> None:
        # Central container holding main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.view_changed.connect(self._on_view_changed)
        main_layout.addWidget(self.sidebar)

        # Main Workspace Panel
        workspace = QWidget()
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        main_layout.addWidget(workspace)

        # 2. Header / Top Bar
        header = QFrame()
        header.setObjectName("HeaderContainer")
        header.setStyleSheet("background-color: #141416; border-bottom: 1px solid rgba(255,255,255,0.05); min-height: 45px;")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 6, 15, 6)
        
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(title)
        
        # Add a status label (Listening/Speaking etc)
        self.status = StatusWidget()
        header_layout.addWidget(self.status)
        header_layout.addStretch()
        
        # Mode / Active model indicator
        self.lbl_model = QLabel("Model: Ollama (Local)")
        self.lbl_model.setStyleSheet("font-size: 11px; color: #94A3B8;")
        header_layout.addWidget(self.lbl_model)
        
        workspace_layout.addWidget(header)

        # 3. Stacked View Layout (Chat, Settings, etc.)
        self.stacked_view = QStackedWidget()
        workspace_layout.addWidget(self.stacked_view)

        # Sub-View 1: Chat interface
        chat_view = QWidget()
        chat_layout = QVBoxLayout(chat_view)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        self.chat = ConversationWidget()
        self.chat.re_run_brain.connect(self._process_query)
        chat_layout.addWidget(self.chat)
        
        # Waveform visualizer right above the chat inputs
        self.waveform = WaveformWidget()
        chat_layout.addWidget(self.waveform)

        # Footer Input area
        footer = QFrame()
        footer.setObjectName("FooterContainer")
        footer.setStyleSheet("background-color: #141416; border-top: 1px solid rgba(255,255,255,0.05);")
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(15, 12, 15, 12)
        footer_layout.setSpacing(10)

        # Microphone Widget
        self.mic = MicrophoneWidget()
        self.mic.toggled_state.connect(self._on_mic_toggled)
        footer_layout.addWidget(self.mic)

        # Text input box
        self.input_box = QLineEdit()
        self.input_box.setObjectName("ChatInput")
        self.input_box.setPlaceholderText("Type a query here or speak aloud...")
        self.input_box.returnPressed.connect(self._send_text_query)
        footer_layout.addWidget(self.input_box)

        # Send Button
        self.btn_send = QPushButton("Send")
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.clicked.connect(self._send_text_query)
        footer_layout.addWidget(self.btn_send)

        # Stop / Interrupt Button
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setStyleSheet("QPushButton { background-color: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); color: #EF4444; } QPushButton:hover { background-color: rgba(239, 68, 68, 0.2); }")
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        footer_layout.addWidget(self.btn_stop)

        chat_layout.addWidget(footer)
        self.stacked_view.addWidget(chat_view)

        # Sub-View 2: Settings Panel
        self.settings = SettingsWidget()
        self.settings.settings_changed.connect(self._on_setting_changed)
        self.stacked_view.addWidget(self.settings)

        # Sub-View 3: Companion Dashboard
        from dashboard.window import CompanionDashboard
        self.companion_dashboard = CompanionDashboard(self.brain)
        self.stacked_view.addWidget(self.companion_dashboard)

        # 4. Right Diagnostics Dashboard Panel
        self.dashboard = DashboardWidget(self.brain)
        main_layout.addWidget(self.dashboard)

    def _start_workers(self) -> None:
        # 1. Setup Stream Worker (bridges event bus notifications to UI thread signals)
        self.stream_worker = StreamWorker()
        self.stream_worker.token_received.connect(self._on_token_received)
        self.stream_worker.speech_started.connect(self._on_speech_started)
        self.stream_worker.speech_completed.connect(self._on_speech_completed)
        self.stream_worker.voice_interaction_received.connect(self._on_voice_interaction_received)

        # 2. Setup Voice worker (runs the mic STT loops)
        self.voice_worker = VoiceWorker()
        self.voice_worker.text_detected.connect(self._on_speech_detected)
        self.voice_worker.status_changed.connect(self._on_voice_status_changed)
        self.voice_worker.audio_amplitude.connect(self.waveform.set_amplitude)
        self.voice_worker.start()

        # Check if model has a custom name config
        if self.brain and self.brain.pipeline:
            # Set display value
            pass

    # ------------------------------------------------------------------
    # Action Triggers
    # ------------------------------------------------------------------

    def _send_text_query(self) -> None:
        query = self.input_box.text().strip()
        if not query:
            return
        
        self.input_box.clear()
        self.chat.add_message(query, "user")
        self._process_query(query)

    def _on_speech_detected(self, text: str) -> None:
        # Routed directly from VoiceWorker thread
        self.chat.add_message(text, "user")
        self._process_query(text)

    def _process_query(self, query: str) -> None:
        # Pause active listening loop while thinking/processing
        self.voice_worker.set_enabled(False)
        self.mic.set_active(False)

        # Visual states
        self.status.set_state("thinking")
        self.waveform.set_state("thinking")
        self.chat.show_thinking()

        # Spawn Brain worker thread
        self.brain_worker = BrainWorker(self.brain, query)
        self.brain_worker.finished.connect(self._on_brain_finished)
        self.brain_worker.failed.connect(self._on_brain_failed)
        self.brain_worker.start()

    @Slot(str, float)
    def _on_brain_finished(self, reply: str, elapsed: float) -> None:
        # Check if we were streaming (i.e. stream bubble exists)
        import voice.speaker as speaker_module
        metadata = {
            "model": self.lbl_model.text().replace("Model: ", ""),
            "total_time": elapsed,
            "tokens": len(reply.split())
        }
        
        if self.chat.active_stream_bubble is not None:
            self.chat.finalize_stream(metadata)
        else:
            self.chat.add_message(reply, "assistant", metadata)
            
        # Speak asynchronously if not already triggered by OllamaProvider chunks
        if not speaker_module._has_spoken_in_turn:
            speaker_module._has_spoken_in_turn = True
            speaking_engine.speak(reply, cancel_previous=True, block=False)
            
        self._refresh_dashboards()

    @Slot(str)
    def _on_brain_failed(self, error_msg: str) -> None:
        self.chat.add_message(f"System Error: {error_msg}", "assistant")
        self._resume_listening()
        self._refresh_dashboards()

    @Slot(str, str)
    def _on_voice_interaction_received(self, user_text: str, assistant_response: str) -> None:
        """Called when a voice command is completed in the background Voice Companion."""
        self.chat.add_message(user_text, "user")
        self.chat.add_message(assistant_response, "assistant")
        self._refresh_dashboards()

    def _refresh_dashboards(self) -> None:
        """Refresh statistics and dashboard visualizations."""
        if hasattr(self, 'dashboard') and self.dashboard:
            try:
                self.dashboard.refresh_data()
            except Exception as e:
                logger.error(f"Failed to refresh DashboardWidget: {e}")
                
        if hasattr(self, 'companion_dashboard') and self.companion_dashboard:
            # Refresh overview view
            overview = getattr(self.companion_dashboard, 'overview', None)
            if overview and hasattr(overview, 'refresh_data'):
                try:
                    overview.refresh_data()
                except Exception as e:
                    logger.error(f"Failed to refresh Overview: {e}")
                    
            # Refresh memory view table model
            mem_view = getattr(self.companion_dashboard, 'mem_view', None)
            if mem_view and hasattr(mem_view, 'model') and hasattr(mem_view.model, 'refresh_data'):
                try:
                    mem_view.model.refresh_data()
                except Exception as e:
                    logger.error(f"Failed to refresh Memory View Table Model: {e}")
                    
            # Refresh reflections view
            reflections = getattr(self.companion_dashboard, 'reflections', None)
            if reflections and hasattr(reflections, 'refresh_data'):
                try:
                    reflections.refresh_data()
                except Exception as e:
                    logger.error(f"Failed to refresh Reflections: {e}")
                    
            # Refresh trackers view
            trackers = getattr(self.companion_dashboard, 'trackers', None)
            if trackers and hasattr(trackers, 'refresh_data'):
                try:
                    trackers.refresh_data()
                except Exception as e:
                    logger.error(f"Failed to refresh Trackers: {e}")
                    
            # Refresh timeline view
            timeline = getattr(self.companion_dashboard, 'timeline', None)
            if timeline and hasattr(timeline, 'refresh_data'):
                try:
                    timeline.refresh_data([])
                except Exception as e:
                    logger.error(f"Failed to refresh Timeline: {e}")
                    
            # Refresh knowledge graph
            knowledge_graph = getattr(self.companion_dashboard, 'knowledge_graph', None)
            if knowledge_graph and hasattr(knowledge_graph, 'refresh'):
                try:
                    knowledge_graph.refresh()
                except Exception as e:
                    logger.error(f"Failed to refresh Knowledge Graph: {e}")

    def _resume_listening(self) -> None:
        # Resume Voice loop if Mic toggled active
        if self.settings.chk_continuous.isChecked():
            self.voice_worker.set_enabled(True)
            self.mic.set_active(True)
            self.status.set_state("listening")
            self.waveform.set_state("listening")
        else:
            self.status.set_state("offline")
            self.waveform.set_state("offline")

    # ------------------------------------------------------------------
    # Worker Signal Bridges
    # ------------------------------------------------------------------

    @Slot(str, str)
    def _on_token_received(self, token: str, full_text: str) -> None:
        # Real-time token streaming
        self.chat.append_stream_token(token, full_text)

    @Slot(str)
    def _on_speech_started(self, req_id: str) -> None:
        self.status.set_state("speaking")
        self.waveform.set_state("speaking")

    @Slot(str, str)
    def _on_speech_completed(self, req_id: str, status: str) -> None:
        logger.info("[MAIN WINDOW] Speech completed with status: %s", status)
        self._resume_listening()

    @Slot(str)
    def _on_voice_status_changed(self, status: str) -> None:
        self.status.set_state(status)
        self.waveform.set_state(status)

    def _on_mic_toggled(self, active: bool) -> None:
        self.voice_worker.set_enabled(active)

    def _on_stop_clicked(self) -> None:
        # Cancel all background speak queues immediately
        speaking_engine.cancel()
        self._resume_listening()

    def _on_view_changed(self, view_name: str) -> None:
        # Swap main view index
        if view_name == "chat":
            self.stacked_view.setCurrentIndex(0)
        elif view_name == "settings":
            self.stacked_view.setCurrentIndex(1)
        elif view_name in ["memory", "knowledge", "timeline"]:
            self.stacked_view.setCurrentIndex(2)

    def _on_setting_changed(self, key: str, value: Any) -> None:
        logger.info("[SETTING] %s changed to: %s", key, value)
        if key == "model":
            self.lbl_model.setText(f"Model: {value}")
            # Update llm parameters if needed in real time
        elif key == "speech_speed":
            # Speed WPM is slider value (e.g. 165)
            pass
        elif key == "speech_volume":
            # Volume value is float 0.0 - 1.0
            pass
        elif key == "continuous_listening":
            self.voice_worker.set_enabled(value)
            self.mic.set_active(value)

    def _show_autonomous_notification(self, suggestion_dict: dict) -> None:
        """Called when the background ProactiveEngine wants to speak up."""
        try:
            from ui.widgets.notification import ToastNotification
            
            title = suggestion_dict.get("action_type", "Suggestion").capitalize()
            msg = suggestion_dict.get("text", "Let's be productive!")
            
            self._active_toast = ToastNotification(self, title=title, message=msg)
            self._active_toast.show_toast()
            
            # Optionally add to chat log
            self.chat.add_message(f"[Autonomous] {msg}", "assistant")
        except Exception as e:
            logger.error(f"Failed to show toast notification: {e}")

    def closeEvent(self, event) -> None:
        # Safely join background workers to prevent thread leaks
        if hasattr(self, 'autonomy_engine') and self.autonomy_engine:
            self.autonomy_engine.stop()
        if self.voice_worker:
            self.voice_worker.stop()
        speaking_engine.cancel()
        event.accept()
