import sys
import time
import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication

from ui.workers.loading_worker import LoadingWorker
from ui.workers.brain_worker import BrainWorker
from automation.workers import AutomationWorker
from ui.workers.memory_worker import MemoryWorker

# Initialize QApplication singleton
app = QApplication.instance() or QApplication(sys.argv)

def test_loading_worker_signals():
    worker = LoadingWorker()
    signals = {"started": False, "finished": False}
    
    worker.started.connect(lambda: signals.update({"started": True}))
    worker.finished.connect(lambda obj: signals.update({"finished": True}))
    
    # Mock inner stages to prevent slow loading
    worker._load_config = MagicMock()
    worker._init_voice = MagicMock()
    worker._init_brain = MagicMock(return_value="mock_brain")
    worker._init_event_store = MagicMock()
    worker._ready_system = MagicMock()
    
    worker.start()
    t0 = time.time()
    while not signals["finished"] and time.time() - t0 < 3.0:
        app.processEvents()
        time.sleep(0.01)
        
    assert signals["started"] is True
    assert signals["finished"] is True

def test_brain_worker_signals():
    mock_brain = MagicMock()
    mock_brain.think.return_value = "hello"
    worker = BrainWorker(mock_brain, "hi")
    
    signals = {"started": False, "progress": False, "finished": False}
    worker.started.connect(lambda: signals.update({"started": True}))
    worker.progress.connect(lambda val, msg: signals.update({"progress": True}))
    worker.finished.connect(lambda rep, t: signals.update({"finished": True}))
    
    worker.start()
    t0 = time.time()
    while not signals["finished"] and time.time() - t0 < 3.0:
        app.processEvents()
        time.sleep(0.01)
        
    assert signals["started"] is True
    assert signals["progress"] is True
    assert signals["finished"] is True

def test_automation_worker_signals():
    func = MagicMock(return_value="done")
    worker = AutomationWorker("test_act", func)
    
    signals = {"started": False, "progress": False, "finished": False}
    worker.started.connect(lambda: signals.update({"started": True}))
    worker.progress.connect(lambda val, msg: signals.update({"progress": True}))
    worker.finished.connect(lambda name, res: signals.update({"finished": True}))
    
    worker.start()
    t0 = time.time()
    while not signals["finished"] and time.time() - t0 < 3.0:
        app.processEvents()
        time.sleep(0.01)
        
    assert signals["started"] is True
    assert signals["progress"] is True
    assert signals["finished"] is True

def test_memory_worker_signals():
    mock_brain = MagicMock()
    worker = MemoryWorker("save_statement", mock_brain, text="test")
    
    signals = {"started": False, "progress": False, "finished": False}
    worker.started.connect(lambda: signals.update({"started": True}))
    worker.progress.connect(lambda val, msg: signals.update({"progress": True}))
    worker.finished.connect(lambda res: signals.update({"finished": True}))
    
    worker.start()
    t0 = time.time()
    while not signals["finished"] and time.time() - t0 < 3.0:
        app.processEvents()
        time.sleep(0.01)
        
    assert signals["started"] is True
    assert signals["progress"] is True
    assert signals["finished"] is True
