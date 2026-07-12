import uuid
import queue
import logging
import threading
from typing import Optional, Dict, Any

from brain.event_bus import event_bus

logger = logging.getLogger(__name__)

class AgentContext:
    def __init__(self, task_id: str, payload: dict):
        self.task_id = task_id
        self.payload = payload

class BaseAgent:
    """
    Abstract Base Class for all Swarm Agents.
    Listens on `agent.{name}` channel.
    """
    def __init__(self, name: str, brain=None):
        self.name = name
        self.brain = brain
        self.channel = f"agent.{name}"
        event_bus.subscribe(self.channel, self._on_message)
        logger.info(f"Agent '{self.name}' initialized and listening on '{self.channel}'.")

    def _on_message(self, message: dict):
        """
        Internal event bus handler.
        Message format expected:
        {
            "task_id": "uuid-1234",
            "reply_to": "coordinator",
            "payload": {...}
        }
        """
        task_id = message.get("task_id")
        reply_to = message.get("reply_to")
        payload = message.get("payload", {})

        if not task_id:
            logger.warning(f"Agent {self.name} received message without task_id. Ignoring.")
            return

        logger.info(f"[{self.name}] Processing task {task_id}...")
        
        # Process task (blocking within this thread for now, or could spawn worker)
        # Assuming event_bus handles subscribers in a thread pool already.
        try:
            context = AgentContext(task_id, payload)
            result = self.process(context)
            
            # Send reply
            if reply_to:
                reply_msg = {
                    "task_id": task_id,
                    "status": "success",
                    "result": result
                }
                event_bus.publish(reply_to, reply_msg)
        except Exception as e:
            logger.error(f"[{self.name}] Task {task_id} failed: {e}")
            if reply_to:
                event_bus.publish(reply_to, {
                    "task_id": task_id,
                    "status": "error",
                    "error": str(e)
                })

    def process(self, context: AgentContext) -> Any:
        """
        Override this method to implement specialized agent logic.
        """
        raise NotImplementedError("Subclasses must implement process()")


class SyncAgentClient:
    """
    Utility for the Coordinator to perform synchronous request-reply over the EventBus.
    """
    def __init__(self, reply_channel: str = "agent.coordinator.reply"):
        self.reply_channel = reply_channel
        self.pending_tasks = {}  # task_id -> Queue
        event_bus.subscribe(self.reply_channel, self._on_reply)

    def _on_reply(self, message: dict):
        task_id = message.get("task_id")
        if task_id and task_id in self.pending_tasks:
            self.pending_tasks[task_id].put(message)

    def request(self, target_agent: str, payload: dict, timeout: int = 30) -> dict:
        """
        Sends a message to `agent.{target_agent}` and blocks until a reply is received
        on `self.reply_channel` or timeout is reached.
        """
        task_id = str(uuid.uuid4())
        q = queue.Queue()
        self.pending_tasks[task_id] = q

        message = {
            "task_id": task_id,
            "reply_to": self.reply_channel,
            "payload": payload
        }

        channel = f"agent.{target_agent}"
        logger.info(f"Delegating task {task_id} to {channel} (Timeout: {timeout}s)")
        event_bus.publish(channel, message)

        try:
            reply = q.get(timeout=timeout)
            return reply
        except queue.Empty:
            logger.warning(f"Task {task_id} to {target_agent} timed out.")
            return {"status": "error", "error": "Timeout"}
        finally:
            del self.pending_tasks[task_id]
