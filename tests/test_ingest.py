"""
Tests for the scraper.ingest pipeline (run_ingestion_pipeline).
"""

import os               # Accesses environment variables for test configuration
import unittest.mock    # Provides tools for mocking and patching dependencies during tests
import scraper.ingest   # Module under test containing the run_ingestion_pipeline function and related logic


@unittest.mock.patch("scraper.ingest.app.database.VectorStoreManager")
@unittest.mock.patch("scraper.ingest.scraper.redactor.redact_pii")
@unittest.mock.patch("scraper.ingest.scraper.crawler.CouncilCrawler")
def test_run_ingestion_pipeline_success(mock_crawler_class, mock_redact, mock_vsm_class, tmp_path, monkeypatch):
    # Point backup path to a temp directory so no real disk writes occur
    monkeypatch.setattr(
        "scraper.ingest.os.path.dirname",
        lambda _: str(tmp_path)
    )

    crawler_inst = unittest.mock.MagicMock()
    crawler_inst.scrape_content.return_value = {"text": "Council tax information here."}
    mock_crawler_class.return_value = crawler_inst

    mock_redact.return_value = "Council tax information here."

    vsm_inst = unittest.mock.MagicMock()
    mock_vsm_class.return_value = vsm_inst

    scraper.ingest.run_ingestion_pipeline("[salford.gov.uk](https://www.salford.gov.uk/council-tax/)")

    mock_redact.assert_called_once_with("Council tax information here.")
    vsm_inst.upsert_document.assert_called_once()


@unittest.mock.patch("scraper.ingest.app.database.VectorStoreManager")
@unittest.mock.patch("scraper.ingest.scraper.redactor.redact_pii")
@unittest.mock.patch("scraper.ingest.scraper.crawler.CouncilCrawler")
def test_run_ingestion_pipeline_no_text(mock_crawler_class, mock_redact, mock_vsm_class):
    crawler_inst = unittest.mock.MagicMock()
    crawler_inst.scrape_content.return_value = None  # Crawler found nothing
    mock_crawler_class.return_value = crawler_inst

    vsm_inst = unittest.mock.MagicMock()
    mock_vsm_class.return_value = vsm_inst

    # Should log an error but not raise
    scraper.ingest.run_ingestion_pipeline("[salford.gov.uk](https://www.salford.gov.uk/council-tax/)")

    mock_redact.assert_not_called()
    vsm_inst.upsert_document.assert_not_called()


@unittest.mock.patch("scraper.ingest.app.database.VectorStoreManager")
@unittest.mock.patch("scraper.ingest.scraper.redactor.redact_pii")
@unittest.mock.patch("scraper.ingest.scraper.crawler.CouncilCrawler")
def test_run_ingestion_pipeline_db_error_logged(mock_crawler_class, mock_redact, mock_vsm_class, tmp_path, monkeypatch):
    monkeypatch.setattr("scraper.ingest.os.path.dirname", lambda _: str(tmp_path))

    crawler_inst = unittest.mock.MagicMock()
    crawler_inst.scrape_content.return_value = {"text": "Some content."}
    mock_crawler_class.return_value = crawler_inst

    mock_redact.return_value = "Some content."

    vsm_inst = unittest.mock.MagicMock()
    vsm_inst.upsert_document.side_effect = Exception("DB write failure")
    mock_vsm_class.return_value = vsm_inst

    # Should not raise despite DB failure
    scraper.ingest.run_ingestion_pipeline("[salford.gov.uk](https://www.salford.gov.uk/council-tax/)")