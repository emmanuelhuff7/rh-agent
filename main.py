from auth import login, logout
from agent import run_agent

def main():
    login()
    print("\nRobinhood Agent ready. Type 'quit' to exit.\n")
    history = []
    try:
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                break
            reply, history = run_agent(user_input, history)
            print(f"\nAgent: {reply}\n")
    finally:
        logout()

if __name__ == "__main__":
    main()
