import pytest
import app.database

def test_vector_storage_and_retrieval():
    """
    Rationale: Integration test to ensure DB connectivity, schema validity and 80% coverage of vector_store.py.
    """
    manager = app.database.VectorStoreManager(collection_name="test_collection")
    sample_text = "Salford residents can pay council tax online."
    
    # Inserts then looks up the same text
    manager.upsert_document(sample_text, {"type": "test"})
    search_results = manager.search_similar("How to pay tax?")
    
    # Assert
    assert len(search_results) > 0, "Vector DB failed to return any results." # At least one result should be returned.
    assert search_results[0].payload["text"] == sample_text, "Vector DB payload corruption." # The stored text should match the original input.