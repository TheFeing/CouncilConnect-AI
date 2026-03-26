import os
import google.genai
import typing

def get_ai_response(query: str) -> str:
    """
    Interacts with the Gemma 3 API using the modern google-genai SDK.
    """
    # Access API key via environment variables
    api_key = os.getenv("GEMMA_API_KEY", "")
    if not api_key:
        return "Configuration Error: API Key missing."

    # Initialize the modern GenAI Client
    client = google.genai.Client(api_key=api_key)

    try:
        # Using the unified generate_content method for Gemma 3 27B
        response = client.models.generate_content(
            model='gemma-3-27b', 
            contents=query
        )
        return response.text
    except Exception as error:
        # Log error for observability
        print(f"Inference Error: {str(error)}")
        return "The service is currently unavailable. Please try again later."