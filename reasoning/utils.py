# reasoning/utils.py
import json
import jsonschema
from typing import Dict, Any
from .llm_client import call_llm

# ----------------------
# JSON Action Schema
# ----------------------
ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "commands": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "type": {"type": "string", "enum": ["move", "act"]},
                    "to": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "action_name": {"type": "string"},
                },
                "required": ["agent_id", "type"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["commands"],
    "additionalProperties": False,
}


def validate_action_json(s: str) -> Dict[str, Any]:
    """
    Extract and validate FINAL_JSON from a string.

    Args:
        s: LLM output (may contain extra text or prefix before JSON).

    Returns:
        Parsed JSON (dict) if valid.

    Raises:
        ValueError if malformed or schema mismatch.
    """
    try:
        # Heuristic: find first { and last }
        start = s.find("{")
        end = s.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("no JSON object found in string")
        json_text = s[start:end]
        data = json.loads(json_text)
    except Exception as e:
        raise ValueError(f"malformed json: {e}")

    try:
        jsonschema.validate(instance=data, schema=ACTION_SCHEMA)
    except Exception as e:
        raise ValueError(f"schema validation error: {e}")

    return data


def get_validated_actions(messages, model=None, temperature=0.2, logger=None) -> Dict[str, Any]:
    """
    Call LLM and enforce JSON validity. Retry once with stricter instructions.

    Returns:
        dict matching ACTION_SCHEMA
    """
    # ---- First Attempt ----
    resp = call_llm(messages, model=model, temperature=temperature)
    text = resp["content"]

    try:
        return validate_action_json(text)
    except ValueError as e1:
        if logger:
            logger.warning(f"Invalid JSON attempt 1: {e1}")
        # ---- Re-prompt ----
        retry_messages = messages + [
            {
                "role": "system",
                "content": (
                    "Your previous output was invalid JSON / schema mismatch. "
                    "Produce ONLY the final JSON matching schema and nothing else."
                ),
            }
        ]
        resp2 = call_llm(retry_messages, model=model, temperature=temperature)
        text2 = resp2["content"]

        try:
            return validate_action_json(text2)
        except ValueError as e2:
            if logger:
                logger.error(f"Invalid JSON attempt 2: {e2} — defaulting to empty commands.")
            return {"commands": []}


def get_validated_actions_with_logging(messages, model=None, temperature=0.2, logger=None):
    """
    Call LLM and enforce JSON validity. Retry once with stricter instructions.
    Returns both actions and response text for logging.

    Returns:
        tuple: (actions_dict, response_text)
    """
    # ---- First Attempt ----
    resp = call_llm(messages, model=model, temperature=temperature)
    text = resp["content"]

    try:
        actions = validate_action_json(text)
        return actions, text
    except ValueError as e1:
        if logger:
            logger.warning(f"Invalid JSON attempt 1: {e1}")
        # ---- Re-prompt ----
        retry_messages = messages + [
            {
                "role": "system",
                "content": (
                    "Your previous output was invalid JSON / schema mismatch. "
                    "Produce ONLY the final JSON matching schema and nothing else."
                ),
            }
        ]
        resp2 = call_llm(retry_messages, model=model, temperature=temperature)
        text2 = resp2["content"]

        try:
            actions = validate_action_json(text2)
            return actions, text2
        except ValueError as e2:
            if logger:
                logger.error(f"Invalid JSON attempt 2: {e2} — defaulting to empty commands.")
            return {"commands": []}, text2
