# reasoning/reflexion.py
import json

SYSTEM_PROMPT = """
You are a Reflexion-based disaster planner.
Use context and optional SCRATCHPAD (past errors, rules).
Always output FINAL_JSON matching schema.
If SCRATCHPAD mentions invalid JSON, fix that issue.
"""

def build_messages(context_json, scratchpad=None):
    user_msg = "CONTEXT_JSON:\n" + json.dumps(context_json)
    if scratchpad:
        user_msg += "\n\nSCRATCHPAD:\n" + json.dumps(scratchpad)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
