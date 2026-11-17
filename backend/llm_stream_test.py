import ollama
import time

MODEL_NAME = "qwen3.5:4b"

messages = [
    {
        "role": "system",
        "content": """
        You are AIRA, a personal AI assistant.
        Be natural, friendly, intelligent and conversational.
        Give clear and helpful responses.
        """
    }
]

print("AIRA Streaming Mode Activated!")

while True:

    question = input("\nYou: ")

    if question.lower() in ["exit", "quit", "stop"]:
        print("AIRA: Goodbye!")
        break

    messages.append({
        "role": "user",
        "content": question
    })

    print("\nAIRA: ", end="", flush=True)

    start_time = time.perf_counter()
    first_chunk_time = None
    full_response = ""

    stream = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        stream=True
    )

    for chunk in stream:

        content = chunk["message"]["content"]

        if content:
            if first_chunk_time is None:
                first_chunk_time = time.perf_counter()

            print(content, end="", flush=True)
            full_response += content

    end_time = time.perf_counter()

    print("\n")

    print("Time to first chunk:",
          round(first_chunk_time - start_time, 2), "seconds")

    print("Total response time:",
          round(end_time - start_time, 2), "seconds")

    messages.append({
        "role": "assistant",
        "content": full_response
    })