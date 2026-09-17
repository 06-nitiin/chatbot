import random

R_EATING = "I don't eat, I'm a bot, silly!"

R_ADVICE = "Look both ways before crossing the street!"

R_ADVICE_FOLLOWUP = "Here's another one: always save your work before closing an application. You never know when something might crash!"

R_NAME = "I'm a chatbot, I don't have a name :("

R_CAPABILITIES = (
    "I can greet you, answer simple questions, give advice, remember recent "
    "conversation context, accept voice input, and use AI for questions I don't "
    "recognize."
)

R_CREATOR = "I was created by Nitin as a hybrid rule-based and AI chatbot project."

R_JOKE = "Why did the developer go broke? Because they used up all their cache!"

R_QUOTE = "Small progress is still progress. Keep building, one improvement at a time."

R_HELP = (
    "Here's what I can do:\n"
    " - Say hi / bye\n"
    " - Give you advice (try 'give me advice', then 'another one')\n"
    " - Tell you if I eat\n"
    " - Tell you my name and capabilities\n"
    " - Tell you who created me\n"
    " - Tell you a joke or quote\n"
    " - Chat with context memory\n"
    " - Accept voice input in supported browsers\n"
    " - Anything else gets passed to a local AI model, if one is configured\n"
    "Type 'quit' or 'exit' anytime to leave (CLI mode)."
)

UNKNOWN_RESPONSES = [
    "Could you please re-phrase that? (I'm a simple bot)",
    "I said... could you please re-phrase that?",
    "I am not sure I understand that fully.",
    "Sorry, I'm not sure I understand.",
]


def unknown():
    return random.choice(UNKNOWN_RESPONSES)


# ---------
# This is just so that bot_engine.py stays readable.
# ---------
