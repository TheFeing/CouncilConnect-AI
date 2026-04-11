import pytest
# MagicMock (unittest.mock) can create sub-objects on the fly (yes to everything), without needing the actual library
# patch (unittest.mock) replaces the Client class in the guardrails module with MagicMock
import unittest.mock
import app.guardrails

# Decorator (type of wrapper) @patch replaces Client class in guardrails module, prevents real API calls
@unittest.mock.patch('app.guardrails.google.genai.Client')   
def test_check_safety_safe_response(mock_client_class): # Tests if "Safe" in response, returns True
    mock_client = unittest.mock.MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = unittest.mock.MagicMock()
    mock_response.text = "The query is Safe."
    mock_client.models.generate_content.return_value = mock_response

    with unittest.mock.patch.dict('os.environ', {'GEMMA_API_KEY': 'fake_key'}): # patch.dict replaces os.environ with fake_key. Library os can be auto-imported by unittest.mock
        result = app.guardrails.check_safety("How do I pay council tax?")
        assert result is True

@unittest.mock.patch('app.guardrails.google.genai.Client')
def test_check_safety_unsafe_response(mock_client_class): # Tests if "Unsafe" in response, returns False
    mock_client = unittest.mock.MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = unittest.mock.MagicMock()
    mock_response.text = "This query is Unsafe and violates policy."
    mock_client.models.generate_content.return_value = mock_response

    with unittest.mock.patch.dict('os.environ', {'GEMMA_API_KEY': 'fake_key'}):
        result = app.guardrails.check_safety("Some malicious query")
        assert result is False

def test_check_safety_missing_api_key(): # Tests fail-closed logic when API key missing
    with unittest.mock.patch.dict('os.environ', {}, clear=True): # patch.dict clears all variables
        result = app.guardrails.check_safety("Any query")
        assert result is False

@unittest.mock.patch('app.guardrails.google.genai.Client')
def test_check_safety_exception_handling(mock_client_class): # Tests fail-closed logic when API call raises an exception (e.g., network error)
    mock_client = unittest.mock.MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.models.generate_content.side_effect = Exception("API Down") # Exception is a master category that catches all exceptions, simulating an API failure

    with unittest.mock.patch.dict('os.environ', {'GEMMA_API_KEY': 'fake_key'}):
        result = app.guardrails.check_safety("Trigger error")
        assert result is False