import random 

R_EATING = "I don't eat, I'm a bot, silly!"

R_ADVICE = "Look both ways before crossing the street!"

R_NAME = "I'm a chatbot, I don't have a name :("

R_HELP = (
    "Here's what I can do:\n"
    " - Say hi / bye\n"
    " - Give advice\n"
    " - Tell you if I eat\n"
    " - Chat a little\n"
    "Type 'quit' or 'exit' anytime to leave"
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