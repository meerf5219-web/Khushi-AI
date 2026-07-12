import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import Qt

from dashboard.models.memory_model import MemoryTableModel

@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.get_timeline.return_value = [
        {"id": "1", "category": "goal", "value": "Learn Python", "created_at": "2026-07-10T10:00:00Z"},
        {"id": "2", "category": "fact", "value": "User likes blue", "created_at": "2026-07-10T11:00:00Z"}
    ]
    return engine

def test_memory_table_model(mock_engine):
    """Test that the table model correctly maps engine data to PySide6 roles."""
    model = MemoryTableModel(mock_engine)
    
    assert model.rowCount() == 2
    assert model.columnCount() == 4
    
    # Test DisplayRole (Cell Text)
    index = model.index(0, 1) # row 0, col 1 (Category)
    assert model.data(index, Qt.DisplayRole) == "goal"
    
    index_val = model.index(1, 2) # row 1, col 2 (Data)
    assert model.data(index_val, Qt.DisplayRole) == "User likes blue"
    
    # Test UserRole (Full Record)
    record = model.data(index, Qt.UserRole)
    assert record["id"] == "1"
