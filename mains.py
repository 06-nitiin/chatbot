from dotenv import load_dotenv

load_dotenv()



from bot_engine import get_response
 
EXIT_COMMANDS = {"quit", "exit", "bye", "goodbye"}
 
 
def main():
    print("Bot: Hi! Type 'quit' or 'exit' to leave.")
    while True:
        user_input = input("You: ").strip()
 
        if not user_input:
            continue
 
        if user_input.lower() in EXIT_COMMANDS:
            print("Bot: See you!")
            break
 
        print("Bot: " + get_response(user_input))
 
 
if __name__ == "__main__":
    main()
 