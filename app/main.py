import fastapi                  # API routing and error responses
import pydantic                 # Data validation and structure
import app.inference            # AI logic bridge to Gemma 3

app_instance = fastapi.FastAPI(
    title="CouncilConnect AI",
    description="A RAG-based resident support agent."
)

class QueryRequest(pydantic.BaseModel):
    prompt: str

@app_instance.get("/health")
def health_check():
    """
    Basic health probe for Azure Container Apps monitoring.
    """
    return {"status": "healthy", "version": "1.0.0"}

@app_instance.post("/chat")
async def chat(request: QueryRequest):
    """
    Primary endpoint for resident queries.
    Uses Pydantic for request validation to ensure structured data handling.
    """
    if not request.prompt.strip(): # Empty string is considered to be False in Python
        raise fastapi.HTTPException(status_code=400, detail="Query cannot be empty.")

    response_text = app.inference.get_ai_response(request.prompt)
    return {"response": response_text}