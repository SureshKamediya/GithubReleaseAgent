# llm_agent/analysis.py

import google.generativeai as genai
import os
from dotenv import load_dotenv
from llm_agent.prompts import COMMIT_ANALYSIS_PROMPT # Import the prompt

# Load environment variables
load_dotenv()

# Configure the Gemini API key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file. Please set it.")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Generative Model
model = genai.GenerativeModel('gemini-1.5-pro-latest') # Or 'gemini-1.5-flash-latest' if you prefer a faster/cheaper option

def analyze_commit_with_llm(commit_message, commit_diff, review_comments=""):
    """
    Sends commit details to the LLM for analysis and confidence scoring.
    """
    # Format the imported prompt with the actual data
    prompt = COMMIT_ANALYSIS_PROMPT.format(
        commit_message=commit_message,
        commit_diff=commit_diff,
        review_comments=review_comments
    )
    
    # Make the API call
    try:
        response = model.generate_content(prompt)
        # Ensure the response has text content
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            print("Warning: LLM response had no text content.")
            return "Confidence Score: 50\nJustification: LLM could not generate a proper response.\nSuggestions for Improvement: Re-evaluate input or prompt."
    except Exception as e:
        print(f"Error calling LLM for commit analysis: {e}")
        return f"Confidence Score: 0\nJustification: LLM API call failed due to error: {e}\nSuggestions for Improvement: Check API key, network, or rate limits."