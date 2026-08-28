import os

import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)

SYSTEM_PROMPT = (
    "You are a small, friendly chatbot bolted onto a rule-based keyword bot. "
    "The rule-based bot handles simple stuff (greetings, small talk) on its own "
    "and only hands you messages it couldn't confidently match. "
    "Keep replies short (1-3 sentences), casual and helpful."
)


class LLMUnavailable(Exception):
    """Raised when the LLM fallback can't be used (no key, network error, etc)."""


def is_configured():
    return bool(GEMINI_API_KEY)


def _build_contents(user_message, history=None):
    """Build Gemini contents list from history + current message."""
    contents = []

    if history:
        for turn in history[-6:]:  # last 6 turns to stay within token limits
            role = turn.get("role")
            msg = turn.get("message", "")
            if role == "user":
                contents.append({"role": "user", "parts": [{"text": msg}]})
            elif role == "bot":
                contents.append({"role": "model", "parts": [{"text": msg}]})

    contents.append({"role": "user", "parts": [{"text": user_message}]})
    return contents


def ask_llm(user_message, history=None, timeout=10):
    if not GEMINI_API_KEY:
        raise LLMUnavailable("No Gemini API key configured")

    contents = _build_contents(user_message, history=history)

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 200, "temperature": 0.7},
    }

    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (requests.RequestException, KeyError, IndexError) as exc:
        raise LLMUnavailable(str(exc)) from exc