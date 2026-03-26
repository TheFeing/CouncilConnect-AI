import os   # OS interfaces for file path management
import google.genai    # GenAI SDK for interacting with Gemma API (S11)

def check_safety(user_query: str) -> bool:    # Input string, return boolean

    api_key = os.getenv("GEMMA_API_KEY")
    if not api_key:
        print("Safety Error: API Key missing. Defaulting to safe for development.")
        return True     # Dev: Fail-open (True) for testing; Prod: Fail-closed (False) for safety

    client = google.genai.Client(api_key=api_key)    # Communication bridge between script and GenAI SDK
    try:
        safety_prompt = (  # Engineered prompt
            # Implicit string concatenation for readability
            "You are a safety classifier. Determine if the following user query "
            "is 'Safe' or 'Unsafe' for a local government chatbot. "
            "Query: " + user_query
        )
        
        response = client.models.generate_content(
            model='shieldgemma-2b', 
            contents=safety_prompt
        )
        
        # Check for safety flags
        is_safe = "Safe" in response.text and "Unsafe" not in response.text
        return is_safe
    except Exception as exception:     # Master category (Exception) for all errors
        print(f"Safety check failed: {exception}")
        return False    # Fail-closed logic for production safety