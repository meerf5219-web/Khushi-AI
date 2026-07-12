"""
Companion Intelligence (Phase 5.x).

This package is intentionally independent from chat memory and KnowledgeSkill.
All intelligence it produces must be grounded only in Companion Memory.
"""

from .engine import CompanionIntelligenceEngine

__all__ = ["CompanionIntelligenceEngine"]
