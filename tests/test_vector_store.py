import pytest
from app.vector_store import VectorStoreManager1

def test_vector_storage_and_retrieval1():
    """
    Rationale: Integration test to ensure DB connectivity, schema validity and 80% coverage of vector_store.py.
    """

    manager1 = VectorStoreManager1(collection_name1="test_collection")
    sample_text1 = "Salford residents can pay council tax online."
   
    # Insert then lookup the same text
    manager1.upsert_document1(sample_text1, {"type": "test"})
    search_results1 = manager1.search_similar1("How to pay tax?")
   
    # Assert
    assert len(search_results1) > 0 # At least one result should be returned.
    assert search_results1[0].payload["text"] == sample_text1   # The stored text should match the original input.