from dataclasses import dataclass
from typing import Dict

@dataclass
class VoiceProfile:
    name: str
    rate: int      # words per minute
    volume: float  # 0.0 to 1.0

# Emotion mappings for basic pyttsx3 fallback
PROFILES: Dict[str, VoiceProfile] = {
    "default": VoiceProfile(name="default", rate=180, volume=1.0),
    "professional": VoiceProfile(name="professional", rate=160, volume=1.0),
    "teaching": VoiceProfile(name="teaching", rate=140, volume=1.0),
    "friendly": VoiceProfile(name="friendly", rate=185, volume=1.0),
    "motivational": VoiceProfile(name="motivational", rate=200, volume=1.0),
    "urgent": VoiceProfile(name="urgent", rate=220, volume=1.0),
    "calm": VoiceProfile(name="calm", rate=130, volume=0.8),
}

def get_profile(emotion: str) -> VoiceProfile:
    return PROFILES.get(emotion.lower(), PROFILES["default"])
