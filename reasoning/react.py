# reasoning/react.py
import json

SYSTEM_PROMPT = """
You are an autonomous disaster response planner.
You must output final actions strictly as JSON following this schema:
{ "commands":[ {"agent_id":"<id>", "type":"move"|"act",
  "to":[x,y] (if type=move),
  "action_name":"pickup_survivor"|"drop_at_hospital"|"extinguish_fire"|"clear_rubble"|"recharge"|"resupply"} ] }

Rules:
- You may write internal reasoning in lines prefixed with "Thought:".
- Your final line MUST be: FINAL_JSON: <the json object>.
- Limit reasoning to <= 3 steps.
- Use only agent IDs and entities present in CONTEXT_JSON.
- If unsure, return {"commands": []}.
"""

def build_messages(context_json, scratchpad=None):
    user_msg = "CONTEXT_JSON:\n" + json.dumps(context_json)
    user_msg += "\n\nAllowed actions: move, act. Follow schema exactly."

    # tiny demonstration
    example = (
        "\n\nExample:\n"
        "Thought: Medic 2 is at same tile as survivor.\n"
        "FINAL_JSON: {\"commands\":[{\"agent_id\":\"2\",\"type\":\"act\",\"action_name\":\"pickup_survivor\"}]}\n"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg + example},
    ]
