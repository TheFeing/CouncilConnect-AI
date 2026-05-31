"""
Tests for the scraper.reindex disaster recovery pipeline.
"""

import json                 # Handles JSON encoding and decoding for test data
import os                   # Accesses environment variables and file paths for test configuration
import unittest.mock        # Provides tools for mocking and patching dependencies during tests
import scraper.reindex      # Module under test containing the rebuild_index function and related logic


@unittest.mock.patch("scraper.reindex.app.database.VectorStoreManager")
def test_rebuild_index_success(mock_vsm_class, tmp_path):
    # Create a fake backup directory with two JSON files
    backup_dir = tmp_path / "knowledge_base" / "processed"
    backup_dir.mkdir(parents=True)

    for i, content in enumerate([
        {"url": "[example.gov](https://example.gov/page1)", "text": "Page one content."},
        {"url": "[example.gov](https://example.gov/page2)", "text": "Page two content."},
    ]):
        (backup_dir / f"file{i}.json").write_text(json.dumps(content), encoding="utf-8")

    vsm_inst = unittest.mock.MagicMock()
    mock_vsm_class.return_value = vsm_inst

    # Patch the path resolution so reindex finds our tmp_path
    with unittest.mock.patch("scraper.reindex.os.path.dirname", return_value=str(tmp_path)):
        scraper.reindex.rebuild_index()

    assert vsm_inst.upsert_document.call_count == 2


@unittest.mock.patch("scraper.reindex.app.database.VectorStoreManager")
def test_rebuild_index_missing_backup_path(mock_vsm_class, tmp_path):
    vsm_inst = unittest.mock.MagicMock()
    mock_vsm_class.return_value = vsm_inst

    # Point to a path that doesn't exist
    with unittest.mock.patch("scraper.reindex.os.path.dirname", return_value=str(tmp_path / "nonexistent")):
        scraper.reindex.rebuild_index()

    vsm_inst.upsert_document.assert_not_called()


@unittest.mock.patch("scraper.reindex.app.database.VectorStoreManager")
def test_rebuild_index_corrupt_json_skipped(mock_vsm_class, tmp_path):
    backup_dir = tmp_path / "knowledge_base" / "processed"
    backup_dir.mkdir(parents=True)

    # One valid file, one corrupt file
    (backup_dir / "good.json").write_text(
        json.dumps({"url": "[example.gov](https://example.gov/ok)", "text": "Good content."}), encoding="utf-8"
    )
    (backup_dir / "bad.json").write_text("{ this is not valid json }", encoding="utf-8")

    vsm_inst = unittest.mock.MagicMock()
    mock_vsm_class.return_value = vsm_inst

    with unittest.mock.patch("scraper.reindex.os.path.dirname", return_value=str(tmp_path)):
        scraper.reindex.rebuild_index()

    # Only the good file should be upserted
    assert vsm_inst.upsert_document.call_count == 1