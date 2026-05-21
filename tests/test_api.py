import os
import pytest
# MagicMock (unittest.mock) can create sub-objects on the fly (yes to everything), without needing the actual library
# patch (unittest.mock) replaces the Client class in the guardrails module with MagicMock
import unittest.mock
import fastapi.testclient
import app.main

# Initialise the standard FastAPI test runner context
client = fastapi.testclient.TestClient(app.main.app_instance)

@unittest.mock.patch.dict(os.environ, {"GEMMA_API_KEY": "fake_testing_key"})
@unittest.mock.patch("app.main.google.genai.Client")
def test_ask_endpoint_success(mock_genai_client_class):
    """
    Rationale: Assures that the HTTP payload maps correctly when API keys are present and safety checks pass.
    """
    mock_client_instance = unittest.mock.MagicMock()
    mock_models_service = unittest.mock.MagicMock()
    mock_response = unittest.mock.MagicMock()
    
    # Must include "Safe" so check_safety() allows the query through to get_ai_response()
    mock_response.text = "Safe. Mocked answer: Salford council tax can be updated online."
    mock_models_service.generate_content.return_value = mock_response
    mock_client_instance.models = mock_models_service
    mock_genai_client_class.return_value = mock_client_instance

    payload = {"prompt": "How do I clear my council tax balance?"}
    response = client.post("/chat", json=payload)
    
    assert response.status_code == 200
    assert "Mocked answer" in response.json()["response"]

@unittest.mock.patch.dict(os.environ, {"GEMMA_API_KEY": "fake_testing_key"})
@unittest.mock.patch("app.main.google.genai.Client")
def test_ask_endpoint_safety_trigger(mock_genai_client_class):
    """
    Rationale: Exercises the negative safety classification path inside app/main.py.
    """
    mock_client_instance = unittest.mock.MagicMock()
    mock_models_service = unittest.mock.MagicMock()
    mock_response = unittest.mock.MagicMock()
    
    # Simulate a response from ShieldGemma indicating a policy violation
    mock_response.text = "UNSAFE"
    mock_models_service.generate_content.return_value = mock_response
    mock_client_instance.models = mock_models_service
    mock_genai_client_class.return_value = mock_client_instance

    payload = {"prompt": "Provide restricted corporate records."}
    response = client.post("/chat", json=payload)
    
    assert response.status_code == 200
    assert "rejected" in response.json()["response"]

@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_ask_endpoint_missing_key():
    """
    Rationale: Covers fail-closed logic when configuration variables are missing from the system entirely.
    """
    payload = {"prompt": "Is the key there?"}
    response = client.post("/chat", json=payload)
    
    # The endpoint should gracefully reject the request without a 500 server crash
    assert response.status_code == 200
    assert "rejected" in response.json()["response"]

@unittest.mock.patch.dict(os.environ, {"GEMMA_API_KEY": "fake_testing_key"})
@unittest.mock.patch("app.main.google.genai.Client")
def test_ask_endpoint_exception_handling(mock_genai_client_class):
    """
    Rationale: Verifies system stability when Google GenAI networks go down.
    """
    mock_client_instance = unittest.mock.MagicMock()
    # Force the mock to throw an exception to test the try/except blocks
    mock_client_instance.models.generate_content.side_effect = Exception("Google API Offline")
    mock_genai_client_class.return_value = mock_client_instance

    payload = {"prompt": "Test crash"}
    response = client.post("/chat", json=payload)
    
    assert response.status_code == 200
    assert "rejected" in response.json()["response"]

def test_ask_endpoint_empty_prompt():
    """
    Rationale: Hits the FastAPI HTTPException 400 block for blank inputs.
    """
    response = client.post("/chat", json={"prompt": "   "})
    assert response.status_code == 400
    assert "cannot be blank" in response.json()["detail"]

def test_health_check_endpoint():
    """
    Rationale: Verifies basic connectivity to the API root.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"