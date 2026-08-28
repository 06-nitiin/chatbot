import re
from difflib import get_close_matches

import llm_fallback
import long_responses as long

INTENTS = [
    {
        "response": "Hello!",
        "words": ["hello", "hi", "hey", "sup", "heyo"],
        "single_response": True,
        "intent_id": "greeting",
    },
    {
        "response": "See you!",
        "words": ["bye", "goodbye", "see", "you", "later"],
        "single_response": True,
        "intent_id": "goodbye",
    },
    {
        "response": "I'm doing fine, and you?",
        "words": ["how", "are", "you", "doing"],
        "required_words": ["how"],
        "intent_id": "how_are_you",
    },
    {
        "response": "You're welcome!",
        "words": ["thank", "thanks", "appreciate"],
        "single_response": True,
        "intent_id": "thanks",
    },
    {
        "response": "Thank you!",
        "words": ["i", "love", "code", "palace"],
        "required_words": ["code", "palace", "love"],
        "intent_id": "love",
    },
    {
        "response": long.R_ADVICE,
        "words": ["give", "advice", "suggestion", "tip"],
        "required_words": ["advice"],
        "intent_id": "advice",
    },
    {
        "response": long.R_EATING,
        "words": ["what", "you", "eat", "food", "drink"],
        "required_words": ["you", "eat"],
        "intent_id": "eating",
    },
    {
        "response": long.R_NAME,
        "words": ["what", "your", "name", "who", "are", "you"],
        "required_words": ["name"],
        "intent_id": "name",
    },
    {
        "response": long.R_HELP,
        "words": ["help", "what", "can", "you", "do"],
        "required_words": ["help"],
        "intent_id": "help",
    },
    # Context-aware follow-up intents
    {
        "response": long.R_ADVICE_FOLLOWUP,
        "words": ["another", "more", "again", "next", "one"],
        "required_words": [],
        "intent_id": "advice_followup",
        "context_required": ["advice", "advice_followup"],
    },
    {
        "response": "Sure! Here's more: try to break big tasks into smaller chunks so they feel less overwhelming.",
        "words": ["tell", "me", "more", "explain", "elaborate", "details"],
        "required_words": [],
        "intent_id": "tell_me_more",
        "context_required": ["advice", "help", "how_are_you", "eating", "name", "advice_followup"],
    },
    {
        "response": "No problem! Let me know if you need anything else.",
        "words": ["no", "nope", "nah", "nothing"],
        "single_response": True,
        "intent_id": "no",
    },
    {
        "response": "Great! What would you like to talk about?",
        "words": ["yes", "yeah", "sure", "yep", "ok", "okay"],
        "single_response": True,
        "intent_id": "yes",
    },
]

ALL_KNOWN_WORDS = sorted({word for intent in INTENTS for word in intent["words"]})

CONFIDENCE_THRESHOLD = 20
CONTEXT_BOOST = 25


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


def get_last_intent(history):
    if not history:
        return None
    for turn in reversed(history):
        if turn.get("role") == "bot" and turn.get("intent"):
            return turn["intent"]
    return None


def best_rule_match(user_input, history=None):
    tokens = correct_typos(tokenize(user_input))
    last_intent = get_last_intent(history)

    scores = {}
    intent_map = {}
    for intent in INTENTS:
        score = message_probability(
            tokens,
            intent["words"],
            single_response=intent.get("single_response", False),
            required_words=intent.get("required_words", []),
        )

        context_required = intent.get("context_required", [])
        if context_required and last_intent in context_required:
            score += CONTEXT_BOOST

        scores[intent["response"]] = score
        intent_map[intent["response"]] = intent["intent_id"]

    best_match = max(scores, key=scores.get)
    confidence = scores[best_match]
    intent_id = intent_map[best_match]

    if confidence < CONFIDENCE_THRESHOLD:
        return None, confidence, None
    return best_match, confidence, intent_id


def get_response_with_confidence(user_input, history=None, allow_llm_fallback=True):
    response, confidence, intent_id = best_rule_match(user_input, history)

    if intent_id:
        return response, confidence, True, "rules", intent_id

    if allow_llm_fallback and llm_fallback.is_configured():
        try:
            llm_response = llm_fallback.ask_llm(user_input, history=history)
            return llm_response, confidence, True, "llm", "llm_fallback"
        except llm_fallback.LLMUnavailable:
            pass

    return long.unknown(), confidence, False, "fallback", "unknown"


def get_response(user_input, history=None):
    response, _confidence, _matched, _source, _intent = get_response_with_confidence(
        user_input, history=history
    )
    return response