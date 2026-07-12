"""
ui/widgets/conversation/conversation_widget.py — Main Conversation Panel Orchestrator
========================================================================================
Integrates message logs, virtualization managers (HistoryManager), auto-scrolling,
search bar, export controls, and stream token dispatch mechanisms.
"""
from __future__ import annotations

import os
import logging
import time
from typing import List, Set, Optional
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFileDialog, QMessageBox
)

from ui.widgets.conversation.message_widget import MessageWidget
from ui.widgets.conversation.scroll_manager import ScrollManager
from ui.widgets.conversation.conversation_search import ConversationSearchWidget
from ui.widgets.conversation.history_manager import HistoryManager
from ui.widgets.conversation.export_manager import ExportManager
from ui.widgets.conversation.stream_renderer import StreamRenderer
from ui.widgets.conversation.thinking_indicator import ThinkingIndicator

logger = logging.getLogger(__name__)


class ConversationWidget(QWidget):
    """
    Main widget wrapper managing conversation logs, scroll actions, and text filters.
    """
    re_run_brain = Signal(str)  # Emitted when the user edits and resubmits a turn

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ChatContainer")
        
        self.history = HistoryManager()
        self.active_stream_bubble: Optional[MessageWidget] = None
        self.stream_renderer: Optional[StreamRenderer] = None
        self.thinking_indicator: Optional[ThinkingIndicator] = None
        
        self._history_offset = 0
        self._all_turns: List[dict] = []
        self._pinned_event_ids: Set[str] = set()

        self._init_ui()
        self._load_initial_history()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Search Toolbar (Top)
        self.search_bar = ConversationSearchWidget()
        self.search_bar.search_changed.connect(self._on_search_changed)
        self.search_bar.clear_search.connect(self._on_search_cleared)
        layout.addWidget(self.search_bar)

        # 2. Main Scroll Area Container
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(15, 15, 15, 15)
        self.scroll_layout.setSpacing(12)
        
        # Spacer stretch keeps bubble messages pinned to the top of the scroll container
        self.scroll_layout.addStretch()
        
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

        # Connect Scroll Manager
        self.scroll_manager = ScrollManager(self.scroll)
        
        # Connect lazy loading on scrollbar close to top
        self.scroll.verticalScrollBar().valueChanged.connect(self._on_scroll_moved)

    def _load_initial_history(self) -> None:
        """Fetch first offset of historical turn cards."""
        turns = self.history.load_recent_turns(offset=self._history_offset, limit=40)
        self._history_offset += len(turns)
        self._all_turns.extend(turns)
        
        # Populate UI
        for turn in turns:
            self._render_message(
                event_id=turn["event_id"],
                text=turn["raw_text"],
                sender=turn["source"],
                timestamp=turn["timestamp"],
                metadata=turn["metadata"],
                append=False # Insert at top
            )
        self.scroll_manager.scroll_to_bottom()

    def _on_scroll_moved(self, value: int) -> None:
        """Triggered when scrollbar position changes. Triggers lazy loading at top."""
        if value == 0 and self._history_offset > 0:
            # Save position before inserting new widgets
            prev_max = self.scroll.verticalScrollBar().maximum()
            
            # Load older items
            turns = self.history.load_recent_turns(offset=self._history_offset, limit=20)
            if turns:
                self._history_offset += len(turns)
                self._all_turns = turns + self._all_turns
                
                # Render them at top (insert at position 0, shifting others down)
                for turn in reversed(turns):
                    self._render_message(
                        event_id=turn["event_id"],
                        text=turn["raw_text"],
                        sender=turn["source"],
                        timestamp=turn["timestamp"],
                        metadata=turn["metadata"],
                        append=False
                    )
                
                # Maintain scrollbar position offset
                new_max = self.scroll.verticalScrollBar().maximum()
                self.scroll.verticalScrollBar().setValue(new_max - prev_max)

    def add_message(self, text: str, sender: str, metadata: dict = None) -> None:
        """Write turn to database, and append to visual log container."""
        # Stop thinking animations if user/assistant writes new message
        self.hide_thinking()

        # Write to SQLite Store
        event_id = self.history.save_turn(sender, text, metadata=metadata)
        
        # Re-sync local caching list
        self._all_turns.append({
            "event_id": event_id,
            "timestamp": time.time(),
            "source": sender,
            "raw_text": text,
            "metadata": metadata or {}
        })

        self._render_message(event_id, text, sender, time.time(), metadata or {}, append=True)

    def _render_message(
        self,
        event_id: str,
        text: str,
        sender: str,
        timestamp: float,
        metadata: dict,
        append: bool = True
    ) -> None:
        msg = MessageWidget(event_id, text, sender, timestamp, metadata)
        msg.edit_submitted.connect(self._on_user_message_edited)
        msg.delete_requested.connect(self._on_message_delete)
        msg.pin_requested.connect(self._on_message_pinned)

        if append:
            # Append before the last spacer stretch at bottom
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, msg)
            self.scroll_manager.scroll_to_bottom()
        else:
            # Insert older items at the top (right after the layout stretch spacer, which is index 0)
            self.scroll_layout.insertWidget(1, msg)

    # ------------------------------------------------------------------
    # Streaming & Thinking animations
    # ------------------------------------------------------------------

    def show_thinking(self) -> None:
        """Display 'Khushi is thinking...' animation dots block."""
        if not self.thinking_indicator:
            self.thinking_indicator = ThinkingIndicator()
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, self.thinking_indicator)
            self.scroll_manager.scroll_to_bottom()

    def hide_thinking(self) -> None:
        """Instantly delete thinking animation."""
        if self.thinking_indicator:
            self.scroll_layout.removeWidget(self.thinking_indicator)
            self.thinking_indicator.stop()
            self.thinking_indicator.deleteLater()
            self.thinking_indicator = None

    def start_streaming(self) -> None:
        """Instantiate empty Assistant bubble and initialize cursor blinkers."""
        self.hide_thinking()
        
        # Save temp turn
        event_id = f"stream_{int(time.time())}"
        self.active_stream_bubble = MessageWidget(event_id, "", "assistant", time.time())
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, self.active_stream_bubble)
        
        self.stream_renderer = StreamRenderer(self.active_stream_bubble)
        self.scroll_manager.scroll_to_bottom()

    def append_stream_token(self, token: str, full_text: str) -> None:
        if not self.active_stream_bubble:
            self.start_streaming()
        
        if self.stream_renderer:
            self.stream_renderer.append_token(token, full_text)
            self.scroll_manager.scroll_to_bottom()

    def finalize_stream(self, metadata: dict = None) -> None:
        """Commit stream content to database, stop blinkers, and parse HTML tags."""
        if self.stream_renderer:
            self.stream_renderer.finalize()
            
            # Save completed turn to database
            final_text = self.stream_renderer.raw_text
            self.active_stream_bubble.deleteLater() # Delete the visual streaming container
            self.active_stream_bubble = None
            self.stream_renderer = None
            
            # Re-render as a standard committed message bubble
            self.add_message(final_text, "assistant", metadata)

    # ------------------------------------------------------------------
    # Action Triggers
    # ------------------------------------------------------------------

    def _on_user_message_edited(self, new_text: str) -> None:
        logger.info("[CONVERSATION] User edited last message to: '%s'", new_text)
        self.history.edit_last_user_event(new_text)
        # Emit signal to main window to run Brain inference
        self.re_run_brain.emit(new_text)

    def _on_message_delete(self, event_id: str) -> None:
        if self.history.delete_message(event_id):
            # Find and remove widget from UI layout
            for i in range(self.scroll_layout.count()):
                child = self.scroll_layout.itemAt(i)
                if child and child.widget() and isinstance(child.widget(), MessageWidget):
                    if child.widget().event_id == event_id:
                        child.widget().deleteLater()
                        break

    def _on_message_pinned(self, event_id: str) -> None:
        if event_id in self._pinned_event_ids:
            self._pinned_event_ids.remove(event_id)
        else:
            self._pinned_event_ids.add(event_id)
        logger.info("[CONVERSATION] Toggled pin on event: %s", event_id)

    # ------------------------------------------------------------------
    # Search & Filters
    # ------------------------------------------------------------------

    def _on_search_changed(self, query: str, filters: dict) -> None:
        query = query.lower().strip()
        
        # Iterate over visible widgets and toggle visibility based on criteria
        for i in range(self.scroll_layout.count()):
            child = self.scroll_layout.itemAt(i)
            if child and child.widget() and isinstance(child.widget(), MessageWidget):
                widget = child.widget()
                
                # Check filters
                matches_filter = True
                if filters.get("user_only") and widget.sender != "user":
                    matches_filter = False
                elif filters.get("assistant_only") and widget.sender != "assistant":
                    matches_filter = False
                elif filters.get("pinned_only") and widget.event_id not in self._pinned_event_ids:
                    matches_filter = False
                
                # Check keyword match
                matches_query = True
                if query and query not in widget.raw_text.lower():
                    matches_query = False
                
                # Set visibility
                widget.setVisible(matches_filter and matches_query)

    def _on_search_cleared(self) -> None:
        # Restore all message bubble visibility
        for i in range(self.scroll_layout.count()):
            child = self.scroll_layout.itemAt(i)
            if child and child.widget() and isinstance(child.widget(), MessageWidget):
                child.widget().show()

    # ------------------------------------------------------------------
    # Export File Controls
    # ------------------------------------------------------------------

    def trigger_export(self, format_name: str) -> None:
        """Trigger Save File dialog and write conversation records."""
        if not self._all_turns:
            return

        fmt = format_name.lower()
        ext_filter = "Text File (*.txt)"
        if fmt == "markdown":
            ext_filter = "Markdown File (*.md)"
        elif fmt == "json":
            ext_filter = "JSON File (*.json)"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Chat Export", os.path.expanduser("~/Documents"), ext_filter
        )
        
        if file_path:
            success = False
            if fmt == "txt":
                success = ExportManager.to_txt(self._all_turns, file_path)
            elif fmt == "markdown":
                success = ExportManager.to_markdown(self._all_turns, file_path)
            elif fmt == "json":
                success = ExportManager.to_json(self._all_turns, file_path)

            if success:
                QMessageBox.information(self, "Export Success", f"Conversation saved to {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "Export Error", "Failed to save conversation. Check logs for details.")

    def clear(self) -> None:
        """Clean layout and reset state flags."""
        self.active_stream_bubble = None
        self.stream_renderer = None
        self._history_offset = 0
        self._all_turns.clear()
        
        while self.scroll_layout.count() > 1:
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
