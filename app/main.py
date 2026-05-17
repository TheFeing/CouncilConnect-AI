import fastapi                  # API routing and error responses
import fastapi.middleware.cors  # CORS handling for frontend-backend communication
import pydantic                 # Data validation and structure
import uvicorn                  # ASGI server
import logging                  # For logging application events and errors
import app.database             # Custom module for database interactions (Qdrant vector store)
import google.genai             # GenAI SDK for interacting with Gemma API


# Configure application logging to print runtime operational signals to the console, which can be captured by Azure Monitor for observability.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_instance = fastapi.FastAPI(
    title="CouncilConnect AI",
    description="A RAG-based resident support agent."
)

class QueryRequest(pydantic.BaseModel): # Any object created using class 'QueryRequest' must have a 'prompt' property that is a string and will be passed to BaseModel for validation and structured handling.
    prompt: str


def check_safety(user_query: str) -> bool:  # Input string, return boolean
"""Evaluates text queries utilising ShieldGemma classification models to ensure policy compliance."""

    secrets = app.database.SecretManager()  # Initialise the manager to fetch the key securely.
    api_key = secrets.get_secret("GEMMA_API_KEY")

    if not api_key:
        logger.error("ShieldGemma execution blocked: GEMMA_API_KEY is unassigned. Failing closed for protection.")
        return False # Dev: Fail-open (True) for testing; Prod: Fail-closed (False) for safety.

    try:
        client = google.genai.Client(api_key=api_key)   # Communication bridge between script and GenAI SDK.

        # Construct the safety prompt for ShieldGemma.
        safety_prompt = (
            # Implicit string concatenation for readability
            "You are a safety classifier. Determine if the following user query "
            "is 'Safe' or 'Unsafe' for a local government chatbot. "
            "Query: {user_query}"
        )
        
        # Send to the safety model.
        response = client.models.generate_content(
            model='shieldgemma-2b', # A smaller, cost-effective model designed for classification tasks. See Google for the latest model names and versions.
            contents=safety_prompt
        )
        
        return "Safe" in response.text and "Unsafe" not in response.text    # Only allows queries that are explicitly classified as safe.
        
    except Exception as error:  # Master category (Exception) for all errors
        logger.error(f"Critical execution error triggered during safety analysis: {error}")
        return False    # Fail-closed logic for production safety


def get_ai_response(query: str) -> str:
    """
    Interacts with the Google AI API using the modern google-genai SDK.
    """

    secrets = app.database.SecretManager()
    api_key = secrets.get_secret("GEMMA_API_KEY")

    if not api_key:
        return "System Configuration Error: API Key missing."

    try:
        client = google.genai.Client(api_key=api_key)   # Initialize the modern GenAI Client
        
        # Using the unified generate_content method for Gemma 4 31B
        response = client.models.generate_content(
            model='gemma-4-31b-it', # See Google for the latest model names and versions
            contents=query
        )
        return response.text
        
    except Exception as error:
        # Log error for observability
        logger.error(f"Inference Error: {str(error)}")
        return "The service is currently unavailable. Please try again later."


@app_instance.get("/health")    # Create a route (network address) named "/health" for communication with Azure Container App Ingress Gateway, for better request queue management and monitoring.
def health_check():
    """
    Basic health probe for Azure Container Apps monitoring.
    """
    return {"status": "healthy", "version": "1.0.0"}


@app_instance.post("/chat")     # Create a route (network address) named "/chat" for communication with Azure Container App Ingress Gateway, for better request queue management and monitoring.
async def chat(request: QueryRequest):  # Define non-blocking background function (async) which expects an incoming data package (web browser) named 'request' that must conform class 'QueryRequest' structure.
    """
    Primary endpoint for resident queries.
    Uses Pydantic for request validation to ensure structured data handling.
    """

    logger.info("Received resident query via /chat endpoint")   # Log the event, not the data (to maintain privacy/PII standards).

    clean_prompt = request.prompt.strip()   # Strip away whitespace formatting padding characters.
    if not clean_prompt:    # Empty string is considered to be False in Python.
        raise fastapi.HTTPException(status_code=400, detail="Query validation error: Input payload cannot be blank.")   # Create and stop further processing with raised exception.

    # Execute the isolated security filter check before routing requests further.
    if not check_safety(clean_prompt):  # Throw clean_prompt into the safety function for evaluation.
        return {"response": "Query rejected: This request contains flags violating compliance safety parameters."}

    response_text = get_ai_response(clean_prompt)   # Fetch the final structural evaluation string response from the generation engine.
    return {"response": response_text}


# Configure CORS to allow frontend communication because the frontend (Streamlit) will be served from a different origin than the FastAPI backend (port 8501 vs 8000).
app_instance.add_middleware(    # FastAPI built-in method.
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=[ # Local allowance still works in prod env because both frontend and backend are on the same localhost origin within the container.
        "http://localhost:8501",  # Streamlit default
        "http://127.0.0.1:8501",  # Alternative local address
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bind to port 8000 to match Terraform configs.
if __name__ == "__main__":
    logger.info("Starting CouncilConnect AI API server on port 8000")
    uvicorn.run(app_instance, host="0.0.0.0", port=8000)