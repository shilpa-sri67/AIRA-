from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()

# Connect to Gemini
client = genai.Client()

print("Connecting to Gemini...")

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Reply with exactly: AIRA connection successful."
)

print("\nGemini response:")
print(response.text)