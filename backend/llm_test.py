from llm import get_response

print("AIRA is ready!")

while True:
    question = input("\nYou: ")

    if question.lower() in ["exit", "quit", "stop"]:
        print("AIRA: Goodbye!")
        break

    print("\nAIRA is thinking...")

    answer = get_response(question)

    print("\nAIRA:", answer)