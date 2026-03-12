import os
import google.genai as genai

def get_ai_response1(user_input1):
    """
    Connects to the Gemma 3 27B model using the Google GenAI SDK.
    Uses the modern Client pattern for efficiency.
    """
    api_key1 = os.getenv("GEMMA_API_KEY")
    if not api_key1:
        return "Configuration Error: API Key missing."

    try:
        client1 = genai.Client(api_key=api_key1)
        # Model selection based on Sprint 2 Project Plan
        response1 = client1.models.generate_content(
            model='gemma-3-27b',
             contents=user_input1
        )
        return response1.text
    except Exception as e1:
        # Prevents server crash by catching SDK-level exceptions
        return f"The AI service is currently unavailable. Error: {str(e1)}"