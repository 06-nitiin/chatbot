import random

R_EATING = "I don't eat, I'm a bot, silly!"

R_ADVICE = "Look both ways before crossing the street!"

R_ADVICE_FOLLOWUP = "Here's another one: always save your work before closing an application. You never know when something might crash!"

R_NAME = "I'm a chatbot, I don't have a name :("

R_HELP = (
    "Here's what I can do:\n"
    " - Say hi / bye\n"
    " - Give you advice (try 'give me advice', then 'another one')\n"
    " - Tell you if I eat\n"
    " - Chat with context memory\n"
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
# This is just so that bot_engine.py stays redable.
# ---------