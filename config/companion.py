from __future__ import annotations

# Companion Memory configuration.
# Kept stdlib-only; defaults tuned to be safe (no destructive behavior).

# Confidence thresholds (not ML-based; rule/heuristic only).
CONFIDENCE_HIGH = 0.95
CONFIDENCE_MEDIUM = 0.7
CONFIDENCE_LOW = 0.0

# Duplicate detection:
# If normalized values match exactly (string match after normalization), we treat as duplicate.
DUPLICATE_THRESHOLD = 0.98

# Default importance for new memories when importance isn't provided by parser.
DEFAULT_IMPORTANCE = 0.5

# Maximum number of timeline events to keep (to prevent unbounded growth).
# Engine will truncate oldest events if needed.
HISTORY_LIMIT = 500
