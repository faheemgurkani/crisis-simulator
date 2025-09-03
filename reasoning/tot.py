# reasoning/tot.py
import json

SYSTEM_PROMPT = """
You are a Tree-of-Thought (ToT) disaster planner.
Explore multiple reasoning branches (prefix with "Thought A:", "Thought B:", etc).
Then select the best branch and output FINAL_JSON strictly following schema.
"""

def build_messages(context_json, scratchpad=None):
    user_msg = "CONTEXT_JSON:\n" + json.dumps(context_json)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg + "\n\nExplore branches, then decide."},
    ]
