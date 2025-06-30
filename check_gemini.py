# check_gemini.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv() # Load environment variables from .env

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GOOGLE_API_KEY not found in .env file. Please set it.")
    exit()

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Attempting to list available Gemini models...")
    for m in genai.list_models():
        # Filter for models that support 'generateContent' (text generation)
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name} (Supports generateContent)")
        else:
            print(f"- {m.name} (Does NOT support generateContent)") # For debugging
except Exception as e:
    print(f"An error occurred while listing models: {e}")
    print("Please ensure your GOOGLE_API_KEY is correct and has access to Gemini API.")