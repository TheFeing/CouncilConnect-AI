"""
Tests for SecretManager and VectorStoreManager.
"""

import os               # Accesses environment variables for test configuration
import unittest.mock    # Provides tools for mocking and patching dependencies during tests
import pytest           # Automated testing framework runner
import app.database     # Module under test containing SecretManager and VectorStoreManager classes


def test_secret_manager_no_vault_env(monkeypatch):
    monkeypatch.delenv("AZURE_KEY_VAULT_ENDPOINT", raising=False)
    sm = app.database.SecretManager()
    assert sm.client is None


def test_secret_manager_get_secret_raises_when_no_client(monkeypatch):
    monkeypatch.delenv("AZURE_KEY_VAULT_ENDPOINT", raising=False)
    sm = app.database.SecretManager()
    with pytest.raises(ValueError, match="offline"):
        sm.get_secret("some-secret")


@unittest.mock.patch("app.database.azure.identity.DefaultAzureCredential")
@unittest.mock.patch("app.database.azure.keyvault.secrets.SecretClient")
def test_secret_manager_get_secret_success(mock_secret_client_class, mock_credential_class, monkeypatch):
    monkeypatch.setenv("AZURE_KEY_VAULT_ENDPOINT", "[fake-vault.vault.azure.net](https://fake-vault.vault.azure.net/)")

    mock_secret_obj = unittest.mock.MagicMock()
    mock_secret_obj.value = "my-secret-value"
    mock_client_inst = unittest.mock.MagicMock()
    mock_client_inst.get_secret.return_value = mock_secret_obj
    mock_secret_client_class.return_value = mock_client_inst

    sm = app.database.SecretManager()
    result = sm.get_secret("MY-SECRET")
    assert result == "my-secret-value"


@unittest.mock.patch("app.database.azure.identity.DefaultAzureCredential")
@unittest.mock.patch("app.database.azure.keyvault.secrets.SecretClient")
def test_secret_manager_get_secret_propagates_error(mock_secret_client_class, mock_credential_class, monkeypatch):
    monkeypatch.setenv("AZURE_KEY_VAULT_ENDPOINT", "[fake-vault.vault.azure.net](https://fake-vault.vault.azure.net/)")

    mock_client_inst = unittest.mock.MagicMock()
    mock_client_inst.get_secret.side_effect = Exception("Vault unreachable")
    mock_secret_client_class.return_value = mock_client_inst

    sm = app.database.SecretManager()
    with pytest.raises(Exception, match="Vault unreachable"):
        sm.get_secret("MY-SECRET")


@unittest.mock.patch("app.database.qdrant_client.QdrantClient")
@unittest.mock.patch("app.database.google.genai.Client")
def test_vector_store_manager_embedding_and_search(mock_genai_client_class, mock_qdrant_class, monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "[fake-qdrant.example.com](https://fake-qdrant.example.com)")
    monkeypatch.setenv("QDRANT_API_KEY", "fake-api-key")
    monkeypatch.setenv("GEMMA_API_KEY", "fake-gemma-key")
    monkeypatch.setenv("GEMINI_EMBEDDING_MODEL", "test-embed-model")

    mock_qdrant = unittest.mock.MagicMock()
    mock_qdrant_class.return_value = mock_qdrant

    mock_genai = unittest.mock.MagicMock()

    class DummyEmbedding:
        values = [0.01] * 3072

    embed_resp = unittest.mock.MagicMock()
    embed_resp.embeddings = [DummyEmbedding()]
    mock_genai.models.embed_content.return_value = embed_resp
    mock_genai_client_class.return_value = mock_genai

    mock_point = unittest.mock.MagicMock()
    mock_point.payload = {"text": "Salford residents can pay council tax online.", "source": "[example.gov](https://example.gov)"}
    mock_query_result = unittest.mock.MagicMock()
    mock_query_result.points = [mock_point]
    mock_qdrant.query_points.return_value = mock_query_result

    vsm = app.database.VectorStoreManager(collection_name="test_collection")

    # ensure_collection_exists — collection missing path
    mock_qdrant.get_collections.return_value.collections = []
    vsm.ensure_collection_exists()
    assert mock_qdrant.create_collection.called

    # ensure_collection_exists — collection already exists path
    existing = unittest.mock.MagicMock()
    existing.name = "test_collection"
    mock_qdrant.get_collections.return_value.collections = [existing]
    mock_qdrant.create_collection.reset_mock()
    vsm.ensure_collection_exists()
    assert not mock_qdrant.create_collection.called

    # upsert_document
    vsm.upsert_document("Test text", {"type": "unit"})
    assert mock_qdrant.upsert.called

    # search_similar
    results = vsm.search_similar("How to pay tax?")
    assert isinstance(results, list)
    assert results[0].payload["text"].startswith("Salford residents")


@unittest.mock.patch("app.database.qdrant_client.QdrantClient")
@unittest.mock.patch("app.database.google.genai.Client")
def test_vector_store_manager_no_client_graceful(mock_genai_client_class, mock_qdrant_class, monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "[fake-qdrant.example.com](https://fake-qdrant.example.com)")
    monkeypatch.setenv("QDRANT_API_KEY", "fake-api-key")
    monkeypatch.setenv("GEMMA_API_KEY", "fake-gemma-key")
    monkeypatch.setenv("GEMINI_EMBEDDING_MODEL", "test-embed-model")

    mock_qdrant_class.return_value = unittest.mock.MagicMock()
    mock_genai_client_class.return_value = unittest.mock.MagicMock()

    vsm = app.database.VectorStoreManager(collection_name="test_collection")
    vsm.client = None  # Simulate broken connection

    # Should not raise; should log and return gracefully
    vsm.ensure_collection_exists()
    vsm.upsert_document("Some text")
    result = vsm.search_similar("query")
    assert result == []


@unittest.mock.patch("app.database.qdrant_client.QdrantClient")
@unittest.mock.patch("app.database.google.genai.Client")
def test_get_embedding_raises_without_ai_client(mock_genai_client_class, mock_qdrant_class, monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "[fake-qdrant.example.com](https://fake-qdrant.example.com)")
    monkeypatch.setenv("QDRANT_API_KEY", "fake-api-key")
    monkeypatch.setenv("GEMMA_API_KEY", "fake-gemma-key")
    monkeypatch.setenv("GEMINI_EMBEDDING_MODEL", "test-embed-model")

    mock_qdrant_class.return_value = unittest.mock.MagicMock()
    mock_genai_client_class.return_value = unittest.mock.MagicMock()

    vsm = app.database.VectorStoreManager(collection_name="test_collection")
    vsm.ai_client = None  # Simulate missing AI client

    import pytest
    with pytest.raises(ValueError, match="unassigned"):
        vsm._get_embedding("test query")


def test_vector_store_manager_qdrant_fallback_to_secret_manager(monkeypatch):
    """Cover lines 66-74: fallback to SecretManager when QDRANT_URL/KEY missing."""
    monkeypatch.delenv("QDRANT_URL", raising=False)
    monkeypatch.delenv("QDRANT_API_KEY", raising=False)
    monkeypatch.setenv("GEMMA_API_KEY", "fake-gemma-key")

    with unittest.mock.patch("app.database.SecretManager") as mock_secret_manager_class:
        mock_secrets = unittest.mock.MagicMock()
        # Return different values based on secret name
        def get_secret_side_effect(name):
            if name == "QDRANT-URL":
                return "https://secret-qdrant-url"
            if name == "QDRANT-API-KEY":
                return "secret-api-key"
            raise ValueError("Unexpected secret")
        mock_secrets.get_secret.side_effect = get_secret_side_effect
        mock_secret_manager_class.return_value = mock_secrets

        with unittest.mock.patch("app.database.qdrant_client.QdrantClient") as mock_qdrant_class:
            with unittest.mock.patch("app.database.google.genai.Client"):
                vsm = app.database.VectorStoreManager()
                mock_qdrant_class.assert_called_once_with(
                    url="https://secret-qdrant-url",
                    api_key="secret-api-key"
                )


def test_vector_store_manager_qdrant_connection_error(monkeypatch):
    """Cover lines 85-90: exception when QdrantClient init fails."""
    monkeypatch.setenv("QDRANT_URL", "https://bad-url")
    monkeypatch.setenv("QDRANT_API_KEY", "bad-key")
    monkeypatch.setenv("GEMMA_API_KEY", "fake-gemma-key")

    with unittest.mock.patch("app.database.qdrant_client.QdrantClient") as mock_qdrant_class:
        mock_qdrant_class.side_effect = Exception("Connection refused")
        vsm = app.database.VectorStoreManager()
        # client should be None after exception
        assert vsm.client is None


def test_vector_store_manager_gemma_key_fallback_to_secret_manager(monkeypatch):
    """Cover lines 95-100: fallback to SecretManager for GEMMA_API_KEY."""
    monkeypatch.delenv("GEMMA_API_KEY", raising=False)
    monkeypatch.setenv("QDRANT_URL", "https://fake")
    monkeypatch.setenv("QDRANT_API_KEY", "key")

    with unittest.mock.patch("app.database.SecretManager") as mock_secret_manager_class:
        mock_secrets = unittest.mock.MagicMock()
        mock_secrets.get_secret.return_value = "secret-gemma-key"
        mock_secret_manager_class.return_value = mock_secrets

        with unittest.mock.patch("app.database.qdrant_client.QdrantClient"):
            with unittest.mock.patch("app.database.google.genai.Client") as mock_genai_class:
                vsm = app.database.VectorStoreManager()
                mock_genai_class.assert_called_once_with(api_key="secret-gemma-key")
                assert vsm.ai_client is not None


def test_vector_store_manager_no_gemma_key_logs_warning(monkeypatch, caplog):
    """Cover lines 106-107: warning when no API key found."""
    import logging
    monkeypatch.delenv("GEMMA_API_KEY", raising=False)
    monkeypatch.setenv("QDRANT_URL", "https://fake")
    monkeypatch.setenv("QDRANT_API_KEY", "key")

    # Make SecretManager also fail
    with unittest.mock.patch("app.database.SecretManager") as mock_secret_manager_class:
        mock_secrets = unittest.mock.MagicMock()
        mock_secrets.get_secret.side_effect = Exception("Vault unreachable")
        mock_secret_manager_class.return_value = mock_secrets

        with unittest.mock.patch("app.database.qdrant_client.QdrantClient"):
            caplog.set_level(logging.WARNING)
            vsm = app.database.VectorStoreManager()
            assert vsm.ai_client is None
            assert "VectorStoreManager starting without active Google GenAI" in caplog.text


def test_upsert_document_exception_handling():
    """Cover line 156 (error log inside upsert_document)."""
    with unittest.mock.patch("app.database.qdrant_client.QdrantClient") as mock_qdrant_class:
        mock_qdrant = unittest.mock.MagicMock()
        mock_qdrant.upsert.side_effect = Exception("Database write error")
        mock_qdrant_class.return_value = mock_qdrant

        with unittest.mock.patch("app.database.google.genai.Client") as mock_genai_class:
            mock_genai = unittest.mock.MagicMock()
            # Simulate successful embedding
            class DummyEmbedding:
                values = [0.01] * 3072
            embed_resp = unittest.mock.MagicMock()
            embed_resp.embeddings = [DummyEmbedding()]
            mock_genai.models.embed_content.return_value = embed_resp
            mock_genai_class.return_value = mock_genai

            vsm = app.database.VectorStoreManager()
            # This should not raise; it will log the error and return
            vsm.upsert_document("Test text", {"meta": "data"})
            # The error log line (156) is executed


def test_search_similar_embedding_error():
    """Cover lines 196-198: exception handler in search_similar."""
    with unittest.mock.patch("app.database.qdrant_client.QdrantClient") as mock_qdrant_class:
        mock_qdrant = unittest.mock.MagicMock()
        mock_qdrant_class.return_value = mock_qdrant

        with unittest.mock.patch("app.database.google.genai.Client") as mock_genai_class:
            mock_genai = unittest.mock.MagicMock()
            mock_genai.models.embed_content.side_effect = Exception("Embedding API failure")
            mock_genai_class.return_value = mock_genai

            vsm = app.database.VectorStoreManager()
            vsm.ai_client = mock_genai
            results = vsm.search_similar("query")
            assert results == []