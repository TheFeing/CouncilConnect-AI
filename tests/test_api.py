import pytest
import os
# MagicMock (unittest.mock) can create sub-objects on the fly (yes to everything), without needing the actual library
# patch (unittest.mock) replaces the Client class in the guardrails module with MagicMock
import unittest.mock
import starlette.testclient
import app.main

@pytest.fixture
def api_client():
    """
    Rationale: Provides a reusable TestClient instance for FastAPI, mocking environment variables.
    """
    with unittest.mock.patch.dict(os.environ, {"GEMMA_API_KEY": "test_key_123"}):
        yield starlette.testclient.TestClient(app.main.app_instance)

@pytest.fixture
def mocked_genai():
    """
    Rationale: Prevents real API calls to Google's servers during unit testing.
    """

    # Patch the 'genai' module where it is imported in the app.inference module
    with unittest.mock.patch("app.inference.google.genai") as mock_genai_module:

        # 1. Create the mock response object with the .text property
        mock_response = unittest.mock.MagicMock()
        mock_response.text = "Mocked Response"
        
        # 2. Create the Client instance mock
        mock_client_instance = unittest.mock.MagicMock()

        # 3. Setup the chain: client.models.generate_content(...)
        # We mock 'models' then 'generate_content' on that mock
        mock_client_instance.models.generate_content.return_value = mock_response

        # 4. Ensure that calling genai.Client(...) returns our configured instance
        mock_genai_module.Client.return_value = mock_client_instance
        
        yield mock_genai_module

def test_get_ai_response_success(api_client, mocked_genai):
    """
    Rationale: Ensures the /chat endpoint returns the correct AI response under normal conditions.
    """
    payload = {"prompt": "Hello, how can I pay my council tax?"}
    response = api_client.post("/chat", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "Mocked Response"

def test_get_ai_response_no_prompt(api_client):
    """
    Rationale: Verifies that empty prompts trigger a 422 Unprocessable Entity error (FastAPI default).
    """
    response = api_client.post("/chat", json={})

    # FastAPI returns 422 Unprocessable Entity for schema validation failures
    assert response.status_code == 422

def test_get_ai_response_missing_api_key(api_client, mocked_genai):
    """
    Rationale: Edge case testing for configuration failures.
    """

    # Override the environment for this specific test to remove the key
    with unittest.mock.patch.dict(os.environ, {"GEMMA_API_KEY": ""}, clear=True):
        payload = {"prompt": "Is there a key?"}
        response = api_client.post("/chat", json=payload)
        
        assert response.status_code == 200
        assert "API Key missing" in response.json()["response"]