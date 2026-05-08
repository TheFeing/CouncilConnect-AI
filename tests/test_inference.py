import pytest
# MagicMock (unittest.mock) can create sub-objects on the fly (yes to everything), without needing the actual library
# patch (unittest.mock) replaces the Client class in the guardrails module with MagicMock
import unittest.mock
import sys
import os

# Patch genai module before import to prevent actual library dependencies during testing
with unittest.mock.patch.dict('sys.modules', {'google.genai': unittest.mock.MagicMock()}):
    import app.inference

@unittest.mock.patch('app.inference.google.genai.Client')
@unittest.mock.patch('os.getenv')
def test_get_ai_response_success(mock_getenv, mock_client_class):
    """
    Rationale: Standard success path test for Google AI integration using modern Client.
    """

    # Setup mocks
    mock_getenv.return_value = "mock-api-key-123"
    mock_client_instance = unittest.mock.MagicMock()
    mock_client_class.return_value = mock_client_instance
    
    mock_response = unittest.mock.MagicMock()
    mock_response.text = "Hello from Gemma 4!"
    mock_client_instance.models.generate_content.return_value = mock_response

    # Execute
    result = app.inference.get_ai_response("Hi")

    # Verify
    assert result == "Hello from Gemma 4!"
    mock_client_instance.models.generate_content.assert_called_once_with(
        model='gemma-4-31b-it', 
        contents="Hi"
    )

@unittest.mock.patch('os.getenv')
def test_get_ai_response_missing_key(mock_getenv):
    """
    Rationale: Verifies correct error messaging when environment variables are unset.
    """
    mock_getenv.return_value = None
    result = app.inference.get_ai_response("Hi")
    assert "Configuration Error" in result

@unittest.mock.patch('app.inference.google.genai.Client')
@unittest.mock.patch('app.inference.os.getenv')
def test_get_ai_response_exception(mock_getenv, mock_client_class):
    """
    Test error handling when the SDK Client call fails.
    """
    mock_getenv.return_value = "mock-api-key-123"
    mock_client_instance = unittest.mock.MagicMock()
    mock_client_class.return_value = mock_client_instance
    
    # Simulate an API failure on the models service
    mock_client_instance.models.generate_content.side_effect = Exception("API Down")

    result = app.inference.get_ai_response("Hi")

    assert "service is currently unavailable" in result