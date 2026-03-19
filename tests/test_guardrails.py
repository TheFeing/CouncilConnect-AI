import pytest

# MagicMock can create sub-objects on the fly (yes to everything), without needing the actual library
# patch replaces the Client class in the guardrails module with MagicMock
from unittest.mock import MagicMock, patch
from app.guardrails import check_safety1


@patch(
    "app.guardrails.genai.Client"
)  # Decorator (type of wrapper) @patch replaces Client class in guardrails module, prevents real API calls
def test_check_safety_safe_response1(
    mock_client_class,
):  # Tests if "Safe" in response, returns True
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = "The query is Safe."
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(
        "os.environ", {"GEMMA_API_KEY": "fake_key"}
    ):  # patch.dict replaces os.environ with fake_key. Library os can be auto-imported by unittest.mock
        result1 = check_safety1("How do I pay council tax?")
        assert result1 is True


@patch("app.guardrails.genai.Client")
def test_check_safety_unsafe_response1(
    mock_client_class,
):  # Tests if "Unsafe" in response, returns False
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = "This query is Unsafe and violates policy."
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict("os.environ", {"GEMMA_API_KEY": "fake_key"}):
        result1 = check_safety1("Some malicious query")
        assert result1 is False


def test_check_safety_missing_api_key1():  # Tests fail-open logic when API key missing
    with patch.dict("os.environ", {}, clear=True):  # patch.dict clears all variables
        result1 = check_safety1("Any query")
        assert result1 is True


@patch("app.guardrails.genai.Client")
def test_check_safety_exception_handling1(
    mock_client_class,
):  # Tests fail-closed logic when API call raises an exception (e.g., network error)
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.models.generate_content.side_effect = Exception(
        "API Down"
    )  # Exception is a master category that catches all exceptions, simulating an API failure

    with patch.dict("os.environ", {"GEMMA_API_KEY": "fake_key"}):
        result1 = check_safety1("Trigger error")
        assert result1 is False
