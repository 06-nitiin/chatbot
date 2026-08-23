import re
from difflib import get_close_matches

import long_responses as long


INTENTS = [
    {
        "response": "Hello!",
        "words": ["hello", "hi", "hey", "sup", "heyo"],
        "single_response": True,
    },
    {
        "response": "See you!",
        "words": ["bye", "goodbye"],
        "single_response": True,
    },
    {
        "response": "I'm doing fine, and you?",
        "words": ["how", "are", "you", "doing"],
        "required_words": ["how"],
    },
    {
        "response": "You're welcome!",
        "words": ["thank", "thanks"],
        "single_response": True,
    },
    {
        "response": "Thank you!",
        "words": ["i", "love", "code", "palace"],
        "required_words": ["code", "palace", "love"],
    },
    {
        "response": long.R_ADVICE,
        "words": ["give", "advice"],
        "required_words": ["advice"],
    },
    {
        "response": long.R_EATING,
        "words": ["what", "you", "eat"],
        "required_words": ["you", "eat"],
    },
    {
        "response": long.R_NAME,
        "words": ["what", "your", "name"],
        "required_words": ["name"],
    },
    {
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
    percentage = matches / len(recognised_words) if recognised_words else 0

    has_required_words = all(word in user_token_set for word in required_words)

    if has_required_words or single_response:
        return int(percentage * 100)
    return 0



def tokenize(user_input):
    tokens = re.split(r"\s+|[,;?!.-]\s*", user_input.lower().strip())
    return [t for t in tokens if t]  # Remove empty tokens


def get_response_with_confidence(user_input):
    tokens = correct_typos(tokenize(user_input))

    scores = {}
    for intent in INTENTS:
        scores[intent["response"]] = message_probability(
            tokens,
            intent["words"],
            single_response=intent.get("single_response", False),
            required_words=intent.get("required_words", []),
        )

    best_match = max(scores, key=scores.get)
    confidence = scores[best_match]

    if confidence < CONFIDENCE_THRESHOLD:
        return long.unknown(), confidence, False
    return best_match, confidence, True



def get_responses(user_input):
    response, _confidence, _matched = get_response_with_confidence(user_input)
    return response