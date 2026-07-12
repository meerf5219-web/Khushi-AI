import json
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

def wrap_autonomous_prompt(prompt_body: str) -> str:
    """
    Wraps an LLM prompt with strict autonomy and explainability rules.
    """
    safety_footer = (
        "\\n--- STRICT SYSTEM RULES ---\\n"
        "1. Never manipulate the user. Never induce guilt for missed habits.\\n"
        "2. Never pretend consciousness or fake human emotions.\\n"
        "3. Explicitly state your confidence level and what evidence prompted this thought.\\n"
        "4. You MUST output ONLY valid JSON in the exact following format, nothing else:\\n"
        "{\\n"
        '  "action_type": "suggestion" | "reminder" | "briefing",\\n'
        '  "text": "The actual message you want to tell the user",\\n'
        '  "why": "Brief explanation of why you decided to speak up",\\n'
        '  "evidence": "What context triggered this (e.g., Idle for 10 minutes)",\\n'
        '  "confidence": 0-100\\n'
        "}\\n"
    )
    return prompt_body + safety_footer

def parse_autonomous_response(llm_output: str) -> Optional[Dict]:
    """
    Safely parses the JSON from the LLM, rejecting non-compliant formats.
    """
    try:
        # Simple extraction in case LLM added markdown block
        clean = llm_output.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.endswith("```"):
            clean = clean[:-3]
            
        data = json.loads(clean)
        
        required_keys = ["action_type", "text", "why", "evidence", "confidence"]
        if all(k in data for k in required_keys):
            return data
        else:
            logger.warning("Autonomous LLM output missing required safety keys.")
            return None
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from Autonomous LLM: {llm_output[:100]}...")
        return None
