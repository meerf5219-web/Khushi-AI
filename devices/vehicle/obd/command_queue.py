import queue
import threading
import logging
from typing import Callable, Any, Dict, Optional

logger = logging.getLogger(__name__)

class OBDCommandQueue:
    """
    Thread-safe command queue for executing sequential diagnostics and sensor readings
    without blocking application logic.
    """
    def __init__(self, obd_connection: Any) -> None:
        self.obd = obd_connection
        self.queue: queue.Queue = queue.Queue()
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Starts the command runner daemon thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("OBD Command Queue runner started.")

    def stop(self) -> None:
        """Stops the queue runner thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            logger.info("OBD Command Queue runner stopped.")

    def enqueue(self, action: str, callback: Callable[[Dict[str, Any]], None], *args) -> None:
        """Enqueues a sensor reading command or diagnostic request."""
        self.queue.put((action, callback, args))
        logger.debug(f"Enqueued action: {action}")

    def _run_loop(self) -> None:
        """Worker thread processing commands sequentially."""
        while self.running:
            try:
                # Polling queue with a short timeout to check self.running regularly
                action, callback, args = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                result = None
                if action == "read_sensor" and args:
                    pid = args[0]
                    result = self.obd.read_sensor(pid)
                elif action == "read_diagnostics":
                    dtcs = self.obd.read_diagnostics()
                    result = {"status": "success", "dtcs": dtcs}
                else:
                    result = {"status": "error", "message": f"Action {action} not recognized."}

                # Trigger callback on main/caller context thread
                callback(result)
            except Exception as e:
                logger.error(f"Error processing enqueued OBD action {action}: {e}")
                callback({"status": "error", "message": str(e)})
            finally:
                self.queue.task_done()
