import logging
import threading
import time

from brain.brain import Brain
from voice.speaker import speak

logger = logging.getLogger(__name__)


def startup() -> Brain:
    """
    Prepare the assistant and return a ready Brain instance.
    Issue 6: Brain() init (SentenceTransformer, memory, companion, skills) runs in
    a background thread while welcome speech plays — parallelizing cold startup.
    """
    print("=" * 40)
    print("Version 0.2")
    print("=" * 40)

    logger.info("Starting Khushi assistant")

    # Issue 6: Start Brain initialization in background thread immediately
    brain_holder: list = [None]
    brain_exc: list = [None]

    def _init_brain() -> None:
        try:
            t0 = time.perf_counter()
            brain_holder[0] = Brain()
            elapsed = time.perf_counter() - t0
            logger.info("[STARTUP] Brain initialized in %.2fs", elapsed)
        except Exception as exc:
            brain_exc[0] = exc
            logger.error("[STARTUP] Brain initialization failed: %s", exc)

    brain_thread = threading.Thread(target=_init_brain, daemon=False)
    brain_thread.start()

    # Play welcome speech while Brain loads in parallel
    speak("Welcome back Faisal.")
    speak("I am ready.")

    # Wait for Brain to finish (it will usually be ready by the time speech ends)
    brain_thread.join()

    if brain_exc[0] is not None:
        raise RuntimeError(f"Brain initialization failed: {brain_exc[0]}") from brain_exc[0]

    return brain_holder[0]