from enum import IntEnum

class AutonomyLevel(IntEnum):
    """
    Defines how much freedom Khushi has to act proactively.
    """
    LEVEL_0_OBSERVE = 0  # Monitor only, no suggestions or interruptions.
    LEVEL_1_SUGGEST = 1  # Send non-intrusive UI toasts suggesting actions.
    LEVEL_2_ASK     = 2  # Ask out loud (Voice) for permission to execute workflows.
    LEVEL_3_EXECUTE = 3  # Automatically execute safe background workflows without asking.

# Active configuration (Loaded from settings ideally)
CURRENT_AUTONOMY_LEVEL = AutonomyLevel.LEVEL_1_SUGGEST
IDLE_THRESHOLD_SECONDS = 300  # 5 minutes
