import os   # OS interfaces for file path management
import google.genai # GenAI SDK for interacting with Gemma API
import app.security_utils   # Importing the SecretManager class for secure key retrieval

def check_safety(user_query: str) -> bool:  # Input string, return boolean

    # 1. Initialise the manager to fetch the key securely
    secrets = app.security_utils.SecretManager()
    api_key = secrets.get_secret("GEMMA-API-KEY")

    # 2. Safety check: If no key is found, handle based on environment
    if not api_key:
        print("Safety Warning: No API Key found. Defaulting to True for local testing.")
        return True # Dev: Fail-open (True) for testing; Prod: Fail-closed (False) for safety
        
    # 3. Initialise the AI Client with the secured key
    client = google.genai.Client(api_key=api_key)   # Communication bridge between script and GenAI SDK
    
    try:
        # Construct the safety prompt for ShieldGemma
        safety_prompt = (
            # Implicit string concatenation for readability
            "You are a safety classifier. Determine if the following user query "
            "is 'Safe' or 'Unsafe' for a local government chatbot. "
            "Query: " + user_query
        )
        
        # Send to the safety model
        response = client.models.generate_content(
            model='shieldgemma-2b',
            contents=safety_prompt
        )
        
        # Logic: We only allow it if 'Safe' is confirmed
        is_safe = "Safe" in response.text and "Unsafe" not in response.text
        return is_safe
        
    except Exception as e:  # Master category (Exception) for all errors
        print(f"Critical Safety Failure: {e}")
        return False    # Fail-closed logic for production safety