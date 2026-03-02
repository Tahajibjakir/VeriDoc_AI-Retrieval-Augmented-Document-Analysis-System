import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

print(f"Key found: {api_key[:10]}...")

models_to_test = ["models/gemini-flash-latest", "models/gemini-2.0-flash-exp", "models/gemini-1.5-flash"]

try:
    genai.configure(api_key=api_key)
    # Using the exact name from the list without prefixes
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("Attempting to generate content with gemini-1.5-flash...")
    response = model.generate_content("Describe the benefits of RAG in one sentence.")
    print(f"Response: {response.text}")
    print("Verification SUCCESSFUL")
except Exception as e:
    print(f"Verification FAILED: {e}")
