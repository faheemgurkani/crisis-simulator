# reasoning/cot.py
import json

SYSTEM_PROMPT = """
You are a Chain-of-Thought planner.
Think step by step (prefix each with "Thought:") about which actions agents should take.
End with FINAL_JSON matching schema.
"""

def build_messages(context_json, scratchpad=None):
    user_msg = "CONTEXT_JSON:\n" + json.dumps(context_json)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]


def cot_plan(context_json, scratchpad=None):
    """
    Chain-of-Thought planning strategy: Step-by-step reasoning.
    
    Args:
        context_json: Current world state from sensors
        scratchpad: Optional running memory/log
    
    Returns:
        List of messages for LLM call
    """
    return build_messages(context_json, scratchpad)
