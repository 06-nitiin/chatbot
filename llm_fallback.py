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
    """Raised when the LLM fallback can't be used."""


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


def request_payload(user_message, history=None):
    return {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": build_contents(user_message, history),
        "generationConfig": {"maxOutputTokens": 200, "temperature": 0.7},
    }


def ask_llm(user_message, history=None, timeout=10):
    """
    Sends the message and recent conversation history to Gemini.
    Raises LLMUnavailable when the key, network request, or response is unusable.
    """
    if not GEMINI_API_KEY:
        raise LLMUnavailable("GEMINI_API_KEY is not set")

    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=request_payload(user_message, history),
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if not text:
            raise LLMUnavailable("Gemini returned an empty response")
        return text
    except LLMUnavailable:
        raise
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise LLMUnavailable(str(exc)) from exc


def ask_llm_stream(user_message, history=None, timeout=30):
    """Yield Gemini response chunks, converting failures to LLMUnavailable."""
    if not GEMINI_API_KEY:
        raise LLMUnavailable("GEMINI_API_KEY is not set")

    stream_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent"
    )

    try:
        with requests.post(
            stream_url,
            params={"key": GEMINI_API_KEY, "alt": "sse"},
            json=request_payload(user_message, history),
            stream=True,
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            yielded_text = False

            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue

                data_str = line[len("data: "):].strip()
                if not data_str or data_str == "[DONE]":
                    continue

                try:
                    chunk = json.loads(data_str)
                    text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                    continue

                if text:
                    yielded_text = True
                    yield text

            if not yielded_text:
                raise LLMUnavailable("Gemini returned an empty streaming response")
    except LLMUnavailable:
        raise
    except (requests.RequestException, TypeError, ValueError) as exc:
        raise LLMUnavailable(str(exc)) from exc
