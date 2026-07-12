import pytest
from companion.autonomy.safety import parse_autonomous_response, wrap_autonomous_prompt
from companion.autonomy.config import AutonomyLevel

def test_explainability_json_parser():
    """Verify that the safety wrapper successfully parses LLM JSON outputs."""
    valid_output = '''
    ```json
    {
      "action_type": "suggestion",
      "text": "It's been 5 hours, time to stand up!",
      "why": "User posture health",
      "evidence": "Idle timer is 0 but continuous work time is 300 minutes",
      "confidence": 95
    }
    ```
    '''
    
    data = parse_autonomous_response(valid_output)
    assert data is not None
    assert data["action_type"] == "suggestion"
    assert data["confidence"] == 95

def test_explainability_rejection():
    """Verify that malformed or incomplete outputs are safely rejected."""
    invalid_output = '''
    {
      "action_type": "suggestion",
      "text": "Stand up!"
      // Missing why, evidence, confidence
    }
    '''
    
    data = parse_autonomous_response(invalid_output)
    assert data is None

def test_safety_wrapper_appends_rules():
    """Verify that the strict system prompt is always appended."""
    prompt = "Suggest a break."
    wrapped = wrap_autonomous_prompt(prompt)
    
    assert "--- STRICT SYSTEM RULES ---" in wrapped
    assert "Never manipulate" in wrapped
    assert "valid JSON" in wrapped
