import logging
import time

import speech_recognition as sr

logger = logging.getLogger(__name__)
recognizer = sr.Recognizer()


def listen() -> str:
    """Capture microphone input and return the recognized speech text."""
    with sr.Microphone() as source:
        logger.info("Listening...")
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        start = time.perf_counter()
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
    except (sr.UnknownValueError, sr.RequestError) as exc:
        logger.warning("Speech recognition failed: %s", exc)
        return ""

    speech_elapsed = time.perf_counter() - start
    print(f"Speech: {speech_elapsed:.3f}s")

    logger.info("You: %s", text)
    print("You:", text)
    return text.lower()
