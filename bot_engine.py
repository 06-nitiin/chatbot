import re
from difflib import get_close_matches

import llm_fallback
import long_responses as long

INTENTS = [
    {
        "id": "greeting",
        "response": "Hello!",
        "words": ["hello", "hi", "hey", "sup", "heyo"],
        "single_response": True,
    },
    {
        "id": "farewell",
        "response": "See you!",
        "words": ["bye", "goodbye"],
        "single_response": True,
    },
    {
        "id": "how_are_you",
        "response": "I'm doing fine, and you?",
        "words": ["how", "are", "you", "doing"],
        "required_words": ["how"],
    },
    {
        "id": "thanks_reply",
        "response": "You're welcome!",
        "words": ["thank", "thanks"],
        "single_response": True,
    },
    {
        "id": "code_palace_love",
        "response": "Thank you!",
        "words": ["i", "love", "code", "palace"],
        "required_words": ["code", "palace", "love"],
    },
    {
        "id": "advice",
        "response": long.R_ADVICE,
        "words": ["give", "advice"],
        "required_words": ["advice"],
    },
    {
        "id": "eating",
        "response": long.R_EATING,
        "words": ["what", "you", "eat"],
        "required_words": ["you", "eat"],
    },
    {
        "id": "name",
        "response": long.R_NAME,
        "words": ["what", "your", "name"],
        "required_words": ["name"],
    },
    {
        "id": "help",
        "response": long.R_HELP,
        "words": ["help", "what", "can", "you", "do"],
        "required_words": ["help"],
    },
]

ALL_KNOWN_WORDS = sorted({word for intent in INTENTS for word in intent["words"]})

CONFIDENCE_THRESHOLD = 20


def correct_typos(tokens, cutoff=0.8):
    corrected = []
    for token in tokens:
        if token in ALL_KNOWN_WORDS:
            corrected.append(token)
            continue
        close = get_close_matches(token, ALL_KNOWN_WORDS, n=1, cutoff=cutoff)
        corrected.append(close[0] if close else token)
    return corrected


def message_probability(user_tokens, recognised_words, single_response=False, required_words=None):
    required_words = required_words or []
    user_token_set = set(user_tokens)

    matches = len(user_token_set.intersection(recognised_words))
    recall = matches / len(recognised_words) if recognised_words else 0
    precision = matches / len(user_token_set) if user_token_set else 0

    has_required_words = all(word in user_token_set for word in required_words)

    if not (has_required_words or single_response):
        return 0

    score = recall if single_response else recall * precision
    return int(score * 100)


def tokenize(user_input):
    tokens = re.split(r"\s+|[,;?!.-]\s*", user_input.lower().strip())
    return [t for t in tokens if t]


def best_rule_match(user_input):
    """Returns (response, confidence, matched, intent_id). intent_id is None if nothing matched."""
    tokens = correct_typos(tokenize(user_input))

    scores = {}
    for intent in INTENTS:
        scores[intent["id"]] = message_probability(
            tokens,
            intent["words"],
            single_response=intent.get("single_response", False),
            required_words=intent.get("required_words", []),
        )

    best_id = max(scores, key=scores.get)
    confidence = scores[best_id]

    if confidence < CONFIDENCE_THRESHOLD:
        return None, confidence, False, None

    best_intent = next(i for i in INTENTS if i["id"] == best_id)
    return best_intent["response"], confidence, True, best_id


def get_response_with_confidence(user_input, history=None, allow_llm_fallback=True):
    response, confidence, matched, intent_id = best_rule_match(user_input)

    if matched:
        return response, confidence, True, "rules", intent_id

    if allow_llm_fallback and llm_fallback.is_configured():
        try:
            llm_response = llm_fallback.ask_llm(user_input, history=history)
            return llm_response, confidence, True, "llm", None
        except llm_fallback.LLMUnavailable:
            pass  # fall through to the canned "I don't understand" reply

    return long.unknown(), confidence, False, "fallback", None


def get_response(user_input):
    response, _confidence, _matched, _source, _intent_id = get_response_with_confidence(user_input)
    return response