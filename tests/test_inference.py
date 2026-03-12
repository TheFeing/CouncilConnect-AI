import pytest
import os
from unittest.mock import patch, MagicMock
from app.inference import get_ai_response1

@patch('google.genai.Client')
def test_get_ai_response_success1(mock_client_class):
    """
    Tests successful AI response generation.
    patch.dict ensures the function sees an API key and proceeds to the SDK.
    """
    with patch.dict('os.environ', {'GEMMA_API_KEY': 'dummy_key'}):
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.models.generate_content.return_value.text = "Hello, I am Gemma 3."

        result = get_ai_response1("Hi")
        assert result == "Hello, I am Gemma 3."

def test_get_ai_response_no_key1():
    """Tests handling of missing API key environment variable."""
    with patch.dict('os.environ', clear=True):
        if "GEMMA_API_KEY" in os.environ:
             del os.environ["GEMMA_API_KEY"]
        result = get_ai_response1("Hi")
        assert "Configuration Error" in result

@patch('google.genai.Client')
def test_get_ai_response_exception1(mock_client_class):
    """Tests that the system catches SDK exceptions gracefully."""
    with patch.dict('os.environ', {'GEMMA_API_KEY': 'dummy_key'}):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("API Down")

        result = get_ai_response1("Hi")
        assert "service is currently unavailable" in result