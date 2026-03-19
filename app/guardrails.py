import os  # OS interfaces for file path management
from google import genai  # GenAI SDK for interacting with Gemma API (S11)


def check_safety1(user_query1: str) -> bool:  # Input string, return boolean

    api_key1 = os.getenv("GEMMA_API_KEY")
    if not api_key1:
        print("Safety Error: API Key missing. Defaulting to safe for development.")
        return True  # Dev: Fail-open (True) for testing; Prod: Fail-closed (False) for safety

    client1 = genai.Client(
        api_key=api_key1
    )  # Communication bridge between script and GenAI SDK
    try:
        safety_prompt1 = (  # Engineered prompt
            # Implicit string concatenation for readability
            "You are a safety classifier. Determine if the following user query "
            "is 'Safe' or 'Unsafe' for a local government chatbot. "
            "Query: " + user_query1
        )

        response1 = client1.models.generate_content(
            model="shieldgemma-2b", contents=safety_prompt1
        )

        # Check for safety flags
        is_safe1 = "Safe" in response1.text and "Unsafe" not in response1.text
        return is_safe1
    except Exception as exception1:  # Master category (Exception) for all errors
        print(f"Safety check failed: {exception1}")
        return False  # Fail-closed logic for production safety
