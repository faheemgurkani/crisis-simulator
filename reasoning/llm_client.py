# reasoning/llm_client.py
import os
import time
from typing import List, Dict, Any, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# provider is chosen via environment variable
PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Debug info (uncomment for debugging)
# print(f"LLM Provider: {PROVIDER}")
# print(f"Groq API Key loaded: {'Yes' if GROQ_API_KEY else 'No'}")
# if GROQ_API_KEY:
#     print(f"Groq API Key (first 10 chars): {GROQ_API_KEY[:10]}...")


class LLMError(Exception):
    pass


def _call_groq(messages: List[Dict[str, str]], model: str, temperature: float):
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=model or "llama-3.3-70b-versatile",
            messages=messages,
            temperature=temperature,
        )
        return {
            "content": resp.choices[0].message.content,
            "raw": resp
        }
    except Exception as e:
        raise LLMError(f"Groq call failed: {e}")


def _call_gemini(messages: List[Dict[str, str]], model: str, temperature: float):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        mdl = genai.GenerativeModel(model or "gemini-1.5-flash")
        # flatten messages into a single string (Gemini doesn’t support roles the same way)
        prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
        resp = mdl.generate_content(prompt, generation_config={"temperature": temperature})
        return {
            "content": resp.text,
            "raw": resp
        }
    except Exception as e:
        raise LLMError(f"Gemini call failed: {e}")


def _call_mock(messages: List[Dict[str, str]], *_args, **_kwargs):
    """
    Context-aware mock LLM that analyzes the game state and provides intelligent responses.
    """
    import json
    import random
    
    # Extract context from user message
    context_json = None
    for msg in messages:
        if msg["role"] == "user" and "CONTEXT_JSON:" in msg["content"]:
            try:
                # Find the JSON part after CONTEXT_JSON:
                json_start = msg["content"].find("CONTEXT_JSON:") + len("CONTEXT_JSON:")
                # Look for various end patterns
                json_end = msg["content"].find("\n\nAllowed actions:")
                if json_end == -1:
                    json_end = msg["content"].find("\n\nOutput PLAN")
                if json_end == -1:
                    json_end = msg["content"].find("\n\nExample:")
                if json_end == -1:
                    json_end = len(msg["content"])
                json_str = msg["content"][json_start:json_end].strip()
                context_json = json.loads(json_str)
                break
            except (json.JSONDecodeError, ValueError):
                pass
    
    if not context_json:
        # Fallback to simple response
        return {
            "content": "Thought: I need to analyze the situation and take appropriate action.\nFINAL_JSON: {\"commands\":[]}",
            "raw": {"mock": True, "messages": messages}
        }
    
    # Analyze the game state
    agents = context_json.get("agents", [])
    survivors = context_json.get("survivors", [])
    fires = context_json.get("fires", [])
    rubble = context_json.get("rubble", [])
    hospitals = context_json.get("hospitals", [])
    
    commands = []
    
    # Strategy: Prioritize rescue operations
    for agent in agents:
        agent_id = agent["id"]
        agent_pos = agent["pos"]
        agent_kind = agent["kind"]
        carrying = agent.get("carrying", False)
        
        if agent_kind == "medic":
            if carrying:
                # Check if already at a hospital
                at_hospital = False
                for hospital in hospitals:
                    if agent_pos == hospital["pos"]:
                        at_hospital = True
                        break
                
                if at_hospital:
                    # Drop the survivor at the hospital
                    commands.append({
                        "agent_id": agent_id,
                        "type": "act",
                        "action_name": "drop_at_hospital"
                    })
                else:
                    # Find nearest hospital
                    nearest_hospital = None
                    min_dist = float('inf')
                    for hospital in hospitals:
                        dist = abs(hospital["pos"][0] - agent_pos[0]) + abs(hospital["pos"][1] - agent_pos[1])
                        if dist < min_dist:
                            min_dist = dist
                            nearest_hospital = hospital
                    
                    if nearest_hospital:
                        commands.append({
                            "agent_id": agent_id,
                            "type": "move",
                            "to": nearest_hospital["pos"]
                        })
            else:
                # Find nearest survivor
                nearest_survivor = None
                min_dist = float('inf')
                for survivor in survivors:
                    dist = abs(survivor["pos"][0] - agent_pos[0]) + abs(survivor["pos"][1] - agent_pos[1])
                    if dist < min_dist:
                        min_dist = dist
                        nearest_survivor = survivor
                
                if nearest_survivor:
                    # Move towards survivor
                    target_pos = nearest_survivor["pos"]
                    # Simple pathfinding: move one step towards target
                    dx = target_pos[0] - agent_pos[0]
                    dy = target_pos[1] - agent_pos[1]
                    
                    if dx == 0 and dy == 0:
                        # Already at survivor location, pick up
                        commands.append({
                            "agent_id": agent_id,
                            "type": "act",
                            "action_name": "pickup_survivor"
                        })
                    else:
                        # Move one step towards target
                        if abs(dx) > abs(dy):
                            new_x = agent_pos[0] + (1 if dx > 0 else -1)
                            new_y = agent_pos[1]
                        else:
                            new_x = agent_pos[0]
                            new_y = agent_pos[1] + (1 if dy > 0 else -1)
                        
                        commands.append({
                            "agent_id": agent_id,
                            "type": "move",
                            "to": [new_x, new_y]
                        })
        
        elif agent_kind == "truck":
            # Handle fires and rubble
            if fires:
                # Find nearest fire
                nearest_fire = None
                min_dist = float('inf')
                for fire in fires:
                    dist = abs(fire[0] - agent_pos[0]) + abs(fire[1] - agent_pos[1])
                    if dist < min_dist:
                        min_dist = dist
                        nearest_fire = fire
                
                if nearest_fire:
                    if min_dist == 0:
                        # At fire location, extinguish
                        commands.append({
                            "agent_id": agent_id,
                            "type": "act",
                            "action_name": "extinguish_fire"
                        })
                    else:
                        # Move towards fire
                        target_pos = nearest_fire
                        dx = target_pos[0] - agent_pos[0]
                        dy = target_pos[1] - agent_pos[1]
                        
                        if abs(dx) > abs(dy):
                            new_x = agent_pos[0] + (1 if dx > 0 else -1)
                            new_y = agent_pos[1]
                        else:
                            new_x = agent_pos[0]
                            new_y = agent_pos[1] + (1 if dy > 0 else -1)
                        
                        commands.append({
                            "agent_id": agent_id,
                            "type": "move",
                            "to": [new_x, new_y]
                        })
            
            elif rubble:
                # Find nearest rubble
                nearest_rubble = None
                min_dist = float('inf')
                for rub in rubble:
                    dist = abs(rub[0] - agent_pos[0]) + abs(rub[1] - agent_pos[1])
                    if dist < min_dist:
                        min_dist = dist
                        nearest_rubble = rub
                
                if nearest_rubble:
                    if min_dist == 0:
                        # At rubble location, clear
                        commands.append({
                            "agent_id": agent_id,
                            "type": "act",
                            "action_name": "clear_rubble"
                        })
                    else:
                        # Move towards rubble
                        target_pos = nearest_rubble
                        dx = target_pos[0] - agent_pos[0]
                        dy = target_pos[1] - agent_pos[1]
                        
                        if abs(dx) > abs(dy):
                            new_x = agent_pos[0] + (1 if dx > 0 else -1)
                            new_y = agent_pos[1]
                        else:
                            new_x = agent_pos[0]
                            new_y = agent_pos[1] + (1 if dy > 0 else -1)
                        
                        commands.append({
                            "agent_id": agent_id,
                            "type": "move",
                            "to": [new_x, new_y]
                        })
        
        elif agent_kind == "drone":
            # Drones can help with reconnaissance and light tasks
            if agent.get("battery", 100) < 20:
                # Need to recharge
                depot = context_json.get("depot", [1, 1])
                if agent_pos == depot:
                    commands.append({
                        "agent_id": agent_id,
                        "type": "act",
                        "action_name": "recharge"
                    })
                else:
                    # Move towards depot
                    dx = depot[0] - agent_pos[0]
                    dy = depot[1] - agent_pos[1]
                    
                    if abs(dx) > abs(dy):
                        new_x = agent_pos[0] + (1 if dx > 0 else -1)
                        new_y = agent_pos[1]
                    else:
                        new_x = agent_pos[0]
                        new_y = agent_pos[1] + (1 if dy > 0 else -1)
                    
                    commands.append({
                        "agent_id": agent_id,
                        "type": "move",
                        "to": [new_x, new_y]
                    })
            else:
                # Help with survivor rescue
                if survivors:
                    nearest_survivor = None
                    min_dist = float('inf')
                    for survivor in survivors:
                        dist = abs(survivor["pos"][0] - agent_pos[0]) + abs(survivor["pos"][1] - agent_pos[1])
                        if dist < min_dist:
                            min_dist = dist
                            nearest_survivor = survivor
                    
                    if nearest_survivor:
                        target_pos = nearest_survivor["pos"]
                        dx = target_pos[0] - agent_pos[0]
                        dy = target_pos[1] - agent_pos[1]
                        
                        if abs(dx) > abs(dy):
                            new_x = agent_pos[0] + (1 if dx > 0 else -1)
                            new_y = agent_pos[1]
                        else:
                            new_x = agent_pos[0]
                            new_y = agent_pos[1] + (1 if dy > 0 else -1)
                        
                        commands.append({
                            "agent_id": agent_id,
                            "type": "move",
                            "to": [new_x, new_y]
                        })
    
    # Limit to 3 commands to avoid overwhelming the system
    commands = commands[:3]
    
    # Generate response based on strategy
    system_msg = messages[0]["content"] if messages else ""
    is_plan_execute = "Plan-and-Execute" in system_msg
    
    if commands:
        if is_plan_execute:
            response = f"PLAN:\n"
            response += f"1. Deploy medics to rescue survivors\n"
            response += f"2. Use trucks to extinguish fires and clear rubble\n"
            response += f"3. Coordinate with hospitals for patient delivery\n"
            response += f"\nFINAL_JSON: {json.dumps({'commands': commands})}"
        else:
            response = f"Thought: Analyzing the current situation and taking appropriate actions.\n"
            response += f"Thought: Found {len(survivors)} survivors, {len(fires)} fires, {len(rubble)} rubble piles.\n"
            response += f"Thought: Executing {len(commands)} strategic commands.\n"
            response += f"FINAL_JSON: {json.dumps({'commands': commands})}"
    else:
        if is_plan_execute:
            response = "PLAN:\n1. Assess the situation\n2. Coordinate rescue operations\n\nFINAL_JSON: {\"commands\":[]}"
        else:
            response = "Thought: No immediate actions needed at this time.\nFINAL_JSON: {\"commands\":[]}"
    
    return {
        "content": response,
        "raw": {"mock": True, "messages": messages, "context_analyzed": True}
    }


def call_llm(
    messages: List[Dict[str, str]],
    model: str = None,
    temperature: float = 0.2,
    retries: int = 2,
    backoff: float = 2.0,
) -> Dict[str, Any]:
    """
    Call an LLM provider with chat-style messages.

    Args:
        messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
        model: model name (provider-specific default if None)
        temperature: sampling temperature
        retries: number of retry attempts on failure
        backoff: exponential backoff base in seconds

    Returns:
        dict with keys:
            - content: str (assistant’s main text reply)
            - raw: provider’s raw response object
    """
    for attempt in range(retries):
        try:
            if PROVIDER == "groq":
                return _call_groq(messages, model, temperature)
            elif PROVIDER == "gemini":
                return _call_gemini(messages, model, temperature)
            else:
                return _call_mock(messages, model, temperature)
        except LLMError as e:
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
                continue
            raise
