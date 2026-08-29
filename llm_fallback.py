import json
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
    "Keep replies short (1-3 sentences), casual, and helpful."
)

ROLE_MAP = {"user": "user", "bot": "model"}


class LLMUnavailable(Exception):
    """Raised when the LLM fallback can't be used (no key, network error, etc.)."""


def is_configured():
    return bool(GEMINI_API_KEY)


def build_contents(user_message, history=None):
    contents = []
    for turn in history or []:
        role = ROLE_MAP.get(turn.get("role"))
        text = turn.get("message")
        if role and text:
            contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})
    return contents


def ask_llm(user_message, history=None, timeout=10):
    """
    Sends the message (plus recent conversation history, if given) to
    Gemini's free API tier and returns the text reply. Raises
    LLMUnavailable if the key is missing or the request fails, so callers
    can gracefully fall back to the bot's own 'unknown' response.
    """
    if not GEMINI_API_KEY:
        raise LLMUnavailable("GEMINI_API_KEY is not set")

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": build_contents(user_message, history),
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

def ask_llm_stream(user_message, history=None, timeout=30):
    if not GEMINI_API_KEY:
        raise LLMUnavailable("GEMINI_API_KEY is not set")

    stream_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent"
    )
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": build_contents(user_message, history),
        "generationConfig": {"maxOutputTokens": 200, "temperature": 0.7},
    }

    with requests.post(
        stream_url,
        params={"key": GEMINI_API_KEY, "alt": "sse"},
        json=payload,
        stream=True,
        timeout=timeout,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data_str = line[len("data: "):].strip()
            if not data_str or data_str == "[DONE]":
                continue
            try:
                chunk = json.loads(data_str)
                text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                if text:
                    yield text
            except (KeyError, IndexError, json.JSONDecodeError):
                continue 