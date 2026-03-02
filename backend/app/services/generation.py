import os
from groq import Groq
from app.core.config import settings

import google.generativeai as genai

client = Groq(
    api_key=settings.GROQ_API_KEY,
)

genai.configure(api_key=settings.GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("models/gemini-flash-latest")

def generate_answer(context: str, question: str) -> str:
    """
    Generates an answer using Groq API based on the provided context.
    Returns a JSON string.
    """
    prompt = f"""
    You are a helpful assistant for completing due diligence questionnaires.
    Use the following pieces of retrieved context to answer the question.
    
    Context:
    {context}
    
    Question: {question}
    
    RESPONSE FORMAT:
    You MUST respond with a JSON object in the following format:
    {{
      "yes_no": "Yes" | "No" | "N/A",
      "answer": "Your detailed answer based on context",
      "is_question": true | false
    }}
    - Set "yes_no" to "Yes" or "No" only if the question explicitly asks for a confirmation or can be answered with a binary state. Otherwise use "N/A".
    - "answer" should contain the reasoning and citations if applicable.
    - Set "is_question" to false if the input is clearly an instruction or header rather than a question.
    
    Return ONLY the JSON object.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"} if "llama-3.3" in "llama-3.3-70b-versatile" else None # Groq supports this for some models
    )
    
    return chat_completion.choices[0].message.content

def generate_answer_gemini(context: str, question: str) -> str:
    """
    Generates an answer using Google Gemini API as a fallback.
    Returns a JSON string.
    """
    prompt = f"""
    You are a helpful assistant for completing due diligence questionnaires.
    Use the following pieces of retrieved context to answer the question.
    
    Context:
    {context}
    
    Question: {question}
    
    RESPONSE FORMAT:
    You MUST respond with a JSON object in the following format:
    {{
      "yes_no": "Yes" | "No" | "N/A",
      "answer": "Your detailed answer based on context",
      "is_question": true | false
    }}
    - Set "yes_no" to "Yes" or "No" only if the question explicitly asks for a confirmation or can be answered with a binary state. Otherwise use "N/A".
    - "answer" should contain the reasoning and citations if applicable.
    - Set "is_question" to false if the input is clearly an instruction or header rather than a question.
    
    Return ONLY the JSON object.
    """
    
    response = gemini_model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        )
    )
    return response.text
