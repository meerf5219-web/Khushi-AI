from __future__ import annotations

"""
Test Suite for integrated Phase 6: Intelligence Layer behavior in Brain.
Covers manual verification requirements.
"""

import os
import tempfile
import unittest
from pathlib import Path

from brain.brain import Brain
from companion.engine import CompanionIntelligenceEngine
from memory import memory as memory_module
from memory.companion.engine import MemoryRecord
from memory.companion.engine import CompanionMemoryStore


class TestPhase6Integration(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        
        # Override standard memory files
        self.original_file_name = memory_module.FILE_NAME
        memory_module.FILE_NAME = str(Path(self.temp_dir.name) / "user_memory.json")
        
        # Override companion memory store to avoid side-effects
        self.comp_memory_file = str(Path(self.temp_dir.name) / "companion_memory.json")
        
        # Set up a clean store
        self.store = CompanionMemoryStore(file_name=self.comp_memory_file)
        
        # Populate initial values in Companion Memory
        # Name
        self.store.upsert_record(
            bucket="identity",
            record_id="identity:name",
            record=MemoryRecord(
                created_date="2026-07-01T10:00:00Z",
                updated_date="2026-07-01T10:00:00Z",
                confidence=1.0,
                source="user",
                category="identity",
                payload={"value": "Faisal", "id": "identity:name"}
            )
        )
        
        # Goal
        self.store.upsert_record(
            bucket="goals",
            record_id="goals:upsc",
            record=MemoryRecord(
                created_date="2026-07-01T10:00:00Z",
                updated_date="2026-07-01T10:00:00Z",
                confidence=1.0,
                source="user",
                category="goals",
                payload={"value": "Crack UPSC", "id": "goals:upsc"}
            )
        )
        
        # Project
        self.store.upsert_record(
            bucket="projects",
            record_id="projects:khushi",
            record=MemoryRecord(
                created_date="2026-07-01T10:00:00Z",
                updated_date="2026-07-01T10:00:00Z",
                confidence=1.0,
                source="user",
                category="projects",
                payload={"value": "Khushi AI Project", "id": "projects:khushi"}
            )
        )
        
        # Timeline
        self.store.append_event(
            bucket="timeline",
            event={
                "created_at": "2026-07-01T10:00:00Z",
                "updated_at": "2026-07-01T10:00:00Z",
                "category": "timeline",
                "confidence": 1.0,
                "value": "Started working on Khushi AI Project",
            }
        )

    def tearDown(self) -> None:
        memory_module.FILE_NAME = self.original_file_name

    def test_manual_verification_case_1(self) -> None:
        """Test 1: 'What ise my name?' should correct typo and recall name directly without LLM."""
        brain = Brain()
        brain.cie = CompanionIntelligenceEngine(store=self.store)
        brain.pipeline.context_router._cie = brain.cie
        brain.pipeline.learning_engine._filepath = str(Path(self.temp_dir.name) / "learning_corrections.json")
        brain.pipeline.learning_engine._load()

        # Save name in standard memory
        brain._save_user_name("Faisal")

        response = brain.think("What ise my name?")
        self.assertIn("Faisal", response)

    def test_manual_verification_case_2(self) -> None:
        """Test 2: 'Who am I?' should rewrite to show my profile."""
        brain = Brain()
        brain.cie = CompanionIntelligenceEngine(store=self.store)
        brain.pipeline.context_router._cie = brain.cie
        brain.pipeline.learning_engine._filepath = str(Path(self.temp_dir.name) / "learning_corrections.json")
        brain.pipeline.learning_engine._load()
        
        response = brain.think("Who am I?")
        self.assertIn("profile", response.lower())

    def test_manual_verification_case_3(self) -> None:
        """Test 3: 'Tell me the name I told you.' should map to what is my name."""
        brain = Brain()
        brain.cie = CompanionIntelligenceEngine(store=self.store)
        brain.pipeline.context_router._cie = brain.cie
        brain.pipeline.learning_engine._filepath = str(Path(self.temp_dir.name) / "learning_corrections.json")
        brain.pipeline.learning_engine._load()
        brain._save_user_name("Faisal")

        response = brain.think("Tell me the name I told you.")
        self.assertIn("Faisal", response)

    def test_manual_verification_case_4(self) -> None:
        """Test 4: 'My objective.' should map to show my goals."""
        brain = Brain()
        brain.cie = CompanionIntelligenceEngine(store=self.store)
        brain.pipeline.context_router._cie = brain.cie
        brain.pipeline.learning_engine._filepath = str(Path(self.temp_dir.name) / "learning_corrections.json")
        brain.pipeline.learning_engine._load()

        response = brain.think("My objective.")
        self.assertIn("goals", response.lower())
        self.assertIn("crack upsc", response.lower())

    def test_manual_verification_case_5(self) -> None:
        """Test 5: 'Open Chrome and tell me today's weather.' should split into two tasks."""
        brain = Brain()
        brain.cie = CompanionIntelligenceEngine(store=self.store)
        brain.pipeline.context_router._cie = brain.cie
        brain.pipeline.learning_engine._filepath = str(Path(self.temp_dir.name) / "learning_corrections.json")
        brain.pipeline.learning_engine._load()

        response = brain.think("Open Chrome and tell me the weather.")
        self.assertIn("opening chrome", response.lower())
        self.assertTrue(
            "weather" in response.lower() or 
            "online" in response.lower() or 
            "configured" in response.lower()
        )

    def test_manual_verification_case_6(self) -> None:
        """Test 6: 'Show the project I was working on.' should query Companion Memory."""
        brain = Brain()
        brain.cie = CompanionIntelligenceEngine(store=self.store)
        brain.pipeline.context_router._cie = brain.cie
        brain.pipeline.learning_engine._filepath = str(Path(self.temp_dir.name) / "learning_corrections.json")
        brain.pipeline.learning_engine._load()

        response = brain.think("Show the project I was working on.")
        self.assertIn("Khushi AI Project", response)

    def test_manual_verification_case_7(self) -> None:
        """Test 7: 'No, I meant my UPSC goal.' should learn the correction mapping."""
        brain = Brain()
        brain.cie = CompanionIntelligenceEngine(store=self.store)
        brain.pipeline.context_router._cie = brain.cie
        brain.pipeline.learning_engine._filepath = str(Path(self.temp_dir.name) / "learning_corrections.json")
        brain.pipeline.learning_engine._load()
        
        # Populate history
        brain.think("What was my target?") # first query
        
        # Correction statement
        response = brain.think("No, I meant my UPSC goal.")
        self.assertIn("learned correction", response.lower())
        self.assertIn("my upsc goal", response.lower())
