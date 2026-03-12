# from ... import ...: Less active memory loading, faster execution

from fastapi import FastAPI, HTTPException      # API routing and error responses
from pydantic import BaseModel                  # Data validation and structure
from app.inference import get_ai_response1      # AI logic bridge to Gemma 3

app1 = FastAPI(
    title="CouncilConnect AI",
    description="A RAG-based resident support agent."
)

class QueryRequest1(BaseModel):
    prompt1: str

# Decorator: Returns target function with wrapped function
# Decorator(): Returns custom decorator before wrapping the function followed

@app1.get("/health")
def health_check1():
    """
    Basic health probe for Azure Container Apps monitoring.
    """
    return {"status": "healthy", "version": "1.0.0"}

@app1.post("/chat")
async def chat1(request1: QueryRequest1):
    """
    Primary endpoint for resident queries.
    Uses Pydantic for request validation to ensure structured data handling.
    """
    if not request1.prompt1.strip(): # Empty string is considered to be False in Python
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    response_text1 = get_ai_response1(request1.prompt1)
    return {"response": response_text1}