import os
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai

# Load environment variables
load_dotenv()

def test_groq():
    print("\n--- Testing Groq ---")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Groq API Key not found")
        return
    client = Groq(api_key=api_key)
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hi"}],
            model="llama-3.3-70b-versatile",
        )
        print(f"Groq Success: {chat_completion.choices[0].message.content}")
    except Exception as e:
        print(f"Groq Failure: {type(e).__name__}: {e}")

def test_gemini():
    print("\n--- Listing All Gemini Models ---")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Gemini API Key not found")
        return
    genai.configure(api_key=api_key)
    try:
        for m in genai.list_models():
            print(f"Name: {m.name}, Display: {m.display_name}, Methods: {m.supported_generation_methods}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    test_groq()
    test_gemini()
