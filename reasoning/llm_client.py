# reasoning/llm_client.py
import os
import time
from typing import List, Dict, Any, Union

# provider is chosen via environment variable
PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


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
    # Always return a safe dummy
    return {
        "content": "FINAL_JSON: {\"commands\":[]}",
        "raw": {"mock": True, "messages": messages}
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
