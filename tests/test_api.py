from fastapi.testclient import TestClient
from app.main import app1
from unittest.mock import patch

client = TestClient(app1)

def test_health_check1():
    """Tests the /health endpoint for monitoring."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "1.0.0"}

def test_chat_empty_prompt1():
    """Tests that empty prompts are rejected with a 400 error."""
    response = client.post("/chat", json={"prompt1": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Query cannot be empty."

@patch('app.main.get_ai_response1')
def test_chat_success1(mock_inference):
    """Tests the successful chat path to reach 80% coverage in main.py."""
    mock_inference.return_value = "Mocked Response"
    response = client.post("/chat", json={"prompt1": "How do I pay tax?"})
    assert response.status_code == 200
    assert response.json() == {"response": "Mocked Response"}