"""Router layer for directing parsed intents to skills."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from memory.companion.engine import CompanionMemoryEngine
from companion.engine import CompanionIntelligenceEngine as _CIE

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from brain.brain import Brain


class Router:
    """Route an intent and optional entity to the appropriate skill handler."""

    def __init__(self, brain: "Brain") -> None:
        self.brain = brain

    def execute_plan(self, plan: list[dict[str, Any]], *, text: Optional[str] = None) -> str:
        """Execute each planned step sequentially, continuing after failures."""
        if not plan:
            return ""

        results: list[str] = []
        for index, step in enumerate(plan, start=1):
            intent = step.get("intent")
            entity = step.get("entity")
            step_text = step.get("text", text)
            logger.info("Executing task %s: %s", index, intent)
            try:
                response = self.route(intent, entity, text=step_text)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Task %s failed: %s", index, exc)
                results.append(f"Task {index} failed.")
                continue

            if response:
                results.append(str(response).strip())
            else:
                results.append(f"Task {index} failed.")

        logger.info("Finished.")

        if not results:
            return ""

        if len(results) == 1:
            return results[0]

        return " ".join(result for result in results if result)

    def route(self, intent: str, entity: Optional[Any] = None, *, text: Optional[str] = None) -> str:
        """Return a response for the provided intent and entity."""
        if text:
            lower_text = text.lower().strip()
            if "relates to" in lower_text or "relationship of" in lower_text or "relationships of" in lower_text or "connected to" in lower_text:
                entity_name = None
                for phrase in ["explain relationships of", "explain relationship of", "what relates to", "how does", "relates to", "connected to"]:
                    if phrase in lower_text:
                        parts = lower_text.split(phrase)
                        if len(parts) > 1:
                            entity_name = parts[1].replace("?", "").strip()
                            for word in ["does", "the", "a", "an", "of"]:
                                if entity_name.startswith(word + " "):
                                    entity_name = entity_name[len(word)+1:].strip()
                            break
                if not entity_name and "relates to" in lower_text:
                    parts = lower_text.split("relates to")
                    entity_name = parts[0].replace("what", "").replace("who", "").strip()

                if entity_name and hasattr(self.brain, "world") and self.brain.world:
                    return self.brain.world.explain_relationship(entity_name)

        if intent == "GRAPH_EXPLAIN":
            entity_str = entity.get("entity") if isinstance(entity, dict) else str(entity or text or "")
            if hasattr(self.brain, "world") and self.brain.world:
                return self.brain.world.explain_relationship(entity_str)
            return "Knowledge graph is not initialized."

        if intent == "OPEN_DASHBOARD":
            from dashboard.window import CompanionDashboard
            # The router operates outside the main thread (sometimes), but QWidgets must be created
            # and shown in the main UI thread. We assume the system event bus or a signal can do it,
            # but for now we'll just instantiate and show it if we are on the main thread, 
            # otherwise it might crash. Actually, we should trigger a UI signal.
            # To be safe, we return a message that the UI will intercept.
            return "DASHBOARD_TRIGGERED"
            
        if intent == "VOICE_COMPANION":
            from voice_companion.speech_router import voice_router
            action = entity.get("action") if isinstance(entity, dict) else str(entity)
            
            if action == "start":
                voice_router.start_service()
                return "Starting voice companion full-duplex mode."
            elif action == "stop":
                voice_router.stop_service()
                return "Stopping voice companion."
                
            return "Voice Companion action not recognized."

        if intent == "BROWSER":
            from browser.controller import browser_controller
            action = entity.get("action") if isinstance(entity, dict) else str(entity)
            
            if action == "start":
                browser_controller.start_session(headless=False)
                return "Starting browser session."
            elif action == "stop":
                browser_controller.stop_session()
                return "Stopping browser session."
            elif action == "navigate":
                target = entity.get("target", "https://google.com")
                browser_controller.navigate(target)
                return f"Navigating to {target}."
            elif action == "summarize":
                browser_controller.extract_summary()
                return "Extracting page summary. Check EventBus for completion."
            elif action == "fill_demo":
                # A theoretical search on google
                browser_controller.fill_and_submit("textarea[name='q']", "Khushi AI", "input[name='btnK']")
                return "Running form automation demo."
                
            return "Browser action not recognized."

        if intent == "VISION":
            from vision.controller import vision_controller
            action = entity.get("action") if isinstance(entity, dict) else str(entity)
            
            if action == "analyze_window":
                vision_controller.analyze_active_window()
                return "Analyzing the active window. Check the event bus for results."
            elif action == "summarize_screen":
                vision_controller.summarize_screen()
                return "Summarizing the screen visually. Check the event bus for results."
            elif action == "highlight_demo":
                # Demo for the walkthrough
                vision_controller.show_overlay([(100, 100, 200, 200), (400, 300, 150, 50)])
                return "Drawing highlight overlay demo on screen."
            elif action == "hide_highlight":
                vision_controller.hide_overlay()
                return "Hiding visual overlays."
            elif action == "start_history":
                vision_controller.enable_continuous_capture(interval_sec=10)
                return "Started continuous screen capture history (10s intervals)."
            elif action == "stop_history":
                vision_controller.disable_continuous_capture()
                return "Stopped continuous screen capture history."
            
            return "Vision action not recognized."

        if intent == "AUTOMATION":
            from automation.controller import automation_controller
            from automation.models import RiskLevel
            import time
            
            action = entity.get("action") if isinstance(entity, dict) else str(entity)
            target = entity.get("target") if isinstance(entity, dict) else str(text)
            
            if action == "open_notepad_and_type":
                # Manual verification scenario: Open Notepad and type "Hello"
                def demo():
                    automation_controller.window.open_app("notepad.exe")
                    time.sleep(1) # wait for notepad
                    automation_controller.keyboard.type_text("Hello")
                
                automation_controller.execute("demo_notepad", "Demo Notepad", RiskLevel.LOW, demo)
                return "Executing automation: Open Notepad and type 'Hello'."
                
            elif action == "open_calculator":
                automation_controller.execute("demo_calc", "Open Calculator", RiskLevel.LOW, automation_controller.window.open_app, "calc.exe")
                return "Executing automation: Open Calculator."
                
            elif action == "copy_text":
                automation_controller.execute("demo_copy", "Copy Text", RiskLevel.LOW, automation_controller.keyboard.hotkey, 'ctrl', 'c')
                return "Executing automation: Copy selected text."
                
            elif action == "capture_ocr":
                def demo_ocr():
                    txt, _ = automation_controller.ocr.extract_text()
                    return txt
                automation_controller.execute("demo_ocr", "Capture OCR", RiskLevel.LOW, demo_ocr)
                return "Executing automation: Capture screenshot and OCR."
                
            elif action == "switch_window":
                automation_controller.execute("demo_switch", "Switch Window", RiskLevel.LOW, automation_controller.keyboard.hotkey, 'alt', 'tab')
                return "Executing automation: Switch window."
                
            elif action == "destructive_test":
                def demo_destructive():
                    automation_controller.system.shutdown()
                automation_controller.execute("demo_shutdown", "Test Shutdown Confirmation", RiskLevel.CRITICAL, demo_destructive)
                return "Executing automation: Destructive action test (Shutdown)."
                
            return "Automation action not recognized."

        if intent == "OPEN_APP":
            return self.brain.skills.app.execute(text or "") or "Sorry, I could not open that app."

        if intent == "OPEN_URL":
            return self.brain.skills.app.open_url(str(entity or "")) or "Sorry, I could not open that URL."

        if intent == "SEARCH":
            return self.brain.skills.search.execute(text or "") or "Sorry, I could not search that."

        if intent == "WEB_SEARCH":
            return self.brain.skills.web_search.execute(text or "") or "Sorry, I could not complete that web search."

        if intent == "KNOWLEDGE_QUERY":
            return self.brain.skills.knowledge.execute(text or "") or "Sorry Faisal, I couldn't find that in your documents."

        if intent == "CALCULATE":
            return self.brain.skills.calculator.execute(text or "") or "I could not calculate that."

        if intent == "WEATHER":
            return self.brain.skills.weather.execute(text or "") or "Weather service is not configured."

        if intent == "NOTE_CREATE":
            return self.brain.skills.notes.create_note(text or "") or "I could not save that note."

        if intent == "NOTE_SHOW":
            return self.brain.skills.notes.show_notes() or "You do not have any notes yet."

        if intent == "NOTE_DELETE":
            return self.brain.skills.notes.delete_notes() or "I could not delete the notes."

        if intent == "SCREENSHOT":
            return self.brain.skills.screenshot.execute(text or "") or "I could not take a screenshot."

        if intent == "SYSTEM":
            return self.brain.skills.system.execute(text or "") or "I could not get system information."

        if intent == "CLIPBOARD":
            return self.brain.skills.clipboard.execute(entity or "") or "I could not access the clipboard."

        if intent == "VOLUME":
            return self.brain.skills.volume.execute(entity or "") or "I could not change the volume."

        if intent == "BRIGHTNESS":
            return self.brain.skills.brightness.execute(entity or "") or "I could not change the brightness."

        if intent == "FILE_SEARCH":
            return self.brain.skills.file_search.execute(text or "") or "I could not find that file."

        if intent == "FILE":
            return self.brain.skills.file.execute(text or "") or "I could not complete that file action."

        if intent == "TIME":
            return self.brain.skills.time.execute()

        if intent == "DATE":
            return self.brain.skills.date.execute()


        if intent == "REMEMBER":
            if isinstance(entity, dict):
                self.brain.memory.remember(entity.get("key", ""), entity.get("value", ""))
                return "I'll remember that."
            return "Say: Remember something is value."

        if intent == "SAVE_MEMORY":
            result = self.brain.memory.save_statement(text or "")
            return "I've remembered that." if result else "I didn't catch that memory."

        if intent == "RECALL_MEMORY":
            result = self.brain.memory.recall_question(text or "")
            return result or "I don't have that saved yet."

        if intent == "NAME":
            if isinstance(entity, str):
                self.brain.user_name = entity
                self.brain._save_user_name(entity)
                return f"Nice to meet you {entity}."
            return "I don't know your name yet."

        if intent == "GREETING":
            return "Hello Faisal."

        if intent == "GOODBYE":
            return "Goodbye."

        if intent == "LIFE_MEMORY":
            # Companion Memory is a first-class independent subsystem.
            from memory.companion.engine import CompanionMemoryEngine
            engine = CompanionMemoryEngine(store=self.brain.cie._store)
            return engine.handle(intent=intent, entity=entity, text=text or "")

        # Companion Intelligence
        if intent == "COMPANION_REFLECT":
            import time as _time
            cie = self.brain.cie
            reflection = cie.get_reflection(now_text=_time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()))
            lines = ["--- Companion Reflection ---"]
            for freq in ["daily", "weekly", "monthly"]:
                block = reflection.get(freq, {})
                lines.append(f"{freq.upper()}: {block.get('natural_summary', 'No data.')}")
            return "\n".join(lines)

        if intent == "COMPANION_RECOMMEND":
            cie = self.brain.cie
            recos = cie.get_recommendations()
            if not recos:
                return "No grounded recommendations yet. Try adding goals or habits first."
            lines = ["--- Personalized Recommendations ---"]
            for r in recos[:5]:
                lines.append(f"[{r.get('domain')}] {r.get('title')}")
                lines.append(f"  Why: {r.get('why')}")
                lines.append(f"  Confidence: {int(float(r.get('confidence', 0)) * 100)}%")
            return "\n".join(lines)

        if intent == "COMPANION_PROFILE":
            import json as _json
            cie = self.brain.cie
            profile = cie.get_profile()
            lines = ["--- Your Profile (from Companion Memory) ---"]
            for section, records in profile.items():
                if records:
                    lines.append(f"\n{section.upper()}:")
                    if isinstance(records, dict):
                        for rid, rec in records.items():
                            payload = rec.get("payload", {}) if isinstance(rec, dict) else {}
                            val = payload.get("value") or payload.get("text") if isinstance(payload, dict) else None
                            if val:
                                lines.append(f"  - {val}")
            return "\n".join(lines) if len(lines) > 1 else "No profile data stored yet."

        if intent == "COMPANION_TIMELINE":
            cie = self.brain.cie
            events = cie.get_timeline()
            if not events:
                return "No timeline events stored yet."
            lines = ["--- Timeline (Chronological, newest first) ---"]
            for ev in events[:20]:
                ts = ev.get("created_at", "")
                cat = ev.get("category", "")
                val = ev.get("value", "")
                if val:
                    lines.append(f"[{ts}] [{cat}] {val}")
            return "\n".join(lines)

        if intent == "COMPANION_STATUS":
            cie = self.brain.cie
            sess = cie.session_summary()
            lines = [
                "--- Companion Intelligence Status ---",
                f"Session turns: {sess.get('session_turns', 0)}",
                f"Intents seen: {', '.join(sess.get('intents_seen', [])) or 'none'}",
                "Recent topics:",
            ]
            for t in sess.get("recent_topics", []):
                lines.append(f"  - {t}")
            return "\n".join(lines)

        return "Sorry Faisal, I don't know that yet."
