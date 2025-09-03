# reasoning/plan_execute.py
import json

SYSTEM_PROMPT = """
You are a disaster response planner using Plan-and-Execute.
First, write a PLAN: a short ordered list of intended steps in natural language.
Then, immediately produce FINAL_JSON: <Action JSON> that enacts the first step(s).
Schema reminder:
{ "commands":[ {"agent_id":"<id>", "type":"move"|"act",
  "to":[x,y] (if move),
  "action_name":"pickup_survivor"|"drop_at_hospital"|"extinguish_fire"|"clear_rubble"|"recharge"|"resupply"} ] }
No extra text after FINAL_JSON line.
"""

def build_messages(context_json, scratchpad=None):
    user_msg = "CONTEXT_JSON:\n" + json.dumps(context_json)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg + "\n\nOutput PLAN then FINAL_JSON."},
    ]
