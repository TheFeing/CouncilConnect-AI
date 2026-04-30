import fastapi                  # API routing and error responses
import pydantic                 # Data validation and structure
import app.inference            # AI logic bridge to Gemma 3
import uvicorn                  # ASGI server

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

# Configure CORS to allow frontend communication.
app_instance.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=[     # In production, this should be restricted to the actual frontend URL(s)
        "http://localhost:8501",  # Streamlit default
        "http://127.0.0.1:8501",  # Alternative local address
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bind to port 8000 to match compute.tf
if __name__ == "__main__":
    uvicorn.run(app_instance, host="0.0.0.0", port=8000)